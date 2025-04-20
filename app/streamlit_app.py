import pandas as pd
import streamlit as st

from queens import QueensSolver

st.set_page_config(page_title="Queens Solver", page_icon="♕", layout="centered")
st.title("♕  Queens Solver (diagonal = 1)")

# tamaño del tablero
n = st.number_input("Tamaño n × n", min_value=2, max_value=15, value=7)

# dataframe editable
df_init = pd.DataFrame([["A"] * n for _ in range(n)])
editor = st.data_editor if hasattr(st, "data_editor") else st.experimental_data_editor
df = editor(
    df_init,
    num_rows="fixed",
    column_config={i: st.column_config.TextColumn(width="small") for i in range(n)},
    key="tablero",
)

raw = [
    "".join(str(df.iloc[r, c]).upper()[:1] or "A" for c in range(n)) for r in range(n)
]

valido = len(raw) == n and all(len(f) == n and f.isalpha() for f in raw)
if not valido:
    st.warning("Cada celda debe contener exactamente una letra A‑Z.")

# botón Resolver
if st.button("Resolver", disabled=not valido):
    sol = QueensSolver(raw).solve()
    if sol is None:
        st.error("No hay solución.")
    else:
        grid = [["·"] * n for _ in range(n)]
        for r, c in sol.values():
            grid[r][c] = "Q"
        st.success("¡Solución encontrada!")
        st.text("\n".join(" ".join(f) for f in grid))
