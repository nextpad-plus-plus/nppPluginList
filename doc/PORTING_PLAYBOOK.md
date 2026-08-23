# Notepad++ plugin → macOS port playbook (agent instructions)

Reference implementation: **`nppPluginsMacOS/CommentToggler.macos/`** (a complete, building port — read it).
Host plugin API header: `notepad-plus-plus-macos/src/NppPluginInterfaceMac.h` (read-only).
Host Scintilla: `notepad-plus-plus-macos/scintilla/include/Scintilla.h` (+ `Sci_Position.h`).

## HARD CONSTRAINTS (violating any = failure)
1. **NO HOST CHANGES.** Never create/modify/delete anything under `notepad-plus-plus-macos/`. Include its headers read-only.
2. **Do NOT touch any existing folder** under `nppPluginsMacOS/`. Only create your new `<WindowsFolder>.macos` folder.
3. If something needs a host feature that doesn't exist → **document it and stop**, do not hack the host.
4. Build must be **universal (arm64;x86_64)**, export all 5 symbols, and **succeed** before you stage or push.

## Known host facts (verified — saves you time; still confirm per plugin)
**Works (use freely):** `NPPM_ADDTOOLBARICON_FORDARKMODE` (toolbar icons — ship `toolbar.png`/`toolbar_dark.png` at plugin root); `NPPM_GETCURRENTSCINTILLA`; `NPPM_GETPLUGINSCONFIGDIR`; `NPPM_GETNPPSETTINGSDIRPATH` (= host config dir); `NPPM_GETCURRENTLANGTYPE` (canonical Windows `L_*`); `NPPM_GETLANGUAGENAME/DESC`; `NPPM_SETMENUITEMCHECK`; `NPPM_DOOPEN`; standard Scintilla `SCI_*`; notifications `SCN_CHARADDED`/`SCN_MODIFIED`/`SCN_UPDATEUI`/`NPPN_BUFFERACTIVATED`/`NPPN_TBMODIFICATION`/`NPPN_SHUTDOWN` reach `beNotified`.

**Does NOT work — work around it, NEVER change the host:**
- `NPPM_SETSTATUSBAR` — **declared but not implemented** (returns 0, no-op). Don't use it for required output; use `NSAlert` or your own surface.
- **Plugin command shortcuts (`FuncItem._pShKey`) are ignored** (`NppPluginManager.mm:478` `// TODO`). A default shortcut won't bind. To set a host menu shortcut, write `shortcuts.xml <InternalCommands>` keyed by the command's Obj-C **selector name**, applied at launch (restart-to-apply) — see `nppPluginsMacOS/VSCodeKeymapNpp.macos`.
- **Keystroke interception** (CORRECTED): the host does NOT forward raw keys via `beNotified`/`SCN_KEY`, **BUT a plugin can install its own process-wide `NSEvent` monitor** — `+[NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown]`, return `nil` to swallow — **no host change**. Established idiom: `SurroundSelection.macos`, DoxyIt, DSpellCheck. **Gate it** on the editor pane having focus + the right state so you don't hijack Find fields/dialogs. (`SCN_CHARADDED` is also forwarded — for char-added reactions like bracket-autoclose either approach works.) `NPPM_GETSHORTCUTBYCMDID`/`REMOVESHORTCUTBYCMDID` remain unimplemented — bind host *menu* shortcuts via `shortcuts.xml` (above).
- `NPPM_MENUCOMMAND` honors only a small built-in IDM whitelist (41001/41002/41006/41003/41004 = New/Open/Save/Close/CloseAll), not arbitrary `IDM_*`. In particular `IDM_FORMAT_*` (encoding/EOL menu) do NOT work — apply EOL via `SCI_CONVERTEOLS`+`SCI_SETEOLMODE`; **encoding has no plugin-reachable apply path** (`NPPM_SETBUFFERENCODING` is declared-but-unimplemented; `SCI_SETCODEPAGE` only changes display) — verified by NppEditorConfig + AutoCodepage.
- **File-lifecycle notifications: only `NPPN_FILESAVED` + `NPPN_BUFFERACTIVATED` are dispatched to plugins** (verified: `EditorView.mm:980`, `MainWindowController.mm:8342`). `NPPN_FILEOPENED` and `NPPN_FILEBEFORECLOSE` are declared but **never fired** — react to file-open via `NPPN_BUFFERACTIVATED` (it fires when a freshly-opened buffer becomes active *and* on every tab switch) and to writes via `NPPN_FILESAVED`. (`NPPN_READY`, `NPPN_SHUTDOWN`/`NPPN_BEFORESHUTDOWN`, `NPPN_TBMODIFICATION` and the `SCN_*` are dispatched.)
- **Only the CURRENT buffer is reachable.** There's no plugin message to read a non-active buffer's text/path: `NPPM_GETOPENFILENAMES` skips untitled tabs, and only `NPPM_GETCURRENTSCINTILLA` exists. A plugin that needs to act on *all* open buffers can only act on the active one (mirror on `NPPN_BUFFERACTIVATED`). `NPPM_GETCURRENTWORD`, `NPPM_SAVECURRENTFILEAS`, `NPPM_RELOADFILE`, `NPPM_ACTIVATEDOC`, `NPPM_SETCURRENTLANGTYPE` are also unimplemented — use Scintilla equivalents where possible (`SCI_WORDSTART/ENDPOSITION` for the current word).
- No app-global busy cursor a plugin can set (drop Win32 `SetCursor(IDC_WAIT)`).

## Steps
1. **Investigate deeply.** Read the Windows source under `nppPluginsWin64/<folder>/` (PluginDefinition.cpp = menu/commands; the main .cpp = DllMain/exports/beNotified; .rc = dialogs/menus/icons). Understand every command, dialog, and toolbar icon. Identify Windows-only APIs to replace.
2. **Create** `nppPluginsMacOS/<folder>.macos/` with `src/` and (if needed) `resources/`. Abort if it already exists.
3. **Copy** any `LICENSE*`, `*.md`/`README*`, and original toolbar icon files (`.ico/.bmp/.png`) from the Windows folder into the `.macos` folder (originals → `resources/`).
4. **Convert toolbar icons** to transparent PNG with `sips`:
   - Prefer the `.ico` (they carry alpha): `sips -s format png IN.ico --out toolbar.png`. Verify `sips -g hasAlpha` = yes.
   - A `_black`/`_dark` variant → `toolbar_dark.png`; the plain/light one → `toolbar.png`. Check the Windows `.rc` / `LoadIcon` calls to see which id is light vs dark-mode.
   - `.bmp` toolbar bitmaps often use magenta `#FF00FF` (or the corner pixel) as transparent — if you must use a `.bmp`, make that color transparent (sips can't; note it / prefer the `.ico`).
   - Put `toolbar.png` + `toolbar_dark.png` at the `.macos` **root** (host looks there first).
5. **Write `src/<Name>.mm`** — port the logic faithfully. Platform mapping:
   - Skeleton + exports: copy CommentToggler.mm's shape (`setInfo`/`getName`/`getFuncsArray`/`beNotified`/`messageProc`, `NPP_EXPORT`, `FuncItem`, `NppData`).
   - `::SendMessage(scintilla,…)` → `nppData._sendMessage(sci, msg, w, l)`; resolve the current Scintilla via `NPPM_GETCURRENTSCINTILLA` (which=0→main,1→second).
   - `::SendMessage(nppHandle, NPPM_*,…)` → `nppData._sendMessage(nppData._nppHandle, NPPM_*, …)`.
   - Multi-byte: TCHAR==char on macOS; menu item names are UTF-8 `char` in `_itemName[NPP_MENU_ITEM_SIZE]`.
   - `MessageBox` → `NSAlert`. `ShellExecute(url)` → `[[NSWorkspace sharedWorkspace] openURL:…]`. `ShellExecute(file)`/run program → `NSTask`.
   - Win file APIs (`CreateFile`/`ReadFile`/`FindFirstFile`) → `NSFileManager`/`NSData`/`std::ifstream`. Registry/INI config → a plist or INI in the config dir.
   - Config/data dir: `nppData._sendMessage(nppData._nppHandle, NPPM_GETPLUGINSCONFIGDIR, sizeof(buf), (intptr_t)buf)`. Bundled resources next to the dylib: resolve via `dladdr(&someFn)` → dylib dir → `/resources`.
   - **Toolbar icon**: in `beNotified` `case NPPN_TBMODIFICATION:` call `nppData._sendMessage(nppData._nppHandle, NPPM_ADDTOOLBARICON_FORDARKMODE, (uintptr_t)funcItem[N]._cmdID, 0);` (lParam 0 → host loads `toolbar.png`/`toolbar_dark.png`). For >1 toolbar icon, pass a distinct C-string hint as lParam and ship `<hint>.png`/`<hint>_dark.png`.
   - **Dialogs**: reimplement Win32 DIALOG templates as **programmatic AppKit** (`NSWindow`/`NSPanel`/`NSAlert` + controls). Reference existing dialog ports: `nppPluginsMacOS/DSpellCheck/src/DSpellCheck.mm`, `nppPluginsMacOS/RandomValuesNppPlugin`. Wire control actions to the same logic the Windows dialog drove. Keep it modal `[NSApp runModalForWindow:]` or a retained panel, matching the original's modality.
   - Shortcuts: leave `_pShKey = nullptr` unless the Windows key maps cleanly and doesn't collide (Cmd+Q = Quit on macOS — never use). Note any dropped shortcut.
6. **Write `CMakeLists.txt`** — copy CommentToggler's verbatim, change the `project(<Name> …)` name, sources, and `PLUGIN_INSTALL_DIR`/install files. Universal, deploy 11.0, ARC, `.dylib`, `-current_version`. If the plugin needs a vendored C/C++ lib, add it as a static lib (see ChineseConverter/DSpellCheck).
   - **⚠️ CRITICAL — dylib filename MUST equal your `.macos` folder's base name.** The host loads each plugin as `plugins/<Folder>/<Folder>.dylib` (`NppPluginManager.mm:243` `dirName + ".dylib"`; the *only* other accepted name is `<Folder>.bundle`). Your folder is `<WindowsFolder>.macos`, so the dylib **must** be named `<WindowsFolder>.dylib` (e.g. folder `rdmd-en-x64.macos` → `rdmd-en-x64.dylib`, staged at `plugins-new/rdmd-en-x64/rdmd-en-x64.dylib`). If your `project()`/target name differs from `<WindowsFolder>`, you MUST set `set_target_properties(<tgt> PROPERTIES OUTPUT_NAME "<WindowsFolder>")` (and match `PLUGIN_INSTALL_DIR`/staging folder), or the host silently skips the plugin. A dylib named anything else = **non-loadable = failed port.**
7. **Build + verify**: `cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j`. Then `lipo -archs` = `x86_64 arm64`; `nm -gU` shows setInfo/getName/getFuncsArray/beNotified/messageProc; `otool -l` current version. Fix all warnings/errors.
8. **Stage** into `~/Library/Application Support/Nextpad++/plugins-new/<Name>/`: the `.dylib`, `toolbar.png`/`toolbar_dark.png` (if any), and any `resources/` the plugin reads. Folder name = dylib base name (no `.macos`).
9. **Repo**: `git init` + commit (end message with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`), `git branch -M main`, `gh repo create nextpad-plus-plus-plugins/<folder>.macos --public --description "…"`, `git remote add origin git@github.com:nextpad-plus-plus-plugins/<folder>.macos.git`, `git push -u origin main`. `.gitignore`: `build/`, `*.dylib`, `.DS_Store`. Do **not** create a GitHub release and do **not** touch any plugin catalog/index.

## Return (structured)
Report: built (yes/no), arch, exports ok, what UI was ported (menu/dialog/toolbar), Windows APIs replaced, any host limitation or feature you could NOT port (and why), repo URL, and anything the user should know when testing.
