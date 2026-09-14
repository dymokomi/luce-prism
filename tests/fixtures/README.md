# Reference fixtures

`core.prisma` was authored for this port. The three binary fixtures were generated
by a fresh Release build of kinogaki-core commit
`ce92a4b37887d4ebb14194ca2ba4084af657c34a`, using `tests/oracle.cpp`:

```sh
oracle core.prisma core.prism binary
oracle core.prisma core-compressed.prism compressed
oracle core.prisma core-package.prism package
```

The package contains an asset at `/world/source`, MIME
`application/octet-stream`, with bytes `00 ff 01`. The fixtures contain no user
project data. Normal tests read these fixtures and do not rewrite them.

`rgba.png` is a synthetic 2×2, 8-bit RGBA PNG generated for this port using Python's
standard-library `struct` and `zlib`. Its pixels are red/opaque, green/alpha 128,
blue/alpha 64 and white/transparent, in row-major order. `tests/media.lucb` embeds
the complete file as a uint8 property and compares the recovered bytes in every
encoding. The optional oracle also exchanges it with the C++ implementation.

For fresh, independent two-way compatibility validation, build the C++ core in a
temporary directory, link `tests/oracle.cpp` to its static library, and pass that
executable to `./test.sh --oracle /path/to/oracle`.
