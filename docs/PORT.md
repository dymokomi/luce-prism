# Package architecture and reference scope

The compatibility reference is kinogaki-core commit
`ce92a4b37887d4ebb14194ca2ba4084af657c34a`, pinned in
`bootstrap/KINOGAKI_CORE`. This is a native implementation; no C++ library is linked
into applications. Import `prism` from the `luce_prism` package in Base or Luce.

| Modules under `src/luce_prism` | Responsibility |
| --- | --- |
| `prism.lucb` | Public types and functions; no parser or codec implementation |
| `types`, `storage`, `value`, `animation`, `path`, `pattern` | Wire types, bounded owned buffers, arrays, interpolation, paths and patterns |
| `model`, `document`, `comparison`, `collections/` | Indexed element identity/topology, mutation, snapshots and content equality |
| `serialization/` | Binary crates, ASCII syntax, catalog types, compression, packages and located errors |
| `authoring/` | Unique names, paths, durable handles, extraction, instantiation and moves |
| `composition/` | Overlay, diff, merge, layer compaction, explicit references, event-log replay |
| `codecs/` | JSON, Markdown, HTML, SVG, text/blob, bundles, custom adapters and diagnostics |
| `evaluation/` | Node registration, owned callbacks, bake contexts, graph evaluation and caches |
| `geometry/`, `scene` | Legacy float32 affine transforms, visibility and evaluated scene snapshots |
| `query/`, `indexes/` | Predicates, lazy queries, aggregation, groups, joins, field/text/spatial/vector indexes |
| `schema`, `columnar` | Authored schemas, violations, typed columns and row masks |
| `logic/`, `surface/` | Facts, grounded rules, priorities, defeasible proofs, math/logic surface syntax |
| `editor/`, `io` | Text projections, codec view restoration, highlighting, settings and durable file replacement |

The authored document remains the persistence boundary. Callbacks, derived
indexes, UI objects and GPU resources are not serialized. Generic values do not
require content-specific renderer objects. Codecs translate domain conventions
into the same element/property model.

`Document.copy()` currently copies owned storage eagerly. Element/path/ID and
parent lookup use hash indexes; ordered children preserve document order. Binary
string-table construction and some field scans remain linear. The port does not
claim the C++ implementation's global interning, O(1) copy-on-write snapshots,
memory mapping, or concurrent access contract. Those are implementation choices,
not new wire features. Public objects follow Luce interop ownership.

Ordinary loading does not resolve references. An explicit `ReferenceLibrary.compose`
or `compose_file` request performs composition. In-memory libraries allow a host
to control exactly which documents are available, with no implicit filesystem I/O.

[The compatibility inventory](../tests/compatibility/inventory.json) retains all
417 named tests from the pinned reference. Its native gate covers 373 cases. The
40 C ABI tests and four C++ global-interner tests are separately scoped with
reasons, rather than reported as native passes. See [validation](VALIDATION.md)
and [behavioral/API differences](LEGACY-DIFFERENCES.md).
