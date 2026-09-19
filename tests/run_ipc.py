#!/usr/bin/env python3
"""Focused six-mode IPC regression; the complete suite also runs these tests."""
import os
from pathlib import Path
import subprocess
from run import ROOT, run_ipc

base = ROOT / 'build/toolchain/luce-base'
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
modes = [(f'native{i}', ['--native', '--opt', str(i)]) for i in range(4)]
modes += [('c', ['--backend=c']), ('c-release', ['--backend=c', '--release'])]
for mode, flags in modes:
    binary = ROOT / 'build' / f'ipc-{mode}'
    subprocess.run([str(base), 'build', str(ROOT / 'tests/ipc.lucb'), *flags,
                    '-o', str(binary)], cwd=ROOT, env=env, check=True, timeout=600)
    run_ipc(binary, env)
    print(f'PASS IPC {mode}', flush=True)
