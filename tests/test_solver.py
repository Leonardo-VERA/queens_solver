# tests/test_solver.py
from queens import QueensSolver

def test_board7():
    board = [
        "AAAABBB",
        "AAACBBB",
        "AADCBBB",
        "DDDCBDB",
        "EEDDDDG",
        "DDDFDDG",
        "DDDFFGG",
    ]
    solver = QueensSolver(board)
    solution = solver.solve()

    assert solution is not None, "El solver no encontró solución para board7"
    assert len(solution) == len(set("ABCDEFG")), "No se colocó una reina por color"
