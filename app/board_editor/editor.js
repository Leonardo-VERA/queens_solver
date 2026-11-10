// Queens board editor — Streamlit custom component (st.components.v2).
//
// Painting happens entirely in the browser, so it is instant. Python only
// receives the board when a stroke ends (state "board"), solves it, and sends
// the result back in `data.result`.
//
// data = {
//   version: int,                 // changes when Python loads a new board
//   board:   ["AAB..", ...],      // '.' = empty cell
//   colors:  {"A": "#rrggbb"},    // palette, in display order
//   result:  {for, queens, kind, text} | null   // `for` = board it applies to
// }

const EDITORS = new WeakMap();

const CROWN =
  '<svg viewBox="0 0 24 24" aria-hidden="true">' +
  '<path d="M4 19h16v2H4zM2.5 7.5l5 4.2L12 4l4.5 7.7 5-4.2L19.6 17H4.4z"/></svg>';

export default function (component) {
  const { data, parentElement, setStateValue } = component;
  let editor = EDITORS.get(parentElement);
  if (!editor) {
    editor = new Editor(parentElement);
    EDITORS.set(parentElement, editor);
  }
  editor.send = (value) => setStateValue("board", value);
  editor.update(data || {});
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

class Editor {
  constructor(parent) {
    this.version = null;
    this.n = 0;
    this.board = [];
    this.colors = {};
    this.active = null;
    this.result = null;
    this.history = [];
    this.stroke = null;
    this.send = () => {};

    this.root = el("div", "qe");
    this.palette = el("div", "qe-palette");
    this.grid = el("div", "qe-grid");
    this.status = el("div", "qe-status");
    const bar = el("div", "qe-bar");
    this.undoBtn = el("button", "qe-btn", "↶ Annuler");
    this.clearBtn = el("button", "qe-btn", "Tout effacer");
    this.undoBtn.type = this.clearBtn.type = "button";
    this.undoBtn.onclick = () => this.undo();
    this.clearBtn.onclick = () => this.clear();
    bar.append(this.undoBtn, this.clearBtn);
    this.root.append(this.palette, this.grid, this.status, bar);
    parent.appendChild(this.root);

    const end = () => this.endStroke();
    this.grid.addEventListener("pointerdown", (e) => this.startStroke(e));
    this.grid.addEventListener("pointermove", (e) => this.moveStroke(e));
    this.grid.addEventListener("pointerup", end);
    this.grid.addEventListener("pointercancel", end);
    this.grid.addEventListener("lostpointercapture", end);
  }

  // ── data from Python ────────────────────────────────────────────────────
  update(data) {
    const rows = Array.isArray(data.board) ? data.board : [];
    if (data.version !== this.version) {
      this.version = data.version;
      this.board = rows.map((row) => row.split(""));
      this.history = [];
      if (rows.length !== this.n) {
        this.n = rows.length;
        this.buildCells();
      }
    }
    this.colors = data.colors || {};
    const letters = Object.keys(this.colors);
    if (this.active !== "." && !(this.active in this.colors)) {
      this.active = letters.length ? letters[0] : ".";
    }
    this.result = data.result || null;
    this.buildPalette();
    this.render();
  }

  // ── DOM ─────────────────────────────────────────────────────────────────
  buildCells() {
    this.grid.textContent = "";
    this.grid.style.gridTemplateColumns = `repeat(${this.n}, 1fr)`;
    this.cells = [];
    for (let i = 0; i < this.n * this.n; i++) {
      const cell = el("div", "qe-cell");
      cell.innerHTML = CROWN;
      this.grid.appendChild(cell);
      this.cells.push(cell);
    }
  }

  buildPalette() {
    this.palette.textContent = "";
    const entries = [...Object.entries(this.colors), [".", null]];
    for (const [letter, color] of entries) {
      const swatch = el("button", "qe-swatch");
      swatch.type = "button";
      if (color) {
        swatch.style.background = color;
        swatch.title = `Couleur ${letter}`;
      } else {
        swatch.classList.add("eraser");
        swatch.title = "Gomme";
        swatch.textContent = "✕";
      }
      swatch.classList.toggle("active", letter === this.active);
      swatch.onclick = () => {
        this.active = letter;
        this.buildPalette();
      };
      this.palette.appendChild(swatch);
    }
  }

  rows() {
    return this.board.map((row) => row.join(""));
  }

  render() {
    const n = this.n;
    const key = this.rows().join("/");
    const result = this.result && this.result.for === key ? this.result : null;
    const queens = new Set((result ? result.queens : []).map(([r, c]) => r * n + c));

    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        const ch = this.board[r][c];
        const cell = this.cells[r * n + c];
        const empty = ch === ".";
        cell.style.background = empty ? "" : this.colors[ch] || "#999";
        cell.classList.toggle("empty", empty);
        cell.classList.toggle("q", queens.has(r * n + c));
        cell.classList.toggle("last-col", c === n - 1);
        cell.classList.toggle("last-row", r === n - 1);
        cell.classList.toggle("wall-r", c < n - 1 && this.board[r][c + 1] !== ch);
        cell.classList.toggle("wall-b", r < n - 1 && this.board[r + 1][c] !== ch);
      }
    }

    this.status.className = "qe-status " + (result ? result.kind : "pending");
    this.status.textContent = result ? result.text : "Résolution…";
    this.undoBtn.disabled = this.history.length === 0;
  }

  // ── painting ────────────────────────────────────────────────────────────
  cellAt(x, y) {
    const rect = this.grid.getBoundingClientRect();
    const c = Math.floor(((x - rect.left) / rect.width) * this.n);
    const r = Math.floor(((y - rect.top) / rect.height) * this.n);
    return r >= 0 && c >= 0 && r < this.n && c < this.n ? [r, c] : null;
  }

  paint(x, y) {
    const hit = this.cellAt(x, y);
    if (!hit) return;
    const [r, c] = hit;
    if (this.board[r][c] === this.active) return;
    this.board[r][c] = this.active;
    this.stroke.changed = true;
    this.render();
  }

  startStroke(e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    if (!this.n || this.active === null) return;
    e.preventDefault();
    this.grid.setPointerCapture(e.pointerId);
    this.stroke = { before: this.board.map((row) => row.slice()), changed: false, x: e.clientX, y: e.clientY };
    this.paint(e.clientX, e.clientY);
  }

  moveStroke(e) {
    if (!this.stroke) return;
    const events = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
    const step = this.grid.getBoundingClientRect().width / this.n / 3;
    for (const ev of events.length ? events : [e]) {
      // Interpolate so a fast swipe does not skip cells.
      const dx = ev.clientX - this.stroke.x;
      const dy = ev.clientY - this.stroke.y;
      const count = Math.max(1, Math.ceil(Math.hypot(dx, dy) / step));
      for (let i = 1; i <= count; i++) {
        this.paint(this.stroke.x + (dx * i) / count, this.stroke.y + (dy * i) / count);
      }
      this.stroke.x = ev.clientX;
      this.stroke.y = ev.clientY;
    }
  }

  endStroke() {
    if (!this.stroke) return;
    const { before, changed } = this.stroke;
    this.stroke = null;
    if (changed) {
      this.history.push(before);
      this.commit();
    }
  }

  undo() {
    if (!this.history.length) return;
    this.board = this.history.pop();
    this.commit();
  }

  clear() {
    if (this.rows().every((row) => /^\.*$/.test(row))) return;
    this.history.push(this.board.map((row) => row.slice()));
    this.board = this.board.map((row) => row.map(() => "."));
    this.commit();
  }

  commit() {
    this.render();
    this.send({ version: this.version, rows: this.rows() });
  }
}
