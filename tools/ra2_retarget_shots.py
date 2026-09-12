"""Rewrite the RA2 self-test screenshot paths onto the run-scoped ShotPath().

Every capture must land in that run's own directory, so a stale file can
never be read as a fresh one. This rewrites the string literal
"build/ra2_shot_x.bmp" into Ra2App.ShotPath("ra2_shot_x.bmp").

Deterministic, so it can be re-run after a checkout without double-applying.
"""
import re
import sys
from pathlib import Path

SRC = Path(r"D:\project\zan-lang\templates\game\ra2\src\main.zan")

# Match DumpScreen("build/ra2_shot_...bmp" but NOT one already wrapped in
# ShotPath(...). The negative lookbehind on ShotPath( would not work across
# the quote, so instead we skip lines that already contain ShotPath.
PAT = re.compile(r'"build/(ra2_shot_[A-Za-z0-9_]+\.bmp)"')

text = SRC.read_text(encoding="utf-8")
lines = text.split("\n")
out = []
changed = 0
for line in lines:
    if "ShotPath" in line:
        out.append(line)
        continue
    new, n = PAT.subn(r'Ra2App.ShotPath("\1")', line)
    if n:
        changed += n
    out.append(new)

SRC.write_text("\n".join(out), encoding="utf-8")
print(f"rewrote {changed} screenshot paths")
