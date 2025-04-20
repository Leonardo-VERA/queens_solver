import copy
from collections import defaultdict


# ────────────────────────────────────────────────────────────────────
#  Función auxiliar: convierte lista[str] -> (n, dict[color, celdas])
# ────────────────────────────────────────────────────────────────────
def leer_tablero(filas):
    n = len(filas)
    reg = defaultdict(list)
    for r in range(n):
        if len(filas[r]) != n:
            raise ValueError("El tablero no es cuadrado n×n.")
        for c, ch in enumerate(filas[r].upper()):
            reg[ch].append((r, c))
    return n, reg


class QueensSolver:
    """Solver del puzzle Queens (diagonal adyacente = ataque)."""

    # ───────────  constructor  ───────────
    def __init__(self, tablero):
        self.n, self.regiones = leer_tablero(tablero)
        self.dom = {col: set(c) for col, c in self.regiones.items()}

        self.filas = set()
        self.cols = set()
        self.asignadas = {}  # color → (r,c)
        self.snap_pila = []  # para deshacer

    # ───────────  ataques  ───────────
    def _ataca(self, r, c):
        if r in self.filas or c in self.cols:
            return True
        for rq, cq in self.asignadas.values():
            if abs(r - rq) == 1 and abs(c - cq) == 1:
                return True
        return False

    # ───────────  colocar / deshacer  ───────────
    def _colocar(self, color, rc):
        r, c = rc
        dom_original = copy.deepcopy(self.dom[color])
        eliminadas = []

        self.asignadas[color] = rc
        self.dom[color] = {rc}
        self.filas.add(r)
        self.cols.add(c)

        for col, dom in self.dom.items():
            if col == color:
                continue
            quitadas = {sq for sq in dom if self._ataca(*sq)}
            if quitadas:
                dom -= quitadas
                eliminadas.extend((col, sq) for sq in quitadas)

        return dom_original, eliminadas

    def _deshacer(self, color, rc, snap):
        dom_original, eliminadas = snap
        self.dom[color] = dom_original
        for col, sq in eliminadas:
            self.dom[col].add(sq)

        del self.asignadas[color]
        r, c = rc
        self.filas.remove(r)
        self.cols.remove(c)

    # ───────────  propagación unitaria  ───────────
    def _propagar_unitarias(self):
        while True:
            unit = None
            for col, dom in self.dom.items():
                if col in self.asignadas:
                    continue
                if len(dom) == 0:
                    return False
                if len(dom) == 1:
                    unit = col
                    break

            if unit is None:
                return True

            rc = next(iter(self.dom[unit]))
            if self._ataca(*rc):
                return False
            snap = self._colocar(unit, rc)
            self.snap_pila.append((unit, rc, snap))

    # ───────────  búsqueda  ───────────
    def _color_MRV(self):
        return min(
            (len(dom), col)
            for col, dom in self.dom.items()
            if col not in self.asignadas
        )[1]

    def _backtrack(self):
        if len(self.asignadas) == len(self.regiones):
            return dict(self.asignadas)

        col = self._color_MRV()
        marca = len(self.snap_pila)

        for rc in list(self.dom[col]):
            if self._ataca(*rc):
                continue
            snap = self._colocar(col, rc)

            if self._propagar_unitarias():
                res = self._backtrack()
                if res:
                    return res

            while len(self.snap_pila) > marca:
                c2, rc2, sn2 = self.snap_pila.pop()
                self._deshacer(c2, rc2, sn2)
            self._deshacer(col, rc, snap)

        return None

    # ───────────  interfaz pública  ───────────
    def solve(self):
        if not self._propagar_unitarias():
            return None
        return self._backtrack()
