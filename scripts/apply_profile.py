#!/usr/bin/env python3
"""Put the values from profile.md into every {{PLACEHOLDER}} in the project. Stdlib only.

Usage: python3 scripts/apply_profile.py [--check]
Reads lines like  - `{{FULL_NAME}}` = Jane Doe  from profile.md, replaces the placeholders in CLAUDE.md,
.claude/**/*.md and docs/*.md, then lists any placeholder still left. --check only lists, changes nothing.
"""
import argparse, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINE_RE = re.compile(r"^- `\{\{([A-Z_]+)\}\}` = ?(.*)$")
TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


def targets():
    yield ROOT / "CLAUDE.md"
    # the setup skill talks about placeholders by name, so it is left as is
    yield from (p for p in (ROOT / ".claude").rglob("*.md") if "skills/setup" not in p.as_posix())
    yield from (ROOT / "docs").rglob("*.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    values = {}
    for line in (ROOT / "profile.md").read_text().splitlines():
        m = LINE_RE.match(line.strip())
        if m and m.group(2).strip():
            values[m.group(1)] = m.group(2).strip()

    left = {}
    for path in targets():
        text = path.read_text()
        new = text if a.check else TOKEN_RE.sub(lambda m: values.get(m.group(1), m.group(0)), text)
        if new != text:
            path.write_text(new)
            print(f"updated {path.relative_to(ROOT)}")
        for key in TOKEN_RE.findall(new):
            left.setdefault(key, set()).add(str(path.relative_to(ROOT)))

    if left:
        print(f"\n{len(left)} placeholders still empty (fill them in profile.md and re-run):")
        for key, files in sorted(left.items()):
            print(f"  {{{{{key}}}}}  in {', '.join(sorted(files))}")
    else:
        print("\n0 placeholders left.")


if __name__ == "__main__":
    main()
