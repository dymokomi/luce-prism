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
- Byte-for-byte media round trips through ASCII text, binary, compressed binary
  and packages: a 512×512 RGBA byte buffer containing every possible byte, an
  encoded 2×2 PNG, an empty byte array, and the entire uint16 range.
- Every finite float16 bit pattern, plus float32/64 signed zeros, subnormals,
  extrema and precision-sensitive values, preserved through those same modes.
  These checks do not assert non-finite floating-point preservation.
- Typed pixel construction and byte extraction through high-level Luce in every
  encoding, and text→compressed-binary media preservation.
- Text→binary→text→binary stability, keyframe handles and all v4 layer records.
- Concrete connection resolution, linear samples, cycle errors, rename/reparent
  path fixes, removal, and retained independent values after mutation.
- Missing headers, unsupported versions/flags, truncated records, malformed
  values/shapes, implausible counts, and decompression-size limits.
- Quoted delimiter strings, retained escaped names, boolean arrays,
  embedded-NUL path rejection and malformed trailing tokens.
- Allocation failure at each of 240 successive allocation positions during text
  parsing, with a counting heap requiring zero outstanding allocations after every
  successful or failed attempt.

The optional `--oracle` gate uses a freshly linked C++ executable to decode new
text/binary/compressed output, and to produce new encodings for the Luce decoder.
All paths are checked against canonical binary documents. A generated image
document also exchanges RGBA pixels, the PNG fixture and all 256 byte values with
the C++ implementation in both directions.

CI is configured for macOS, Linux and Windows with exact compiler pins. ARM64
macOS has executed the full media gate locally. The initial hosted macOS/Linux
[correctness run](https://github.com/dymokomi/luce-prism/actions/runs/34895899061)
passed. The initial Windows build failed on an unresolved `_snprintf_l` symbol
from the Base standard library; see the separate
[language follow-up](LUCE-BASE-ISSUES.md#windows-ucrt64-stringsformat_f64-fails-to-link-in-native-mode).
Consult the repository's Actions page for subsequent hosted results. No GPU,
performance, composition, query or codec-parity claim is made by this gate.
