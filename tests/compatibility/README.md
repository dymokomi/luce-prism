# Legacy behavioral compatibility tests

`inventory.json` records all 417 named tests from kinogaki-core at
`bootstrap/KINOGAKI_CORE`. `coverage.py` maps called native test functions and
independent fixtures to their original names. It fails for a stale mapping or
unmapped native case. It is a case inventory, not a line/branch coverage tool.

The 373 applicable native cases cover the format, composition, evaluation,
codecs, editor services, queries, indexes, schema and logic. Forty C ABI cases
and four C++ global-interner cases remain listed with explicit scope reasons;
the package exports owned Luce objects instead of those interfaces.

The `.lucb` suites are imported by `tests/format.lucb`, `semantics.lucb`,
`authoring.lucb`, `logic.lucb`, `editor.lucb`, `query.lucb`, and `foreign.lucb`.
High-level consumers exercise the public bridge and callbacks. Every gate
builds and runs these sources in the requested compiler modes.

`codecs.json`, `surface.json`, and `native.json` carry input data and SHA-256
hashes generated with independently compiled C++ code. `oracle.py` checks the
native outputs against these hashes. With `--oracle`, it also reruns C++ and
exchanges newly generated files in both directions. Native-format comparisons
canonicalize through uncompressed binary, permitting equivalent ASCII spelling
and valid alternative LZSS match choices. Do not regenerate hashes from Luce.

```sh
python3 tests/compatibility/coverage.py --require-complete
./test.sh --base /path/to/luce-base --luce /path/to/luce --oracle /path/to/oracle
```

The C++ adapter is `tests/oracle.cpp`. Build it against the exact pinned
kinogaki-core headers and static library. C++ is optional for normal builds and
CI because provenance hashes and source fixtures are checked in.

Allocation tests replace the heap with a counting/failing allocator, enumerate
every allocation position in representative operations, and require zero live
allocations after success or failure. They also verify that transactional edits
leave the prior state intact. This covers failures beyond ordinary round trips.
