/* wasm32 shim: zig's wasi-musl setjmp.h hard-errors without the wasm EH
 * proposal. FreeType reaches setjmp only on the untrusted-font validator
 * paths (ttcmap), which a trusted UI font never enters; provide the type and
 * trap implementations so the header resolves and the archive links. */
#ifndef FT_WASM_SETJMP_SHIM_H
#define FT_WASM_SETJMP_SHIM_H
typedef long ft_wasm_jmp_buf[32];
typedef ft_wasm_jmp_buf jmp_buf;
int ft_wasm_setjmp(jmp_buf b);
void ft_wasm_longjmp(jmp_buf b, int v) __attribute__((noreturn));
#define setjmp(b) ft_wasm_setjmp(b)
#define longjmp(b, v) ft_wasm_longjmp(b, v)
#endif
