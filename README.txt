Zan IDE - self-contained release
================================

This folder is the SDK installation. It is not a workspace: create your Zan
projects anywhere else and run the IDE from here.

Contents
  ZanIDE.exe     The Zan IDE. It runs from this folder; the GUI runtime is
                 statically
                 linked in, and stdlib/toolchain resolve from here.
  (skins, ide.css, help topics)
                 Baked into ZanIDE.exe as embedded resources and read from
                 memory -- no files required beside the exe. A file of the same
                 name next to the exe (ide.css, skins\, docs\topics.json) still
                 wins, which is how you override one without a rebuild.
  toolchain\     The Zan compiler and everything it links with, all as siblings:
                   zanc.exe                the compiler
                   zan-lsp.exe             language server (for external editors)
                   zan-dap.exe             debug adapter (for external editors)
                   zanfmt/zandoc           format / doc CLIs
                   ld.exe, mingw\          bundled linker + MinGW-w64 runtime
                   linux-musl\             sysroot for --target linux-* builds
                   debugger\bin\gdb.exe    bundled native debugger (used by
                                           zan-dap; no system gdb needed)
                   zanrt_io*, zanrt_sync*  runtime objects
                 The IDE locates zanc here, and zanc finds its linker / sysroot
                 next to itself in this same folder, so producing an .exe needs
                 no external toolchain. Keep this folder intact.
  stdlib\        Standard library sources. zanc auto-includes the .zan files
                 it needs from here; keep this folder next to ZanIDE.exe.
  knowledge\     Offline knowledge base for the built-in assistant:
                   symbols.json  API index generated from stdlib (api_search)
                   gallery.json  golden-example catalog (example tool)
                 The assistant queries these instead of grepping the stdlib.
  examples\      Sample programs shown in the IDE's Examples pane (optional).
  templates\     Built-in New Project templates (one folder each, with a
                 template.manifest). Edit or drop in your own folders to add
                 templates -- no rebuild needed.
  tools\         Zan tools shown in the IDE's Tools panel (double-click to run,
                 right-click to open the source), plus zan-mcp.exe -- the MCP
                 server for AI clients. See the AI section below.
  ai\            Templates installed into your own projects by
                 "tools\zan-mcp.exe --init-agent" (see below).
  llms.txt       AI entry index of this folder (generated from what shipped):
                 the paths to the rules, tools, knowledge, skills and docs an
                 AI agent needs, readable without an MCP connection.
  AI_README.md   How AI uses this SDK (in Chinese): setup, the MCP tool
                 catalog, skills, the knowledge base. Start here when wiring
                 up an AI coding tool.
  README.CN.txt  Chinese version of this readme.

AI coding tools (Claude Code / Cursor / Copilot / Windsurf)
  Enable them per PROJECT, not here. Two ways, same implementation:

    In the IDE   Assistant panel -> "为当前项目启用 AI 接入" (one click on the
                 project you have open).
    Without it   tools\zan-mcp.exe --init-agent D:\path\to\your-project
                 (add --force to overwrite files that already exist)

  Either one writes into THAT project, with this SDK's paths filled in:
    AGENTS.md            the rules an AI agent must follow in Zan code
    .agents\skills\      zan-development / zan-debugging / zan-mcp workflows
    .mcp.json            Claude Code and most clients
    .cursor\mcp.json     Cursor
    .vscode\mcp.json     VS Code / Copilot
  Then open that project in your AI editor and it starts the server itself.
  Existing files are kept, not overwritten, and reported.

  tools\zan-mcp.exe
                 The MCP server behind all of it, run as
                   tools\zan-mcp.exe --stdio <your project dir>
                 It answers what a model would otherwise guess at:
                 zan_start_here (project layout, commands, rules, tools in one
                 call), zan_api_search (exact stdlib signatures), zan_example
                 (shipped, build-verified programs), zan_compile /
                 zan_build_project (structured diagnostics), plus workspace
                 file access. Add --read-only or --no-exec to restrict it;
                 without --stdio it serves the same API over HTTP. It finds
                 knowledge\, toolchain\ and stdlib\ one level up on its own
                 (--sdk-root <dir> overrides).
  ai\            The templates the two commands above install (AGENTS.md,
                 skills\, mcp.json / cursor.mcp.json / vscode.mcp.json). They
                 still carry <ZAN_MCP> / <ZAN_SDK> / <ZAN_PROJECT> placeholders,
                 so use --init-agent rather than copying them by hand.
  docs\AI_ONBOARDING.md
                 The full connection guide (also covers zan-lsp / zan-dap for
                 editors that speak LSP/DAP directly).

  Website mirror    The same ai\ content (rules + skills + mcp configs) is
                  mirrored on the project website at /ai-connect, generated
                  from this pack so they never drift. This SDK copy is the
                  authoritative one that --init-agent installs; the site copy
                  is for reading.

Requirement
  None for normal use: zanc links via the bundled toolchain\ folder, so no
  external LLVM/clang install is needed. (If the linker files under toolchain\
  are removed, zanc falls back to a system clang on PATH.)

Run
  Double-click ZanIDE.exe (or run it from a terminal). Everything the IDE
  needs to build and run Zan programs ships in this folder.

Note
  This folder is produced by scripts\publish_ide.ps1. Do not hand-edit or
  drop unrelated files here -- re-run the publish script to refresh it.
