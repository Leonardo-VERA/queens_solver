import streamlit as st
from queens import QueensSolver

# --- Configuracion inicial ---
st.set_page_config(page_title="Queens Solver - Grid Click", layout="centered")
st.title("🟪 Queens Solver - Grid Click Edition")

# Tamaño del tablero
n = st.selectbox("Board size (n x n)", options=list(range(4, 13)), index=3)

# Definir letras disponibles (colores mapeados)
COLOR_MAP = {
    "A": "#FF0000",
    "B": "#00FF00",
    "C": "#0000FF",
    "D": "#FFFF00",
    "E": "#FF00FF",
    "F": "#00FFFF",
    "G": "#FFA500",
    "H": "#A52A2A",
    "I": "#808080",
    "J": "#800080",
    ".": "#FFFFFF"  # sin color
}

# Estado inicial del tablero (letras)
if "grid" not in st.session_state or st.session_state.grid_size != n:
    st.session_state.grid = [["." for _ in range(n)] for _ in range(n)]
    st.session_state.grid_size = n

# Seleccionar letra actual
letra_actual = st.selectbox("Select region letter", list(COLOR_MAP.keys())[:-1])

# Renderizar grilla
st.write("Click to paint each cell:")

for r in range(n):
    cols = st.columns(n)
    for c in range(n):
        cell_value = st.session_state.grid[r][c]
        color = COLOR_MAP.get(cell_value, "#FFFFFF")
        if cols[c].button(" ", key=f"{r}-{c}", help=f"Cell ({r},{c})", args=()):
            st.session_state.grid[r][c] = letra_actual
        cols[c].markdown(
            f"""
            <div style='width: 100%; height: 30px; background-color: {color}; border: 1px solid #555;'></div>
            """,
            unsafe_allow_html=True,
        )

# Mostrar matriz resultante
st.write("\nBoard interpreted as:")
st.code("\n".join("".join(row) for row in st.session_state.grid))

# Resolver
if st.button("🧠 Solve puzzle"):
    board = ["".join(row) for row in st.session_state.grid]
    solver = QueensSolver(board)
    sol = solver.solve()
    if sol:
        st.success("Solution found!")
        result = [["·" for _ in range(n)] for _ in range(n)]
        for color, (r, c) in sol.items():
            result[r][c] = "♕"
        st.code("\n".join(" ".join(row) for row in result))
    else:
        st.error("No solution found. Try adjusting regions.")