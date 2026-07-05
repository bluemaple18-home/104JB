import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader


class ImportStatus(StrEnum):
    READY = "ready"
    NEEDS_FALLBACK = "needs_fallback"


@dataclass(frozen=True)
class ImportResult:
    status: ImportStatus
    text: str = ""
    raw_path: Path | None = None
    sha256: str = ""
    fallbacks: list[str] | None = None


class SourceImporter:
    def __init__(self, source_dir: Path, fetch: Callable[[str], httpx.Response] | None = None) -> None:
        self.source_dir = source_dir
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.fetch = fetch or (lambda url: httpx.get(url, follow_redirects=True, timeout=15))

    def _save(self, content: bytes, suffix: str) -> tuple[Path, str]:
        digest = hashlib.sha256(content).hexdigest()
        path = self.source_dir / f"{digest}{suffix}"
        path.write_bytes(content)
        return path, digest

    def from_html(self, html: str, *, source_ref: str) -> ImportResult:
        path, digest = self._save(html.encode(), ".html")
        text = "\n".join(BeautifulSoup(html, "html.parser").stripped_strings)
        return ImportResult(ImportStatus.READY, text, path, digest, [])

    def from_url(self, url: str) -> ImportResult:
        try:
            response = self.fetch(url)
        except httpx.HTTPError:
            return ImportResult(ImportStatus.NEEDS_FALLBACK, fallbacks=["pdf", "text"])
        if response.status_code != 200:
            return ImportResult(ImportStatus.NEEDS_FALLBACK, fallbacks=["pdf", "text"])
        return self.from_html(response.text, source_ref=url)

    def from_text(self, text: str) -> ImportResult:
        path, digest = self._save(text.encode(), ".txt")
        return ImportResult(ImportStatus.READY, text, path, digest, [])

    def from_pdf(self, path: Path) -> ImportResult:
        raw, digest = self._save(path.read_bytes(), ".pdf")
        text = "\n".join(page.extract_text() or "" for page in PdfReader(raw).pages)
        return ImportResult(ImportStatus.READY, text, raw, digest, [])
