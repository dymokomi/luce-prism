# Compatibility and API differences

Prism v4 crate/package bytes and legacy text syntax are the interchange contract.
The independent oracle is pinned in `bootstrap/KINOGAKI_CORE`. The package preserves
the legacy model and services through native Luce APIs; it does not export the
C++ classes, global token table, or C ABI.

## Native API and ownership

- Public objects use ordinary Luce ownership / Base `interop.Reference`, not raw
  C handles or caller-sized output arrays. Unsigned 64-bit APIs remain available
  to Base; Luce preserves these values through their bytes and serialization.
- `Value.number` and `Value()` construct float64. Request `DType.float32` explicitly
  for float32 arrays or use a declared `float` property. Legacy geometry performs
  float32 arithmetic behind public float64 coordinate carriers.
- Copies have independent value semantics and preserve element IDs, but currently
  allocate eagerly. No O(1) C++ copy-on-write or shared global interner is claimed.
- Custom codecs are owned `CodecAdapter` objects installed on a projection. The
  package does not expose a mutable process-wide C++ codec singleton/registry.
- `Bundle` uses an explicit `/bundle` element for its root. File import/materialize
  APIs operate on that document; filesystem traversal belongs to the caller.
- References load only through explicit composition or I/O calls. Opening or
  parsing a document never fetches its external files.
- Package assets live with `Document`. Unified decoding retains them. Plain
  text/crate encoding rejects an asset-bearing document instead of losing the
  sidecar; typed byte properties are the representation for inline ASCII data.
- Immutable results are owned; string/byte views in Base borrow their owner.
  Mutating source documents inside active query callbacks is rejected. Callback
  contexts expire after baking. Closing a projection/cache from its callback is
  deferred until that operation unwinds.

## Accepted input and fidelity

- Text versions 1–4 and binary/package version 4 are supported. Unsupported
  versions, malformed UTF-8 strings, bad paths, duplicate records, unreasonable
  counts/ranks, overlapping blobs and corrupt compression are errors. The old
  reader accepted some malformed inputs that this implementation rejects.
- Input/output buffers and expansion are bounded at 256 MiB; nesting at 128,
  rank at 16, paths at 4096 bytes, and record collections at 1,048,576 entries.
  These are documented resource bounds, not an unbounded-file compatibility claim.
- JSON rejects lone Unicode surrogates; valid surrogate pairs decode correctly.
  XML entities handle full Unicode scalar values. Historical acceptance or
  truncation of invalid text is not reproduced.
- ASCII uses legacy role spellings and tuples, catalog labels, reference
  directives, and relative consumer connections. Equivalent whitespace or
  quoting can differ. Signed zero and full-precision time/handle doubles are
  retained, improving on the old text writer's rounding.
- Float32/64 non-finite payloads normalize to zero during serialization, matching
  the reference policy. Binary float16 retains its bit pattern; text cannot
  preserve float16 NaN payloads. Boolean bytes should be canonical 0/1.
- Sparse documents without explicit ancestors remain supported in binary.
  ASCII refuses to drop orphan elements. Anonymous text children are positional
  and acquire canonical `[N]` names on parsing, as in the C++ implementation.
- Non-ASCII byte characters and keyframes with varying declared dtype/fixed
  shape require binary. Dynamic legacy float/int/float2 array samples may change
  length; their ASCII spelling remains an array even at tuple-sized lengths.
  Use `uint8` for arbitrary bytes that must travel through
  ASCII. The legacy text writer can emit some declarations its own parser cannot
  read (notably general bool arrays); Luce supports those bool arrays.

## Service corrections

Wildcard link precedence follows insertion order; concrete connections take
priority. Attribute `eval` reads one incoming source and defaults to float32 zero when
absent, matching C++; computed graphs use `Evaluator`. Float interpolation, held
values, Bézier handles, explicit reference
composition, layer operations and defeasible proof outcomes are tested against
the legacy cases. Malformed surface syntax fails transactionally rather than
returning a silently truncated document.

Duplicate math/logic builder names use one consistent unique root for all
properties and children. A recent-file cap of zero returns no entries. Spatial
queries reject non-finite inputs and negative radii; distance ties use stable
source order. These cases avoid accidental corruption or undefined behavior in
the old implementation.

The [inventory](../tests/compatibility/inventory.json) and
[validation guide](VALIDATION.md) state exactly which tests run. No claim of
100% measured line/branch coverage, thread-safe shared mutation, GPU execution,
or identical performance is implied by passing the behavioral suite.
