# Zan Programming Language

Modern systems programming language with **C#-style syntax**, an **LLVM AOT
backend**, and **ARC memory management**. This repository is the **Zan SDK**:
clone it (or download the ZIP) and start developing immediately — no build
step, no installer, no prerequisites.

## Quick Start (Windows)

```bash
git clone https://github.com/joyspinch/zanlang.git
cd zanlang
start ZanIDE.exe
```

That's it. The IDE resolves the compiler (`toolchain\zanc.exe`), the standard
library (`stdlib\`) and its linker/sysroots from its own folder, so producing a
native `.exe` needs nothing else on the machine.

## What's Inside

| Path | Contents |
|---|---|
| `ZanIDE.exe` | The Zan IDE — self-contained; skins, help topics and styles are embedded |
| `toolchain\` | `zanc.exe` compiler, `zan-lsp.exe` language server, `zan-dap.exe` debug adapter, `zanfmt`/`zandoc`, bundled linker (`ld.exe` + `mingw\`), cross sysroots, runtime objects, bundled `gdb` |
| `stdlib\` | Standard library as `.zan` source — auto-included by `zanc` at compile time |
| `templates\` | Built-in New Project templates (data-driven, no rebuild needed) |
| `examples\` | Runnable sample programs (GUI gallery, charts, games, web, DB, …) |
| `ai\` + `tools\zan-mcp.exe` | AI coding integration: agent rules + skills + MCP server for Claude Code / Cursor / Copilot / Windsurf |
| `knowledge\` | Offline API index + example catalog used by the built-in assistant |

## Highlights

- **Familiar syntax** — C#/Java style, no cryptic symbols or lifetime annotations
- **AOT compilation** — straight to native machine code via LLVM
- **ARC memory** — automatic reference counting with deterministic destruction
- **Value semantics** — structs on the stack, copy-on-write collections
- **Easy FFI** — direct DLL imports for system APIs and native libraries
- **Source-based stdlib** — the standard library ships and compiles as `.zan` source

## License

The contents of this repository (standard library, templates, examples, agent
skills, docs) are released under the MIT License (see `LICENSE`).

The Zan compiler and IDE are distributed here as **binaries**; their sources
are not part of this repository.
