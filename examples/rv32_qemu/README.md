# rv32 裸机 QEMU 套件（体积 / 内存 / CPU / 可靠性实测）

在 `qemu-system-riscv32 -M virt` 上把 `zanc --target riscv32` 的产物真正
**跑起来**的全套裸机件：M-mode `-bios none` 启动、UART 控制台、CLINT 定时器、
`Task.Delay` 真睡眠、退出时自动报告栈高水位与堆池水位，并让 QEMU 自动结束。
也是量化 Zan 裸机程序的体积 / 内存 / CPU 三项成本、以及验证故障路径
（trap 报告、栈哨兵、分配器水位）的标尺。

与 `examples/esp32_hello`（ESP-IDF 工程，上真机）互补：这里不需要 ESP-IDF，
只要一台装了 QEMU 的 Linux（或 WSL），就能验证 rv32 产物 + 裸机适配层的
行为与成本。

## 文件

| 文件 | 作用 |
|---|---|
| `hello.zan` | 被测程序：5 个 tick，`Task.Delay(1000)` 间隔，然后退出 |
| `soak.zan` | 稳定性浸泡：8000 轮混合尺寸字符串 churn + 变长 `Task.Delay`，验证分配器长跑不碎片化、不泄漏、不漂移 |
| `crt0.S` | `_start`：装载 gp、卫兵涂写 32 KiB 栈、清 bss、装 mtvec、预清 CLINT 比较器，`__libc_init_array` 后进 `main`，返回即 `exit`；`zan_irq_timer` 只做"比较器推到 +∞"（清 MTIP）。**统一 trap 向量 `zan_trap`**：mcause 位 31 = 中断且码 7（MTIP）走两寄存器快路径（清比较器 + mret），其余一律保存现场调 `zan_fault_report` 报告后停机 |
| `bsp.c` | 板级：NS16550A UART 控制台（picolibc tinystdio 不带 stdout/stderr 对象，这里用 `FDEV_SETUP_STREAM` 提供）；CLINT mtime 覆写 weak `zan_timer_now_ms` 与 `gettimeofday`；POSIX 文件桩（open/read/write/… → -1，软日志 fopen 按设计降级）；`poll()` 装 mtimecmp + MTIE + `wfi`——定时器中断唤醒调度器；rv32imc 无 A 扩展，zan 对象引用的 `__atomic_*` 用关中断临界区实现；**`zan_fault_report`** 打印 `mcause/mepc/mtval/ra` 后 FAIL 停机（退出码 139）；**栈哨兵**：`poll()` 每轮检查 28K 预算线卫兵字，越线即报 STACK OVERFLOW 停机；`exit()` 打印退出码、栈高水位与堆池报告 |
| `link.ld` | RAM @ 0x80000000（QEMU `-kernel` 的装载地址）；`.init_array` 保留给 picolibc stdio 构造器；栈区在 bss 之后（卫兵扫描报告用，不计入 bss） |
| `build.sh` / `run.sh` | 一键构建 / 运行 |

## 构建与运行

Ubuntu/Debian（或 Windows 上走 WSL，脚本对 `zanc.exe` 自动做 wslpath 转换）：

```bash
apt-get install -y gcc-riscv64-unknown-elf picolibc-riscv64-unknown-elf \
                   qemu-system-misc
ZANC=/path/to/zanc bash build.sh     # --publish --target riscv32 出 .o，再链成 ELF
bash run.sh                          # qemu-system-riscv32 -M virt -nographic -bios none -kernel …
```

预期输出（墙钟 ≈ 4.1 s，QEMU 自动退出，无需超时杀）：

```
tick 0
tick 1
tick 2
tick 3
tick 4

[zan] exit code: 0
[zan] stack high-water: 128 of 32768 bytes
[zan] pool: live 0 / peak 96 / oom 0 / frees 10/10
[zan] free-walk: total 65520 / maxhole 65520 / holes 1
```

## 实测数字（hello.zan，`--publish`）

| 维度 | 数值 | 说明 |
|---|---|---|
| **flash 载荷** | **4,608 B** | objcopy 二进制；Berkeley text 4,504 + data 96。libc/libgcc 侧大头是整数 printf 与 `__udivdi3`/`__umoddi3`（64 位除法） |
| **静态 RAM** | 65,632 B (bss) | 其中 **64 KiB 是垫片确定性堆池**（`-DZAN_BARE_HEAP_BYTES=` 可调，剩余静态仅 96 B）；对照 ESP32-C3 的 400 KiB SRAM |
| **栈** | 预留 32 KiB，**实测高水位 128 B** | crt0 用 `0xABABABAB` 涂满栈区，`exit()` 扫描第一个被覆盖的卫兵字，随程序复杂度增长、每次退出自动打印；`poll()` 另有 28 KiB 预算线哨兵，越线当场报错停机而不是静默踩内存 |
| **CPU** | 墙钟 4.106 s（= 4×1 s 延时 + 启动），QEMU 进程主机 CPU ≈ 45 ms（≈1%） | `poll()` 用 mtimecmp+MTIE+`wfi` 睡眠，定时器中断唤醒——`Task.Delay` 不忙等；tick 精度即 CLINT mtime（10 MHz）精度 |

## 浸泡实测（soak.zan，8000 轮）

混合尺寸字符串 churn（每轮一个短串临时 + 一个增长至 4 KiB 的长串重建）+
隔轮 `Task.Delay(15)`，全程走 `--publish` 优化：

```
[zan] exit code: 0
[zan] stack high-water: 216 of 32768 bytes
[zan] pool: live 49688 / peak 57960 / oom 0 / frees 24040/24044
[zan] free-walk: total 15768 / maxhole 15768 / holes 1
[zan] live-top: 32768 8192 8192 536
```

- **分配/释放平衡**（24040/24044，差的 4 个是常驻块），live 稳定不漂移；
- **自由表始终合并成一整块**（maxhole = total）：垫片分配器按地址序插入 +
  立即合并——没有合并时这组 churn 会在池 90% 空闲时碎片化 OOM（40 个洞、
  最大 1200 B、请求 1392 B）；
- **`live-top` 的 4 个常驻块是异常安全脚手架**（EH 状态块 536 B + 两个
  8 KiB 处理器槽 chunk + 32 KiB 临时 chunk，宿主机上同样常驻、只是无人
  计量）：首次托管分配后终生持有，默认 64 KiB 池里占 76%。裸机给堆池
  定容时按"脚手架 ≈ 48 KiB + 工作集"估算，或直接调大
  `ZAN_BARE_HEAP_BYTES`（ESP32-C3 有 400 KiB，128 KiB 池很宽裕）。

## 故障路径（实测）

- **同步异常**：对象里埋非法指令（全零字），trap 向量转 `zan_fault_report`：
  `TRAP mcause=0x2 mepc=0x80000574 mtval=0x0 ra=0x8000056c`，退出码 139。
- **栈越线**：`poll()` 每轮检查预算线卫兵字，越线打印
  `STACK OVERFLOW: past 28K of 32K budget` 后停机（不再静默踩内存）。
- **定时器中断**：mcause 位 31 + 码 7 走两寄存器快路径，与故障路径共用
  一个向量但互不拖累。

## 边界（照实说）

- **ISA**：QEMU virt 的核是 rv32imac，本套件按该多库链接；zanc 产物仍是
  rv32imc（ESP32-C3/C6 的无 FPU 核画像）。真机上用 ESP-IDF 工具链，见
  `examples/esp32_hello`。
- **libc**：picolibc（Ubuntu 无 newlib 包）。它的 tinystdio 归档不提供
  `stdout`/`stderr` 对象——由 `bsp.c` 提供控制台 FILE；printf 链的是整数版
  （浮点会换 vfprintf 变体并增大 text，属预期）。
- **原子**：按程序实际引用用关中断临界区实现（hello 引用 4 个；soak 的
  协程状态机另需 `__atomic_compare_exchange_8`）。宽程序按
  `examples/esp32_hello/README.md` 的符号契约表补齐（同款写法）。
- **单核单线程**：`ZAN_BARE_METAL` 的既定模型；poll/pthread 桩在
  `src/runtime/rt_bare_shim.c`（weak，可被板卡覆盖）。
- **EH 脚手架**：见浸泡一节——托管分配首次发生即常驻 ≈48 KiB，这是
  宿主机与裸机共有的行为，裸机侧靠堆池定容吸收；进一步按目标裁剪
  chunk 容量属未来工作。
