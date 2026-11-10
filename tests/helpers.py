"""Test helpers: random puzzles, solution checks and synthetic board images."""

import random

import cv2
import numpy as np

PASTELS = [
    (187, 163, 226), (255, 201, 146), (150, 190, 255), (179, 223, 160),
    (223, 223, 223), (255, 123, 96), (230, 243, 136), (185, 178, 158),
    (223, 160, 191), (163, 210, 216), (98, 239, 234), (255, 147, 243),
]  # fmt: skip


def random_puzzle(n, rng):
    """Board with at least one valid solution (regions grown from queens)."""
    while True:
        cols = list(range(n))
        rng.shuffle(cols)
        if all(abs(cols[r] - cols[r + 1]) != 1 for r in range(n - 1)):
            break
    grid = [[None] * n for _ in range(n)]
    frontier = []
    for r, c in enumerate(cols):
        grid[r][c] = "ABCDEFGHIJKLMNOP"[r]
        frontier.append((r, c))
    while frontier:
        i = rng.randrange(len(frontier))
        r, c = frontier[i]
        free = [
            (r + dr, c + dc)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < n and 0 <= c + dc < n and grid[r + dr][c + dc] is None
        ]
        if not free:
            frontier.pop(i)
            continue
        rr, cc = rng.choice(free)
        grid[rr][cc] = grid[r][c]
        frontier.append((rr, cc))
    return ["".join(row) for row in grid]


def is_valid_solution(board, solution):
    n = len(board)
    queens = list(solution.values())
    if len(queens) != n or {board[r][c] for r, c in queens} != set("".join(board)):
        return False
    if len({r for r, _ in queens}) != n or len({c for _, c in queens}) != n:
        return False
    return all(
        not (abs(r1 - r2) == 1 and abs(c1 - c2) == 1)
        for i, (r1, c1) in enumerate(queens)
        for (r2, c2) in queens[i + 1 :]
    )


def same_partition(a, b):
    """True if two boards describe the same regions (letters may differ)."""
    mapping = {}
    for ra, rb in zip(a, b):
        for x, y in zip(ra, rb):
            if mapping.setdefault(x, y) != y:
                return False
    return len(set(mapping.values())) == len(mapping)


def render_board(board, cell=48, dark=False, queens=(), page=True, seed=0):
    """LinkedIn-style board: pastel cells, thin cell lines, thick region borders."""
    rng = random.Random(seed)
    n = len(board)
    colors = rng.sample(PASTELS, len(set("".join(board))))
    cmap = {ch: colors[i] for i, ch in enumerate(sorted(set("".join(board))))}
    size = n * cell
    img = np.zeros((size, size, 3), np.uint8)
    for r in range(n):
        for c in range(n):
            img[r * cell : (r + 1) * cell, c * cell : (c + 1) * cell] = cmap[board[r][c]]
    line = (40, 40, 40)
    for k in range(1, n):
        cv2.line(img, (k * cell, 0), (k * cell, size), (90, 90, 90), 1)
        cv2.line(img, (0, k * cell), (size, k * cell), (90, 90, 90), 1)
    for r in range(n):
        for c in range(n):
            if c + 1 < n and board[r][c] != board[r][c + 1]:
                x = (c + 1) * cell
                cv2.line(img, (x, r * cell), (x, (r + 1) * cell), line, 3)
            if r + 1 < n and board[r][c] != board[r + 1][c]:
                y = (r + 1) * cell
                cv2.line(img, (c * cell, y), ((c + 1) * cell, y), line, 3)
    for r, c in queens:
        centre = (c * cell + cell // 2, r * cell + cell // 2)
        cv2.circle(img, centre, cell // 5, (20, 20, 20), -1)
    img = cv2.copyMakeBorder(img, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=line)
    if not page:
        return img
    bg = (27, 31, 35) if dark else (244, 242, 238)
    pad = cell
    out = cv2.copyMakeBorder(img, pad * 3, pad * 4, pad, pad, cv2.BORDER_CONSTANT, value=bg)
    text = (230, 230, 230) if not dark else (60, 60, 60)
    fg = (40, 40, 40) if not dark else (220, 220, 220)
    cv2.rectangle(out, (pad, pad), (pad + 4 * cell, pad + cell // 2), text, -1)
    cv2.putText(out, "Queens #123", (pad, pad * 2), cv2.FONT_HERSHEY_SIMPLEX, 1, fg, 2)
    y = pad * 4 + size
    cv2.rectangle(out, (pad, y), (pad + 3 * cell, y + cell), fg, 2)
    return out


def photo_of(img, seed=0, tilt=0.08, blur=1.2, noise=6.0):
    """Simulate a phone photo of a screen: perspective, blur, noise, lighting."""
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    canvas_w, canvas_h = int(w * 1.6), int(h * 1.4)
    ox, oy = (canvas_w - w) / 2, (canvas_h - h) / 2
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    jitter = rng.uniform(-tilt, tilt, (4, 2)) * [w, h]
    dst = (src + [ox, oy] + jitter).astype(np.float32)
    m = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, m, (canvas_w, canvas_h), borderValue=(70, 60, 55))
    out = cv2.GaussianBlur(out, (0, 0), blur).astype(np.float32)
    yy, xx = np.mgrid[0:canvas_h, 0:canvas_w]
    light = 0.85 + 0.25 * (xx / canvas_w) * (1 - 0.3 * yy / canvas_h)
    out = out * light[..., None] + rng.normal(0, noise, out.shape)
    return np.clip(out, 0, 255).astype(np.uint8)
