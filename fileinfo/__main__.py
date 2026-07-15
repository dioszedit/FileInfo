"""Entry point: GUI without arguments, terminal output with a file argument."""

from __future__ import annotations

import sys
from pathlib import Path


def _print_metadata(target: Path) -> int:
    from .i18n import load_saved_language, tr
    load_saved_language()
    from .extractors import extract_all

    # exists() returns False for a broken symlink, yet there is still info to show
    if not (target.exists() or target.is_symlink()):
        print(f"{tr('Not found')}: {target}", file=sys.stderr)
        return 1
    for section in extract_all(target):
        print(f"\n=== {section.title} ===")
        width = max((len(f.key) for f in section.fields), default=0)
        for fld in section.fields:
            print(f"  {fld.key:<{width}}  {fld.value}")
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        return _print_metadata(Path(sys.argv[1]).expanduser().absolute())
    from .app import run_gui
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
