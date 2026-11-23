"""Bridge between the Android app (Kotlin) and the shared Python code.

Called through Chaquopy. The screenshot arrives as raw RGBA bytes straight
from Android's ImageReader; the result goes back as a JSON string.
"""

import json

import numpy as np

from queens.screen import solve_screenshot


def warm_up() -> str:
    """Import the heavy modules once, so the first tap is fast."""
    import cv2  # noqa: F401

    solve_screenshot(np.full((400, 300, 3), 240, np.uint8))
    return "ok"


def solve_rgba(data, width: int, height: int, row_stride: int) -> str:
    """Solve the board in an RGBA frame; positions are in screen pixels."""
    buf = np.frombuffer(bytes(data), dtype=np.uint8)
    frame = buf[: height * row_stride].reshape(height, row_stride)
    rgb = np.ascontiguousarray(frame[:, : width * 4].reshape(height, width, 4)[:, :, :3])

    result = solve_screenshot(rgb, max_side=1200)
    return json.dumps(
        {
            "ok": result.ok,
            "message": result.message,
            "n": result.n,
            "cell": result.cell_size,
            "queens": [[x, y] for x, y in result.queens],
        }
    )
