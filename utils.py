import html
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, Iterable, List, Sequence
from zoneinfo import ZoneInfo


ARXIV_API_URL = "https://export.arxiv.org/api/query"
DEFAULT_FIELDS = ("ti", "abs")
DEFAULT_TAG_PREFIXES = ("cs", "eess", "stat")


def remove_duplicated_spaces(text: str) -> str:
    return " ".join((text or "").split())


def get_daily_date() -> str:
    beijing_timezone = ZoneInfo("Asia/Shanghai")
    today = datetime.now(beijing_timezone)
    return today.strftime("%B %d, %Y")


def build_search_query(
    keyword: str,
    fields: Sequence[str] = DEFAULT_FIELDS,
    link: str = "OR",
) -> str:
    link = link.upper()
    if link not in {"OR", "AND"}:
        raise ValueError("link should be 'OR' or 'AND'")

    phrase = f'"{keyword.strip()}"'
    return f"+{link}+".join(f"{field}:{phrase}" for field in fields)


def request_papers_with_arxiv_api(
    keyword: str,
    max_results: int,
    link: str = "OR",
    timeout: int = 30,
) -> List[Dict[str, object]]:
    import feedparser

    query = build_search_query(keyword, link=link)
    params = {
        "search_query": query,
        "max_results": str(max_results),
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "3D-Reconstruction-DailyArXiv/1.0 (GitHub Actions)",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        feed = feedparser.parse(response.read())

    papers: List[Dict[str, object]] = []
    for entry in feed.entries:
        papers.append(
            {
                "Title": remove_duplicated_spaces(entry.get("title", "").replace("\n", " ")),
                "Abstract": remove_duplicated_spaces(entry.get("summary", "").replace("\n", " ")),
                "Authors": [
                    remove_duplicated_spaces(author.get("name", "").replace("\n", " "))
                    for author in entry.get("authors", [])
                ],
                "Link": remove_duplicated_spaces(entry.get("link", "").replace("\n", " ")),
                "Tags": [
                    remove_duplicated_spaces(tag.get("term", "").replace("\n", " "))
                    for tag in entry.get("tags", [])
                ],
                "Comment": remove_duplicated_spaces(
                    entry.get("arxiv_comment", "").replace("\n", " ")
                ),
                "Date": entry.get("updated", entry.get("published", "")),
            }
        )
    return papers


def filter_tags(
    papers: Iterable[Dict[str, object]],
    target_prefixes: Sequence[str] = DEFAULT_TAG_PREFIXES,
) -> List[Dict[str, object]]:
    prefixes = tuple(target_prefixes)
    results: List[Dict[str, object]] = []
    for paper in papers:
        tags = paper.get("Tags", [])
        if any(str(tag).split(".")[0] in prefixes for tag in tags):
            results.append(paper)
    return results


def select_columns(
    papers: Iterable[Dict[str, object]],
    column_names: Sequence[str],
) -> List[Dict[str, object]]:
    return [{column_name: paper.get(column_name, "") for column_name in column_names} for paper in papers]


def get_daily_papers_by_keyword(
    keyword: str,
    column_names: Sequence[str],
    max_result: int,
    link: str = "OR",
    target_prefixes: Sequence[str] = DEFAULT_TAG_PREFIXES,
) -> List[Dict[str, object]]:
    papers = request_papers_with_arxiv_api(keyword, max_result, link)
    papers = filter_tags(papers, target_prefixes)
    papers = deduplicate_papers(papers)
    return select_columns(papers, column_names)


def get_daily_papers_by_keyword_with_retries(
    keyword: str,
    column_names: Sequence[str],
    max_result: int,
    link: str = "OR",
    retries: int = 3,
    retry_delay: int = 60,
    target_prefixes: Sequence[str] = DEFAULT_TAG_PREFIXES,
) -> List[Dict[str, object]]:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            papers = get_daily_papers_by_keyword(
                keyword,
                column_names,
                max_result,
                link,
                target_prefixes,
            )
            if not papers:
                print(f'No papers found for keyword: "{keyword}"')
            return papers
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt == retries:
                break
            print(f'arXiv request failed for "{keyword}" on attempt {attempt}: {exc}')
            time.sleep(retry_delay)

    raise RuntimeError(f'Failed to query arXiv for "{keyword}" after {retries} attempts') from last_error


def deduplicate_papers(papers: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    seen = set()
    results: List[Dict[str, object]] = []
    for paper in papers:
        key = paper.get("Link") or paper.get("Title")
        if not key or key in seen:
            continue
        seen.add(key)
        results.append(paper)
    return results


def markdown_cell(value: object) -> str:
    text = html.escape(str(value or ""), quote=False)
    text = text.replace("|", "&#124;")
    return remove_duplicated_spaces(text)


def format_date(value: object) -> str:
    text = str(value or "")
    if not text:
        return ""
    if "T" in text:
        return text.split("T", 1)[0]
    try:
        return parsedate_to_datetime(text).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return text[:10]


def generate_table(
    papers: Sequence[Dict[str, object]],
    ignore_keys: Sequence[str] = (),
) -> str:
    if not papers:
        return "_No papers found for this keyword._"

    formatted_papers: List[Dict[str, str]] = []
    keys = list(papers[0].keys())
    for paper in papers:
        formatted_paper: Dict[str, str] = {}
        title = markdown_cell(paper.get("Title", "Untitled"))
        link = markdown_cell(paper.get("Link", ""))
        formatted_paper["Title"] = f"**[{title}]({link})**" if link else f"**{title}**"
        formatted_paper["Date"] = format_date(paper.get("Date", ""))

        for key in keys:
            if key in {"Title", "Link", "Date"} or key in ignore_keys:
                continue
            value = paper.get(key, "")
            if key == "Abstract":
                formatted_paper[key] = (
                    f"<details><summary>Show</summary><p>{markdown_cell(value)}</p></details>"
                )
            elif key == "Authors":
                authors = list(value) if isinstance(value, list) else []
                formatted_paper[key] = markdown_cell(f"{authors[0]} et al." if authors else "")
            elif key == "Tags":
                tags = ", ".join(value) if isinstance(value, list) else str(value)
                formatted_paper[key] = markdown_cell(tags)
            elif key == "Comment":
                formatted_paper[key] = markdown_cell(value)
            else:
                formatted_paper[key] = markdown_cell(value)
        formatted_papers.append(formatted_paper)

    columns = list(formatted_papers[0].keys())
    header = "| " + " | ".join(f"**{column}**" for column in columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = ["| " + " | ".join(paper[column] for column in columns) + " |" for paper in formatted_papers]
    return "\n".join([header, divider, *body])
