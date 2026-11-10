# tests/test_solver.py
import random

import pytest

from queens import QueensSolver

from .helpers import is_valid_solution, random_puzzle

BOARD7 = [
    "AAAABBB",
    "AAACBBB",
    "AADCBBB",
    "DDDCBDB",
    "EEDDDDG",
    "DDDFDDG",
    "DDDFFGG",
]


def test_board7():
    solution = QueensSolver(BOARD7).solve()
    assert solution is not None, "El solver no encontró solución para board7"
    assert is_valid_solution(BOARD7, solution)


@pytest.mark.parametrize("n", range(5, 13))
def test_random_puzzles_are_solved(n):
    rng = random.Random(n)
    for _ in range(10):
        board = random_puzzle(n, rng)
        solution = QueensSolver(board).solve()
        assert solution is not None and is_valid_solution(board, solution), board


def test_unsolvable_board():
    # Two regions confined to the same single row: impossible.
    board = ["ABCD", "CCCD", "CCCD", "CCCD"]
    assert QueensSolver(board).solve() is None
