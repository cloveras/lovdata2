#!/usr/bin/env python3
"""
download_raw.py

Download Lovdata public datasets (laws + central regulations) into raw/tarballs/.

Usage:
    python scripts/download_raw.py
"""

import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "raw"
TARBALL_DIR = RAW_DIR / "tarballs"

LAWS_URL = "https://api.lovdata.no/v1/publicData/get/gjeldende-lover.tar.bz2"
REGS_URL = "https://api.lovdata.no/v1/publicData/get/gjeldende-sentrale-forskrifter.tar.bz2"


def download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1024 * 64):
                if chunk:
                    f.write(chunk)
    tmp.rename(dest)


def main():
    RAW_DIR.mkdir(exist_ok=True)
    TARBALL_DIR.mkdir(exist_ok=True)

    laws_path = TARBALL_DIR / "gjeldende-lover.tar.bz2"
    regs_path = TARBALL_DIR / "gjeldende-sentrale-forskrifter.tar.bz2"

    # Download or skip if already present
    if laws_path.exists():
        print(f"[skip] {laws_path} already exists")
    else:
        download(LAWS_URL, laws_path)

    if regs_path.exists():
        print(f"[skip] {regs_path} already exists")
    else:
        download(REGS_URL, regs_path)

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(1)