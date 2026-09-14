# Port boundary and architecture

The reference is kinogaki-core commit
`ce92a4b37887d4ebb14194ca2ba4084af657c34a`. Its `CANONICAL.md` describes four strata:
format-independent storage; bundle/filesystem conventions; shared content schemas;
foreign-format codecs. The Luce port starts at storage, preserving the wire format.
The charter's document/image/vector/scene vocabularies are content conventions,
not special cases in a `Value` or `Document` implementation.

| C++ area | luce-prism status |
| --- | --- |
| `Path`, named and anonymous `[N]` identity | Implemented; absolute paths and slot paths, boundary-aware subtree edits |
| `Value`, all 14 dtype codes, rank 0–16 | Implemented; float16/32/64, signed and unsigned integers, byte characters, booleans and UTF-8 strings |
| `Element`, properties and metadata | Implemented; ordered elements, sorted property/metadata names, copied value ownership |
| `TimeSamples` | Authored keys and handles preserved; held and floating linear resolution implemented; Bézier evaluation deferred |
| Concrete connections | Stored, rewritten on subtree edits, chain evaluation with cycle errors |
| Binary `PRSMC` v4 | Reader/writer, string table, property aliases, all layer records and tagged trailing sections |
| LZSS compression | Compatible encoder/decoder; output size bounded; encoder uses a fixed hash table |
| Text `#prisma` | Reads version headers 1.0–4.0; writes 4.0; general shapes, legacy roles, catalog aliases and layer syntax |
| `PRSMZ` packages and `AssetStore` | Reader/writer; byte-preserving assets, MIME types, overlap/duplicate checks |
| Overrides, unset/delete/disconnect, reorder, glob links | Authored data preserved; application/expansion of these opinions deferred |
| `Compose`, references, overlay, diff, merge | Reference arcs preserved as metadata; composition, resolver, overlay/diff/merge execution deferred |
| NodeRegistry, Evaluate, Compute, Logic, EvalCache | Registered behavior, graph execution and caching deferred; `eval` only resolves concrete property chains |
| Schema, Query, Search, PathPattern | Schema validation, indexed queries and wildcard expansion deferred |
| Columnar, Spatial, Scene, Transform, Surface | Derived views and domain mathematics deferred |
| JSON/Markdown/HTML/SVG/text/blob codecs | Deferred; no dependency on another agent's `luce-image` implementation |
| Bundle filesystem import/export, AppSettings, EventLog, TextProjection, Highlight | Deferred consumers/services |
| C ABI | Not ported; use ordinary Base imports and Luce interop |

The document remains the authored source of truth. No GPU handles, image-library
objects, UI references, executable callbacks or compiler internals are serialized.
`Value.array` is the initial bridge for external buffers: it copies a typed,
shaped little-endian payload. A future zero-copy or mapped-storage interface needs
an explicit lifetime and immutability contract; this port does not imply one.

## Deliberate differences

- Connected-value cycles produce an error. The old evaluator sometimes substituted
  defaults; applications should not mistake a cycle for a successfully evaluated value.
- Decode rejects unknown flags, duplicate records and trailing compressed bytes.
  Some corresponding legacy paths were permissive. Rejection never drops unknown data.
- Noncanonical/sparse anonymous indices, missing explicit ancestors, varying sample
  dtypes/shapes and non-ASCII byte characters can be retained in binary. Text encoding
  reports a limitation when it cannot preserve their meaning.
- Public shape arguments use `i64[]` for Luce interoperability and are validated
  into uint32 storage. Unsigned 64-bit scalar access is currently a Base API; Luce
  can preserve such values and their raw bytes without converting them to `int`.
- Stored UTF-8 strings are validated on decode. Numeric/asset payloads remain bytes.
- Package decode keeps assets on `Document`. Encoding an asset-bearing document as
  plain text/binary errors, so callers cannot silently lose package contents.

## Next work

1. Composition/resolver and overlay execution, with independent C++ semantic fixtures.
2. Complete animation evaluation and an authored handle-editing API.
3. Shared content schemas and a `luce-image` adapter, coordinated with that package's API.
4. Indexed lookup, mapped buffers and streaming I/O based on real document workloads.
5. Query/compute and editor integrations driven by consumers.

Current record lookup and string interning use linear scans. The implementation is
an initial compatibility foundation, not a claim of the C++ core's performance or
its complete feature set. Threading and GPU work should enter through separate
services after profiling, rather than being embedded into persistence.
