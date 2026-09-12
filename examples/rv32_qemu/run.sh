#!/usr/bin/env bash
# run.sh -- boot the kit in QEMU and capture five ticks.
# Works on a Linux host directly; on Windows it goes through WSL.
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
ELF=${ELF:-$DIR/build/zan_hello.elf}
SECS=${SECS:-12}

QEMU=(qemu-system-riscv32 -M virt -nographic -bios none -kernel "$ELF")
if command -v qemu-system-riscv32 >/dev/null 2>&1; then
    timeout "$SECS" "${QEMU[@]}" || true
else
    timeout "$SECS" wsl -e "${QEMU[@]}" || true
fi
