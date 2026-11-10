# tests/test_vision.py
import random
from pathlib import Path

import pytest

from queens import QueensSolver
from queens.vision import load_image, read_board

from .helpers import is_valid_solution, photo_of, random_puzzle, render_board, same_partition

DATA = Path(__file__).parent / "data"


def test_real_screenshot():
    image = load_image((DATA / "capture_7x7.png").read_bytes())
    reading = read_board(image)
    assert reading.n == 7
    assert same_partition(
        reading.board,
        [
            "PPPPPPP",
            "PPPPPGP",
            "PPOOOGG",
            "PRRRRRW",
            "BBYYYWW",
            "WBBBWWW",
            "WWWWWWW",
        ],
    )
    assert reading.warnings == []
    assert is_valid_solution(reading.board, QueensSolver(reading.board).solve())


@pytest.mark.parametrize("n", [5, 7, 9, 10, 12])
@pytest.mark.parametrize("variant", ["screenshot", "dark", "queens", "photo"])
def test_synthetic_boards(n, variant):
    board = random_puzzle(n, random.Random(100 + n))
    if variant == "screenshot":
        image = render_board(board, seed=n)
    elif variant == "dark":
        image = render_board(board, dark=True, seed=n)
    elif variant == "queens":
        queens = list(QueensSolver(board).solve().values())[: n // 2]
        image = render_board(board, queens=queens, seed=n)
    else:
        image = photo_of(render_board(board, seed=n), seed=n)

    reading = read_board(image)
    assert reading.n == n
    assert same_partition(reading.board, board)


def test_forced_size():
    board = random_puzzle(8, random.Random(3))
    reading = read_board(render_board(board, seed=3), n=8)
    assert reading.n == 8 and same_partition(reading.board, board)
