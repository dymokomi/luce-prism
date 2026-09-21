#!/usr/bin/env python3
"""Audit named legacy cases against executable Luce tests and C++ codec fixtures."""
import argparse
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# Kept in the inventory, but not claimed as native Luce test coverage. These
# assert a C calling convention or an implementation-specific global singleton.
EXTERNAL_SUITES = {
    'tests/c_api_test.cpp': 'C ABI ownership, pointer and buffer contracts; Luce exposes owned interop objects instead.',
    'tests/c_api_coverage_test.cpp': 'C ABI entry points; equivalent format operations are covered by the native suites.',
    'tests/interner_test.cpp': 'C++ global string-interner implementation; native documents own their strings.',
}


def audit(update=False, require_complete=False):
    path = HERE / 'inventory.json'
    inventory = json.loads(path.read_text(encoding='utf-8'))
    implementations = {}
    for source in sorted(HERE.glob('*.lucb')):
        text = source.read_text(encoding='utf-8')
        names = set(re.findall(r'^func ([A-Za-z_][A-Za-z0-9_]*)\(', text, re.M))
        names.update(re.findall(r'Case\("([A-Za-z_][A-Za-z0-9_]*)"', text))
        for name in names:
            # Function bodies must be invoked; declarations by themselves are not coverage.
            if f'Case("{name}"' not in text and len(re.findall(r'\b' + re.escape(name) + r'\(', text)) < 2:
                continue
            implementations.setdefault(name, []).append(f'{source.relative_to(ROOT)}::{name}')
    for source in sorted(HERE.glob('*.json')):
        if source.name == 'inventory.json':
            continue
        fixtures = json.loads(source.read_text(encoding='utf-8'))
        if not isinstance(fixtures, list):
            continue
        for fixture in fixtures:
            if 'name' in fixture and ('cpp_prism_sha256' in fixture or fixture.get('reject')):
                evidence = f'{source.relative_to(ROOT)}::{fixture["name"]}'
                bucket = implementations.setdefault(fixture['name'], [])
                if evidence not in bucket:
                    bucket.append(evidence)
    covered = total = excluded = 0
    pending = []
    for suite in inventory['suites']:
        for case in suite['cases']:
            if suite['source'] in EXTERNAL_SUITES:
                excluded += 1
                if update:
                    case['scope'] = EXTERNAL_SUITES[suite['source']]
                continue
            total += 1
            evidence = implementations.get(case['name'])
            if evidence:
                covered += 1
            else:
                pending.append((suite['source'], case['name']))
            if update:
                case['luce_test'] = evidence
            elif case['luce_test'] != evidence:
                raise AssertionError(f'Stale inventory mapping: {case["name"]}; run coverage.py --update')
    if update:
        path.write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'Legacy compatibility inventory: {covered}/{total} native cases mapped; {len(pending)} pending; {excluded} C ABI/interner cases outside the native API (retained in inventory).', flush=True)
    if require_complete and pending:
        for suite, name in pending:
            print(f'PENDING {suite}: {name}')
        raise SystemExit(1)
    return covered, total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    audit(args.update, args.require_complete)
