#!/usr/bin/env python3
"""Bounded listener shutdown regression in every supported compiler mode."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'build/toolchain/luce-base'
env = dict(os.environ)
env.setdefault('LUCE_STD', str(ROOT.parent / 'luce-base/src/std'))
env.setdefault('LUCE_CACHE', str(ROOT / 'build/cache'))
modes = [(f'native{i}', ['--native', '--opt', str(i)]) for i in range(4)]
modes += [('c', ['--backend=c']), ('c-release', ['--backend=c', '--release'])]
for mode, flags in modes:
    binary = ROOT / 'build' / f'listener-close-{mode}'
    subprocess.run([str(base), 'build', str(ROOT / 'tests/listener_close.lucb'),
                    *flags, '-o', str(binary)], env=env, cwd=ROOT, check=True, timeout=600)
    with tempfile.TemporaryDirectory(prefix='prism-close-', dir='/tmp') as scratch:
        path = Path(scratch) / 'store.db'
        subprocess.run([str(binary), str(path)], env=env, check=True, timeout=10)
        assert not Path(str(path) + '.sock').exists(), 'listener socket was not removed'
    print(f'PASS listener shutdown {mode}', flush=True)
