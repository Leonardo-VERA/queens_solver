"""Read a Queens board (n×n grid of coloured regions) from a photo or screenshot.

Pipeline
--------
1. ``locate_board``   – find the board outline (largest square-ish quadrilateral)
                        and warp it to a top-down square image.
2. ``fit_grid``       – find the grid size ``n`` (and exact grid bounds) by scoring
                        how well each candidate lattice matches the grid lines.
3. ``sample_cells``   – robust colour of each cell (ring around the centre, so
                        queens / crosses drawn in the middle are ignored).
4. ``cluster_colors`` – group the n² cell colours into exactly ``n`` regions.

Everything is pure numpy / OpenCV (no Streamlit), so it can be unit-tested.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import cv2
import numpy as np

MIN_N, MAX_N = 4, 12
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
WARP_SIZE = 600  # side (px) of the top-down board image


@dataclass
class BoardReading:
    n: int
    board: list[str]  # n strings of n letters, one letter per region
    colors: dict[str, str]  # letter -> "#rrggbb" (colour seen in the image)
    board_image: np.ndarray  # RGB top-down crop of the board
    grid: tuple[float, float, float, float]  # x0, x1, y0, y1 of the grid in board_image
    found_outline: bool  # False -> no outline found, whole image was used
    color_margin: float  # >~1.5 means regions are clearly separated
    warnings: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────────────
def load_image(data: bytes, max_side: int = 1400) -> np.ndarray:
    """Decode image bytes to an RGB uint8 array (honours EXIF rotation)."""
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, img)
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    return np.asarray(img)


def read_board(image: np.ndarray, n: int | None = None) -> BoardReading:
    """Recognise the board in an RGB image. ``n`` forces the grid size."""
    # Every (outline, grid size) pair is judged the same way: a correct reading
    # has single-coloured cells (uniformity ~1) that fall into n well-separated
    # colour groups (margin > 1). Wrong outlines / sizes fail one or the other.
    best = None
    for warped, found in _board_candidates(image):
        # A detected outline hugs the board, so the grid must fill it.
        for _, size, grid in fit_grid(warped, n, top=3, margin=0.05 if found else 0.15):
            cells, uniformity = sample_cells(warped, size, grid)
            labels, margin = cluster_colors(cells.reshape(-1, 3), size)
            quality = uniformity + 0.15 * min(margin, 2.0) + (0.05 if found else 0.0)
            if best is None or quality > best[0]:
                best = (quality, warped, found, size, grid, cells, labels, margin)
    _, warped, found, size, grid, cells, labels, margin = best

    board, colors = _label_board(labels.reshape(size, size), cells)

    warnings = []
    if not found:
        warnings.append("Contour de la grille non trouvé : toute l'image a été utilisée.")
    if margin < 1.2:
        warnings.append("Certaines couleurs se ressemblent : vérifie la grille.")
    split = [ch for ch in colors if _components(board, ch) > 1]
    if split:
        warnings.append(
            "Région(s) en plusieurs morceaux (%s) : vérifie la grille." % ", ".join(split)
        )

    return BoardReading(
        n=size,
        board=board,
        colors=colors,
        board_image=warped,
        grid=grid,
        found_outline=found,
        color_margin=margin,
        warnings=warnings,
    )


def draw_grid(reading: BoardReading) -> np.ndarray:
    """Board image with the detected lattice drawn on top (for debugging)."""
    img = reading.board_image.copy()
    x0, x1, y0, y1 = reading.grid
    n = reading.n
    for k in range(n + 1):
        x = int(round(x0 + k * (x1 - x0) / n))
        y = int(round(y0 + k * (y1 - y0) / n))
        cv2.line(img, (x, int(y0)), (x, int(y1)), (255, 0, 80), 2)
        cv2.line(img, (int(x0), y), (int(x1), y), (255, 0, 80), 2)
    return img


# ──────────────────────────────────────────────────────────────────────────────
#  1. Locate the board
# ──────────────────────────────────────────────────────────────────────────────
def _board_candidates(image: np.ndarray) -> list[tuple[np.ndarray, bool]]:
    """Top-down board images to try: detected outlines + the whole image."""
    out = [(_warp(image, quad), True) for quad in _find_quads(image)[:5]]
    h, w = image.shape[:2]
    whole = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], np.float32)
    out.append((_warp(image, whole), False))
    return out


def _find_quads(image: np.ndarray) -> list[np.ndarray]:
    """Square-ish quadrilaterals, largest first."""
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    masks = []
    # Grid lines are darker than their surroundings -> adaptive threshold.
    block = max(11, (min(h, w) // 40) | 1)
    masks.append(
        cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, block, 7
        )
    )
    # Plain edges, for boards without a dark frame (e.g. dark mode).
    edges = cv2.Canny(gray, 40, 120)
    masks.append(cv2.dilate(edges, np.ones((3, 3), np.uint8)))

    quads = []
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            hull = cv2.convexHull(cnt)
            area = cv2.contourArea(hull)
            if area < 0.03 * h * w:
                continue
            quad = _approx_quad(hull)
            if quad is None or not _is_squareish(quad):
                continue
            # The hull must be well described by its quad (filters blobs).
            if cv2.contourArea(quad) < 0.85 * area:
                continue
            quads.append((cv2.contourArea(quad), quad))

    quads.sort(key=lambda t: -t[0])
    unique: list[np.ndarray] = []
    for _, q in quads:
        if all(np.abs(q - u).max() > 0.03 * max(h, w) for u in unique):
            unique.append(q)
    return unique


def _approx_quad(hull: np.ndarray) -> np.ndarray | None:
    peri = cv2.arcLength(hull, True)
    for eps in (0.01, 0.02, 0.03, 0.05, 0.08):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            return _order_corners(approx.reshape(4, 2).astype(np.float32))
    return None


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Return corners as top-left, top-right, bottom-right, bottom-left."""
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array(
        [pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]],
        dtype=np.float32,
    )


def _is_squareish(q: np.ndarray) -> bool:
    top, right = np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[2] - q[1])
    bottom, left = np.linalg.norm(q[2] - q[3]), np.linalg.norm(q[3] - q[0])
    if min(top, right, bottom, left) < 1:
        return False
    ratio = (top + bottom) / (left + right)
    return 0.6 < ratio < 1.6


def _warp(image: np.ndarray, quad: np.ndarray) -> np.ndarray:
    s = WARP_SIZE
    dst = np.array([[0, 0], [s - 1, 0], [s - 1, s - 1], [0, s - 1]], np.float32)
    m = cv2.getPerspectiveTransform(quad.astype(np.float32), dst)
    return cv2.warpPerspective(image, m, (s, s), flags=cv2.INTER_AREA)


# ──────────────────────────────────────────────────────────────────────────────
#  2. Grid size
# ──────────────────────────────────────────────────────────────────────────────
def _line_profiles(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Edge strength per column (vertical lines) and per row (horizontal lines)."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
    gx = np.abs(cv2.Sobel(lab, cv2.CV_32F, 1, 0, ksize=3)).sum(axis=2)
    gy = np.abs(cv2.Sobel(lab, cv2.CV_32F, 0, 1, ksize=3)).sum(axis=2)
    # Median over the orthogonal axis: a grid line crosses the whole board,
    # an icon or a region corner does not.
    px = np.median(gx, axis=0) + 0.5 * gx.mean(axis=0)
    py = np.median(gy, axis=1) + 0.5 * gy.mean(axis=1)
    return px, py


def _fit_axis(profile: np.ndarray, n: int, margin: float) -> tuple[float, float, float]:
    """Best (score, start, end) of an n-cell lattice along one axis."""
    length = len(profile)
    scale = np.percentile(profile, 98) + 1e-6
    cell_guess = length / n
    w = max(1, int(round(cell_guess * 0.08)))
    peak = cv2.dilate(profile.astype(np.float32).reshape(1, -1), np.ones((1, 2 * w + 1)))
    peak = peak.ravel() / scale

    span = int(length * margin)
    step = max(1, length // 300)
    starts = np.arange(0, span + 1, step)
    ends = np.arange(length - 1 - span, length, step)
    a, b = np.meshgrid(starts, ends, indexing="ij")
    a = a.ravel()[:, None].astype(np.float32)
    b = b.ravel()[:, None].astype(np.float32)
    cell = (b - a) / n

    def sample(offset: float) -> np.ndarray:
        k = np.arange(0, n + (offset == 0), dtype=np.float32)[None, :] + offset
        return peak[np.clip(np.rint(a + k * cell), 0, length - 1).astype(int)]

    lines = sample(0.0)
    # Inside cells there must be no line: probe the centre, and the thirds /
    # quarters too, otherwise e.g. a 4×4 lattice fits a 12×12 grid perfectly.
    inside = np.max([sample(f).mean(axis=1) for f in (0.25, 1 / 3, 0.5, 2 / 3, 0.75)], axis=0)
    # Inner lines matter most; the outer frame only pins the bounds.
    score = 0.8 * lines[:, 1:-1].mean(axis=1) + 0.2 * lines[:, [0, -1]].mean(axis=1) - inside
    i = int(np.argmax(score))
    return float(score[i]), float(a[i, 0]), float(b[i, 0])


def fit_grid(img: np.ndarray, n: int | None = None, top: int = 1, margin: float = 0.12):
    """Best-matching lattices as a list of (score, n, (x0, x1, y0, y1)).

    ``margin`` is how far (fraction of the side) the grid may sit from the
    image edges.
    """
    px, py = _line_profiles(img)
    sizes = [n] if n else range(MIN_N, MAX_N + 1)
    fits = []
    for size in sizes:
        sx, x0, x1 = _fit_axis(px, size, margin)
        sy, y0, y1 = _fit_axis(py, size, margin)
        # Cells should be roughly square once the board is warped.
        aspect = (x1 - x0) / (y1 - y0 + 1e-6)
        score = sx + sy - 0.5 * abs(np.log(aspect))
        fits.append((score, size, (x0, x1, y0, y1)))
    fits.sort(key=lambda f: -f[0])
    return fits[:top]


# ──────────────────────────────────────────────────────────────────────────────
#  3. Cell colours
# ──────────────────────────────────────────────────────────────────────────────
def sample_cells(img: np.ndarray, n: int, grid) -> tuple[np.ndarray, float]:
    """Median RGB colour of each cell, as an (n, n, 3) float array.

    Also returns the uniformity: the share of sampled pixels close to their
    cell's colour (~1 when the lattice is right, lower when cells straddle lines).
    """
    x0, x1, y0, y1 = grid
    cw, ch = (x1 - x0) / n, (y1 - y0) / n
    out = np.zeros((n, n, 3), np.float32)
    uniform = np.zeros((n, n), np.float32)
    for r in range(n):
        for c in range(n):
            cx0, cy0 = x0 + c * cw, y0 + r * ch
            top, bottom = int(cy0 + 0.15 * ch), int(np.ceil(cy0 + 0.85 * ch))
            left, right = int(cx0 + 0.15 * cw), int(np.ceil(cx0 + 0.85 * cw))
            patch = img[top:bottom, left:right].astype(np.float32)
            ph, pw = patch.shape[:2]
            yy, xx = np.mgrid[0:ph, 0:pw]
            # Ring: skip the middle, where queens / crosses are drawn.
            inner = (np.abs(yy - ph / 2) < ph * 0.25) & (np.abs(xx - pw / 2) < pw * 0.25)
            ring = patch[~inner]
            # Ignore very dark pixels (lines, icons) when there is enough left.
            light = ring[ring.sum(axis=1) > 150]
            colour = np.median(light if len(light) > len(ring) // 4 else ring, axis=0)
            out[r, c] = colour
            uniform[r, c] = np.mean(np.linalg.norm(ring - colour, axis=1) < 25)
    return out, float(uniform.mean())


# ──────────────────────────────────────────────────────────────────────────────
#  4. Colour clustering
# ──────────────────────────────────────────────────────────────────────────────
def _to_lab(rgb: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(
        (rgb.reshape(-1, 1, 3) / 255.0).astype(np.float32), cv2.COLOR_RGB2LAB
    ).reshape(-1, 3)
    lab[:, 0] *= 0.6  # lighting changes mostly affect lightness
    return lab


def cluster_colors(rgb: np.ndarray, k: int) -> tuple[np.ndarray, float]:
    """Average-linkage clustering of colours into exactly ``k`` groups.

    Returns (labels, margin) where margin = closest pair of cluster centres
    divided by the widest cluster spread (large = unambiguous).
    """
    x = _to_lab(rgb)
    m = len(x)
    k = min(k, m)
    dist = np.linalg.norm(x[:, None] - x[None], axis=2)
    np.fill_diagonal(dist, np.inf)
    sizes = np.ones(m)
    active = np.ones(m, bool)
    labels = np.arange(m)

    for _ in range(m - k):
        i, j = np.unravel_index(np.argmin(dist), dist.shape)
        if i > j:
            i, j = j, i
        # Lance–Williams update for average linkage.
        new = (sizes[i] * dist[i] + sizes[j] * dist[j]) / (sizes[i] + sizes[j])
        dist[i, :], dist[:, i] = new, new
        dist[i, i] = np.inf
        dist[j, :], dist[:, j] = np.inf, np.inf
        sizes[i] += sizes[j]
        active[j] = False
        labels[labels == j] = i

    # A few k-means steps to fix chaining mistakes.
    labels = np.searchsorted(np.unique(labels), labels)
    centres = np.array([x[labels == i].mean(axis=0) for i in range(k)])
    for _ in range(5):
        new = np.argmin(np.linalg.norm(x[:, None] - centres[None], axis=2), axis=1)
        if len(np.unique(new)) < k or np.array_equal(new, labels):
            break
        labels = new
        centres = np.array([x[labels == i].mean(axis=0) for i in range(k)])

    spread = max(np.linalg.norm(x[labels == i] - centres[i], axis=1).max() for i in range(k))
    cd = np.linalg.norm(centres[:, None] - centres[None], axis=2)
    np.fill_diagonal(cd, np.inf)
    margin = float(cd.min() / (2 * spread + 2.0)) if k > 1 else 99.0
    return labels, margin


def _label_board(labels: np.ndarray, cells: np.ndarray):
    """Letters in reading order of first appearance + representative colours."""
    n = labels.shape[0]
    mapping: dict[int, str] = {}
    for lab in labels.ravel():
        if lab not in mapping:
            mapping[lab] = LETTERS[len(mapping)]
    board = ["".join(mapping[labels[r, c]] for c in range(n)) for r in range(n)]
    colors = {}
    for lab, letter in mapping.items():
        rgb = np.median(cells[labels == lab], axis=0).round().astype(int)
        colors[letter] = "#%02x%02x%02x" % tuple(int(v) for v in rgb)
    return board, colors


def _components(board: list[str], letter: str) -> int:
    """Number of 4-connected pieces of a region."""
    n = len(board)
    seen = set()
    count = 0
    for r in range(n):
        for c in range(n):
            if board[r][c] != letter or (r, c) in seen:
                continue
            count += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < n and 0 <= nx < n and (ny, nx) not in seen and board[ny][nx] == letter:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
    return count
