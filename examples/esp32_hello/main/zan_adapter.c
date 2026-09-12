/* zan_adapter.c -- glue between ESP-IDF and the object zanc emits.
 *
 * The zan object is freestanding: it defines `main(int, char**)` and
 * references libc (newlib, which IDF retargets to the UART console),
 * libgcc (lock-based __atomic_* for rv32imc), IDF's pthread/vfs symbols,
 * and the timer reactor from src/runtime/rt_timer.c compiled below with
 * -DZAN_BARE_METAL (single thread: no mutex, no signal-based crash log).
 */
#include <stdarg.h>
#include <stdio.h>

int main(int argc, char **argv);

/* The zan entrypoint initializes the runtime, runs Program.Main and exits
 * through exit() when it returns -- app_main never comes back (IDF's
 * _exit path restarts the chip). */
void app_main(void) {
    main(0, (char **)0);
}

/* The compiler routes IR snprintf calls here on 32-bit targets: the IR
 * declares the size parameter as i64 (Zan int), and a mid-list i64 breaks
 * ilp32 register-pair alignment for the varargs after it. A C wrapper
 * with a real long long parameter restores the ABI before forwarding. */
int zan_w32_snprintf(char *s, long long n, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    int r = vsnprintf(s, (size_t)n, fmt, ap);
    va_end(ap);
    return r;
}
