#!/usr/bin/env python3
"""Focused export ownership gate: six modes, macOS leaks, and ASan/UBSan."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'build/toolchain/luce-base'
source = ROOT / 'src/luce_prism/table_export_tests.lucb'
output = ROOT / 'build/table-export-tests'
output.mkdir(parents=True, exist_ok=True)
runtime = ROOT.parent / 'luce-base/runtime'
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
env['ASAN_OPTIONS'] = 'halt_on_error=1:abort_on_error=1'
env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'

def run(command):
    subprocess.run(list(map(str, command)), cwd=ROOT, env=env, check=True, timeout=600)

modes = [(f'native{i}', ['--native', '--opt', str(i)]) for i in range(4)]
modes += [('c', ['--backend=c']), ('c-release', ['--backend=c', '--release'])]
for name, flags in modes:
    binary = output / name
    run([base, 'build', source, *flags, '-o', binary])
    run([binary])
    if sys.platform == 'darwin':
        run(['/usr/bin/leaks', '--quiet', '--noContent', '--atExit', '--', binary])
    print(f'PASS table export {name}', flush=True)
generated = output / 'sanitize.c'
run([base, 'build', source, '--emit=c', '-o', generated])
run([os.environ.get('CC', 'cc'), '-std=gnu11', '-O1', '-g', '-w', '-fno-strict-aliasing',
     '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', runtime,
     generated, runtime / 'lucb_rt.c', '-pthread', '-lm', '-o', output / 'sanitize'])
run([output / 'sanitize'])
print('PASS table export ASan/UBSan (Linux includes leak detection)', flush=True)
