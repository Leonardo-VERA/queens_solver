# tests/test_screen.py
import random

import numpy as np
import pytest

from queens.screen import solve_screenshot

from .helpers import is_valid_solution, random_puzzle, render_screen


@pytest.mark.parametrize("n,dark", [(7, False), (9, False), (10, True), (11, False)])
def test_queens_land_on_the_right_cells(n, dark):
    board = random_puzzle(n, random.Random(n))
    cell = 60
    screen, (ox, oy) = render_screen(board, cell=cell, dark=dark, seed=n)

    result = solve_screenshot(screen)
    assert result.ok, result.message
    assert result.n == n
    assert abs(result.cell_size - cell) < 0.1 * cell

    # Map each on-screen queen back to a cell of the true board.
    placed = {}
    for x, y in result.queens:
        c, r = (x - ox) / cell, (y - oy) / cell
        # The centre must be close to the middle of the cell.
        assert abs(c - int(c) - 0.5) < 0.15 and abs(r - int(r) - 0.5) < 0.15
        placed[len(placed)] = (int(r), int(c))
    assert is_valid_solution(board, placed)


def test_no_board_on_screen():
    screen = np.full((900, 1600, 3), 240, np.uint8)
    result = solve_screenshot(screen)
    assert not result.ok and result.queens == []
