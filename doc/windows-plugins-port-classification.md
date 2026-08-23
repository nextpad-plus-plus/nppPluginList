# Windows Notepad++ Plugins — macOS Port Classification

_Generated 2026-06-30. Scope: every non-underscore folder in `nppPluginsWin64/` (underscore = already ported, excluded). **141 plugins.**_

> **Criterion (per user):** a full rewrite is acceptable, so **language is _not_ a blocker**. “Not worth porting” means the plugin's **feature makes no sense on macOS** — it depends on a Windows-only OS facility (registry, shell, taskbar, UAC, ActiveX, Active-Scripting), a Windows-only external app, or something macOS already does natively. .NET/Delphi plugins whose feature is meaningful are **port candidates** (rewrite), not exclusions.

## How this was produced

- **One read-only agent per plugin** (141 agents; ~5.6M tokens; ~1,955 tool calls) read each plugin's source for UI surface (toolbar `NPPM_ADDTOOLBARICON`, `.rc` dialogs, `DockingDlgInterface`/`DMM_`, custom windows) and Windows-only APIs (Registry, COM/OLE, ActiveX, .NET, shell, SAPI, WMI, UAC, WebView2, WinINet…).

- **Lead-reviewed & re-judged** on the *feature-makes-sense-on-macOS* axis (not language): the agents' coarse “windows-specific” was split into genuine **Windows-OS-feature** vs **implementation-only** (swap a Win API) vs **managed-stack rewrite**. 11 binary-only (no-source) folders bucketed separately. 137/141 high confidence; no failures.

## At a glance
| Outcome | Count | |
|---|---:|---|
| ✅ **Worth porting** | **105** | feature is meaningful on macOS (effort varies) |
| &nbsp;&nbsp;↳ direct (portable C/C++) | 45 | least effort |
| &nbsp;&nbsp;↳ impl-swap (C/C++, replace a Win API) | 12 | e.g. SAPI→AVSpeech, WinINet→NSURLSession |
| &nbsp;&nbsp;↳ full rewrite (.NET / Delphi / Rust) | 48 | function portable, code is not |
| 🟢 **Already ported** (macOS port, different folder name) | 8 | see §0 |
| 🚫 **Don't port — Windows-OS feature** | 10 | registry/shell/taskbar/UAC/Win-only app |
| 🚫 **Don't port — meaningless** | 5 | native macOS dup / obsolete / dev-tool |
| 🚫 Demo / template | 2 | SDK samples |
| ⛔ No source available (binary-only) | 11 | can't port or verify |
| **Total** | **141** | |

The **No-UI** axis is orthogonal: **20 plugins have no UI** (menu/message-box only) — see §1.

🔧 **51 plugins add a main Notepad++ toolbar icon** (`NPPM_ADDTOOLBARICON`) — extra porting work (register the command + supply bitmaps). Flagged with 🔧 in §3 and the appendix:

> `3P`, `AndroidLogger`, `AnotherMarkdown`, `BigFiles`, `BlitzSearch`, `BunyanLogViewer`, `CADdyTools`, `CodeAlignmentNpp`, `CodeStats`, `CommentToggler`, `CSScriptNpp`, `CSVLint`, `CsvQuery`, `dark_mode_C`, `Explorer`, `FileFinder`, `FWDataViz`, `GitSCM`, `GotoLineCol`, `HugeFiles`, `ImgTag`, `JSFunctionViewer`, `JsonTools`, `LocationNavigate`, `MarkdownTableEditor`, `MarkdownViewerPlusPlus`, `MultiReplace`, `MusicPlayer_1.0.11x64`, `NavigateTo`, `NestedDSV`, `NewFileBrowser`, `npp.connections`, `NppDocShare`, `NppExec`, `NPPFSIPlugin`, `NppGist`, `NppGZipFileViewer`, `NppPluginDemo`, `NppQrCode64`, `NppRegExTractorPlugin`, `NppRgaIsaPlugin`, `NppScripts`, `NppSnippets`, `NppTags`, `NWScript-Npp`, `PlantUmlViewer`, `PreviewHTML`, `PythonScript`, `SourceCookifier`, `WakaTime`, `WebEdit`

---
## 0 · Already ported — macOS port exists under a different folder name

_These Windows folders are NOT underscore-prefixed, so the "underscore = already ported" convention missed them — but their feature is already available on macOS under a differently-named port. They are **not** porting candidates._

| Windows folder | Already on macOS as |
|---|---|
| `ComparePlugin` | ComparePlus (released) |
| `DiscordRPC` | notepadpp_rpc — Discord Rich Presence (released) |
| `nppConverter` | converter — ASCII<->Hex (local, not yet released) |
| `NppExport` | NPP_ExportPlugin (released) |
| `NPPJSONViewer` | JSON Viewer / NppJsonViewer (released) |
| `PoorMansTSqlFormatterNppPlugin` | PoorMansTSqlFormatter (released; C#->C++ reimpl) |
| `QuickText` | nppQuickText (released) |
| `urlPlugin` | nppURLPlugin — URL Encode/Decode (released) |

---
## 1 · Plugins with NO UI (orthogonal)

_Only Plugins-menu items (± a `MessageBox`→`NSAlert`); **no** toolbar icon, dialog, dockable panel, or custom window — so nothing to rebuild in AppKit. Source-verified._

| Plugin | Lang | UI | Worth porting? |
|---|---|---|---|
| `BracketsCheck` | .NET | menu-only | ✅ yes |
| `EmojiDescription` | C++ | menu-only | ✅ yes |
| `EnhanceAnyLexer` | Pascal/Delphi | messagebox-only | ✅ yes |
| `HLASMLexer` | C++ | menu-only | ✅ yes |
| `Linter` | C++ | menu-only | ✅ yes |
| `MZC8051` | C++ | messagebox-only | 🚫 Win-feature |
| `NppCrossCheck` | C++ | menu-only | ✅ yes |
| `NppExport` | C++ | menu-only | 🟢 already ported |
| `nppplugin_solutionhub` | C++ | messagebox-only | ✅ yes |
| `nppplugin_svn` | C++ | menu-only | 🚫 Win-feature |
| `RAScript` | C++ | messagebox-only | ✅ yes |
| `rdmd-en-x64` | Pascal/Delphi | menu-only | ✅ yes |
| `rdmd-ja-x64` | Pascal/Delphi | menu-only | ✅ yes |
| `Remove Duplicate Lines` | .NET | messagebox-only | ✅ yes |
| `rustnpp` | Rust | menu-only | ✅ yes |
| `SpeechPlugin` | C++ | menu-only | ✅ yes |
| `TCSyslogFinder` | C++ | menu-only | ✅ yes |
| `TreeSitterLexer` | C++ | messagebox-only | ✅ yes |
| `VSCodeKeymapNpp` | C++ | menu-only | ✅ yes |
| `XBrackets` | C++ | menu-only | ✅ yes |

**⭐ Lowest-effort ports overall** — no UI, portable C/C++ (8): `EmojiDescription`, `HLASMLexer`, `NppCrossCheck`, `nppplugin_solutionhub`, `RAScript`, `TreeSitterLexer`, `VSCodeKeymapNpp`, `XBrackets`.

---
## 2 · Don't port

### 2a · Windows-specific OS functionality — feature makes no macOS sense (10)

| Plugin | Lang | Why it makes no sense on macOS |
|---|---|---|
| `3P` | .NET | IDE for the Windows-only OpenEdge/Progress runtime (prowin32.exe) + Registry/Win32 hooks |
| `BlitzSearch` | C++ | Launcher/IPC shim for the separate Windows-only Blitz.exe desktop app |
| `Explorer` | C++ | Windows shell integration (IShellFolder/IContextMenu native context menus, IShellLink) |
| `MZC8051` | C++ | Front-end for a bundled Windows-only MZC8051.exe 8051 compiler |
| `NppJumpList` | C++ | Windows taskbar Jump List (ICustomDestinationList) — no macOS analog |
| `nppplugin_solutiontools` | C++ | Bundle whose SVN piece drives TortoiseSVN (Windows-only); registry HKLM |
| `nppplugin_svn` | C++ | Wraps TortoiseSVN.exe (Windows-only GUI client) via registry+CreateProcess |
| `NppRgaIsaPlugin` | C++ | Spawns AMD rga.exe to compile HLSL/DX12→AMD ISA (Windows GPU-dev workflow) |
| `NppSaveAsAdmin` | C++ | Windows UAC elevation (ShellExecuteEx "runas" + IAT-hooking Kernel32) |
| `Papyrus` | C++ | Compiles Bethesda Skyrim/Fallout scripts via Windows-only PapyrusCompiler.exe |

### 2b · Meaningless — native macOS feature / obsolete (5)

| Plugin | Lang | Why |
|---|---|---|
| `dark_mode_C` | C++ | Light/dark switching is native on macOS; host already has an appearance toggle |
| `Npp-Highlighter` | C++ | Reimplements scrollbar change/match markers Scintilla already provides natively |
| `NppGZipFileViewer` | .NET | Officially deprecated (README says use CompressedFileViewer) |
| `NppUISpy` | Pascal/Delphi | Win32 HMENU/toolbar introspection dev-tool — no end-user value, Windows-internals |
| `StayAwake_NPP` | C++ | macOS `caffeinate`/IOPMAssertion is native; no Scroll-Lock on Mac keyboards |

### 2c · Demo / template (2)

`NppPluginDemo`, `NppPluginTemplate` — Notepad++ plugin-SDK samples, not real features.

---
## 3 · Worth porting — by effort

### 3a · Direct — portable C/C++ (45)
_Cross-platform function in portable C/C++; main cost is rebuilding any Win32 UI in AppKit._

| Plugin | Lang | UI | Toolbar | Note |
|---|---|---|:--:|---|
| `AndroidLogger` | C++ | docking-panel | 🔧 | An Android-developer toolkit for Notepad++ that provides a logcat syn… |
| `BigFiles` | C++ | toolbar | 🔧 | A Notepad++ plugin that previews/pages through very large files by lo… |
| `BunyanLogViewer` | C++ | docking-panel | 🔧 | A Notepad++ plugin that parses Bunyan JSON log lines from the current… |
| `ColumnsPlusPlus` | C++ | dialog | — | A Notepad++ plugin for working with text/data arranged in columns: el… |
| `ColumnTools` | C++ | dialog | — | A Notepad++ plugin that highlights the current column (via Scintilla … |
| `CommentToggler` | C++ | toolbar | 🔧 | A single-command "toggle comment" plugin that auto-detects per-langua… |
| `EmojiDescription` | C++ | — | — | A Notepad++ plugin that shows the character-under-cursor's encoding i… |
| `FingerText2` | C++ | docking-panel | — | A tab-triggered snippet/template plugin: type a trigger word, press T… |
| `FWDataViz` | C++ | docking-panel | 🔧 | A Notepad++ plugin that visualizes fixed-width data files by color/st… |
| `GedcomLexer` | C++ | docking-panel | — | A Notepad++ plugin that provides Scintilla syntax highlighting for GE… |
| `GotoLineCol` | C++ | docking-panel | 🔧 | A Notepad++ plugin that navigates the editor to a specified line/colu… |
| `HLASMLexer` | C++ | — | — | A Notepad++ plugin that applies column-aware syntax highlighting to I… |
| `HTMLTag` | C++ | dialog | — | Notepad++ plugin for HTML/XML tag matching, renaming and selection, p… |
| `Language_Selector` | C++ | window | — | A Notepad++ plugin that lets the user quickly assign a programming la… |
| `Linter++` | C++ | docking-panel | — | A Notepad++ plugin that runs external checkstyle-compatible command-l… |
| `LocationNavigate` | C++ | docking-panel | 🔧 | A Notepad++ navigation plugin that records cursor-position history ac… |
| `MarkdownTableEditor` | C++ | multiple | 🔧 | A Notepad++ plugin that edits Markdown pipe tables in the editor buff… |
| `MultiReplace` | C++ | multiple | 🔧 | A Notepad++ plugin for complex, repeatable multi-search/replace manag… |
| `NestedDSV` | C++ | multiple | 🔧 | A Notepad++ plugin that visualizes nested (hierarchical) delimiter-se… |
| `NppCrossCheck` | C++ | — | — | Compares two whitespace-separated lists in the current document and a… |
| `nppcrypt` | C++ | dialog | — | A Notepad++ encryption plugin that encrypts/decrypts selected text or… |
| `NppDocShare` | C++ | docking-panel | 🔧 | A collaborative real-time document-sharing plugin (later renamed NppN… |
| `NppEditorConfig` | C++ | dialog | — | EditorConfig plugin that reads the nearest .editorconfig file via the… |
| `NppGTags` | C++ | multiple | — | A Notepad++ front-end to the GNU GLOBAL (gtags) and Universal Ctags s… |
| `NppJavaPlugin` | C++ | docking-panel | — | A Notepad++ plugin that compiles and runs the current Java file via t… |
| `nppplugin_ofis2` | C++ | dialog | — | A fast "Open File In Solution" finder (Visual Assist-style): type a s… |
| `nppplugin_solutionhub` | C++ | — | — | A headless backend service/broker plugin that indexes "solutions" (na… |
| `NppSnippets` | C++ | docking-panel | 🔧 | A snippet/template manager plugin that stores reusable code snippets … |
| `NppStripIpAndHost` | C++ | dialog | — | A Notepad++ plugin that sanitizes the current document by regex-repla… |
| `NppTags` | C++ | docking-panel | 🔧 | A Universal CTags plugin that indexes source code (via the external c… |
| `NppTaskList` | C++ | docking-panel | — | Scans the active document for keyword markers (TODO:, BUG:, FIX:, etc… |
| `NppTextViz` | C++ | docking-panel | — | A TextFX-derived plugin that hides/shows, copies, cuts, deletes and "… |
| `NppVim` | C++ | dialog | — | Adds Vim-style modal editing (Normal/Insert/Visual/Command modes, mot… |
| `NWScript-Npp` | C++ | multiple | 🔧 | A Notepad++ plugin that adds a Scintilla lexer (syntax highlighting +… |
| `NX_ASCII_Database_Helper` | C++ | docking-panel | — | A Notepad++ plugin for Siemens NX CAM ASCII database files that colum… |
| `pycalc` | C++ | dialog | — | A Notepad++ plugin that evaluates Python (embedded CPython 3.8) on th… |
| `PythonScript` | C++ | multiple | 🔧 | Embeds a full CPython interpreter into Notepad++, exposing the Notepa… |
| `RAScript` | C++ | — | — | A Notepad++ plugin that provides syntax highlighting for the RAScript… |
| `SecurePad` | C++ | dialog | — | A Notepad++ plugin that encrypts/decrypts the current document or sel… |
| `selectNLaunch` | C++ | dialog | — | Takes the editor's selected text, optionally Base64-decodes it, write… |
| `SurroundSelection` | C++ | dialog | — | A Notepad++ plugin that automatically wraps the current Scintilla sel… |
| `TreeSitterLexer` | C++ | — | — | A Notepad++ external lexer plugin that implements Scintilla's ILexer5… |
| `VirtualFolders` | C++ | docking-panel | — | Adds a dockable Notepad++ tree panel where users build a custom virtu… |
| `VSCodeKeymapNpp` | C++ | — | — | A native C++ Notepad++ plugin that remaps a curated set of VS Code ke… |
| `XBrackets` | C++ | — | — | A "smart" bracket/quote autocompletion plugin that inserts the matchi… |

### 3b · Impl-swap — C/C++, replace one Windows API (12)
_Feature is fine on macOS; swap a Windows-only API for the macOS equivalent._

| Plugin | Lang | UI | Toolbar | Note |
|---|---|---|:--:|---|
| `CollectionInterface` | C++ | dialog | — | WinINet → NSURLSession (drop UAC) |
| `Compose` | C++ | dialog | — | niche — macOS has native dead-keys/input sources |
| `GitSCM` | C++ | docking-panel | 🔧 | runs `git` CLI; drop TortoiseGit |
| `jN` | C++ | multiple | — | heavy — effectively a ground-up reimplementation |
| `Linter` | C++ | — | — | MSXML → libxml2 |
| `NewFileBrowser` | C++ | docking-panel | 🔧 | IE ActiveX preview → WKWebView |
| `NppEventExec` | C++ | dialog | — | rides on NppExec port |
| `NppExec` | C++ | multiple | 🔧 | CreateProcess/ConPTY → NSTask/pty (large) |
| `nppplugin_solutionhub_ui` | C++ | window | — | Win32 dialog → AppKit (config UI for SolutionHub) |
| `RestApiToText` | C++ | dialog | — | WinINet → NSURLSession/libcurl |
| `SpeechPlugin` | C++ | — | — | SAPI → AVSpeechSynthesizer |
| `TCSyslogFinder` | C++ | — | — | niche — Siemens Teamcenter-specific |

### 3c · Full rewrite — .NET / Delphi / Lazarus / Rust (48)
_Function is portable, but the managed/RAD code can't load in the C++ host — reimplement in C++ (as PoorMansTSqlFormatter was)._

| Plugin | Lang | UI | Toolbar | Note |
|---|---|---|:--:|---|
| `AnotherMarkdown` | .NET | multiple | 🔧 | ⚠ redundant — markdown preview already ported (NppMarkdownPanel) |
| `AutoCodepage` | Pascal/Delphi | dialog | — | Automatically switches a document's character encoding/code page base… |
| `AutoEolFormat` | Pascal/Delphi | dialog | — | A Notepad++ plugin that automatically converts the active document's … |
| `BracketsCheck` | .NET | — | — | A Notepad++ plugin that scans the current document (all text or selec… |
| `CADdyTools` | .NET | docking-panel | 🔧 | A surveying/geodesy plugin that reformats, sorts, code-swaps, and geo… |
| `CodeAlignmentNpp` | .NET | dialog | 🔧 | A "Code Alignment" plugin that vertically aligns source code by linin… |
| `CodeStats` | .NET | dialog | 🔧 | A Code::Stats XP tracker that counts editing activity per programming… |
| `CompressedFileViewer` | .NET | multiple | — | A Notepad++ plugin that transparently decompresses files on open and … |
| `CSScriptNpp` | .NET | multiple | 🔧 | A full C# (and VB.NET) script IDE inside Notepad++: edit, IntelliSens… |
| `CSVLint` | .NET | multiple | 🔧 | A CSV/fixed-width data quality tool for Notepad++ that adds syntax hi… |
| `CsvQuery` | .NET | docking-panel | 🔧 | A Notepad++ plugin that parses CSV/TSV (and similar) files, loads the… |
| `CustomLineNumbers` | Pascal/Delphi | dialog | — | Displays Notepad++ line numbers (and the status-bar line/column reado… |
| `dbgpPlugin` | Pascal/Delphi | multiple | — | A DBGp-protocol debugger client (built mainly for PHP/Xdebug) that tu… |
| `DraftSync` | .NET | dialog | — | A Notepad++ plugin that auto-saves unsaved "scratch" tabs as fun-name… |
| `EnhanceAnyLexer` | Pascal/Delphi | — | — | A Notepad++ plugin that applies additional regex-driven foreground co… |
| `ERPHelper` | .NET | docking-panel | — | A Notepad++ plugin providing Workday ERP integration developer utilit… |
| `ExtSettings` | Pascal/Delphi | dialog | — | A Notepad++ plugin offering a dialog to configure extra Scintilla edi… |
| `FileFinder` | .NET | window | 🔧 | A Notepad++ plugin to quickly open files by name via recursive file-n… |
| `HugeFiles` | .NET | window | 🔧 | A Notepad++ plugin that lets you view and edit very large files one c… |
| `ImgTag` | .NET | multiple | 🔧 | A Notepad++ helper that inserts/updates HTML <img> tags (with auto wi… |
| `JSFunctionViewer` | .NET | docking-panel | 🔧 | A Notepad++ plugin that, when a JavaScript function name is selected,… |
| `JsMapParser.NppPlugin` | .NET | docking-panel | — | A JavaScript "Map Parser" that parses JS/HTML source and shows a navi… |
| `JsonTools` | .NET | multiple | 🔧 | A feature-rich Notepad++ plugin for working with JSON: pretty-print/c… |
| `MarkdownViewerPlusPlus` | .NET | multiple | 🔧 | ⚠ redundant — markdown preview already ported |
| `Merge files in one` | .NET | window | — | A C#/.NET Notepad++ plugin that opens a WinForms dialog to merge two … |
| `MusicPlayer_1.0.11x64` | .NET | toolbar | 🔧 | low value — plays music inside the editor |
| `NavigateTo` | .NET | docking-panel | 🔧 | A fuzzy file/tab navigator that lets you type a keyword to quickly se… |
| `npp.connections` | Pascal/Delphi | multiple | 🔧 | A Notepad++ plugin that connects to MS SQL / Sybase / PostgreSQL / OD… |
| `NppESPHome` | Pascal/Delphi | multiple | — | A Notepad++ plugin that wraps the external ESPHome CLI, letting users… |
| `NPPFSIPlugin` | Pascal/Delphi | docking-panel | 🔧 | Embeds an F# Interactive (FSI) REPL in a dockable Notepad++ console p… |
| `NppGist` | .NET | window | 🔧 | A Notepad++ plugin for managing GitHub Gists (create, edit, delete, r… |
| `NppMenuSearch` | .NET | window | — | Adds a search text box to the Notepad++ toolbar (plus a floating fall… |
| `NppQrCode64` | Pascal/Delphi | multiple | 🔧 | A Notepad++ plugin that generates a QR code image from the currently … |
| `nppRandomStringGenerator` | .NET | window | — | Generates any number of random strings/passwords (or GUIDs) into a ne… |
| `NppRegExTractorPlugin` | .NET | docking-panel | 🔧 | A Notepad++ plugin that is a thin wrapper embedding the external Wind… |
| `NppScripts` | .NET | docking-panel | 🔧 | A managed Notepad++ plugin (part of CS-Script.Npp) that lets users au… |
| `PlantUmlViewer` | .NET | multiple | 🔧 | A Notepad++ plugin that takes the current document's text, pipes it t… |
| `PreviewHTML` | Pascal/Delphi | docking-panel | 🔧 | ≈ overlaps existing HTML/markdown preview |
| `rdmd-en-x64` | Pascal/Delphi | — | — | "RDMD for Notepad++" compiles/runs the currently open source file via… |
| `rdmd-ja-x64` | Pascal/Delphi | — | — | "RDMD for Notepad++" compiles/runs the currently-open file with D-lan… |
| `RedisPlugin` | .NET | docking-panel | — | A Notepad++ plugin that connects to a Redis server, lists its keys (w… |
| `Remove Duplicate Lines` | .NET | — | — | A Notepad++ plugin that removes duplicate lines from the current Scin… |
| `rustnpp` | Rust | — | — | A Notepad++ plugin that adds "Run" and "Build" menu commands to compi… |
| `SourceCookifier` | .NET | multiple | 🔧 | A Notepad++ source-code symbol/outline browser: it runs bundled Exube… |
| `VirtualTabGroups` | .NET | docking-panel | — | A dockable Notepad++ panel that lets users drag open documents into h… |
| `WakaTime` | .NET | dialog | 🔧 | Automatic coding time-tracker that queues editing/save "heartbeats" (… |
| `WebEdit` | .NET | toolbar | 🔧 | A Notepad++ plugin that wraps the selected text in customizable tag p… |
| `zoomdisabler_x64` | Pascal/Delphi | dialog | — | A Notepad++ plugin that disables Ctrl+mouse-wheel and/or Ctrl+keyboar… |

---
## 4 · No source available — binary-only (11)

_Cloned repo ships no source (binaries only in GitHub Releases, or docs-only). Can't port/verify. 7 are clones of the source-less `francostellari/NppPlugins` repo._

`AutoSave`, `BookmarksDook`, `LanguageHelp`, `MenuIcons`, `OpenSelection`, `PlanetCNCNpp64`, `RegexTrainer`, `RunMe`, `ShtirlitzNppPlugin`, `TakeNotes`, `TopMost`.

---
## Appendix · Full classification (all 141)

| Plugin | Lang | UI | Toolbar | Has UI | Outcome | Effort | Conf |
|---|---|---|:--:|:--:|---|---|:--:|
| `3P` | .NET | multiple | 🔧 | yes | 🚫 Win-feature | — | high |
| `AndroidLogger` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `AnotherMarkdown` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `AutoCodepage` | Pascal/Delphi | dialog | — | yes | ✅ port | rewrite | high |
| `AutoEolFormat` | Pascal/Delphi | dialog | — | yes | ✅ port | rewrite | high |
| `AutoSave` | Pascal/Delphi | dialog | — | yes | ⛔ no-source | — | high |
| `BigFiles` | C++ | toolbar | 🔧 | yes | ✅ port | direct | high |
| `BlitzSearch` | C++ | toolbar | 🔧 | yes | 🚫 Win-feature | — | high |
| `BookmarksDook` | Pascal/Delphi | none | — | no | ⛔ no-source | — | high |
| `BracketsCheck` | .NET | menu-only | — | no | ✅ port | rewrite | high |
| `BunyanLogViewer` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `CADdyTools` | .NET | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `CodeAlignmentNpp` | .NET | dialog | 🔧 | yes | ✅ port | rewrite | high |
| `CodeStats` | .NET | dialog | 🔧 | yes | ✅ port | rewrite | high |
| `CollectionInterface` | C++ | dialog | — | yes | ✅ port | impl-swap | high |
| `ColumnsPlusPlus` | C++ | dialog | — | yes | ✅ port | direct | high |
| `ColumnTools` | C++ | dialog | — | yes | ✅ port | direct | high |
| `CommentToggler` | C++ | toolbar | 🔧 | yes | ✅ port | direct | high |
| `ComparePlugin` | C++ | multiple | — | yes | 🟢 already ported | — | high |
| `Compose` | C++ | dialog | — | yes | ✅ port | impl-swap | high |
| `CompressedFileViewer` | .NET | multiple | — | yes | ✅ port | rewrite | high |
| `CSScriptNpp` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `CSVLint` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `CsvQuery` | .NET | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `CustomLineNumbers` | Pascal/Delphi | dialog | — | yes | ✅ port | rewrite | high |
| `dark_mode_C` | C++ | multiple | 🔧 | yes | 🚫 meaningless | — | high |
| `dbgpPlugin` | Pascal/Delphi | multiple | — | yes | ✅ port | rewrite | high |
| `DiscordRPC` | C++ | dialog | — | yes | 🟢 already ported | — | high |
| `DraftSync` | .NET | dialog | — | yes | ✅ port | rewrite | high |
| `EmojiDescription` | C++ | menu-only | — | no | ✅ port | direct | high |
| `EnhanceAnyLexer` | Pascal/Delphi | messagebox-only | — | no | ✅ port | rewrite | high |
| `ERPHelper` | .NET | docking-panel | — | yes | ✅ port | rewrite | high |
| `Explorer` | C++ | docking-panel | 🔧 | yes | 🚫 Win-feature | — | high |
| `ExtSettings` | Pascal/Delphi | dialog | — | yes | ✅ port | rewrite | high |
| `FileFinder` | .NET | window | 🔧 | yes | ✅ port | rewrite | high |
| `FingerText2` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `FWDataViz` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `GedcomLexer` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `GitSCM` | C++ | docking-panel | 🔧 | yes | ✅ port | impl-swap | high |
| `GotoLineCol` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `HLASMLexer` | C++ | menu-only | — | no | ✅ port | direct | high |
| `HTMLTag` | C++ | dialog | — | yes | ✅ port | direct | high |
| `HugeFiles` | .NET | window | 🔧 | yes | ✅ port | rewrite | high |
| `ImgTag` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `jN` | C++ | multiple | — | yes | ✅ port | impl-swap | high |
| `JSFunctionViewer` | .NET | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `JsMapParser.NppPlugin` | .NET | docking-panel | — | yes | ✅ port | rewrite | high |
| `JsonTools` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `Language_Selector` | C++ | window | — | yes | ✅ port | direct | high |
| `LanguageHelp` | C++ | multiple | — | yes | ⛔ no-source | — | high |
| `Linter` | C++ | menu-only | — | no | ✅ port | impl-swap | high |
| `Linter++` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `LocationNavigate` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `MarkdownTableEditor` | C++ | multiple | 🔧 | yes | ✅ port | direct | high |
| `MarkdownViewerPlusPlus` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `MenuIcons` | Pascal/Delphi | none | — | no | ⛔ no-source | — | high |
| `Merge files in one` | .NET | window | — | yes | ✅ port | rewrite | high |
| `MultiReplace` | C++ | multiple | 🔧 | yes | ✅ port | direct | high |
| `MusicPlayer_1.0.11x64` | .NET | toolbar | 🔧 | yes | ✅ port | rewrite | high |
| `MZC8051` | C++ | messagebox-only | — | no | 🚫 Win-feature | — | high |
| `NavigateTo` | .NET | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `NestedDSV` | C++ | multiple | 🔧 | yes | ✅ port | direct | high |
| `NewFileBrowser` | C++ | docking-panel | 🔧 | yes | ✅ port | impl-swap | high |
| `Npp-Highlighter` | C++ | window | — | yes | 🚫 meaningless | — | high |
| `npp.connections` | Pascal/Delphi | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `nppConverter` | C++ | docking-panel | — | yes | 🟢 already ported | — | high |
| `NppCrossCheck` | C++ | menu-only | — | no | ✅ port | direct | high |
| `nppcrypt` | C++ | dialog | — | yes | ✅ port | direct | high |
| `NppDocShare` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `NppEditorConfig` | C++ | dialog | — | yes | ✅ port | direct | high |
| `NppESPHome` | Pascal/Delphi | multiple | — | yes | ✅ port | rewrite | high |
| `NppEventExec` | C++ | dialog | — | yes | ✅ port | impl-swap | high |
| `NppExec` | C++ | multiple | 🔧 | yes | ✅ port | impl-swap | high |
| `NppExport` | C++ | menu-only | — | no | 🟢 already ported | — | high |
| `NPPFSIPlugin` | Pascal/Delphi | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `NppGist` | .NET | window | 🔧 | yes | ✅ port | rewrite | high |
| `NppGTags` | C++ | multiple | — | yes | ✅ port | direct | high |
| `NppGZipFileViewer` | .NET | multiple | 🔧 | yes | 🚫 meaningless | — | high |
| `NppJavaPlugin` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `NPPJSONViewer` | C++ | docking-panel | — | yes | 🟢 already ported | — | high |
| `NppJumpList` | C++ | dialog | — | yes | 🚫 Win-feature | — | high |
| `NppMenuSearch` | .NET | window | — | yes | ✅ port | rewrite | high |
| `nppplugin_ofis2` | C++ | dialog | — | yes | ✅ port | direct | high |
| `nppplugin_solutionhub` | C++ | messagebox-only | — | no | ✅ port | direct | high |
| `nppplugin_solutionhub_ui` | C++ | window | — | yes | ✅ port | impl-swap | medium |
| `nppplugin_solutiontools` | C++ | window | — | yes | 🚫 Win-feature | — | high |
| `nppplugin_svn` | C++ | menu-only | — | no | 🚫 Win-feature | — | high |
| `NppPluginDemo` | C++ | docking-panel | 🔧 | yes | demo | — | high |
| `NppPluginTemplate` | C++ | multiple | — | yes | demo | — | high |
| `NppQrCode64` | Pascal/Delphi | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `nppRandomStringGenerator` | .NET | window | — | yes | ✅ port | rewrite | high |
| `NppRegExTractorPlugin` | .NET | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `NppRgaIsaPlugin` | C++ | docking-panel | 🔧 | yes | 🚫 Win-feature | — | high |
| `NppSaveAsAdmin` | C++ | dialog | — | yes | 🚫 Win-feature | — | high |
| `NppScripts` | .NET | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `NppSnippets` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `NppStripIpAndHost` | C++ | dialog | — | yes | ✅ port | direct | high |
| `NppTags` | C++ | docking-panel | 🔧 | yes | ✅ port | direct | high |
| `NppTaskList` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `NppTextViz` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `NppUISpy` | Pascal/Delphi | multiple | — | yes | 🚫 meaningless | — | medium |
| `NppVim` | C++ | dialog | — | yes | ✅ port | direct | high |
| `NWScript-Npp` | C++ | multiple | 🔧 | yes | ✅ port | direct | high |
| `NX_ASCII_Database_Helper` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `OpenSelection` | Pascal/Delphi | none | — | no | ⛔ no-source | — | high |
| `Papyrus` | C++ | docking-panel | — | yes | 🚫 Win-feature | — | high |
| `PlanetCNCNpp64` | C++ | window | — | yes | ⛔ no-source | — | medium |
| `PlantUmlViewer` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `PoorMansTSqlFormatterNppPlugin` | .NET | dialog | — | yes | 🟢 already ported | — | high |
| `PreviewHTML` | Pascal/Delphi | docking-panel | 🔧 | yes | ✅ port | rewrite | high |
| `pycalc` | C++ | dialog | — | yes | ✅ port | direct | high |
| `PythonScript` | C++ | multiple | 🔧 | yes | ✅ port | direct | high |
| `QuickText` | C++ | dialog | — | yes | 🟢 already ported | — | high |
| `RAScript` | C++ | messagebox-only | — | no | ✅ port | direct | high |
| `rdmd-en-x64` | Pascal/Delphi | menu-only | — | no | ✅ port | rewrite | high |
| `rdmd-ja-x64` | Pascal/Delphi | menu-only | — | no | ✅ port | rewrite | high |
| `RedisPlugin` | .NET | docking-panel | — | yes | ✅ port | rewrite | high |
| `RegexTrainer` | .NET | docking-panel | — | yes | ⛔ no-source | — | high |
| `Remove Duplicate Lines` | .NET | messagebox-only | — | no | ✅ port | rewrite | high |
| `RestApiToText` | C++ | dialog | — | yes | ✅ port | impl-swap | high |
| `RunMe` | C++ | dialog | — | yes | ⛔ no-source | — | high |
| `rustnpp` | Rust | menu-only | — | no | ✅ port | rewrite | high |
| `SecurePad` | C++ | dialog | — | yes | ✅ port | direct | high |
| `selectNLaunch` | C++ | dialog | — | yes | ✅ port | direct | high |
| `ShtirlitzNppPlugin` | .NET | messagebox-only | — | no | ⛔ no-source | — | high |
| `SourceCookifier` | .NET | multiple | 🔧 | yes | ✅ port | rewrite | high |
| `SpeechPlugin` | C++ | menu-only | — | no | ✅ port | impl-swap | high |
| `StayAwake_NPP` | C++ | docking-panel | — | yes | 🚫 meaningless | — | high |
| `SurroundSelection` | C++ | dialog | — | yes | ✅ port | direct | high |
| `TakeNotes` | Pascal/Delphi | dialog | — | yes | ⛔ no-source | — | high |
| `TCSyslogFinder` | C++ | menu-only | — | no | ✅ port | impl-swap | high |
| `TopMost` | C++ | dialog | — | yes | ⛔ no-source | — | high |
| `TreeSitterLexer` | C++ | messagebox-only | — | no | ✅ port | direct | high |
| `urlPlugin` | C++ | dialog | — | yes | 🟢 already ported | — | high |
| `VirtualFolders` | C++ | docking-panel | — | yes | ✅ port | direct | high |
| `VirtualTabGroups` | .NET | docking-panel | — | yes | ✅ port | rewrite | high |
| `VSCodeKeymapNpp` | C++ | menu-only | — | no | ✅ port | direct | high |
| `WakaTime` | .NET | dialog | 🔧 | yes | ✅ port | rewrite | medium |
| `WebEdit` | .NET | toolbar | 🔧 | yes | ✅ port | rewrite | high |
| `XBrackets` | C++ | menu-only | — | no | ✅ port | direct | high |
| `zoomdisabler_x64` | Pascal/Delphi | dialog | — | yes | ✅ port | rewrite | high |
