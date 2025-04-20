# ♕ queens-solver

**Queens Solver** is a logic puzzle solver and visual app designed to solve a variation of the classic N-Queens puzzle.

In this version:
> A queen attacks another if they are on the **same row**, **same column**, or **diagonally adjacent** (only 1 unit of diagonal distance).

The goal:  
Place **one queen per color region** on the board such that no queens attack each other.

---

## 🌟 Features

- ♟️ Custom rule: **diagonal attack only at distance = 1**
- ⚡ Efficient solver using:
  - Backtracking
  - Forward checking
  - Unit propagation
  - MRV (minimum remaining values)
- 🖼️ Visual board editor with [Streamlit](https://streamlit.io)
- 🧪 Test suite with `pytest`
- 🔧 Modern project structure with editable install (`-e .`)
- ✅ GitHub Actions CI included

---

## 📷 Demo

> You can run the visual version locally or deploy it online (Streamlit Cloud)

<img src="https://raw.githubusercontent.com/Leonardo-VERA/queens_solver/docs/demo_screenshot.png" width="600"/>

---

## 📦 Installation

Clone the repository and install the dependencies:

git clone https://github.com/Leonardo-VERA/queens-solver.git
cd queens-solver

> Editable install with development tools
pip install -e ".[dev]"


---

## 🚀 Usage

🧠 Command-line solver (CLI)
Solve a board from file:

queens --file examples/board7.txt

Where board7.txt contains a region-based board:
AAAABBB
AAACBBB
AADCBBB
DDDCBDB
EEDDDDG
DDDFDDG
DDDFFGG


· Q · · · · ·
· · · Q · · ·
· · · · · Q ·
· · Q · · · ·
Q · · · · · ·
· · · · · · Q
· · · · Q · ·

---

## 🎨 Streamlit visual app
Launch the board editor:
streamlit run app/streamlit_app.py
You can define regions, edit the board, and see the solution rendered instantly.

---

## 🧪 Run tests
Make sure everything works:
pytest

---

queens_solver/
├── app/              ← Streamlit app
├── examples/         ← Board samples
├── src/queens/       ← Solver and CLI
├── tests/            ← Unit tests
├── requirements.txt
├── pyproject.toml
└── setup.py

---

## 🧠 Rules Recap
One queen must be placed per color region

No two queens can be in the same row or same column

Diagonal attacks are only allowed if adjacent (distance = 1)

---

This project is 100% compatible with Streamlit Cloud.
Just deploy it using your GitHub repo and make sure requirements.txt includes:
-e .
streamlit
pandas

---

## 🧑‍💻 Contributing
Pull requests are welcome!
Feel free to open issues for suggestions or bug reports.