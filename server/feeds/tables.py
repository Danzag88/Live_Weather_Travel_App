"""HTML table helpers for gov.je / ports.je boards."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def parse_update_stamp(html: str) -> str | None:
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    patterns = [
        r"Last update received at\s+([0-9:.]+)",
        r"last updated at\s+([0-9:.]+)",
        r"This information was last updated at\s+([0-9:.]+)",
        r"last updated[:\s]+([0-9:.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    return None


def table_rows(html: str, columns: list[str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            joined = " ".join(cells).lower()
            if any(header in joined for header in ("sched", "flight no", "vessel", "status")) and (
                "td" not in {tag.name for tag in tr.find_all(True, recursive=False)}
                or tr.find("th")
            ):
                if tr.find("th") or cells[0].lower().startswith(
                    ("sched", "vessel", "time")
                ):
                    continue
            if len(cells) < len(columns):
                cells.extend([""] * (len(columns) - len(cells)))
            row = {columns[i]: cells[i] for i in range(len(columns))}
            first = list(row.values())[0]
            if not first or first.lower() in {"sched.", "sched", "vessel", "time"}:
                continue
            rows.append(row)
    return rows
