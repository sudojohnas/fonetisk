#!/usr/bin/env python3
"""Compile static-site JavaScript, including inline HTML scripts."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.current = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and not attrs.get("src"):
            kind = attrs.get("type", "").lower()
            if kind in ("", "module", "text/javascript", "application/javascript"):
                self.current = [kind, ""]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.items.append(self.current)
            self.current = None


def main():
    root = Path(__file__).resolve().parents[1]
    count = 0
    for path in root.rglob("*"):
        if not path.is_file() or any(p in (".git", "node_modules") for p in path.parts):
            continue
        if path.suffix in (".js", ".mjs", ".cjs"):
            subprocess.run(["node", "--check", str(path)], check=True)
            count += 1
        elif path.suffix == ".html":
            parser = Scripts()
            parser.feed(path.read_text())
            if parser.current is not None:
                raise RuntimeError(f"Unclosed script in {path}")
            for kind, source in parser.items:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".mjs" if kind == "module" else ".js") as f:
                    f.write(source)
                    f.flush()
                    subprocess.run(["node", "--check", f.name], check=True)
                count += 1
    print(f"JavaScript syntax verified: {count} scripts")


if __name__ == "__main__":
    main()
