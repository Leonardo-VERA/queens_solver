# app/streamlit_app_v4.py
import streamlit as st
import cv2
import numpy as np
from queens import QueensSolver
from queens.vision.image_parser import closest_color
from queens.vision.palette_utils import extract_palette_from_image

st.set_page_config(page_title="Queens Solver - From Image", layout="centered")
st.title("📷 Queens Solver - Board from Image")

# Paso 1: Elegir tamaño de tablero
n = st.slider("Board size (n x n)", 4, 12, 9)

# Paso 2: Subir imagen
uploaded = st.file_uploader("Upload an image of a colored grid", type=["png", "jpg", "jpeg"])

if uploaded:
    file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    st.image(img_rgb, caption="Original image", use_container_width=True)

    # Paso 3: Extraer paleta y asignar letras
    color_map = extract_palette_from_image(img_rgb, n=n)

    if color_map:
        # Paso 4: Convertir imagen a tablero usando asignaciones manuales
        h, w, _ = img_rgb.shape
        square_h = h // n
        square_w = w // n
        board = []

        st.subheader("🧾 Interpreted board")
        for i in range(n):
            row = ""
            for j in range(n):
                y1, y2 = i * square_h, (i + 1) * square_h
                x1, x2 = j * square_w, (j + 1) * square_w
                cell = img_rgb[y1:y2, x1:x2]
                avg_color = np.mean(cell.reshape(-1, 3), axis=0).astype(int)
                # Buscar color más cercano en el mapa creado por el usuario
                best_label = "."
                min_dist = float("inf")
                for ref_rgb, label in color_map.items():
                    dist = np.linalg.norm(avg_color - np.array(ref_rgb))
                    if dist < min_dist:
                        min_dist = dist
                        best_label = label
                row += best_label
            board.append(row)

        st.code("\n".join(board))

        # Paso 5: Resolver
        if st.button("🧠 Solve board"):
            solver = QueensSolver(board)
            sol = solver.solve()
            if sol:
                st.success("Solution found!")
                result = [["·" for _ in range(n)] for _ in range(n)]
                for color, (r, c) in sol.items():
                    result[r][c] = "♕"
                st.code("\n".join(" ".join(row) for row in result))
            else:
                st.error("No solution found.")
    else:
        st.info("Please assign letters to the detected colors.")
