# Prism v4 storage contract

The original specification and executable reference are kinogaki-core's
`include/kinogaki/Serialize.h`, `src/SerializeCommon.h`, `src/SerializeBinary.cpp`,
`src/SerializePackage.cpp`, `src/Compress.cpp`, and `src/TextParser.cpp` at the
revision in `bootstrap/KINOGAKI_CORE`.

## Encodings

| Convention | Magic | Reader/writer |
| --- | --- | --- |
| `.prisma` authored text | `#prisma <version>` | Reads headers 1.0–4.0, writes 4.0 |
| `.prism` binary crate | `PRSMC` + NUL | Version 4, little-endian |
| `.prism` asset package | `PRSMZ` + NUL | Version 4, little-endian |

Magic, not the filename, selects decoding. The text syntax uses nested
`def`/`over` elements, typed property assignments, `string` metadata,
`.timeSamples`, `reference`, `connect`, `unset`, `delete`, `disconnect`, and
`reorder`. A string Value is `str`; `string` is metadata. Canonical content is
independent of whitespace and of the writer's choice of legacy role spelling.

## Values

Wire dtype codes must never be reordered:

| Code | Type | Width |
| --- | --- | --- |
| 0, 1 | bool, char | 1 byte |
| 2, 3, 4, 5 | int8, int16, int32, int64 | 1, 2, 4, 8 bytes |
| 6, 7, 8, 9 | uint8, uint16, uint32, uint64 | 1, 2, 4, 8 bytes |
| 10, 11 | float32, float64 | 4, 8 bytes |
| 12 | str | u32 byte length + UTF-8 bytes per component |
| 13 | float16 | 2-byte IEEE binary16 pattern |

A value is `u8 dtype`, `u8 rank`, `u32 dimensions[rank]`, then its row-major
payload. Rank zero is one scalar; a zero dimension gives no components. The
float16 code was appended to preserve the existing codes. Catalog aliases label
existing dtype/shape combinations; they do not introduce new wire dtypes.

### Images and binary content in text mode

Raw pixels and encoded files are ordinary typed values in both encodings. For
example, a red RGBA pixel is `uint8[1,1,4] pixels = [[[255, 0, 0, 255]]]`, and
opaque bytes can be written as `uint8[4] payload = [0, 255, 128, 10]`. The binary
crate stores those same four component bytes after the type and shape. No base64,
string escaping or image codec is involved. A PNG file stored as `uint8[N]` keeps
its entire encoded file, including headers and compressed image bytes.

"ASCII mode" refers to the numeric text representation; `.prisma` itself permits
UTF-8 strings and metadata. Numeric payload bytes are never interpreted as UTF-8.
Text files expand the numeric payload and remain subject to the 256 MiB buffer
limit. Numeric tokens are consumed with one-token lookahead, avoiding a separate
allocation or record entry for each component and comma.

Legacy package assets are distinct wire records in `PRSMZ`. This port retains
that format: `set_asset` requires package encoding. Typed byte properties provide
embedded binary content in plain `.prisma` text and `PRSMC` binary crates.

## Crates and packages

A crate begins with 6 magic bytes, `u16 version`, `u16 flags`, then a deterministic
string table, ordered elements/properties/metadata, connections, deletion and
disconnection records. Property records include named aliases and complete
keyframes (time, value, interpolation, handle kind and paired handles). Each
element includes its override flag and property/metadata tombstones. Optional
trailing tag 1 stores reorders; tag 2 stores wildcard links.

Flag bit 0 compresses the body. Compression starts with a u64 expanded length,
followed by groups of up to eight tokens with LSB-first flag bits. A zero bit
means a literal byte; a one bit means `u16(distance-1), u8(length-4)`.
Back-references can overlap. The encoder chooses valid matches with a fixed-size
hash index; the C++ encoder may choose different matches with its hash chains.

A package starts with magic, version, reserved zero flags, and a u32 entry count.
Each TOC entry contains a length-prefixed name, u8 kind (text scene 0, binary scene
1, asset 2), a length-prefixed MIME string, and u64 absolute offset and size.
Entries are sorted by name; payloads are concatenated. The scene is named `scene`.
Asset names are owning element paths. Exactly one scene is required; nested
package scenes, unknown entry kinds, duplicate names and overlapping blobs fail.

## Compatibility caveats

Finite values in the checked-in fixture have byte-identical v4 crates across
Luce and C++. Float32/64 non-finites normalize to zero when encoding, as in the
legacy writer. Binary float16 payload bits are retained, including NaNs; text
normalizes non-finite values, so bitwise identity is not promised for those values.
Boolean values should use canonical 0/1 bytes.

The writer uses the legacy role spellings (`float`, `float2`, `matrix`,
`float2[]`, etc.) when applicable, general dtype/shape syntax otherwise, and
preserves explicit catalog labels. Both representations are accepted on input.
Unlike the old text formatter, signed zero is retained and key times/handles
retain full double precision. The legacy C++ text parser has some asymmetries: for example its
`bool` legacy-type branch rejects general boolean array declarations emitted by
its own writer. Binary interchange covers that case; the new parser supports it.
Quoted animated property names and unusual sparse/anonymous documents also need
care when interchanging with the historical text implementation. No new magic,
dtype code or incompatible format version was invented for this port.
