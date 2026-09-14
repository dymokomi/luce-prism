# API and ownership

Import the `prism` module exported by package `luce_prism`.

## Values

`Value()`/`Value(number)` creates a float64 scalar. Static factories return owned
references: `integer(i64)`, `unsigned(u64)`, `number(f64)`, `boolean(bool)`,
`text(str)`, `array(dtype, shape, bytes)`, `numbers(shape, values, dtype=float64)`
and `strings(shape, values)`. Factories and insertion copy caller buffers.

Shapes are `const i64[]` at the public boundary. Each dimension must fit uint32;
rank is at most 16. Numeric array payloads contain exactly product(shape) × dtype
width bytes, in row-major, little-endian order. String payloads use length-prefixed
UTF-8 records internally; use `strings` for construction.

Inspection: `dtype`, `rank`, `dimension(index)`, `count`, `bytes`, `number_at`,
`integer_at`, `unsigned_at`, and `text_at`. Component access checks bounds.
`number_at` coerces numeric components; `integer_at` requires a signed integer.
`unsigned_at` reads an integer component's raw unsigned bit pattern. Raw `bytes`
from a string Value contains length prefixes, not concatenated text.

## Documents

- `add(path, type_name, override=false)` adds an element after its parent.
  `/` is the pseudo-root, not a stored element. Names use ASCII letters, digits
  and underscores or anonymous `[N]` segments. Type tokens and property names may
  be arbitrary text. Slots must use the path grammar's single name component.
- `set(path, name, value, type_name="")` sets the default; existing animation stays.
  The optional catalog label must match the dtype/shape when encoding text.
- `get(path, name)` returns an independent value snapshot. `contains`, `path_at`,
  `type_at`, `element_count`, `property_count`, `property_name` inspect records.
- `set_metadata`/`metadata` handle non-animatable strings. Reference arcs use
  reserved `reference` and `referencePath` metadata, also read from text directives.
- `set_sample` inserts/replaces a finite-time key. `sample_count` inspects the set;
  `resolve(path, name, time=0)` clamps to endpoints and resolves held/linear keys.
  Only equal-shaped float values interpolate linearly. Other values hold.
- `connect(source, target)` requires existing endpoint elements and replaces a
  target's previous source. Slot properties need not already exist (registered
  behavior may provide them later). `source`, `disconnect`, `connection_count`
  inspect/edit connections. `eval(slot, time=0)` follows concrete connections and
  resolves the final authored property. Missing properties and cycles error.
- `rename(path, destination)` moves the subtree and rewrites concrete connections,
  assets, applicable wildcard prefixes, and layer path records. It allocates before
  committing, so allocation failure leaves the document unchanged.
- `remove(path)` removes the subtree, incident wires and owned assets. Existing
  independent values/asset snapshots remain valid. Sparse anonymous identities may
  require binary encoding after edits; they are never silently renumbered.
- `mark_deleted`, `mark_disconnected`, `mark_unset`, `reorder`, `connect_pattern`
  author layer records. These methods do not execute composition or expand patterns.
- `set_asset(path, bytes, mime="application/octet-stream")`, `asset`, `asset_mime`,
  `asset_count` manage package assets. Assets may have paths whose content is
  supplied by a referenced document; local element existence is not required.

## I/O

`detect(bytes)` sniffs content, not a filename extension. `Document.decode(bytes)`,
`parse(text)` and `load(path)` create independent documents. `encode(encoding=binary,
compressed=false)` returns an owned `Blob`. `save(path, encoding=binary,
compressed=false)` writes it. `Encoding` has `text`, `binary`, `package`, `unknown`.
Compression applies to binary crates, including the inner crate in a package.

A `Blob` supplies `bytes`, `size` and fallible UTF-8 `text`. `save` is an ordinary
create/truncate/write operation, **not atomic replacement or durable sync**. Use a
caller-managed temporary file and the standard filesystem publication operations
when an editor needs those guarantees.

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
Error strings are static; source line/column diagnostics are a future API.

Input/output buffers and expanded compressed data are limited to 256 MiB. Tables
and arrays of records have a 1,048,576-entry ceiling; text nesting is limited to
128 and paths to 4096 bytes. String-table expansion and token memory have separate
256 MiB budgets. These are per-buffer/collection limits, not a process-wide memory
quota. Decode is whole-file and callers should apply their own admission limits.
