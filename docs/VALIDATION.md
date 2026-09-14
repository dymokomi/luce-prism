# Validation

Toolchain pins: Base `162ff10fce15997abe38337029069971643614b2`, Luce
`88d0e5d1847b489c0c3fb44425e8f56ee3bcc033`, and the C++ reference
`ce92a4b37887d4ebb14194ca2ba4084af657c34a`. Compiler binaries and the independently
linked C++ oracle are built in a temporary toolchain directory. No sibling
compiler or `luce-image` source is modified.

```sh
./test.sh --base /path/to/luce-base --luce /path/to/luce
# Also regenerate encodings with the independently built reference executable:
./test.sh --base /path/to/luce-base --luce /path/to/luce --oracle /path/to/oracle
# One optimization level during development:
./test.sh --base /path/to/luce-base --luce /path/to/luce --opt 0
```

## Gate and evidence

The default runner builds and executes native optimization levels 0–3,
`--backend=c`, and `--backend=c --release`. It runs Base suites, three high-level
Luce consumers, the explicit-reference media example, and codec/oracle adapters.
Builds and output files use temporary directories. The complete case inventory
must pass before compilation begins.

| Check | Scope |
| --- | --- |
| Legacy inventory | 373 applicable native cases mapped; 40 C ABI and four C++ global-interner cases retained with scope reasons |
| Foreign codecs | 70 inputs; 153 independently pinned C++ model/output comparisons per mode |
| Math/logic surface | Seven inputs; 21 pinned C++ outputs per mode, 42 checks with a fresh oracle |
| Native formats | Eight rich inputs; 32 pinned binary-model comparisons per mode, 128 cross-reader/writer checks with a fresh oracle |
| Ownership/failure | 5,748 injected allocation-failure positions across codecs, composition, queries, schema, evaluation, surfaces, projections, logs, caches and handles |
| Media | 512×512 RGBA, an actual PNG, all byte values, all uint16 values, every finite half pattern, float32/64 extrema/subnormals and signed zeros |
| Authoring | Stable IDs/handles, exact copy isolation, transactional edits and 50,000-element assembly |
| Malformed input | Every truncated prefix of representative crates/packages, corrupt counts/offsets/compression, bad syntax, invalid shapes, versions and nesting |

Format checks include all 14 dtypes, named aliases, arrays, animation, complete
Bézier handles, layer/tombstone records, concrete and wildcard connections,
reference directives, compression, package assets, and both ASCII/binary scene
chunks. Determinism tests construct the same wiring through different edit orders.
Decoded values and composed scenes are checked separately from re-encoded bytes.

Reference tests cover explicit loading, local opinions, nested references,
cycles, default targets, wildcard grafts, a diamond graph, and relative file paths.
The media example opens an ASCII document without loading its external payload,
then explicitly loads its binary sidecar. A fresh C++ composer independently
verifies the resulting inline and referenced pixels.

Callback tests exercise native and high-level producers, retained results,
expired bake views, query mutation guards, partial codec lenses, and closing
projections/caches during callback execution. Allocation tests check cleanup after
every failure and state preservation for transactional mutations.

## What the numbers mean

The inventory is a behavioral test mapping, not line/branch instrumentation.
The gate does not claim measured 100% source coverage or every possible input.
C++ ABI tests cannot certify native Luce calling conventions; the high-level
consumer programs test those boundaries directly. See
[compatibility notes](LEGACY-DIFFERENCES.md) for resource bounds and API differences.

CI uses pinned compilers on macOS, Linux and Windows. Current results are visible
on the [Actions page](https://github.com/dymokomi/luce-prism/actions). The prior
Windows UCRT64 run failed on Base's `_snprintf_l` linkage; its reproduction is in
[LUCE-BASE-ISSUES.md](LUCE-BASE-ISSUES.md). Hosted status is reported separately from
local ARM64 macOS results; a successful local gate does not certify Windows.
