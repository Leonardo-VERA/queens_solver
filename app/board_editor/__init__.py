"""Browser-side board editor (Streamlit custom component v2, no build step)."""

from pathlib import Path

import streamlit as st

_HERE = Path(__file__).parent

_component = st.components.v2.component(
    "queens_board_editor",
    js=(_HERE / "editor.js").read_text(encoding="utf-8"),
    css=(_HERE / "editor.css").read_text(encoding="utf-8"),
)


def board_editor(*, board, colors, version, result, key, on_change):
    """Mount the editor.

    When the user finishes a stroke, ``on_change`` runs and
    ``st.session_state[key]["board"]`` holds ``{"version": int, "rows": [...]}``.
    """
    return _component(
        key=key,
        data={"board": board, "colors": colors, "version": version, "result": result},
        default={"board": None},
        on_board_change=on_change,
    )
