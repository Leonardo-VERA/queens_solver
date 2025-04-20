'''

#!/usr/bin/env python3
"""
Solver “Queens” con diagonales de distancia 1.

• Una reina cubre TODA su fila y TODA su columna.
• Diagonalmente solo cubre las cuatro casillas adyacentes.


"""

from collections import defaultdict
import copy

# -------------  PARTE 1: CARGA DE TABLERO  ----------------

def leer_tablero(brut):
    """
    `brut` = lista de strings (una por fila, todo en MAYÚSCULAS)
    Devuelve:
      - n            tamaño n × n
      - regiones     {color → lista[(r,c)]}
    """
    n = len(brut)
    reg = defaultdict(list)
    for r in range(n):
        for c in range(n):
            reg[brut[r][c]].append((r, c))
    return n, reg


# -------------  PARTE 2: BACKTRACKING + FORWARD‑CHECKING  --

class QueensSolver:
    def __init__(self, tablero):
        self.n, self.regiones = leer_tablero(tablero)

        # dominios: casillas disponibles por color
        self.dom = {col: set(celdas) for col, celdas in self.regiones.items()}

        # estado incremental
        self.filas = set()
        self.cols = set()
        self.asignadas = {}                  # color → (r,c)
        self.snap_pila = []                  # para deshacer

    # --------  comprobación de ataques con la nueva regla  --
    def _ataca(self, r, c):
        if r in self.filas or c in self.cols:
            return True                     # misma fila/col
        for rq, cq in self.asignadas.values():
            if abs(r - rq) == 1 and abs(c - cq) == 1:
                return True                 # diagonal adyacente
        return False

    # ----------------  operaciones básicas  ----------------
    def _colocar(self, color, rc):
        """
        Fija `color` en `rc`; devuelve snapshot para poder deshacer.
        """
        r, c = rc
        dom_original = copy.deepcopy(self.dom[color])
        eliminadas = []                     # [(otro_color, casilla), …]

        # registrar la colocación
        self.asignadas[color] = rc
        self.dom[color] = {rc}
        self.filas.add(r)
        self.cols.add(c)

        # podar casillas atacadas en los demás dominios
        for col, dom in self.dom.items():
            if col == color:
                continue
            quito = {sq for sq in dom if self._ataca(*sq)}
            if quito:
                dom -= quito
                eliminadas.extend((col, sq) for sq in quito)

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

    # ----------  forward‑checking (unit propagation)  -------
    def _propagar_unitarias(self):
        while True:
            # busca una región todavía NO asignada
            # con dominio 0 ó 1 (la que salga primero)
            unit = None
            for col, dom in self.dom.items():
                if col in self.asignadas:
                    continue
                if len(dom) == 0:
                    return False              # contradicción
                if len(dom) == 1:
                    unit = col
                    break

            if unit is None:                  # ninguna de tamaño 0‑1
                return True                   # nada más que propagar

            # colocar la reina “forzada”
            rc = next(iter(self.dom[unit]))   # ahora sí hay 1 casilla
            if self._ataca(*rc):              # seguridad extra
                return False
            snap = self._colocar(unit, rc)
            self.snap_pila.append((unit, rc, snap))




    # ----------------  búsqueda recursiva  ------------------
    def _color_MRV(self):
        """Escoge el color no asignado con dominio más pequeño."""
        return min(
            (len(d), col) for col, d in self.dom.items()
            if col not in self.asignadas
        )[1]

    def _backtrack(self):
        if len(self.asignadas) == len(self.regiones):
            return dict(self.asignadas)     # ¡solución completa!

        col = self._color_MRV()
        estado_pila = len(self.snap_pila)

        for rc in list(self.dom[col]):
            if self._ataca(*rc):
                continue
            snap = self._colocar(col, rc)

            if self._propagar_unitarias():
                res = self._backtrack()
                if res:
                    return res

            # --- backtrack ---
            while len(self.snap_pila) > estado_pila:
                c2, rc2, sn2 = self.snap_pila.pop()
                self._deshacer(c2, rc2, sn2)
            self._deshacer(col, rc, snap)

        return None                         # callejón sin salida

    # ----------------  interfaz pública  --------------------
    def solve(self):
        if not self._propagar_unitarias():
            return None
        return self._backtrack()


# -------------  PARTE 3: PEQUEÑO *driver*  ----------------

if __name__ == "__main__":
    tablero = [
        "AAAABBB",
        "AAACBBB",
        "AADCBBB",
        "DDDCBDB",
        "EEDDDDG",
        "DDDFDDG",
        "DDDFFGG",
    ]

    solver = QueensSolver(tablero)
    sol = solver.solve()

    if sol is None:
        print("No hay solución.")
    else:
        # pintar la solución
        n = len(tablero)
        grid = [["·"] * n for _ in range(n)]
        for (r, c) in sol.values():
            grid[r][c] = "Q"
        for fila in grid:
            print(" ".join(fila))


'''
