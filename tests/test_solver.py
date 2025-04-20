# tests/test_solver.py
import queens

def test_board7():
    board = [
        "AAAABBB",
        "AAACBBB",
        ...
    ]
    sol = queens.QueensSolver(board).solve()
    assert sol is not None
    # comprueba que hay 7 reinas
    assert len(sol) == len(set(ch for row in board for ch in row))
