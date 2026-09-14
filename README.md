# luce-prism

Prism's native data container, written in **Luce Base** and usable from **Luce**.
A document holds path-addressed elements, typed multidimensional values, metadata,
animation and connections. Documents, images, vectors, scenes and bundles can share
this substrate without the container depending on their renderers or codecs.

This first port implements the format/storage layer of
`kinogaki-core`, including v4 `.prism`
crates, legacy LZSS compression, `.prisma` text and asset packages. The C++ core is
a compatibility oracle for tests; it is **not a runtime or build dependency**.
See [the feature map](docs/PORT.md) for the boundary of this initial implementation.

```toml
# Your application's luce.toml
[dependencies]
luce_prism = "../luce-prism"
```

```luce
from prism import Document, Value, DType, Encoding

pub func main(arguments: list[str]) -> int!:
    let document = Document()
    document.add("/world", "group")
    document.add("/world/object", "object")
    document.set("/world/object", "name", Value.text("Example"))
    document.set("/world/object", "position",
                 Value.numbers([3], [1.0, 2.0, 3.0], DType.float32))
    document.save("example.prism", Encoding.binary, true)
    let loaded = Document.load("example.prism")
    print(loaded.get("/world/object", "name").text_at())
    return 0
```

The dependency exports `prism`. Shapes are row-major; an empty shape denotes a
scalar and a zero dimension denotes an empty array. Dimensions are checked against
the format's uint32 range. `Value.array` accepts little-endian numeric payloads;
`Value.numbers` and `Value.strings` provide convenient typed construction.

`Document.set` copies its input, and `get`/`resolve` return independent values.
Luce manages the public objects automatically. Base callers explicitly `release`
returned references and `close` directly constructed documents. See
[API and ownership](docs/API.md) and [format details](docs/FORMAT.md).

Images and opaque binary data can be embedded in **either binary or ASCII text
mode** as typed properties. Use `uint8[height,width,channels]` for byte pixels or
`uint8[length]` for an encoded PNG, JPEG or any other byte buffer. For example,
inside a Luce function:

```luce
let document = Document()
document.add("/image", "image")
let pixels = b"\xff\x00\x00\xff\x00\xff\x00\x80"
document.set("/image", "pixels", Value.array(DType.uint8, [1, 2, 4], pixels))
document.save("image.prisma", Encoding.text)
document.save("image.prism", Encoding.binary, true)
```

Text uses decimal arrays; binary stores the payload bytes. Both preserve all 256
byte values exactly, including NUL and bytes that are not valid UTF-8. Typed
`uint16` and `float16`/`float32` arrays support higher-precision pixels. See the
[floating-point caveats](docs/FORMAT.md#compatibility-caveats) for non-finite values.
The separate `set_asset` API uses legacy package attachments and requires
`Encoding.package`.

An ASCII document can also refer to another `.prism` file while retaining inline
data of its own:

```prisma
#prisma 4.0
def image "hero" {
    uint8[1,1,4] preview = [[[255, 0, 0, 255]]]
    reference "media.prism" "/image"
}
```

Here the preview is embedded in the ASCII file, and `/image` in `media.prism` can
hold the full pixels or other binary content. The reference is retained across
encodings. Current `load`/`parse` read the authored document; callers explicitly
load external files when needed. See [external media](docs/REFERENCES.md) and the
[tested Luce example](examples/referenced_media.luc) for writing and reading both
files together.

```sh
./test.sh
# Or select already-built compilers without changing sibling checkouts:
./test.sh --base /path/to/luce-base --luce /path/to/luce
```

Build sibling compilers at the commits in `bootstrap/BASE` and `bootstrap/LUCE`.
The gate runs Base and Luce consumers at native optimization levels 0–3 and both
C comparison modes. It includes checked-in C++ fixtures, compressed and package
round trips, malformed input, path edits and injected allocation failures. Builds
and test outputs use temporary directories. Media tests compare payload bytes for
a 512×512 RGBA image, an embedded PNG, 16-bit channels and finite floating-point
arrays in every encoding. See [validation](docs/VALIDATION.md).

This package has no GPU, threading, UI or foreign-format dependencies. Image
codecs belong in `luce-image`; content schemas and adapters can target Prism's typed
properties. Composition execution, query engines, registered node evaluation and
foreign codecs remain future work. Bézier keys and handles round-trip; evaluating
a Bézier interval currently reports `unsupported`.

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
