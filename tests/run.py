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
        for index, flags in enumerate(modes):
            print('Testing', ' '.join(flags), flush=True)
            for compiler, source in [(args.base, 'main.lucb'), (args.base, 'media.lucb'), (args.luce, 'consumer.luc')]:
                binary = scratch / ('consumer' + SUFFIX)
                run([compiler.resolve(), 'build', ROOT / 'tests' / source, *flags, '-o', binary], env=env)
                run([binary], env=env)
            example = scratch / ('referenced-media' + SUFFIX)
            output = scratch / f'referenced media {index}'
            output.mkdir()
            run([args.luce.resolve(), 'build', ROOT / 'examples/referenced_media.luc', *flags, '-o', example], env=env)
            run([example, output], env=env)
        if args.oracle:
            codec = scratch / ('codec' + SUFFIX)
            run([args.base.resolve(), 'build', ROOT / 'tests/codec.lucb', '--native', '-o', codec], env=env)
            fixture = ROOT / 'tests/fixtures/core.prism'
            generated = scratch / 'generated.prism'
            run([args.oracle.resolve(), ROOT / 'tests/fixtures/core.prisma', generated, 'binary'])
            assert generated.read_bytes() == fixture.read_bytes(), 'C++ fixture provenance changed'
            media_text, media_binary = scratch / 'media.prisma', scratch / 'media.prism'
            png = (ROOT / 'tests/fixtures/rgba.png').read_bytes()
            media_text.write_text(
                '#prisma 4.0\ndef image "image" {\n'
                'uint8[2,2,4] pixels = [[[255,0,0,255],[0,255,0,128]],[[0,0,255,64],[255,255,255,0]]]\n'
                f'uint8[{len(png)}] png = [{",".join(map(str, png))}]\n'
                f'uint8[256] opaque = [{",".join(map(str, range(256)))}]\n'
                'string mime = "image/png"\n}\n', encoding='ascii')
            run([args.oracle.resolve(), media_text, media_binary, 'binary'])
            run([codec, media_text, generated, 'binary'])
            assert generated.read_bytes() == media_binary.read_bytes(), 'C++ and Luce image bytes differ'
            for source in (fixture, media_binary):
                for mode in ('text', 'binary', 'compressed'):
                    encoded, decoded = scratch / 'encoded', scratch / 'decoded'
                    run([codec, source, encoded, mode])
                    run([args.oracle.resolve(), encoded, decoded, 'binary'])
                    assert decoded.read_bytes() == source.read_bytes(), f'C++ rejected or changed {source.name}: {mode}'
                    run([args.oracle.resolve(), source, encoded, mode])
                    run([codec, encoded, decoded, 'binary'])
                    assert decoded.read_bytes() == source.read_bytes(), f'Luce rejected or changed {source.name}: {mode}'
            print('PASS independent C++ cross-encoding oracle, including pixels and embedded PNG bytes', flush=True)
            composed, expected = scratch / 'composed.prism', scratch / 'expected.prism'
            expected_text = scratch / 'expected.prisma'
            expected_text.write_text(
                '#prisma 4.0\ndef document "page" { def image "hero" {\n'
                'uint8[1,1,4] preview = [[[255,0,0,255]]]\n'
                'uint8[1,2,4] pixels = [[[255,0,0,255],[0,255,0,128]]]\n'
                'uint8[5] payload = [0,255,128,34,10]\n'
                '} }\n', encoding='ascii')
            run([args.oracle.resolve(), output / 'page.prisma', composed, 'compose'])
            run([codec, expected_text, expected, 'binary'])
            assert composed.read_bytes() == expected.read_bytes(), 'C++ reference composition changed the media'
            print('PASS C++ resolves the authored ASCII reference to the external binary payload', flush=True)
    print('PASS all Prism compiler modes', flush=True)


if __name__ == '__main__':
    main()
