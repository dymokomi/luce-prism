# Validation

Local validation uses ARM64 macOS, Luce Base commit
`162ff10fce15997abe38337029069971643614b2` and Luce commit
`88d0e5d1847b489c0c3fb44425e8f56ee3bcc033`. The compilers were built under a
temporary toolchain directory from the checked-out sources. Neither compiler
checkout nor `luce-image` was modified.

Run the same package gate with explicit paths:

```sh
./test.sh --base /path/to/luce-base --luce /path/to/luce
```

The gate builds and executes both Base and high-level Luce consumers with native
optimization levels 0–3, `--backend=c`, and `--backend=c --release`. It verifies:

- All 14 dtype codes, scalar integer endpoints, half floats, multidimensional
  arrays, empty arrays, strings, aliases and legacy tuple/array roles.
- Byte-identical v4 binary output against an independently built C++ fixture.
- Legacy compressed input, newly compressed output, and package asset retention.
- Text→binary→text→binary stability, keyframe handles and all v4 layer records.
- Concrete connection resolution, linear samples, cycle errors, rename/reparent
  path fixes, removal, and retained independent values after mutation.
- Missing headers, unsupported versions/flags, truncated records, malformed
  values/shapes, implausible counts, and decompression-size limits.
- Quoted delimiter strings, boolean arrays and embedded-NUL path rejection.
- Allocation failure at each of 240 successive allocation positions during text
  parsing, with a counting heap requiring zero outstanding allocations after every
  successful or failed attempt.

The optional `--oracle` gate uses a freshly linked C++ executable to decode new
text/binary/compressed output, and to produce new encodings for the Luce decoder.
All paths are checked against the same canonical binary document.

CI is configured for macOS, Linux and Windows with exact compiler pins. Only
ARM64 macOS has been executed locally; hosted results should be assessed on the
repository's Actions page. No GPU, performance, composition, query or codec-parity
claim is made by this gate.
