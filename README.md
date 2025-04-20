# ♕ queens-solver

A visual solver for the **Queens Puzzle** with custom rules:  
> Two queens attack each other if they share the same row, column, or are **adjacent diagonally** (only distance = 1).

Includes:
- 🧠 A fast backtracking solver with constraint propagation.
- 🖥️ A visual interface with [Streamlit](https://streamlit.io).
- 🧪 Unit tests and GitHub CI workflow.
- 🐍 Easy to install, easy to extend.

---

## ✨ Demo

<img src="https://raw.githubusercontent.com/Leonardo-VERA/queens-solver/main/docs/demo_screenshot.png" width="600"/>

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/Leonardo-VERA/queens-solver.git
cd queens-solver

# Install dependencies (editable mode with dev tools)
pip install -e .[dev]
