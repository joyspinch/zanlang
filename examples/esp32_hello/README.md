# esp32_hello — Zan on ESP32-C3 (RISC-V rv32imc)

Prints `hello from Zan on rv32: <n>` over the console (UART) once a second.
One Zan program, one adapter file, zero zan-specific CMake plumbing beyond a
custom command.

## Status of verification

Verified locally (no ESP-IDF/hardware on the dev box): the compiler emits a
valid ELF32 RISC-V object for this program class (`ctest -R cross_riscv32_object`
pins the format; `llvm-objdump -d` shows RV32IMC code), and the full
undefined-symbol surface of such objects is exactly the contract in the table
below, every entry of which resolves from ESP-IDF's newlib/libgcc/pthread/vfs
plus `rt_timer.c` compiled with `-DZAN_BARE_METAL`. The `idf.py build` step
itself and the on-chip run have **not** been executed by this repo's CI —
check the troubleshooting section if the first build trips on IDF component
details.

## Prerequisites

- ESP-IDF 5.x (with the riscv32 toolchain it bundles) — `idf.py --version` works
- The zan compiler `zanc` on PATH (any build that has the RISCV LLVM backend;
  official zan distributions include it — `zanc --list-targets` must list
  `riscv32`/`esp32c3`)

## Build & flash

```bash
idf.py set-target esp32c3
idf.py -DZANC=$(which zanc) build flash monitor
```

`main/CMakeLists.txt` runs `zanc hello.zan --auto-stdlib --publish --target
riscv32` for you (regenerated when `hello.zan` changes), links the result with
`main/zan_adapter.c` and `src/runtime/rt_timer.c` (`-DZAN_BARE_METAL`), and
puts `main` under ESP-IDF's `app_main`.

## How it fits together

```
hello.zan ──zanc --target riscv32──▶ zan_hello.o   (ELF32 RISC-V, defines main)
                                          │
rt_timer.c (-DZAN_BARE_METAL)             │  timer reactor + fail-soft reports
zan_adapter.c                             │  app_main → main(0,0), snprintf ABI
ESP-IDF: newlib · libgcc · pthread · vfs ◀┘  libc, __atomic_*, mutexes, poll
```

- **Single thread**: the bare-metal contract is one thread; `ZAN_BARE_METAL`
  makes the timer heap lock-free and drops the signal-based crash logger.
- **Time**: `clock_gettime(CLOCK_MONOTONIC)` — ESP-IDF maps it onto esp_timer.
  A libc without it can override `zan_timer_now_ms` (weak under
  `ZAN_BARE_METAL`).
- **64-bit atomics**: rv32imc has no A extension; libgcc's lock-based
  `__atomic_*_8` fallbacks cover them.
- **Publish mode**: `--publish` gives per-function `.text.<fn>` sections +
  string obfuscation; ESP-IDF links with `--gc-sections`, so dead code from
  the stdlib surface is dropped there.

## Symbol contract (what the zan object leaves undefined)

| Symbols | Provided by |
|---|---|
| `printf` `setvbuf` `stdout` `exit` `malloc` `free` `calloc` | ESP-IDF newlib (UART console, heap_caps-backed malloc) |
| `memcpy` `memset` `strlen` | newlib |
| `_setjmp` `longjmp` | newlib (try/throw lower onto them — no DWARF unwinding) |
| `__atomic_load_8` `__atomic_fetch_add_8` `__atomic_fetch_sub_8` `__atomic_exchange_4` `__atomic_compare_exchange_8` | libgcc (lock-based on rv32) |
| `poll` | vfs (falls back to the timer dispatch; single-thread = no sockets) |
| `pthread_mutex_lock` `pthread_mutex_unlock` `pthread_self` | pthread component (uncontended fast path) |
| `zan_timer_delay` `zan_timer_cancel_delay` `zan_timer_dispatch_due` `zan_timer_next_timeout` `zan_timer_runtime_reset` `zan_timer_set_ready_hook` `zan_rt_soft_note` `zan_rt_soft_is_hard` | `rt_timer.c` with `-DZAN_BARE_METAL` |
| `zan_w32_snprintf` | `zan_adapter.c` (ilp32 snprintf ABI wrapper) |

Re-derive the list for any program with:
`llvm-nm --undefined-only zan_hello.o`.

## Without ESP-IDF

Any other rv32imc board: compile `src/runtime/rt_bare_shim.c` with the board
toolchain and link it with the zan object plus a riscv32 libc (picolibc /
newlib-nano). The shim provides a deterministic 64 KB pool allocator
(`-DZAN_BARE_HEAP_BYTES=` to size), single-thread pthread stubs, a
`poll` stub and the snprintf wrapper — the symbol table above says what else
your libc must supply.

## Troubleshooting

- **`zanc not found`** — pass it explicitly: `idf.py -DZANC=/full/path/zanc build`.
- **undefined `poll`** — your IDF build has no vfs in the component closure:
  keep `PRIV_REQUIRES pthread vfs` in `main/CMakeLists.txt`.
- **undefined `__atomic_*_8`** — the riscv32 libgcc is missing from the link;
  this should not happen with IDF's toolchain — check you are on esp32c3
  target, not a custom toolchain without libgcc.
- **garbled console text** — the program prints UTF-8; set the monitor to
  UTF-8 (`idf.py monitor` defaults).
- **crash on startup** — main-task stack too small for your program's frames:
  raise `CONFIG_ESP_MAIN_TASK_STACK_SIZE` in `sdkconfig.defaults`.
