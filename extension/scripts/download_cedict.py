#!/usr/bin/env python3
"""Download CC-CEDICT from MDBG and save as cedict_ts.u8."""

import gzip
import sys
import urllib.request
from pathlib import Path

CEDICT_GZ_URL = (
    'https://www.mdbg.net/chinese/export/cedict/'
    'cedict_1_0_ts_utf-8_mdbg.txt.gz'
)


def main() -> int:
    base = Path(__file__).resolve().parent
    out_path = base / 'cedict_ts.u8'

    print(f'Downloading {CEDICT_GZ_URL} ...')
    with urllib.request.urlopen(CEDICT_GZ_URL, timeout=120) as resp:
        data = gzip.decompress(resp.read())

    out_path.write_bytes(data)
    lines = sum(1 for _ in out_path.open(encoding='utf-8'))
    print(f'Saved {lines} lines ({out_path.stat().st_size // 1024} KB) to {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
