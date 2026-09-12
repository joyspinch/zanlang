Zan IDE 自包含发布包
====================

本目录是 SDK 安装目录，不是工作区：请把 Zan 项目建在别处，从这里运行 IDE。

目录内容
  ZanIDE.exe     Zan 集成开发环境。GUI 运行时已静态链接进 exe，皮肤/帮助主题为内嵌
                 资源从内存读取，旁边不需要任何 dll 或数据文件。在 exe 旁边放
                 同名文件（ide.css、skins\、docs\topics.json）仍会优先生效，
                 这就是不重新打包就替换它们的办法。
  toolchain\     Zan 编译器及其链接所需的一切，全部作为同目录的兄弟文件平铺：
                   zanc.exe                编译器
                   zan-lsp.exe             语言服务器（供外部编辑器）
                   zan-dap.exe             调试适配器（供外部编辑器）
                   zanfmt.exe / zandoc.exe 格式化 / 文档生成命令行
                   ld.exe, mingw\          内置链接器 + MinGW-w64 运行库
                   linux-musl\             --target linux-* 静态 ELF 的 sysroot
                   debugger\bin\gdb.exe    内置原生调试器（zan-dap 使用）
                   zanrt_io*, zanrt_sync*  运行时目标文件
                 IDE 在这里找 zanc，zanc 在自己旁边找链接器 / sysroot / 标准库，
                 生成 .exe 不依赖任何外部工具链。请保持本目录完整。
  stdlib\        标准库源码。zanc 自动按需引入；请与 ZanIDE.exe 放在一起。
  knowledge\     内置 AI 助手的离线知识库：
                   symbols.json  由随包 stdlib 生成的 API 索引（api_search 用）
                   gallery.json  金标示例目录（example 工具用）
                 助手查这些索引，而不是去 grep 标准库源码。
  examples\      IDE 示例面板展示的示例程序（可选）。
  templates\     内置"新建项目"模板（每个模板一个目录，含 template.manifest）。
                 编辑或放入新目录即可增删模板——无需重新构建。
  tools\         IDE 工具面板展示的 Zan 工具（双击运行），以及 zan-mcp.exe——
                 AI 客户端的 MCP 服务器。见下方 AI 一节。
  ai\            由 "tools\zan-mcp.exe --init-agent" 安装进你自己项目的模板
                 （AGENTS.md、skills\、三个 mcp 配置），见下。
  llms.txt       本目录的 AI 索引（按实际发布内容生成）：AI 需要的规矩、工具、
                 知识库、技能、文档路径一览，没接 MCP 也能读。
  AI_README.md   怎么让 AI 用这个 SDK（中文）：接入方式、MCP 工具目录、技能、
                 知识库、常见问题。接 AI 工具前先读它。
  docs\          AI_ONBOARDING.md（AI 接入完整指南）、TOOLING.md、ai-assist.md、
                 MCP_HOSTING.md、AI_DEV_INFRASTRUCTURE.md。

AI 编程工具（Claude Code / Cursor / Copilot / Windsurf）
  按"项目"启用，而不是在这里启用。两种方式，同一实现：

    IDE 里    助手面板 ->「为当前项目启用 AI 接入」（对你打开的项目一键完成）
    命令行    tools\zan-mcp.exe --init-agent D:\path\to\your-project
              （加 --force 覆盖已存在的文件）

  两种方式都会把内容写进那个项目，并填好本 SDK 的真实路径：
    AGENTS.md            AI 在 Zan 代码里必须守的规矩
    .agents\skills\      zan-development / zan-debugging / zan-mcp 三个技能
    .mcp.json            Claude Code 及多数客户端
    .cursor\mcp.json     Cursor
    .vscode\mcp.json     VS Code / Copilot
  然后用你的 AI 编辑器打开那个项目，客户端会自己启动服务器。
  已存在的文件保留不覆盖，并逐个报告。

  tools\zan-mcp.exe
                 背后的 MCP 服务器，运行方式：
                   tools\zan-mcp.exe --stdio <你的项目目录>
                 它回答模型原本只能靠猜的问题：zan_start_here（项目布局、命令、
                 规矩、工具目录一次拿全）、zan_api_search（标准库精确签名）、
                 zan_example（可编译的官方示例）、zan_compile / zan_build_project
                 （结构化诊断），外加工作区文件读写。加 --read-only 或 --no-exec
                 收权；不带 --stdio 时以 HTTP 提供同一套 API。它会自己在上一级
                 找 knowledge\、toolchain\ 和 stdlib\（--sdk-root <目录> 可覆盖）。
  ai\            上面两条命令安装的模板。里面保留 <ZAN_MCP> / <ZAN_SDK> /
                 <ZAN_PROJECT> 占位符，所以请用 --init-agent，不要手工复制。
  docs\AI_ONBOARDING.md
                 完整接入指南（也覆盖 zan-lsp / zan-dap 直连 LSP/DAP 的编辑器）。

  官网镜像        ai\ 的同样内容（规矩 + 技能 + mcp 配置）镜像在项目官网
                 /ai-connect，由本包生成，两边不会漂移。本 SDK 里这份是权威
                 副本，--init-agent 安装的就是它；网站上那份供在线阅读。

环境要求
  正常使用为零依赖：zanc 通过内置 toolchain\ 里的链接器完成链接，不需要安装
  外部 LLVM/clang。（若删除 toolchain\ 下的链接器文件，zanc 回退到 PATH 上
  的系统 clang。）

运行
  双击 ZanIDE.exe（或在终端里运行）。构建和运行 Zan 程序所需的一切都在本目录。

注意
  本目录由 scripts\publish_ide.ps1 生成。不要手工编辑或往里放无关文件——
  重新运行发布脚本即可刷新。
