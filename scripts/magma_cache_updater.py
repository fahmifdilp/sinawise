from __future__ import annotations

import os
import re
import sys
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


DEFAULT_MAGMA_TINGKAT_URL = "https://magma.esdm.go.id/v1/gunung-api/tingkat-aktivitas"


def _extract_report_id(report_url: str) -> str | None:
    m = re.search(r"/laporan/(\d+)", report_url)
    return m.group(1) if m else None


def _extract_radius_km(rekomendasi: list[str]) -> list[str]:
    results: list[str] = []
    for line in rekomendasi or []:
        for m in re.finditer(
            r"radius(?:\s+(radial|sektoral))?\s+(\d+(?:[.,]\d+)?)\s*km",
            line,
            flags=re.I,
        ):
            tipe = (m.group(1) or "").lower()
            km = m.group(2).replace(",", ".")
            if tipe:
                results.append(f"Radius {km} km ({tipe})")
            else:
                results.append(f"Radius {km} km")
    seen: set[str] = set()
    uniq: list[str] = []
    for item in results:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    return uniq


def _get_latest_report_url(tingkat_url: str) -> str:
    with httpx.Client(timeout=30) as client:
        r = client.get(tingkat_url, headers={"User-Agent": "sinabung-alert-mvp/1.0"})
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    candidates = soup.find_all(string=re.compile(r"\bSinabung\b", re.IGNORECASE))
    for text_node in candidates:
        parent = getattr(text_node, "parent", None)
        if parent is None:
            continue
        container = parent.find_parent(["li", "tr", "div", "p"]) or parent
        a = container.find("a", href=re.compile(r"/v1/gunung-api/laporan/"))
        if a and a.get("href"):
            return urljoin(tingkat_url, a["href"])

    raise RuntimeError("Link laporan Sinabung tidak ditemukan di halaman tingkat aktivitas.")


def _fetch_detail(report_url: str) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.get(report_url, headers={"User-Agent": "sinabung-alert-mvp/1.0"})
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    m_level = re.search(r"(Level\s+[IV]+\s*\([^)]+\))", text)
    level = m_level.group(1) if m_level else None

    title = None
    for line in text.split("\n"):
        if "Sinabung" in line and "periode" in line.lower():
            title = line
            break

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
        "title": title,
        "rekomendasi": rekomendasi,
        "radius_info": _extract_radius_km(rekomendasi),
    }


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} wajib diisi.")
    return value


def main() -> int:
    backend_url = _require_env("BACKEND_URL").rstrip("/")
    admin_username = _require_env("ADMIN_USERNAME")
    admin_password = _require_env("ADMIN_PASSWORD")
    tingkat_url = (os.getenv("MAGMA_TINGKAT_URL") or DEFAULT_MAGMA_TINGKAT_URL).strip()

    report_url = _get_latest_report_url(tingkat_url)
    detail = _fetch_detail(report_url)

    with httpx.Client(timeout=30) as client:
        login_resp = client.post(
            f"{backend_url}/admin/login",
            json={"username": admin_username, "password": admin_password},
        )
        login_resp.raise_for_status()
        token = login_resp.json()["token"]

        payload = {
            "level": detail.get("level"),
            "report_id": detail.get("report_id"),
            "report_url": detail.get("report_url"),
            "title": detail.get("title"),
            "rekomendasi": detail.get("rekomendasi") or [],
            "radius_info": detail.get("radius_info") or [],
        }
        set_resp = client.post(
            f"{backend_url}/admin/magma/cache",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        set_resp.raise_for_status()

    print("MAGMA cache updated.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
