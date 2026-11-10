"""Queens Solver — Streamlit app.

1. Take a photo / screenshot of the puzzle -> the board is recognised.
2. Fix any cell in the grid (painting runs in the browser: instant).
3. Every change is solved right away by ``QueensSolver``.
"""

import time

import streamlit as st
from board_editor import board_editor

from queens import QueensSolver
from queens.vision import draw_grid, load_image, read_board

PALETTE = [
    "#bba3e2", "#ffc992", "#96beff", "#b3dfa0", "#dfdfdf", "#ff7b60",
    "#e6f388", "#b9b29e", "#dfa0bf", "#a3d2d8", "#62efea", "#ff93f3",
]  # fmt: skip
LETTERS = "ABCDEFGHIJKL"
MIN_N, MAX_N, DEFAULT_N = 4, 12, 8

st.set_page_config(page_title="Queens Solver", page_icon="♛", layout="centered")
ss = st.session_state


# ── state helpers ────────────────────────────────────────────────────────────
def default_colors(n):
    return {LETTERS[i]: PALETTE[i] for i in range(n)}


def load_board(board, colors):
    """Replace the board shown in the editor (new photo, new size...)."""
    ss.board = board
    ss.colors = colors
    ss.size = len(board)
    ss.version += 1


if "version" not in ss:
    ss.version = 0
    ss.image = None  # RGB array of the last photo
    ss.image_id = None
    ss.reading = None
    load_board(["." * DEFAULT_N] * DEFAULT_N, default_colors(DEFAULT_N))


def on_size_change():
    n = ss.size
    if ss.image is not None:
        ss.reading = read_board(ss.image, n=n)
        load_board(ss.reading.board, ss.reading.colors)
    else:
        ss.reading = None
        load_board(["." * n] * n, default_colors(n))


def on_editor_change():
    value = ss["editor"]["board"]
    if value and value.get("version") == ss.version:
        ss.board = value["rows"]


@st.cache_data(max_entries=500, show_spinner=False)
def analyse(board):
    """Solve the board if it is complete; returns the editor's `result`."""
    n = len(board)
    out = {"for": "/".join(board), "queens": []}
    empty = sum(row.count(".") for row in board)
    regions = set("".join(board)) - {"."}
    if empty == n * n:
        return {**out, "kind": "info", "text": "Importe une photo ou peins la grille."}
    if empty:
        return {**out, "kind": "info", "text": f"Encore {empty} case(s) à colorier."}
    if len(regions) != n:
        text = f"{len(regions)} couleurs pour une grille {n}×{n} : il en faut {n}."
        return {**out, "kind": "warning", "text": text}

    start = time.perf_counter()
    solution = QueensSolver(list(board)).solve()
    ms = (time.perf_counter() - start) * 1000
    if solution is None:
        return {**out, "kind": "error", "text": "Aucune solution : vérifie les couleurs."}
    queens = sorted([r, c] for r, c in solution.values())
    return {**out, "queens": queens, "kind": "success", "text": f"♛ Résolu en {ms:.0f} ms"}


# ── UI ───────────────────────────────────────────────────────────────────────
st.title("♛ Queens Solver")

PHOTO, CAMERA = ":material/image: Photo / capture", ":material/photo_camera: Caméra"
source = st.segmented_control(
    "Source", [PHOTO, CAMERA], default=PHOTO, label_visibility="collapsed"
)
if source == CAMERA:
    shot = st.camera_input("Cadre la grille", label_visibility="collapsed")
else:
    shot = st.file_uploader(
        "Photo ou capture d'écran du puzzle",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )

if shot is not None and shot.file_id != ss.image_id:
    ss.image_id = shot.file_id
    with st.spinner("Lecture de la grille…"):
        ss.image = load_image(shot.getvalue())
        ss.reading = read_board(ss.image)
    load_board(ss.reading.board, ss.reading.colors)

st.number_input("Taille de la grille", MIN_N, MAX_N, key="size", on_change=on_size_change)

if ss.reading is not None:
    for warning in ss.reading.warnings:
        st.warning(warning, icon=":material/warning:")

st.caption("Choisis une couleur, puis touche ou glisse sur les cases pour corriger.")
board_editor(
    board=ss.board,
    colors=ss.colors,
    version=ss.version,
    result=analyse(tuple(ss.board)),
    key="editor",
    on_change=on_editor_change,
)

if ss.reading is not None:
    with st.expander("Détection", icon=":material/center_focus_strong:"):
        st.image(draw_grid(ss.reading), caption=f"Grille {ss.reading.n}×{ss.reading.n} détectée")
