# Language follow-ups observed while bringing up luce-prism

Compiler sources were left unchanged. Tested revisions:

- Luce Base: `162ff10fce15997abe38337029069971643614b2`
- Luce: `88d0e5d1847b489c0c3fb44425e8f56ee3bcc033`

No confirmed Luce Base compiler defect has been reproduced so far. The following
are integration limitations, not claims of incorrect behavior under the current
language contracts.

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
