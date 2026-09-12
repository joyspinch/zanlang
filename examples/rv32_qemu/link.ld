/* link.ld -- bare-metal rv32 image for QEMU riscv32 -M virt.
 *
 * QEMU -bios none -kernel jumps to the ELF entry in RAM at 0x80000000 and
 * loads every PROGBITS segment at its virtual address, so .data needs no
 * copy-down. .init_array is kept for picolibc's __libc_init_array (stdio
 * init). The stack is reserved after .bss (not counted in the bss RAM
 * number; exit() reports its actual high-water usage against the guard).
 */
OUTPUT_FORMAT("elf32-littleriscv")
OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    RAM (rwxa) : ORIGIN = 0x80000000, LENGTH = 16M
}

SECTIONS
{
    .text : {
        KEEP(*(.init.enter))
        *(.text .text.*)
    } > RAM

    .rodata : ALIGN(8) {
        *(.rodata .rodata.* .srodata .srodata.*)
    } > RAM

    .data : ALIGN(8) {
        __data_start = .;
        *(.data .data.*)
        . = ALIGN(8);
        /* gp-relative addressing window for the small-data sections */
        __global_pointer$ = . + 0x800;
        *(.sdata .sdata.*)
        __data_end = .;
    } > RAM

    .preinit_array : ALIGN(4) {
        __preinit_array_start = .;
        KEEP(*(.preinit_array))
        __preinit_array_end = .;
    } > RAM

    .init_array : ALIGN(4) {
        __init_array_start = .;
        KEEP(*(SORT_BY_INIT_PRIORITY(.init_array.*)))
        KEEP(*(.init_array))
        __init_array_end = .;
    } > RAM

    .fini_array : ALIGN(4) {
        __fini_array_start = .;
        KEEP(*(SORT_BY_INIT_PRIORITY(.fini_array.*)))
        KEEP(*(.fini_array))
        __fini_array_end = .;
    } > RAM

    .bss (NOLOAD) : ALIGN(8) {
        __bss_start = .;
        *(.bss .bss.* .sbss .sbss.* COMMON)
        __bss_end = .;
    } > RAM

    . = ALIGN(16);
    __stack_bottom = .;
    . += 0x8000;              /* 32 KiB stack; guarded + reported at exit */
    __stack_top = .;

    /DISCARD/ : { *(.eh_frame .eh_frame_hdr .riscv.attributes .comment) }
}
