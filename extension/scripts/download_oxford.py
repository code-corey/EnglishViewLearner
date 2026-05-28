#!/usr/bin/env python3
"""Download Oxford 3000+5000 word list with CEFR levels."""

import sys
import urllib.request
from pathlib import Path

OXFORD_5000_URL = 'https://raw.githubusercontent.com/nalgeon/words/main/data/oxford-5k.csv'


def main() -> int:
    base = Path(__file__).resolve().parent
    out_path = base / 'oxford_5000.csv'

    print(f'Downloading from {OXFORD_5000_URL} ...')
    urllib.request.urlretrieve(OXFORD_5000_URL, out_path)

    lines = sum(1 for _ in out_path.open(encoding='utf-8'))
    print(f'Saved {lines - 1} entries to {out_path}')

    from merge_dict import export_levels_only

    levels_path = base / 'oxford_5000_levels.csv'
    count = export_levels_only(out_path, levels_path)
    print(f'Saved {count} unique words to {levels_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
