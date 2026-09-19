#!/usr/bin/env python3
"""Validate public Base/Luce consumers in native opt 0-3 and C comparison modes."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time
from compatibility.oracle import run_codecs, run_surface, run_native
from compatibility.coverage import audit

ROOT = Path(__file__).resolve().parents[1]
SUFFIX = '.exe' if os.name == 'nt' else ''


def run(command, **kwargs):
    print('RUN', ' '.join(str(arg) for arg in command), flush=True)
    # High-level bindings and optimized C compilation are slower on hosted CPUs.
    timeout = 600 if len(command) > 1 and str(command[1]) == 'build' else 180
    subprocess.run([str(arg) for arg in command], check=True, cwd=ROOT, timeout=timeout, **kwargs)


def run_ipc(binary, env):
    # Short runner-owned paths also fit Unix socket path limits on macOS.
    with tempfile.TemporaryDirectory(prefix='prism-ipc-', dir='/tmp') as temporary:
        db = Path(temporary) / 'root.db'
        sock = Path(str(db) + '.sock')
        owner = subprocess.Popen([str(binary), 'owner', str(db), str(sock)], cwd=ROOT, env=env)
        try:
            deadline = time.monotonic() + 10
            while not sock.exists():
                if owner.poll() is not None:
                    raise RuntimeError(f'IPC owner exited early: {owner.returncode}')
                if time.monotonic() >= deadline:
                    raise TimeoutError('IPC owner socket did not appear')
                time.sleep(0.02)
            run([binary, 'client', db, sock], env=env)
        finally:
            if owner.poll() is None:
                owner.terminate()
            try:
                owner.wait(timeout=5)
            except subprocess.TimeoutExpired:
                owner.kill()
                owner.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=Path(os.environ.get('LUCE_BASE_COMPILER', ROOT / f'build/toolchain/luce-base{SUFFIX}')))
    parser.add_argument('--luce', type=Path, default=Path(os.environ.get('LUCE_COMPILER', ROOT / f'build/toolchain/luce{SUFFIX}')))
    parser.add_argument('--opt', type=int, choices=range(4))
    parser.add_argument('--oracle', type=Path, help='Optional C++ oracle built against kinogaki-core')
    args = parser.parse_args()
    audit(require_complete=True)
    for compiler in (args.base, args.luce):
        if not compiler.is_file():
            parser.error(f'compiler not found: {compiler}; build the pinned sibling or pass its path')
    levels = [args.opt] if args.opt is not None else range(4)
    modes = [["--native", "--opt", str(level)] for level in levels]
    if args.opt is None:
        modes += [["--backend=c"], ["--backend=c", "--release"]]
    env = dict(os.environ, LUCE_BASE=str(args.base.resolve()))
    env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
    env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
    consumers = [
        (args.base, name + '.lucb') for name in (
            'main', 'format', 'media', 'semantics', 'authoring',
            'logic', 'editor', 'query', 'foreign', 'store', 'store_workers', 'ipc',
        )
    ] + [(args.base, '../src/luce_prism/storage_empty_tests.lucb')] + [
        (args.luce, name + '.luc') for name in (
            'consumer', 'advanced_consumer', 'editor_consumer',
        )
    ]
    with tempfile.TemporaryDirectory(prefix='luce-prism-test-') as temporary:
        scratch = Path(temporary)
        for index, flags in enumerate(modes):
            print('Testing', ' '.join(flags), flush=True)
            for compiler, source in consumers:
                binary = scratch / ('consumer' + SUFFIX)
                run([compiler.resolve(), 'build', ROOT / 'tests' / source, *flags, '-o', binary], env=env)
                if source == 'ipc.lucb':
                    run_ipc(binary, env)
                elif source == 'store.lucb':
                    store_scratch = scratch / f'store-{index}'
                    store_scratch.mkdir()
                    run([binary, store_scratch], env=env)
                else:
                    run([binary, scratch] if source in ('semantics.lucb', 'editor.lucb') else [binary], env=env)
            example = scratch / ('referenced-media' + SUFFIX)
            output = scratch / f'referenced media {index}'
            output.mkdir()
            run([args.luce.resolve(), 'build', ROOT / 'examples/referenced_media.luc', *flags, '-o', example], env=env)
            run([example, output], env=env)
            codec = scratch / ('codec' + SUFFIX)
            run([args.base.resolve(), 'build', ROOT / 'tests/codec.lucb', *flags, '-o', codec], env=env)
            run_codecs(codec, args.oracle.resolve() if args.oracle and index == 0 else None, scratch)
            run_surface(codec, args.oracle.resolve() if args.oracle and index == 0 else None, scratch)
            run_native(codec, args.oracle.resolve() if args.oracle and index == 0 else None, scratch)
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
    print('PASS requested Prism compiler modes', flush=True)


if __name__ == '__main__':
    main()
