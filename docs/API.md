# API and ownership

Import the `prism` module exported by package `luce_prism`.

## Values

`Value()`/`Value(number)` creates a float64 scalar. Static factories return owned
references: `integer(i64)`, `unsigned(u64)`, `number(f64)`, `boolean(bool)`,
`text(str)`, `array(dtype, shape, bytes)`, `numbers(shape, values, dtype=float64)`
and `strings(shape, values)`. `lerp(left, right, amount)` interpolates compatible
floating values; other dtypes/shapes hold the left value. `equals` compares dtype,
shape and payload. Factories and insertion copy caller buffers.

Shapes are `const i64[]` at the public boundary. Each dimension must fit uint32;
rank is at most 16. Numeric array payloads contain exactly product(shape) × dtype
width bytes, in row-major, little-endian order. String payloads use length-prefixed
UTF-8 records internally; use `strings` for construction.

For encoded image files or arbitrary binary content, use
`Value.array(DType.uint8, [length], payload)`. For raw pixels, use a shape such as
`[height, width, 4]`. These values work with `Encoding.text` and `Encoding.binary`,
including binary compression; retrieve the original data through `bytes()`.
Prism does not decode the embedded file or assign a color space to pixel arrays.
Callers can author MIME type, color space and other schema details as metadata.

Inspection: `dtype`, `rank`, `dimension(index)`, `count`, `bytes`, `number_at`,
`integer_at`, `unsigned_at`, and `text_at`. Component access checks bounds.
`number_at` coerces numeric components; `integer_at` requires a signed integer.
`unsigned_at` reads an integer component's raw unsigned bit pattern. Raw `bytes`
from a string Value contains length prefixes, not concatenated text.

## Documents

- `add(path, type_name, override=false)` inserts a unique exact path.
  `append` chooses a unique name; `add_child` allocates an anonymous child.
  `define(document, path, kind)` and `edit(document, path)` return stable, chainable
  handles with typed `get_*` defaults and `require_*` checked getters.
  `/` is the pseudo-root, not a stored element. Names use ASCII letters, digits
  and underscores or anonymous `[N]` segments. Type tokens and property names may
  be arbitrary text. Slots must use the path grammar's single name component.
- `set(path, name, value, type_name="")` sets the default; existing animation stays.
  The optional catalog label must match the dtype/shape when encoding text.
- `get(path, name)` returns an independent value snapshot. `contains`, `path_at`,
  `type_at`, `element_count`, `property_count`, `property_name` inspect records.
- `set_metadata`/`metadata` handle non-animatable strings. Reference arcs use
  reserved `reference` and `referencePath` metadata, also read from text directives.
  `reference` is the Store catalog key. `Session.get` / `children` / `Query` stay
  inside one identity. Cross-mount reads use `Store.lookup` / `Store.read`;
  `compose` / `compose_file` remain explicit graft. See [external media](REFERENCES.md).
- `set_sample` inserts/replaces a finite-time key. `sample_count` inspects the set;
  `resolve(path, name, time=0)` clamps to endpoints and resolves held, linear and
  Bézier keys with automatic or authored handles. `animate` creates a default
  when needed; `set_sample` requires an existing property. `set_handles`,
  `remove_sample`, and `sample_*_at` edit/inspect complete keyframe data.
  Only equal-shaped float values interpolate linearly. Other values hold.
- `connect(source, target)` validates slot paths and replaces a
  target's previous source. Forward/dangling element paths are allowed.
  Slot properties need not already exist (registered
  behavior may provide them later). `source`, `disconnect`, `connection_count`
  inspect/edit connections. `eval(slot, time=0)` reads the authored source
  property through one incoming link, following the legacy attribute evaluator.
  An absent source yields float32 zero. Use `Evaluator` for computed graphs;
  `get` and `resolve` report missing authored properties as errors.
- `rename(path, destination)` moves the subtree and rewrites concrete connections,
  assets, applicable wildcard prefixes, and layer path records. It allocates before
  committing, so allocation failure leaves the document unchanged.
- `remove(path)` removes the subtree, incident wires and owned assets. Existing
  independent values/asset snapshots remain valid. Anonymous ASCII children use
  positional names reconstructed on parsing, following the original format.
- `mark_deleted`, `mark_disconnected`, `mark_unset`, `reorder`, `connect_pattern`
  author layer records. `overlay(layer)` applies them to a new document;
  `diff(target)` produces a replayable layer. Wildcard sources resolve in authored
  order after concrete links.
- `set_asset(path, bytes, mime="application/octet-stream")`, `asset`, `asset_mime`,
  `asset_count`, `remove_asset` manage package assets. Assets may have paths whose content is
  supplied by a referenced document; local element existence is not required.
  A document with these attachments requires `Encoding.package`; plain text or
  binary encoding returns an error. Use typed properties for payloads that must
  travel through both plain text and binary crates. Legacy `diff`/merge/event-log
  records require unchanged package attachments; asset changes report
  `unsupported`. Use typed byte properties for media edited through layers.

## I/O

`detect(bytes)` sniffs content, not a filename extension. `Document.decode(bytes)`,
`parse(text)` and `load(path)` create independent documents. `encode(encoding=binary,
compressed=false)` returns an owned `Blob`. `save(path, encoding=binary,
compressed=false)` writes it. `Encoding` has `text`, `binary`, `package`, `unknown`.
`encode_package(text_scene=false, compressed=false)` also supports packages
whose scene chunk is ASCII. Compression applies to binary crates, including
the inner crate in a package.
These operations read one authored document. They preserve external reference
metadata without loading or composing the referenced files.

A `Blob` supplies `bytes`, `size`, fallible UTF-8 `text`, and `from_bytes`.
`Document.save` and the extension-aware free `save(document, path, codec=auto)`
use durable temporary-file replacement. `write_durable(path, bytes)` exposes that
primitive. Free `load(path, codec=auto)` selects foreign codecs by extension.
`decode_diagnosed(bytes, codec)` returns success or a located error, retaining a
copyable document on success. Explicit native decoding rejects unknown magic;
`Codec.auto` additionally accepts arbitrary text/blob content.

## Composition, queries and services

| API | Contract |
| --- | --- |
| `copy`, `equals`, `extract`, `instantiate`, `rename`, `move`, `renames` | Independent documents, stable element IDs, subtrees, unique destination names and move detection |
| `children`, `find`, `element_id`, `path_for_id` | Ordered topology, path patterns and identity lookup |
| `merge(base, a, b)`, `LayerStack` | Three-way conflict reporting, composed layers and compaction |
| `ReferenceLibrary`, `compose_file`, `materialize_file` | Explicit graft for export/oracle; see [references](REFERENCES.md) |
| `Store.lookup`, `Store.read`, `Store.kind`, `Store.entries` | Cross-identity `namei` and std.files-shaped helpers. `kind`/`read`/`entries` follow; `delete`/`remove_all` do not. |
| `EventLog(base)` | Commit diffs, replay `at(offset)`, read `since(offset)`, compact retained history |
| `NodeRegistry`, `Evaluator`, `compute`, `compute_slot` | Declared inputs/outputs, owned node callbacks, lazy baking, registered math and materialized output |
| `world_matrix`, `visible`, `Affine2`, `Scene` | Float32-compatible transform/visibility evaluation and independent scene snapshots |
| `ValueCache`, `DocumentCache`, `EvalKey` | Revision/time caches; owned producer results and failed-producer preservation |
| `Query(document, pattern)`, `Predicate` | Lazy selection, filters, ordering, limits, null-aware comparisons, aggregates and grouped aggregates |
| `FieldIndex`, `join_on`, `join_by_connection` | Reusable field lookup, relational joins and wire traversal |
| `TextIndex`, `SpatialIndex`, `VectorIndex` | Text search, spatial queries and metric-based nearest-neighbor results |
| `Schema`, `Violations` | Type/property requirements and validation against explicitly declared schema fields |
| `ColumnTable`, `RowMask` | Typed column snapshots, filtering, masks and aggregates |
| `Atom`, `Atoms`, `Logic`, `conclude`, `why`, `derive` | Grounded strict/defeasible rules, defeaters, priorities and proof provenance |
| `parse_surface`, `serialize_surface`, `compile_math`, `compile_logic` | Editable math/logic syntax translated to canonical Prism elements |

`Query` retains its source document and re-evaluates on demand; selected rows and
indexes own snapshots. Callback-driven queries reject source mutation during
traversal. `Evaluator` caches within a time context and retains its source and
registry. `BakeContext` is a checked callback view, not an independently owned
mutable document.

The executable [advanced Luce consumer](../tests/advanced_consumer.luc) exercises
these APIs and callback signatures without manual reference management.

## Store lookup

`Store.mount(identity)` inserts a catalog entry; `identity` is the `reference`
metadata string (1–200 bytes, ASCII `[A-Za-z0-9._-]`, not `"."` / `".."`).
`Store.lookup(path, follow=true)` walks `/` components and switches identity at a
`link` without copying elements. A missing `referencePath` is the mount root
`"/"`. Terminal `follow=false` returns `LookKind.link`; intermediate links always
hop. `Store.read` / `Store.kind` / `Store.entries` call `lookup(follow=true)` then
`Session` on that identity. `Look` is `{identity, path, kind}` with `kind` one of
`missing`, `directory`, `file`, `link`, `other`. Host names that fail `valid_name`
(including `.`) match an anonymous `[N]` child via metadata `name`.

`entries` yields `{name, path, kind}` sorted by name; `name` is `path_name` or
metadata `name`; `kind` is the followed target (no `link` member). `list` is those
names. `exists` / `is_dir` / `is_file` are kind after follow. `make_directory`
creates missing parents and is idempotent if the path is already a directory;
`Session.add` does not create parents. `delete` errors on a directory and unlinks
a terminal link. `remove_directory` requires an empty directory that is not a
link. `remove_all` is idempotent on a missing path and **does not follow** links
(the link node is removed; the target identity is left alone). There is no public
`kind_nofollow` and no `mode`. `Session.set` refuses a value larger than one
journal frame (`max_frame - 32`).

`Store.dump(dir)` writes one atomic crate per catalog identity as `dir/{identity}`.
`Store.load(dir)` installs those basenames (valid identities only) as tables.

`memory_limit` is Store-wide (default 256 MiB). RAM `Store.memory()` refuses when
resident would exceed it. Durable `Store.open` LRU-evicts unpinned published
payloads to `{dbpath}.ext` and `get`/`read` fault them back. `children` / `lookup`
/ `kind` do not fault. `Session.pin(path)` holds a subtree; pin fails rather than
evicting that working set. Layers stay pinned until bake or the view dies.

`Store.open(path, token="")` is the durable owner: it takes `{basename}.lock` using
Prism's own WAL. A nonempty `token` is required on `Store.connect`. After open,
`Store.listen()` binds `{dbpath}.sock` (unlinking a stale socket only after the
exclusive OS lock succeeds). `Store.serve()` waits while the accept loop runs. In-process workers
still borrow `Store*`. Other processes use `Store.connect(socket)` — they must not
`engine.open` the journal. IPC is length-prefixed; tokens are owner-side
`snap_id`/`tx_id`. v1 verbs: snapshot, get, children, lookup, begin, set, add,
remove, set_metadata, commit, close. Not in v1: Query, bake/checkpoint/dump from
clients, TCP.

## Codecs and editor integration

`Codec` includes `prisma`, `prism`, `json`, `markdown`, `html`, `svg`, `text`,
`blob`, and `auto`. Use free `decode(bytes, codec)` / `encode(document, codec)`;
`codec_by_name`, `codec_for_path`, and `document_lens` select conventions.
`CodecAdapter(name, encoder, decoder, whole_document=true)` owns custom callbacks.
A partial adapter rebases represented content while retaining unrepresented
roots, surviving root metadata, and applicable external wires.

`Bundle` creates an explicit `/bundle` folder, imports folders/files, preserves
original filenames, and materializes file bytes through the matching codec.
Structured documents and opaque blobs share the bundle model.

`TextProjection` retains user text and the last successfully parsed document.
`set_text` returns false and a located diagnosis for invalid edits, preserving
that document. Switching codecs restores exact prior user formatting when the
canonical representation remains unchanged. `set_adapter` installs an owned
custom lens. `amend` accepts metadata/document changes only when rendered text
stays unchanged. Mutation from an active callback is rejected; closing from a
callback takes effect when the operation unwinds.

`highlight_line` returns owned token spans with byte offsets. `AppSettings` offers
typed/defaulted values, string lists, recent-file management, explicit load, and
durable save. See the [editor Luce consumer](../tests/editor_consumer.luc).

## Lifetimes and failure

Base returned references must be released once; Base copies of a reference borrow,
they do not retain. Use `.clone()` when retaining another strong reference. A stack
`Document` needs `defer document.close()`. Public objects have standard interop
ownership, so high-level Luce performs retain/release automatically.

`get`, `resolve`, `decode`, `asset`, and `encode` return snapshots with their own
storage. Base strings/spans returned by inspection borrow the owning object's
storage and expire on mutation or close. Luce copies these projections at its
native boundary. Explicit close is idempotent; calling through a closed reference
returns the standard interop error. Objects are thread-confined by the interop
runtime; there is no internal locking or worker transfer contract.

Allocations use `memory.heap`; keep the heap allocator stable for the lifetime of
these objects. The format code propagates allocator failure and standard I/O
errors. Prism errors are `invalid`, `limit_exceeded`, `missing`, and `unsupported`.
Located parse diagnostics use one-based byte columns; successful diagnoses
report line and column zero. Ordinary fallible APIs propagate error codes.

Input/output buffers and expanded compressed data are limited to 256 MiB. Tables
and arrays of records have a 1,048,576-entry ceiling; text nesting is limited to
128 and paths to 4096 bytes. String-table expansion and decoded escaped strings
have separate 256 MiB budgets. The text parser borrows numeric tokens from the
input with one-token lookahead; image components do not consume table entries or
allocate individual token buffers. These are per-buffer/collection limits, not a
process-wide memory quota. Decode is whole-file and callers should apply their own
admission limits. Decimal text can be substantially larger than its binary payload
and must still fit the input/output buffer limit.
