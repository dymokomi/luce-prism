# Inline data and external media

An ASCII `.prisma` document can embed binary data as typed numeric arrays and
refer to a separate `.prism` document containing larger payloads. A single
document can use both. Binary `.prism` documents retain the same reference model.

For example, `page.prisma` can hold a small preview and point at a full image:

```prisma
#prisma 4.0
def document "page" {
    def image "hero" {
        uint8[1,1,4] preview = [[[255, 0, 0, 255]]]
        reference "media.prism" "/image"
    }
}
```

`media.prism` stores an `/image` element whose `pixels` property is a
`uint8[height,width,channels]` value. It can also contain an encoded PNG, JPEG or
arbitrary file as a `uint8[length]` property, with every original byte retained.
Use `Encoding.binary`, optionally compressed, when saving this external document.

The `reference` directive is the legacy syntax for two metadata keys:

```luce
page.set_metadata("/page/hero", "reference", "media.prism")
page.set_metadata("/page/hero", "referencePath", "/image")
```

The current text writer emits equivalent `string reference = "media.prism"` and
`string referencePath = "/image"` declarations. Both spellings preserve the same
binary records and work with the original C++ implementation.

## Loading external content

`Document.load`, `decode` and `parse` read one authored document. Opening the ASCII
file exposes its inline preview and reference metadata even if the external file
is unavailable. The caller chooses when to load the external content:

```luce
let page = Document.load(directory + "/page.prisma")
let file = page.metadata("/page/hero", "reference")
let target = page.metadata("/page/hero", "referencePath")
let media = Document.load(directory + "/" + file)
let pixels = media.get(target, "pixels").bytes()
```

This example uses a known sibling filename. General filesystem resolution should
resolve relative filenames against the referring document's directory, as the
legacy `composeFile` does. The host supplies that location; `parse` and `decode`
have no filesystem origin. Storage accepts references without fetching them or
rewriting their filenames. Missing files, malformed data or absent target elements
are reported by the explicit load/get calls.

[`examples/referenced_media.luc`](../examples/referenced_media.luc) writes both
files and verifies the recovered bytes. Build and run it with an existing output
directory:

```sh
luce build examples/referenced_media.luc --native -o /tmp/referenced-media
mkdir -p /tmp/prism-media-example
/tmp/referenced-media /tmp/prism-media-example
```

Its checks run in all six compiler modes. The optional C++ oracle also composes
the generated ASCII page with its binary sidecar and compares the resulting
properties byte for byte against the expected document.

## Reference semantics and package assets

In the legacy composition model, an explicit `referencePath` selects the subtree
whose root becomes the referencing element. Local properties take precedence.
When that key is omitted, the first top-level referenced element is selected.
Recursive composition, default target selection, wildcard targets, cycle
detection and automatic property fallback have not yet been ported to Luce.
The example uses an explicit concrete target and loads it directly. `get` and
`resolve` currently inspect the local authored document; they do not follow
external references.

A `.prism` external file may also use the legacy `PRSMZ` package encoding for
`set_asset` attachments. `Document.load` detects the encoding from its magic;
callers can retrieve an attachment with `asset(path)`. Attachments remain package
records. Inline data that must live in an ASCII document uses typed properties.
