from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


def _extract_report_id(report_url: str) -> str | None:
    m = re.search(r"/laporan/(\d+)", report_url)
    return m.group(1) if m else None


def _candidate_tingkat_urls(tingkat_url: str) -> list[str]:
    base = (tingkat_url or "").strip()
    if not base:
        return []
    urls = [base]
    if base.startswith("https://"):
        urls.append("http://" + base.removeprefix("https://"))
    return list(dict.fromkeys(urls))


def _candidate_report_urls(report_url: str) -> list[str]:
    base = (report_url or "").strip()
    if not base:
        return []
    urls = [base]
    if base.startswith("https://"):
        urls.append("http://" + base.removeprefix("https://"))
    return list(dict.fromkeys(urls))


async def _get_with_fallback(urls: Iterable[str], timeout: float = 20.0) -> httpx.Response:
    errors: list[str] = []
    async with httpx.AsyncClient(
        timeout=timeout,
        # Force IPv4 to avoid broken IPv6 routes in some cloud runtimes.
        transport=httpx.AsyncHTTPTransport(retries=2, local_address="0.0.0.0"),
    ) as client:
        for url in urls:
            try:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "sinabung-alert-mvp/1.0"},
                )
                resp.raise_for_status()
                return resp
            except httpx.HTTPError as e:
                errors.append(f"{url}: {type(e).__name__}")
                continue
    raise httpx.ConnectError(f"MAGMA request failed on all candidates: {', '.join(errors)}")


async def get_latest_sinabung_report_url(tingkat_url: str) -> str:
    """
    Ambil URL laporan terbaru Sinabung dari halaman 'Tingkat Aktivitas' MAGMA.
    tingkat_url contoh:
      https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas
    """
    if not tingkat_url:
        raise ValueError("tingkat_url kosong")

    resp = await _get_with_fallback(_candidate_tingkat_urls(tingkat_url), timeout=20)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Cari node teks yang mengandung "Sinabung", lalu cari link laporan di container terdekat.
    candidates = soup.find_all(string=re.compile(r"\bSinabung\b", re.IGNORECASE))
    for text_node in candidates:
        parent = getattr(text_node, "parent", None)
        if parent is None:
            continue

        container = parent.find_parent(["li", "tr", "div", "p"]) or parent
        a = container.find("a", href=re.compile(r"/v1/gunung-api/laporan/"))
        if a and a.get("href"):
            return urljoin(tingkat_url, a["href"])

    raise RuntimeError("Tidak menemukan link laporan Sinabung di halaman Tingkat Aktivitas.")


async def fetch_report_detail(report_url: str) -> dict:
    """
    Fetch halaman laporan MAGMA dan ambil ringkasan:
    - report_id
    - level (contoh: 'Level II (Waspada)')
    - title (baris ringkas)
    - rekomendasi (list beberapa baris)
    """
    if not report_url:
        raise ValueError("report_url kosong")

    resp = await _get_with_fallback(_candidate_report_urls(report_url), timeout=20)

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    # Heuristik level
    m_level = re.search(r"(Level\s+[IV]+\s*\([^)]+\))", text)
    level = m_level.group(1) if m_level else None

    # Judul ringkas (sering memuat periode)
    title_line = None
    for line in text.split("\n"):
        if "Sinabung" in line and "periode" in line:
            title_line = line
            break

    # Rekomendasi: ambil beberapa baris setelah kata 'Rekomendasi'
    rekomendasi: list[str] = []
    if "Rekomendasi" in text:
        after = text.split("Rekomendasi", 1)[1]
        for line in after.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "Copyright" in line:
                break
            rekomendasi.append(line)
            if len(rekomendasi) >= 10:
                break

    return {
        "report_url": report_url,
        "report_id": _extract_report_id(report_url),
        "level": level,
        "title": title_line,
        "rekomendasi": rekomendasi,
    }
