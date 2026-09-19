# luce-prism

Prism's native document engine, written in **Luce Base** and usable from **Luce**.
It is self-contained: in-memory tables, WAL, flock, save/load, and a Unix owner
socket. It does not depend on luce-db. A document holds path-addressed elements,
typed multidimensional values, metadata, animation and connections. Documents,
images, vectors, scenes and bundles can share this substrate without the container
depending on their renderers or codecs.

This package ports the Prism format and its document services from `kinogaki-core`:
composition and explicit references, overlay/diff/merge, animation, registered
node evaluation, queries and indexes, schema validation, columnar views, logic,
surface syntax, foreign codecs, bundles, and editor projections. The C++ core is
an independent test oracle; it is **not a runtime or build dependency**.

Implementation modules have separate responsibilities under `src/luce_prism`.
The public `prism` module is a facade. See [architecture](docs/PORT.md),
[API and ownership](docs/API.md), and [compatibility differences](docs/LEGACY-DIFFERENCES.md).

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
encodings. `load`/`parse` read the authored document; callers explicitly
load external files when needed. See [external media](docs/REFERENCES.md) and the
[tested Luce example](examples/referenced_media.luc) for writing and reading both
files together.

```sh
python3 tools/bootstrap.py
./test.sh
# Or select already-built compilers without changing sibling checkouts:
./test.sh --base /path/to/luce-base --luce /path/to/luce
```

Check out sibling compilers, crypto and TLS at the commits in `bootstrap/BASE`,
`bootstrap/LUCE`, `bootstrap/CRYPTO` and `bootstrap/TLS`. Bootstrap verifies those
inputs and builds package-local compilers without modifying language sources.
The gate runs Base and Luce consumers at native optimization levels 0–3 and both
C comparison modes. It includes checked-in C++ fixtures, compressed and package
round trips, malformed input, path edits and injected allocation failures. Builds
and test outputs use temporary directories; compiler caches default to
`build/cache`. Persistent-store cases use separate runner-owned paths, and the
runner terminates/reaps its IPC owner before removing the fixture directory.
This IPC process-exit cleanup is not a graceful Store/TLS shutdown test.
Media tests compare payload bytes for
a 512×512 RGBA image, an embedded PNG, 16-bit channels and finite floating-point
arrays in every encoding. See [validation](docs/VALIDATION.md).

`python3 tests/snapshot_reclaim.py --mode all` checks the transition from
inline snapshot chunks to an external snapshot file and reopens a committed,
unbaked generation in a fresh process. Use `--mode sanitize` for ASan/UBSan and
`--mode native0 --heap` on macOS to require zero leaked allocations. Existence
checks during reclamation borrow WAL entries instead of allocating discarded
copies of chunk payloads. The heap runner is adapted from the same author's
dual-licensed `luce-auth` test helper; it captures output in regular files and
cleans up only the process group it starts.

Prism includes JSON, Markdown, HTML, SVG, text, and blob adapters. Image decoding
remains in `luce-image`; Prism stores its pixels and encoded files without a
runtime dependency on that package. GPU, threading, and rendering remain the
responsibility of the Luce infrastructure and consuming applications.

The compatibility inventory maps **373 native legacy behavioral cases** to tests.
An additional 44 legacy C ABI/global-interner cases are retained in the inventory
and explicitly outside this native API. This is a behavioral compatibility gate,
not a claim of measured 100% line or branch coverage. Differential tests compare
against pinned C++ outputs and optionally a freshly built C++ oracle.

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
