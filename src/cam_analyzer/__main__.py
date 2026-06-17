"""Enable ``python -m cam_analyzer`` as an alias for the ``cam-analyze`` CLI."""

from __future__ import annotations

from cam_analyzer.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
