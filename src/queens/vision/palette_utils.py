# src/queens/vision/palette_utils.py
import numpy as np
import streamlit as st
from sklearn.cluster import KMeans


def extract_palette_from_image(image, n=7, num_colors=10):
    """Extrae los colores promedio detectados en un tablero y permite asignar letras."""
    h, w, _ = image.shape
    square_h = h // n
    square_w = w // n

    colors = []
    for i in range(n):
        for j in range(n):
            y1, y2 = i * square_h, (i + 1) * square_h
            x1, x2 = j * square_w, (j + 1) * square_w
            cell = image[y1:y2, x1:x2]
            avg_color = np.mean(cell.reshape(-1, 3), axis=0)
            colors.append(avg_color)

    colors = np.array(colors)
    kmeans = KMeans(n_clusters=min(num_colors, len(colors)), n_init=10)
    labels = kmeans.fit_predict(colors)
    centers = kmeans.cluster_centers_.astype(int)

    st.subheader("🎨 Detected color palette:")
    color_map = {}
    for i, center in enumerate(centers):
        hex_color = '#%02x%02x%02x' % tuple(center)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(
                f"""
                <div style='width: 40px; height: 40px; background-color: {hex_color}; border: 1px solid black'></div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            letra = st.text_input(f"Assign letter to color {hex_color}", key=f"color-{i}")
            if letra:
                color_map[tuple(center)] = letra.upper()

    return color_map
