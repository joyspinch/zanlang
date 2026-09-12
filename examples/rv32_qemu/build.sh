#!/usr/bin/env bash
# build.sh -- assemble the bare-metal rv32 ELF for the QEMU 'virt' board.
#
# Inputs:  hello.zan (this dir), ../../src/runtime/{rt_timer.c,rt_bare_shim.c}
# Output:  build/zan_hello.elf (+ memory-usage + Berkeley size reports)
#
# Toolchain (Debian/Ubuntu packages): gcc-riscv64-unknown-elf +
# picolibc-riscv64-unknown-elf + qemu-system-misc (to run). zanc must be a
# build with the RISCV backend (official zan distributions have it; point
# ZANC at it).
#
# Flags worth noting:
#   -march=rv32imc_zicsr  objects: csr instructions (mtvec/wfi traps) need
#                         the zicsr ISA extension bit with modern binutils;
#                         emitted code stays rv32imc (ESP32-C3 profile).
#   -march=rv32imac       link only: selects picolibc's rv32imac/ilp32
#                         multilib (rv32imc alone falls back to rv32im).
#   --specs=picolibc.specs headers + libc; tinystdio with NO stdout object
#                         -- bsp.c provides the console FILE over the UART.
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$DIR/build}
mkdir -p "$OUT"

CC=${CC:-riscv64-unknown-elf-gcc}
ZANC=${ZANC:-zanc}
OBJCFLAGS="-march=rv32imac_zicsr -mabi=ilp32 -mcmodel=medany -ffreestanding \
 -Os -ffunction-sections -fdata-sections --specs=picolibc.specs"
LNKFLAGS="-march=rv32imac -mabi=ilp32 -nostartfiles --specs=picolibc.specs"

# 1. the zan program -> rv32 object (rv32imc codegen; C3/C6 profile)
# A Windows zanc.exe (run from WSL via interop) needs win32 paths.
case "$ZANC" in
*.exe|*.EXE)
    SRC_ARG=$(wslpath -w "$DIR/hello.zan"); OBJ_ARG=$(wslpath -w "$OUT/zan_hello.o") ;;
*)
    SRC_ARG="$DIR/hello.zan"; OBJ_ARG="$OUT/zan_hello.o" ;;
esac
if [ ! -f "$OUT/zan_hello.o" ] || [ "$DIR/hello.zan" -nt "$OUT/zan_hello.o" ]; then
    # --stdlib-path: the stdlib root is discovered relative to the compiler
    # executable, so a zanc outside the repo tree (a copied binary, a WSL
    # interop invocation) silently resolves no `using` namespaces at all --
    # only compiler intrinsics keep working. Pin the root explicitly.
    "$ZANC" "$SRC_ARG" --auto-stdlib --publish --target riscv32         --stdlib-path "$DIR/../../stdlib" -o "$OBJ_ARG"
fi

# 2. board support, the deterministic pool shim, and the timer reactor
#    (ZAN_BARE_METAL: single hart, no signal-based crash logger, weak
#    zan_timer_now_ms that bsp.c overrides with CLINT mtime)
$CC $OBJCFLAGS -c "$DIR/bsp.c" -o "$OUT/bsp.o"
$CC $OBJCFLAGS -c "$DIR/../../src/runtime/rt_bare_shim.c" -o "$OUT/shim.o"
$CC $OBJCFLAGS -DZAN_BARE_METAL -I "$DIR/../../src/runtime" \
    -c "$DIR/../../src/runtime/rt_timer.c" -o "$OUT/rt_timer.o"
$CC $OBJCFLAGS -c "$DIR/crt0.S" -o "$OUT/crt0.o"

# 3. link: our _start / poll / exit / __atomic_* / stdout win over libc
#    members; picolibc brings printf/memcpy/..., libgcc soft-float + __udivdi3
$CC $LNKFLAGS -T "$DIR/link.ld" \
    -Wl,--gc-sections -Wl,--print-memory-usage -Wl,-Map,"$OUT/zan_hello.map" \
    -o "$OUT/zan_hello.elf" \
    "$OUT/crt0.o" "$OUT/bsp.o" "$OUT/shim.o" "$OUT/rt_timer.o" \
    "$OUT/zan_hello.o"

riscv64-unknown-elf-size "$OUT/zan_hello.elf"
echo "ELF: $OUT/zan_hello.elf"
