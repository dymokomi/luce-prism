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

The writer emits the `reference` directive. The reader also accepts the legacy
`string reference` and `string referencePath` metadata declarations.

## Loading external content

`Document.load`, `decode` and `parse` read one authored document. Opening the ASCII
file exposes its inline preview and reference metadata even if the external file
is unavailable. `Session.get` does not follow `reference` arcs.

Live path lookup mounts the `reference` string as a catalog identity and walks
OS components with `Store.lookup`. A missing `referencePath` is `"/"` (the mount
root), not compose's first top-level child:

```luce
store.mount("media.prism")
# photos is type link; reference "media.prism"; no referencePath
store.lookup("/users/alice/photos", true)
# Look("media.prism", "/", directory)
store.read("/users/alice/photos/vacation")
# media's /vacation bytes; the root identity is not grafted
```

`Store.kind` uses `lookup(follow=true)`. Intermediate links always switch
identity; a terminal link with `follow=false` stays `LookKind.link`. Cycles are
visited identities. `compose` / `compose_file` / `ReferenceLibrary.materialize`
still graft for export and the oracle.

Callers that are not using a Store can still load a sibling file explicitly:

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
That default is compose-only: `Store.lookup` uses `"/"`. Recursive composition,
default target selection, wildcard targets and cycle handling are implemented by
`ReferenceLibrary.compose(name)` / `materialize(name)` and `compose_file(path)`.
The latter resolves filenames relative to the referring file. Calling either is
an explicit request to expand references; `get`, `resolve`, `load`, and `parse`
themselves inspect only authored local data.

For host-controlled resolution, construct `ReferenceLibrary()`, add each document
with `add(name, document)`, then call `compose(name)`. Registration captures an
independent snapshot. Missing documents or reference targets report an error;
cyclic arcs follow the reference core's cycle-cut behavior. Composition returns a
new document and leaves the authored source and its arcs available to the caller.

A `.prism` external file may also use the legacy `PRSMZ` package encoding for
`set_asset` attachments. `Document.load` detects the encoding from its magic;
callers can retrieve an attachment with `asset(path)`. Attachments remain package
records. Inline data that must live in an ASCII document uses typed properties.
