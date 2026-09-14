#!/usr/bin/env python3
"""Validate public Base/Luce consumers in native opt 0-3 and C comparison modes."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SUFFIX = '.exe' if os.name == 'nt' else ''


def run(command, **kwargs):
    subprocess.run([str(arg) for arg in command], check=True, cwd=ROOT, timeout=180, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path(os.environ.get('LUCE_BASE_COMPILER', ROOT.parent / f'luce-base/build/luce-base{SUFFIX}')))
    parser.add_argument('--luce', type=Path, default=Path(os.environ.get('LUCE_COMPILER', ROOT.parent / f'luce/build/luce{SUFFIX}')))
    parser.add_argument('--opt', type=int, choices=range(4))
    parser.add_argument('--oracle', type=Path, help='Optional C++ oracle built against kinogaki-core')
    args = parser.parse_args()
    for compiler in (args.base, args.luce):
        if not compiler.is_file():
            parser.error(f'compiler not found: {compiler}; build the pinned sibling or pass its path')
    levels = [args.opt] if args.opt is not None else range(4)
    modes = [["--native", "--opt", str(level)] for level in levels]
    if args.opt is None:
        modes += [["--backend=c"], ["--backend=c", "--release"]]
    env = dict(os.environ, LUCE_BASE=str(args.base.resolve()))
    with tempfile.TemporaryDirectory(prefix='luce-prism-test-') as temporary:
        scratch = Path(temporary)
        for flags in modes:
            print('Testing', ' '.join(flags), flush=True)
            for compiler, source in [(args.base, 'main.lucb'), (args.luce, 'consumer.luc')]:
                binary = scratch / ('consumer' + SUFFIX)
                run([compiler.resolve(), 'build', ROOT / 'tests' / source, *flags, '-o', binary], env=env)
                run([binary], env=env)
        if args.oracle:
            codec = scratch / ('codec' + SUFFIX)
            run([args.base.resolve(), 'build', ROOT / 'tests/codec.lucb', '--native', '-o', codec], env=env)
            fixture = ROOT / 'tests/fixtures/core.prism'
            generated = scratch / 'generated.prism'
            run([args.oracle.resolve(), ROOT / 'tests/fixtures/core.prisma', generated, 'binary'])
            assert generated.read_bytes() == fixture.read_bytes(), 'C++ fixture provenance changed'
            for mode in ('text', 'binary', 'compressed'):
                encoded, decoded = scratch / 'encoded', scratch / 'decoded'
                run([codec, fixture, encoded, mode])
                run([args.oracle.resolve(), encoded, decoded, 'binary'])
                assert decoded.read_bytes() == fixture.read_bytes(), f'C++ rejected or changed {mode}'
                run([args.oracle.resolve(), fixture, encoded, mode])
                run([codec, encoded, decoded, 'binary'])
                assert decoded.read_bytes() == fixture.read_bytes(), f'Luce rejected or changed {mode}'
            print('PASS independent C++ cross-encoding oracle', flush=True)
    print('PASS all Prism compiler modes', flush=True)


if __name__ == '__main__':
    main()
