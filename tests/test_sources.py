from pathlib import Path

import httpx

from resume_os.sources import ImportStatus, SourceImporter


def test_url_failure_returns_pdf_and_text_fallback(tmp_path: Path) -> None:
    def fail(_: str) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    result = SourceImporter(tmp_path, fetch=fail).from_url("https://example.invalid/resume")
    assert result.status == ImportStatus.NEEDS_FALLBACK
    assert result.fallbacks == ["pdf", "text"]


def test_url_transport_error_returns_pdf_and_text_fallback(tmp_path: Path) -> None:
    def fail(_: str) -> httpx.Response:
        raise httpx.ConnectError("offline")

    result = SourceImporter(tmp_path, fetch=fail).from_url("https://example.invalid/resume")
    assert result.status == ImportStatus.NEEDS_FALLBACK
    assert result.fallbacks == ["pdf", "text"]


def test_html_import_keeps_original_and_extracts_visible_text(tmp_path: Path) -> None:
    html = "<html><body><main><h1>王小明</h1><p>專案經理</p></main></body></html>"
    result = SourceImporter(tmp_path).from_html(html, source_ref="fixture")
    assert "王小明" in result.text
    assert result.raw_path is not None
    assert result.raw_path.read_text("utf-8") == html
    assert len(result.sha256) == 64


def test_text_import_keeps_original(tmp_path: Path) -> None:
    result = SourceImporter(tmp_path).from_text("產品經理\n負責需求與驗收")

    assert result.raw_path is not None
    assert result.raw_path.read_text("utf-8") == "產品經理\n負責需求與驗收"
    assert result.status == ImportStatus.READY
