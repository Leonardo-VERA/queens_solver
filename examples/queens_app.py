
'''
# queens_app.py
import streamlit as st
import pandas as pd
from queens_solver import QueensSolver   # <-- tu clase

st.set_page_config(page_title="Queens Solver", page_icon="♕", layout="centered")
st.title("♕  Queens Solver (diagonal = 1)")

# ----------  entrada del usuario  ----------
n = st.number_input("Tamaño del tablero  n × n:", min_value=2, max_value=15, value=7)

# dataframe inicial con 'A'
df_init = pd.DataFrame([[ "A" for _ in range(n)] for _ in range(n)])
# -----------------------------------------------------------------------------
# Editor de tabla (nombre cambia según la versión de Streamlit)
#  1.25+  ->  st.data_editor
#  1.21–1.24  ->  st.experimental_data_editor
# -----------------------------------------------------------------------------
if hasattr(st, "data_editor"):           # versión nueva
    editor = st.data_editor
else:                                    # versiones 1.21‑1.24
    editor = st.experimental_data_editor

df = editor(
    df_init,
    num_rows="fixed",
    column_config={i: st.column_config.TextColumn(width="small")
                   for i in range(n)},
    key="tablero"
)


# --- validación rápida ---
raw = ["".join(str(df.iloc[r, c]).upper()[:1] or "A"   # coerción a 1 carácter A‑Z
               for c in range(n))
        for r in range(n)]

valido = (len(raw) == n and all(len(f) == n and f.isalpha() for f in raw))

if not valido:
    st.warning("Cada celda debe contener **una** letra A‑Z.")

# ----------  botón “Resolver”  ----------
if st.button("Resolver", disabled=not valido):
    solucion = QueensSolver(raw).solve()

    if solucion is None:
        st.error("No hay solución para este tablero.")
    else:
        # pintar la solución
        tablero = [["·"] * n for _ in range(n)]
        for (r, c) in solucion.values():
            tablero[r][c] = "Q"

        st.success("¡Solución encontrada!")
        grid = "\n".join(" ".join(fila) for fila in tablero)
        st.text(grid) 

        
        
'''
