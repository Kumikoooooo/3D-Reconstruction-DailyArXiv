import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from zoneinfo import ZoneInfo

from utils import (
    generate_table,
    get_daily_date,
    get_daily_papers_by_keyword_with_retries,
)


REPO_URL = "https://github.com/Kumikoooooo/3D-Reconstruction-DailyArXiv"
BEIJING_TIMEZONE = ZoneInfo("Asia/Shanghai")

KEYWORDS: List[str] = [
    "3D reconstruction",
    "三维重建",
    "multi-view stereo",
    "structure from motion",
    "surface reconstruction",
    "neural rendering",
    "novel view synthesis",
    "3D Gaussian Splatting",
    "3DGS",
    "Gaussian Splatting",
    "Gaussian rasterization",
    "Gaussian surface reconstruction",
    "Gaussian pruning",
    "Gaussian compression",
    "Gaussian density control",
    "Gaussian importance",
    "Gaussian uncertainty",
    "feed-forward 3D reconstruction",
    "feed-forward Gaussian Splatting",
    "pose-free 3D reconstruction",
    "sparse-view Gaussian Splatting",
    "large-scale Gaussian Splatting",
    "outdoor Gaussian Splatting",
    "dynamic Gaussian Splatting",
    "Gaussian Splatting SLAM",
    "relightable Gaussian Splatting",
    "semantic Gaussian Splatting",
    "Gaussian Splatting editing",
    "active view selection",
    "thermal 3D reconstruction",
    "infrared Gaussian Splatting",
]

COLUMN_NAMES = ["Title", "Link", "Abstract", "Date", "Comment"]


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if not value:
        return default
    return float(value)


def get_keywords() -> List[str]:
    raw_keywords = os.environ.get("ARXIV_KEYWORDS")
    if not raw_keywords:
        return KEYWORDS
    return [keyword.strip() for keyword in raw_keywords.split(";") if keyword.strip()]


def keyword_link(keyword: str) -> str:
    return "AND" if len(keyword.split()) == 1 else "OR"


def build_sections(max_result: int, issues_result: int, sleep_seconds: float) -> Dict[str, Dict[str, str]]:
    sections: Dict[str, Dict[str, str]] = {}
    for keyword in get_keywords():
        print(f'Fetching papers for keyword: "{keyword}"')
        papers = get_daily_papers_by_keyword_with_retries(
            keyword,
            COLUMN_NAMES,
            max_result,
            keyword_link(keyword),
        )
        sections[keyword] = {
            "readme": generate_table(papers),
            "issue": generate_table(papers[:issues_result], ignore_keys=["Abstract"]),
        }
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return sections


def build_readme(current_date: str, sections: Dict[str, Dict[str, str]]) -> str:
    lines = [
        "# 3D Reconstruction Daily Papers",
        "",
        "The project automatically fetches the latest arXiv papers for 3D reconstruction and 3D Gaussian Splatting keywords.",
        "",
        "The subheadings represent the search keywords. For each keyword, the table keeps the most recently updated arXiv records returned by the API.",
        "",
        "Click the repository's Watch button to receive notifications from the daily issue workflow.",
        "",
        f"Last update: {current_date}",
        "",
    ]
    for keyword, tables in sections.items():
        lines.extend([f"## {keyword}", tables["readme"], ""])
    return "\n".join(lines).rstrip() + "\n"


def build_issue_body(issues_result: int, sections: Dict[str, Dict[str, str]]) -> str:
    lines = [
        f"# Latest {issues_result} Papers - {get_daily_date()}",
        "",
        f"Please check the [GitHub repository]({REPO_URL}) for a better reading experience and more papers.",
        "",
    ]
    for keyword, tables in sections.items():
        lines.extend([f"## {keyword}", tables["issue"], ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    current_date = datetime.now(BEIJING_TIMEZONE).strftime("%Y-%m-%d")
    max_result = env_int("ARXIV_MAX_RESULT", 100)
    issues_result = env_int("ARXIV_ISSUES_RESULT", 15)
    sleep_seconds = env_float("ARXIV_SLEEP_SECONDS", 5.0)

    sections = build_sections(max_result, issues_result, sleep_seconds)
    Path("README.md").write_text(build_readme(current_date, sections), encoding="utf-8")
    Path(".github").mkdir(exist_ok=True)
    Path(".github/ISSUE_TEMPLATE.md").write_text(
        build_issue_body(issues_result, sections),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
