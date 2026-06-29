from pathlib import Path

import main
import utils


def test_empty_keyword_results_do_not_crash():
    table = utils.generate_table([])

    assert "No papers found" in table


def test_main_generates_markdown_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    def fake_fetch(keyword, column_names, max_result, link):
        if keyword == "3D reconstruction":
            return [
                {
                    "Title": "Example Paper",
                    "Link": "https://arxiv.org/abs/0000.00000",
                    "Abstract": "Example abstract",
                    "Date": "2026-06-29T00:00:00Z",
                    "Comment": "",
                }
            ]
        return []

    monkeypatch.setattr(main, "get_keywords", lambda: ["3D reconstruction", "3DGS"])
    monkeypatch.setattr(main, "get_daily_papers_by_keyword_with_retries", fake_fetch)
    monkeypatch.setenv("ARXIV_SLEEP_SECONDS", "0")

    main.main()

    readme = Path("README.md").read_text(encoding="utf-8")
    issue = Path(".github/ISSUE_TEMPLATE.md").read_text(encoding="utf-8")

    assert "# 3D Reconstruction Daily Papers" in readme
    assert "Example Paper" in readme
    assert "_No papers found for this keyword._" in readme
    assert "Latest 15 Papers" in issue
