"""Solve a Queens board straight from a screenshot.

Platform-independent core of the desktop overlay (``tools/queens_overlay.py``):
takes the screenshot as an RGB array and returns where the queens go, in the
screenshot's own pixel coordinates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import cv2
import numpy as np

from .solver import QueensSolver
from .vision import cell_centers, read_board


@dataclass
class ScreenSolution:
    ok: bool
    message: str
    n: int = 0
    queens: list[tuple[float, float]] = field(default_factory=list)  # (x, y) centres
    cell_size: float = 0.0  # approximate cell side, in pixels
    board: list[str] = field(default_factory=list)
    seconds: float = 0.0


def solve_screenshot(rgb: np.ndarray, max_side: int = 1400) -> ScreenSolution:
    """Find the board in a screenshot, solve it, locate the queens on screen."""
    start = time.perf_counter()
    h, w = rgb.shape[:2]
    scale = min(1.0, max_side / max(h, w))
    small = rgb if scale == 1.0 else cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    reading = read_board(small)
    if not reading.found_outline:
        return ScreenSolution(False, "Grille introuvable : elle doit être entièrement visible à l'écran.")

    regions = set("".join(reading.board))
    if len(regions) != reading.n:
        return ScreenSolution(False, f"{len(regions)} couleurs lues pour une grille {reading.n}×{reading.n}.")

    solution = QueensSolver(reading.board).solve()
    if solution is None:
        return ScreenSolution(False, "Grille lue mais sans solution : relance avec --debug.")

    centres = cell_centers(reading) / scale
    n = reading.n
    cell = float(np.mean([
        np.linalg.norm(centres[0, -1] - centres[0, 0]) / (n - 1),
        np.linalg.norm(centres[-1, 0] - centres[0, 0]) / (n - 1),
    ]))
    queens = [(float(centres[r, c][0]), float(centres[r, c][1])) for r, c in sorted(solution.values())]
    seconds = time.perf_counter() - start
    return ScreenSolution(
        True, f"{n}×{n} résolu en {seconds:.2f} s", n, queens, cell, reading.board, seconds
    )
