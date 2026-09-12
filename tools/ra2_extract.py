"""Extract per-screen specifications from the reference engine.

The reference is a TypeScript project (Tauri/WebView shell). Every screen
under `src/gui/screen/<area>/` declares its title, sidebar button list, and
the screen it pushes (or action it takes) when clicked. This script walks
those files and emits a machine-checkable table so the Zan port has an
authoritative spec to diff against.

Output: tools/ra2_spec/screens.json

For each screen we capture:
  - file:   path under the reference
  - title:  CSF key the screen sets (e.g. "GUI:MainMenu")
  - sidebar: list of {label, tooltip, isBottom, disabled, target}
  - flags:  hooks the screen pulls (toggleMainVideo, showVersion, etc.)

This is intentionally conservative: it uses a small set of patterns
matched against the AST-shaped text rather than a full TypeScript
parser, because the reference's structure is uniform enough that
string/regex works and avoids an extra dependency. The script is
deterministic and idempotent.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

REF = Path(r"D:\project\zan-lang\_scratch\reference-ra2\redalert2\src")
OUT = Path(r"D:\project\zan-lang\tools\ra2_spec\screens.json")

# Files of interest: a screen's `*Screen.ts` that has an onEnter with a
# sidebar button list. We scan the whole tree, but only emit screens that
# actually match the pattern.
SCREEN_FILES = sorted(REF.glob("gui/screen/**/*Screen.ts"))
SCREEN_FILES += [REF / "gui" / "screen" / "mainMenu" / "main" / "HomeScreen.ts"]
SCREEN_FILES = sorted(set(SCREEN_FILES))


def find_title(src: str) -> str:
    # `this.title = this.strings.get("GUI:Key")` -- the screen's own title.
    m = re.search(r"this\.title\s*=\s*this\.strings\.get\(\s*\"([^\"]+)\"", src)
    if m:
        return m.group(1)
    m = re.search(r"this\.title\s*=\s*this\.strings\.get\(\s*'([^']+)'", src)
    if m:
        return m.group(1)
    return ""


def find_version_hook(src: str) -> bool:
    return "showVersion(" in src


def find_main_video(src: str) -> bool:
    return "toggleMainVideo(" in src


def extract_buttons(onenter_body: str) -> list[dict]:
    out: list[dict] = []
    # Buttons in the reference come from four places:
    # 1. The inline array literal:  const buttons: SidebarButton[] = [ {...}, ... ]
    # 2. Spread inside it:          ...(cond ? [ {...} ] : [])
    # 3. Conditional push after:    if (cond) { buttons.push({...}) }
    # 4. Passed straight in:        setSidebarButtons([ {...}, ... ])
    out.extend(_buttons_in_array(onenter_body))
    out.extend(_buttons_in_push_calls(onenter_body))
    if not out:
        out.extend(_buttons_in_call_arg(onenter_body, "setSidebarButtons"))
    return out


def _buttons_in_call_arg(s: str, call: str) -> list[dict]:
    """`setSidebarButtons([ {...}, {...} ], true)` -- the array is the
    first argument of the call rather than a named local."""
    out: list[dict] = []
    m = re.search(rf"{call}\(\s*\[", s)
    if not m:
        return out
    lb = m.end() - 1
    rb = _find_matching_close(s, lb, "[", "]")
    if rb < 0:
        return out
    _collect_from_array(s, lb, rb, out)
    return out


def _buttons_in_array(onenter_body: str) -> list[dict]:
    out: list[dict] = []
    m = re.search(r"const\s+buttons\b[^\n]*?=\s*\[", onenter_body)
    if not m:
        return out
    lb = m.end() - 1
    # Walk the *whole* literal so we can recurse into ternary spreads.
    # We need a balanced-bracket walker; reuse the same depth counter and
    # collect any { ... label: ... } object, then check whether it is a
    # Spread of a ternary array, in which case we recurse into that
    # array's body too.
    arr_end = _find_matching_close(onenter_body, lb, "[", "]")
    if arr_end < 0:
        return out
    _collect_from_array(onenter_body, lb, arr_end, out)
    return out


def _collect_from_array(s: str, lb: int, rb: int, out: list[dict]) -> None:
    """Walk s[lb+1..rb-1] (an array body), collect top-level button
    objects, and recurse into ternary spreads.

    Depth bookkeeping: a button object sits at depth 1 -- one level
    inside the array. We start the counter at 1 (already inside the
    array) and look for '{' at depth 1; '[' at depth 1 is a nested
    array (e.g. the truthy branch of a spread ternary)."""
    depth = 1
    i = lb + 1
    while i < rb:
        c = s[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        elif c == "{" and depth == 1:
            block = _read_brace(s, i)
            i += len(block)
            stripped = block.lstrip()
            if "label" in stripped[:200] and stripped.find("label:") < 80:
                out.append(parse_button(block))
            continue
        elif c == "." and s[i:i + 3] == "..." and depth == 1:
            m = re.search(r"\?\s*\[", s[i:])
            if m:
                inner_lb = i + m.end() - 1
                inner_rb = _find_matching_close(s, inner_lb, "[", "]")
                if inner_rb > 0:
                    _collect_from_array(s, inner_lb, inner_rb, out)
                    i = inner_rb + 1
                    continue
        i += 1


def _find_matching_close(s: str, start: int, open_c: str,
                        close_c: str) -> int:
    depth = 0
    i = start
    while i < len(s):
        if s[i] == open_c:
            depth += 1
        elif s[i] == close_c:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _buttons_in_push_calls(onenter_body: str) -> list[dict]:
    """Catch the `if (cond) { buttons.push({...}, {...}); }` pattern: the
    reference adds buttons to the array after the literal, conditional
    on flags the build knows at runtime (storageEnabled, nativeShell).

    A single push can carry several button objects separated by `, `,
    so we walk the whole argument list rather than just the first."""
    out: list[dict] = []
    for m in re.finditer(r"buttons\.push\(", onenter_body):
        open_paren = m.end() - 1
        close_paren = _find_matching_close(onenter_body, open_paren, "(", ")")
        if close_paren < 0:
            continue
        args = onenter_body[open_paren + 1:close_paren]
        i = 0
        while i < len(args):
            if args[i] == "{":
                block = _read_brace(args, i)
                i += len(block)
                if "label" in block[:200]:
                    out.append(parse_button(block))
                continue
            i += 1
    return out


def _read_brace(s: str, start: int) -> str:
    """Return the substring from `start` (a '{') to the matching '}'."""
    depth = 0
    i = start
    while i < len(s):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
        i += 1
    return s[start:]


def parse_button(block: str) -> dict:
    info: dict = {"label": "", "tooltip": "", "isBottom": False,
                  "disabled": "", "target": "", "spreads": []}

    def grab(field: str, src: str) -> str:
        # Field values come in three shapes: a literal string, a
        # strings.get("KEY") call (optionally followed by "|| 'fallback'"),
        # and a strings.get with a hotkey as the second argument.
        m = re.search(
            rf"{field}\s*:\s*"
            r"(?P<v>\"[^\"]*\"|'[^']*'|"
            r"this\.strings\.get\(\s*['\"][^'\"]+['\"]"
            r"(?:\s*,\s*getHumanReadableKey\([^)]+\))?\s*\)"
            r"(?:\s*\|\|\s*['\"][^'\"]+['\"])?)",
            src)
        if not m:
            return ""
        v = m.group("v")
        m2 = re.search(r"strings\.get\(\s*['\"]([^'\"]+)['\"]", v)
        if m2:
            return m2.group(1)
        return v.strip('"').strip("'")

    info["label"] = grab("label", block)
    info["tooltip"] = grab("tooltip", block)
    info["disabled"] = grab("disabled", block)

    if re.search(r"\bisBottom\s*:\s*true\b", block):
        info["isBottom"] = True

    m = re.search(r"\.(?:pushScreen|goToScreen)\(\s*([A-Za-z0-9_.]+)\s*\)", block)
    if m:
        info["target"] = m.group(1)
    else:
        m = re.search(r"window\.location\.hash\s*=\s*['\"]([^'\"]+)['\"]", block)
        if m:
            info["target"] = "hash:" + m.group(1)
    if not info["target"]:
        if "toggleFullscreen" in block or "FullScreen" in block:
            info["target"] = "Fullscreen"
        elif "toggleAsync" in block:
            info["target"] = "Fullscreen"

    if "..." in block:
        info["spreads"].append("conditional")

    return info


def extract_onenter(src: str) -> str:
    return _method_body(src, "onEnter")


def extract_all_button_bodies(src: str) -> dict[str, list[dict]]:
    """Button lists can be declared in onEnter, or in a helper the screen
    calls (SkirmishScreen builds its three rows in
    `refreshSidebarButtons`). Return a mapping method -> buttons so the
    spec records where each list came from."""
    result: dict[str, list[dict]] = {}
    for method in ("onEnter", "refreshSidebarButtons", "initSidebarButtons",
                   "initSidebar", "updateSidebar", "buildSidebarButtons"):
        body = _method_body(src, method)
        if not body:
            continue
        btns = extract_buttons(body)
        if btns:
            result[method] = btns
    # Fallback: some screens declare the list in a helper with a name we
    # did not anticipate. Find any method whose body feeds
    # setSidebarButtons and mine that. A method that only *catches* an
    # exception mentioning the sidebar is not a button list, so require
    # the setSidebarButtons call to be a direct statement in the body.
    if not result:
        for m in re.finditer(r"(?:^|\n)\s*(?:(?:public|private|protected|"
                             r"static|async)\s+)*(\w+)\([^)]*\)[^{]*\{", src):
            name = m.group(1)
            if name in ("constructor", "captureException"):
                continue
            body = _method_body(src, name)
            if not re.search(r"(?:^|\n)\s*(?:this\.)?(?:controller\.)?"
                             r"setSidebarButtons\(", body):
                continue
            btns = extract_buttons(body)
            if btns:
                result[name] = btns
    return result


def _method_body(src: str, name: str) -> str:
    """Return the body of a *declaration* of `name`, not a call site.

    A declaration is preceded by a visibility/qualifier keyword or sits
    at the start of a line with no `this.` / `.` before it. Matching a
    call site (`this.refreshSidebarButtons()`) would then run forward to
    the next method's opening brace and return the wrong body."""
    pat = (rf"(?:^|\n)\s*(?:(?:public|private|protected|static|async)\s+)*"
           rf"{name}\([^)]*\)[^{{]*\{{")
    m = re.search(pat, src)
    if not m:
        return ""
    start = m.end() - 1
    depth = 0
    i = start
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[start + 1:i]
        i += 1
    return ""


def main() -> None:
    spec: list[dict] = []
    for f in SCREEN_FILES:
        if not f.exists():
            continue
        src = f.read_text(encoding="utf-8", errors="replace")
        title = find_title(src)
        if not title:
            continue
        lists = extract_all_button_bodies(src)
        merged: list[dict] = []
        origins: list[str] = []
        for method, btns in lists.items():
            merged.extend(btns)
            origins.append(f"{method}({len(btns)})")
        if not merged and "setSidebarButtons" not in src:
            continue
        # The second argument of setSidebarButtons(list, true) marks a
        # screen whose sidebar replaces the previous one outright.
        replace = bool(re.search(r"setSidebarButtons\([^;]*,\s*true\s*\)", src))
        entry = {
            "file": str(f.relative_to(REF.parent)),
            "title": title,
            "showVersion": find_version_hook(src),
            "toggleMainVideo": find_main_video(src),
            "sidebarOrigins": origins,
            "sidebarReplace": replace,
            "sidebar": merged,
        }
        if "hideSidebarButtons" in src:
            entry["hidesSidebar"] = True
        if "toggleSidebarPreview" in src:
            entry["sidebarPreview"] = True
        if "setSidebarMpContent" in src:
            entry["sidebarMpText"] = True
        spec.append(entry)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"wrote {len(spec)} screens to {OUT}")
    for s in spec:
        print(f"  {s['title']:26} n={len(s['sidebar']):2} "
              f"{','.join(s['sidebarOrigins'])}")


if __name__ == "__main__":
    main()
