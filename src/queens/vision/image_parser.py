# src/queens/vision/image_parser.py
import numpy as np
import streamlit as st

# Mapa de colores a letras (usa valores aproximados)
COLOR_TO_LETTER = {
    "A": (255, 0, 0),     # rojo
    "B": (0, 255, 0),     # verde
    "C": (0, 0, 255),     # azul
    "D": (255, 255, 0),   # amarillo
    "E": (255, 0, 255),   # fucsia
    "F": (0, 255, 255),   # cian
    "G": (255, 165, 0),   # naranja
    "H": (128, 0, 128),   # violeta
    "I": (0, 0, 0),       # negro
    ".": (255, 255, 255)  # blanco = vacío
}

COLOR_LABELS = list(COLOR_TO_LETTER.keys())
COLOR_VALUES = list(COLOR_TO_LETTER.values())

# Tolerancia en la distancia de color (cuanto más alto, más permisivo)
COLOR_TOLERANCE = 100

def closest_color(rgb):
    rgb = np.array(rgb)
    min_dist = float("inf")
    best_label = "."
    for i, ref in enumerate(COLOR_VALUES):
        dist = np.linalg.norm(rgb - np.array(ref))
        if dist < min_dist:
            min_dist = dist
            best_label = COLOR_LABELS[i]
    if min_dist > COLOR_TOLERANCE:
        return "."  # fuera de rango
    return best_label

def image_to_board(image, n=7):
    h, w, _ = image.shape
    square_h = h // n
    square_w = w // n
    board = []

    st.subheader(":mag_right: Color debug info")
    for i in range(n):
        row = ""
        for j in range(n):
            y1, y2 = i * square_h, (i + 1) * square_h
            x1, x2 = j * square_w, (j + 1) * square_w
            cell = image[y1:y2, x1:x2]
            avg_color = np.mean(cell.reshape(-1, 3), axis=0).astype(int)
            letter = closest_color(tuple(avg_color))

            # Mostrar color promedio con su letra
            st.markdown(
                f"Cell ({i},{j}) → Avg RGB: `{tuple(avg_color)}` → Letter: **{letter}**",
                unsafe_allow_html=True
            )

            row += letter
        board.append(row)
    return board