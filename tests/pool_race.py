#!/usr/bin/env python3
"""Stress concurrent identity bakes against the shared pool under ASan/UBSan."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'build/toolchain/luce-base'
source = ROOT / 'tests/store_workers.lucb'
output = ROOT / 'build/pool-race'
output.mkdir(parents=True, exist_ok=True)
runtime = ROOT.parent / 'luce-base/runtime'
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
env['ASAN_OPTIONS'] = 'halt_on_error=1:abort_on_error=1'
env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'


def run(command, timeout=600):
    subprocess.run(list(map(str, command)), cwd=ROOT, env=env, check=True, timeout=timeout)


generated = output / 'sanitize.c'
binary = output / 'sanitize'
run([base, 'build', source, '--emit=c', '-o', generated])
run([os.environ.get('CC', 'cc'), '-std=gnu11', '-O1', '-g', '-w', '-fno-strict-aliasing',
     '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', runtime,
     generated, runtime / 'lucb_rt.c', '-pthread', '-lm', '-o', binary])
for attempt in range(64):
    with tempfile.TemporaryDirectory(prefix='prism-pool-race-') as temporary:
        run([binary, temporary], timeout=60)
print('PASS shared pool race: 64 ASan/UBSan runs, 256 workers, 2048 cross-identity bakes')
