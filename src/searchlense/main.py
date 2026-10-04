"""Entry point for `python -m searchlense`.

Delegates to the stdio bridge. This is what non-Python agents spawn.
"""

from __future__ import annotations

from .bridge import main

if __name__ == "__main__":
    main()
