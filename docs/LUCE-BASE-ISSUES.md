# Language follow-ups observed while bringing up luce-prism

Compiler sources were left unchanged. Tested revisions:

- Luce Base: `162ff10fce15997abe38337029069971643614b2`
- Luce: `88d0e5d1847b489c0c3fb44425e8f56ee3bcc033`

One Windows standard-library linkage failure was observed in hosted CI. The
remaining entries are integration limitations, not claims of incorrect behavior
under the current language contracts.

## Windows UCRT64: strings.format_f64 fails to link in native mode

Observed on 2026-09-14 in the public
[Windows CI run](https://github.com/dymokomi/luce-prism/actions/runs/34895899008),
using the compiler pins above, Windows 2025 and MSYS2 UCRT64 GCC 16.2.0. The Base
and Luce compiler builds succeeded. The first Prism consumer build failed:

```sh
luce-base.exe build tests/main.lucb --native --opt 0 -o consumer.exe
```

```text
ld.exe: gen.o:fake:(.text+0x2a0b3): undefined reference to `_snprintf_l'
collect2.exe: error: ld returned 1 exit status
luce-base: the linker rejected the generated code
```

The original storage-port text writer called `strings.format_f64`. The expanded
package still reaches that standard-library formatter through foreign codecs.
At the pinned Base revision,
`src/std/strings/floats.lucb:13` declares the foreign symbol `_snprintf_l`, and
`format_float` calls it in its Windows branch. This identifies the relevant
standard-library/linker boundary; the exact UCRT linkage remedy needs confirmation
on Windows. No compiler or standard-library source was changed for this port.

A reduced probe for follow-up (not separately executed on Windows yet):

```luce-base
import strings

pub func main(arguments: str[]) -> i32!:
    var buffer: u8[64]
    print(try strings.format_f64(1.25, buffer))
    return 0
```

Expected: build, print `1.25`, exit successfully. Check native optimization levels
0–3 and C comparison modes after fixing the linkage, then rerun the Prism gate.
Windows format validation remains blocked at the first native build; no later
Windows mode is claimed to pass. ARM64 macOS passes all six compiler modes, and
the initial macOS/Linux hosted correctness job passed.

## Ordinary packages do not support standard-library ORDER modules

The standard library assembles `name/ORDER` fragments. A package export such as
`prism = "luce_prism.prism"` cannot resolve `src/luce_prism/prism/module.lucb` plus
`ORDER`; it reports `an exported module does not exist`.

Evidence: `luce-base/src/support/modules.lucb`, `source_file`, checks `.luc` and
`.lucb` files only. `luce-base/src/std/README.md` documents the separate standard
module assembly. The package uses a normal `.lucb` module. Consider supporting
module fragments in ordinary packages if the same organization is desired there.

## Luce hides signatures containing u32/u64, including shape spans

Base correctly describes `Value.numbers(shape: const u32[], values: const f64[])`.
The high-level compiler omits that method, yielding `no member numbers`, because
its boundary type mapping does not accept u32 or u64. `const usize[]` also lacks a
list adapter. This is a Luce boundary limitation, not a Base dtype/serialization bug.

Evidence: `luce/src/sema/boundary.lucb`, `type_node`, accepts `i64`, `usize`, `f64`,
`bool`, `str` and selected projections; its span branch explicitly excludes usize
lists. The package's public shape APIs now use checked `const i64[]` conversion.
Unsigned scalar constructors/accessors remain available to Base; Luce can retain
and serialize those Values. A future diagnostic should explain why a native method
is unavailable instead of making it look absent.

## Luce also excludes public structs containing f32 coordinates

The same boundary mapper excludes `f32`. Importing the initial public
`Vec3 { x: f32, y: f32, z: f32 }` through the Prism facade produced:

```text
luce: prelude:13:17: this Base declaration uses a type that cannot cross into Luce
```

Observed while compiling `tests/advanced_consumer.luc` against the pinned
toolchains above. This is consistent with the documented boundary contract,
not a Base arithmetic defect. The synthetic `prelude` location obscures which
field caused the rejection; reporting the original declaration would help.

Prism now exposes `Vec2`, `Vec3`, and `Affine2` coordinates as `f64`, with explicit
conversion to private `f32` records for legacy arithmetic. High-level geometry
tests cover this bridge. No compiler sources were changed.

## Luce omits a public alias of a generic Base type specialization

On the pinned toolchains, exporting `pub type ValueCache = EvalCache[Value]`
with a matching `interop.Type[ValueCache]` compiles for Base consumers but a
Luce import reports that `luce_prism.prism` has no `ValueCache`. The generic
cache's managed fields are private; its public methods use supported
`EvalKey`, `Reference[Value]`, and callback types.

Observed in `tests/editor_consumer.luc`. This is a Luce boundary limitation,
not a failure of Base's generic implementation. The package now wraps each
exported specialization in a concrete opaque struct in
`src/luce_prism/evaluation/cache_api.lucb`. The generic implementation remains
in `src/luce_prism/evaluation/cache.lucb`; no sibling compiler sources changed.

Confirmed independently with a temporary module declaring both the generic alias
and its `interop.Type` locally: Base describes `type SpecializedCache =
EvalCache[Value]`, while declaring `EvalCache` itself unavailable as a generic.
Luce's boundary type mapper does not accept that specialized type spelling.
Concrete wrappers must declare their `interop.Type` in their defining module
so `describe` exposes an object rather than an unavailable private struct.
