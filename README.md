# Queens‑Solver

Pequeña librería + app Streamlit para resolver el puzzle **Queens**
(en el que 2 reinas solo se atacan si comparten fila, columna o la
diagonal inmediatamente adyacente).

## Uso rápido

```bash
# instalar en editable
pip install -e .

# CLI
queens --file examples/board7.txt

# Streamlit
streamlit run app/streamlit_app.py
