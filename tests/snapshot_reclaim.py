#!/usr/bin/env python3
"""Regression for copied existence-check leaks at snapshot format transitions."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import heap_process

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode', choices=['native0', 'all', 'sanitize'], default='all')
parser.add_argument('--heap', action='store_true', help='Require macOS leaks to report zero leaks')
args = parser.parse_args()
if args.heap and sys.platform != 'darwin': parser.error('--heap requires macOS')
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
out = ROOT / 'build/snapshot-reclaim'
out.mkdir(parents=True, exist_ok=True)
base = ROOT / 'build/toolchain/luce-base'
source = ROOT / 'tests/snapshot_reclaim.lucb'
modes = [(f'native{i}', ['--native', '--opt', str(i)]) for i in range(4)]
modes += [('c', ['--backend=c']), ('c-release', ['--backend=c', '--release'])]
if args.mode == 'native0': modes = modes[:1]
if args.mode == 'sanitize': modes = [('sanitize', [])]

def run(command):
    print('RUN', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), env=env, cwd=ROOT, check=True, timeout=600)

for name, flags in modes:
    binary = out / name
    if name == 'sanitize':
        generated = out / 'sanitize.c'
        runtime = ROOT.parent / 'luce-base/runtime'
        run([base, 'build', source, '--emit=c', '-o', generated])
        run([os.environ.get('CC', 'cc'), '-std=gnu11', '-O1', '-g', '-w', '-fno-strict-aliasing',
             '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', runtime,
             generated, runtime / 'lucb_rt.c', '-pthread', '-lm', '-o', binary])
        env['ASAN_OPTIONS'] = 'halt_on_error=1:abort_on_error=1'
        env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
    else:
        run([base, 'build', source, *flags, '-o', binary])
    with tempfile.TemporaryDirectory(prefix='snapshot-reclaim-', dir='/tmp') as temporary:
        for phase in ('write', 'read'):
            run([binary, Path(temporary) / 'store', phase])
        if args.heap:
            for phase in ('write', 'read'):
                result = heap_process.run(['/usr/bin/leaks', '--atExit', '--', binary,
                                           Path(temporary) / 'heap-store', phase], env=env, timeout=180)
                print(result.stdout, end='', flush=True)
                print(result.stderr, end='', file=sys.stderr, flush=True)
                result.check_returncode()
                assert 'PASS snapshot reclaim and unbaked reopen' in result.stdout
                assert '0 leaks for 0 total leaked bytes' in result.stdout + result.stderr
    print(f'PASS snapshot reclaim {name}', flush=True)
