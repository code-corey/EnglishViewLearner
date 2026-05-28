#!/usr/bin/env python3
"""Merge CC-CEDICT and Oxford 5000 into graded_dict.json for NeonLingo."""

import csv
import json
import re
import sys
from pathlib import Path

LEVEL_INDEX = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
VALID_LEVELS = set(LEVEL_INDEX)


def clean_en(gloss: str) -> str:
    g = gloss.split('CL:')[0].split(';')[0].strip()
    g = re.sub(r'\s*\([^)]*\)', '', g).strip()
    g = g.split(',')[0].strip().lower()
    return g


def parse_cedict(path: Path) -> dict[str, list[str]]:
    """Parse CC-CEDICT simplified Chinese → list of English glosses."""
    ch_to_ens: dict[str, list[str]] = {}
    pattern = re.compile(r'^(\S+)\s+(\S+)\s+\[.*?\]\s+/(.+?)/')

    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            match = pattern.match(line)
            if not match:
                continue
            ch = match.group(2)
            en = clean_en(match.group(3))
            if ch and en and re.search(r'[\u4e00-\u9fff]', ch):
                bucket = ch_to_ens.setdefault(ch, [])
                if en not in bucket:
                    bucket.append(en)

    return ch_to_ens


def pick_en(candidates: list[str], en_to_level: dict[str, str]) -> str | None:
    """Prefer an Oxford-listed gloss; tie-break by lowest CEFR level then length."""
    in_oxford = [e for e in candidates if e in en_to_level]
    if in_oxford:
        return min(in_oxford, key=lambda e: (LEVEL_INDEX[en_to_level[e]], len(e)))
    return candidates[0] if candidates else None


def parse_oxford(path: Path) -> dict[str, str]:
    """Parse Oxford 5000 CSV (word, level, ...). Duplicate words keep lowest CEFR level."""
    en_to_level: dict[str, str] = {}

    with path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        if 'word' not in (reader.fieldnames or []) or 'level' not in (reader.fieldnames or []):
            f.seek(0)
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 2:
                    continue
                word, level = row[0].strip().lower(), row[1].strip().upper()
                _set_level(en_to_level, word, level)
            return en_to_level

        for row in reader:
            word = (row.get('word') or '').strip().lower()
            level = (row.get('level') or '').strip().upper()
            _set_level(en_to_level, word, level)

    return en_to_level


def _set_level(en_to_level: dict[str, str], word: str, level: str) -> None:
    if not word or level not in VALID_LEVELS:
        return
    existing = en_to_level.get(word)
    if existing is None or LEVEL_INDEX[level] < LEVEL_INDEX[existing]:
        en_to_level[word] = level


def export_levels_only(oxford_path: Path, out_path: Path) -> int:
    """Write deduplicated word,level CSV from full Oxford file."""
    en_to_level = parse_oxford(oxford_path)
    with out_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'level'])
        for word in sorted(en_to_level):
            writer.writerow([word, en_to_level[word]])
    return len(en_to_level)


def merge(ch_to_ens: dict[str, list[str]], en_to_level: dict[str, str]) -> dict:
    final: dict = {}
    for ch, candidates in ch_to_ens.items():
        en = pick_en(candidates, en_to_level)
        if not en:
            continue
        level = en_to_level.get(en, 'C1')
        if level == 'C2':
            continue
        final[ch] = {'en': en, 'level': level}
    return final


def main() -> int:
    base = Path(__file__).resolve().parent
    cedict_path = base / 'cedict_ts.u8'
    oxford_path = base / 'oxford_5000.csv'
    levels_path = base / 'oxford_5000_levels.csv'
    out_path = base.parent / 'dict' / 'graded_dict.json'

    if not oxford_path.exists():
        print(f'Missing {oxford_path}', file=sys.stderr)
        print('Run: python download_oxford.py', file=sys.stderr)
        return 1

    count = export_levels_only(oxford_path, levels_path)
    print(f'Wrote {count} unique words to {levels_path}')

    if not cedict_path.exists():
        print(f'Missing {cedict_path}', file=sys.stderr)
        print('Download from https://www.mdbg.net/chinese/dictionary?page=cedict', file=sys.stderr)
        return 1

    ch_to_ens = parse_cedict(cedict_path)
    en_to_level = parse_oxford(oxford_path)
    final = merge(ch_to_ens, en_to_level)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f'Wrote {len(final)} entries to {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
