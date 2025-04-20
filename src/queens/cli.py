import argparse, sys
from .solver import QueensSolver


def _read_board(path: str):
    with open(path) as fh:
        rows = [ln.strip().upper() for ln in fh if ln.strip()]
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="queens", description="Queens Solver CLI")
    ap.add_argument("-f", "--file", required=True, help="Fichero de tablero")
    args = ap.parse_args(argv)

    board = _read_board(args.file)
    sol = QueensSolver(board).solve()

    if sol is None:
        print("No hay solución.")
        sys.exit(1)

    n = len(board)
    grid = [["·"] * n for _ in range(n)]
    for (r, c) in sol.values():
        grid[r][c] = "Q"
    print("\n".join(" ".join(row) for row in grid))


if __name__ == "__main__":
    main()
