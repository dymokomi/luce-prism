"""Differential tests against independently compiled kinogaki-core, not golden self-output."""
import json
import hashlib
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def run_native(native, oracle, scratch):
    """Both encodings must reconstruct independently pinned C++ model bytes."""
    comparisons = 0
    for case in json.loads((HERE / 'native.json').read_text(encoding='utf-8')):
        source = scratch / 'native-corpus-source'
        source.write_text(case['source'], encoding='utf-8')
        for writer in ([native, oracle] if oracle else [native]):
            for mode in ('text', 'binary', 'compressed', 'package-empty'):
                encoded = scratch / 'native-corpus-encoded'
                subprocess.run([str(writer), str(source), str(encoded), mode], check=True, timeout=30)
                for reader in ([native, oracle] if oracle else [native]):
                    decoded = scratch / 'native-corpus-decoded'
                    subprocess.run([str(reader), str(encoded), str(decoded), 'binary'], check=True, timeout=30)
                    assert hashlib.sha256(decoded.read_bytes()).hexdigest() == case['cpp_prism_sha256'], (case['name'], mode, writer, reader, 'model differs from pinned C++')
                    comparisons += 1
    print(f'PASS {comparisons} pinned C++ native-format cross-encoding comparisons', flush=True)


def run_surface(native, oracle, scratch):
    comparisons = 0
    for case in json.loads((HERE / 'surface.json').read_text(encoding='utf-8')):
        source = scratch / 'surface-source'
        source.write_text(case['source'], encoding='utf-8')
        for program in ([native, oracle] if oracle else [native]):
            document, destination = scratch / 'surface-doc', scratch / 'surface-output'
            subprocess.run([str(program), str(source), str(document), 'parse-surface'], check=True, timeout=30)
            for mode, expected in case['cpp_sha256'].items():
                if mode == 'parse-surface':
                    data = document.read_bytes()
                else:
                    subprocess.run([str(program), str(document), str(destination), mode], check=True, timeout=30)
                    data = destination.read_bytes()
                assert hashlib.sha256(data).hexdigest() == expected, (case['name'], mode, program, 'differs from pinned C++')
                comparisons += 1
    print(f'PASS {comparisons} pinned C++ surface, math, and logic output comparisons', flush=True)


def run_codecs(native, oracle, scratch):
    cases = json.loads((HERE / 'codecs.json').read_text(encoding='utf-8'))
    comparisons = 0
    for index, case in enumerate(cases):
        context = f'{case["name"]} [{index}]'
        source = scratch / 'foreign-source'
        source.write_bytes(bytes.fromhex(case['source_hex']) if 'source_hex' in case else case['source'].encode())
        documents = [scratch / 'native-doc']
        programs = [native]
        if oracle is not None:
            programs.append(oracle)
            documents.append(scratch / 'oracle-doc')
        for program, document in zip(programs, documents):
            result = subprocess.run([str(program), str(source), str(document), 'decode-' + case['codec']], capture_output=True, timeout=30)
            if case.get('reject'):
                assert result.returncode == 1, (context, program, result.returncode, result.stderr)
            else:
                assert result.returncode == 0, (context, program, result.returncode, result.stderr)
        if case.get('reject'):
            continue
        for document in documents:
            model = document.read_bytes()
            digest = hashlib.sha256(model).hexdigest()
            assert digest == case['cpp_prism_sha256'], (
                context, 'decoded Prism differs from pinned C++',
                f'expected={case["cpp_prism_sha256"]}', f'actual={digest}',
                f'bytes={model.hex()}',
            )
        comparisons += 1
        outputs = [case['codec']]
        if case['codec'] in ('markdown', 'html'):
            outputs = ['markdown', 'html']
        for codec in outputs:
            rendered = [scratch / 'native-render', scratch / 'oracle-render']
            for program, document, destination in zip(programs, documents, rendered):
                subprocess.run([str(program), str(document), str(destination), 'encode-' + codec], check=True, timeout=30)
            for destination in rendered[:len(programs)]:
                assert hashlib.sha256(destination.read_bytes()).hexdigest() == case['cpp_encoded_sha256'][codec], (context, codec, 'rendered bytes differ from pinned C++', destination.read_bytes())
            comparisons += 1
            if (codec == case['codec'] and case.get('stable', True)) or case.get('shared_model'):
                restored = scratch / 'restored'
                subprocess.run([str(native), str(rendered[0]), str(restored), 'decode-' + codec], check=True, timeout=30)
                assert restored.read_bytes() == documents[0].read_bytes(), (context, codec, 'model changed after re-import')
    print(f'PASS {len(cases)} foreign codec fixtures, {comparisons} pinned C++ model/output comparisons' + (' and a fresh C++ oracle' if oracle else ''), flush=True)
