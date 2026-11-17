"""Queens overlay for Windows: press a hotkey, the queens appear over the game.

    Ctrl+Alt+Q   capture the screen under the mouse, solve, show the queens
    Ctrl+Alt+H   hide the overlay
    Ctrl+Alt+X   quit

The overlay is click-through: you double-click the marked cells yourself,
the clicks go straight to the game. Nothing is clicked automatically.

Options:
    --once         solve once after --delay seconds (no hotkeys), for testing
    --delay S      seconds to wait with --once (default 3)
    --debug        save the screenshot and what was detected in ./debug/
    --hide-after S hide the overlay automatically after S seconds (default 30)
    --opacity O    overlay opacity, 0.2 (very light) to 1 (solid), default 0.5

See docs/overlay_windows.md for the installation steps.
"""

from __future__ import annotations

import argparse
import ctypes
import queue
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

if sys.platform != "win32":
    sys.exit("Cet outil fonctionne sous Windows (lance-le avec le Python de Windows, pas WSL).")

# Before any window or capture: work in real screen pixels, even with
# Windows display scaling at 125 % / 150 %.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

import tkinter as tk  # noqa: E402

import mss  # noqa: E402
import numpy as np  # noqa: E402

from queens.screen import ScreenSolution, solve_screenshot  # noqa: E402

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
HOTKEYS = {1: ("solve", ord("Q")), 2: ("hide", ord("H")), 3: ("quit", ord("X"))}

KEY_COLOR = "#010203"  # painted pixels of this colour are fully transparent
RING_COLOR = "#ff1f6b"
DEBUG_DIR = Path("debug")


# ── screen helpers ───────────────────────────────────────────────────────────
def cursor_position() -> tuple[int, int]:
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def monitor_under_cursor(sct: mss.base.MSSBase) -> dict:
    x, y = cursor_position()
    for mon in sct.monitors[1:]:
        if mon["left"] <= x < mon["left"] + mon["width"] and mon["top"] <= y < mon["top"] + mon["height"]:
            return mon
    return sct.monitors[1]


def grab(monitor: dict) -> np.ndarray:
    with mss.mss() as sct:
        shot = np.asarray(sct.grab(monitor))  # BGRA
    return np.ascontiguousarray(shot[:, :, 2::-1])  # -> RGB


# ── global hotkeys (Win32 RegisterHotKey, no extra dependency) ───────────────
class HotkeyThread(threading.Thread):
    def __init__(self, events: queue.Queue):
        super().__init__(daemon=True)
        self.events = events
        self.thread_id = None

    def run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        failed = []
        for hk_id, (name, vk) in HOTKEYS.items():
            if not user32.RegisterHotKey(None, hk_id, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk):
                failed.append(f"Ctrl+Alt+{chr(vk)}")
        if failed:
            self.events.put(("error", "Raccourci déjà utilisé par un autre programme : " + ", ".join(failed)))
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam in HOTKEYS:
                self.events.put((HOTKEYS[msg.wParam][0], None))
        for hk_id in HOTKEYS:
            user32.UnregisterHotKey(None, hk_id)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)


# ── transparent, click-through overlay ───────────────────────────────────────
class Overlay:
    def __init__(self, root: tk.Tk, opacity: float = 0.5):
        self.root = root
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", KEY_COLOR)
        root.attributes("-alpha", opacity)  # whole overlay semi-transparent
        root.configure(bg=KEY_COLOR)
        self.canvas = tk.Canvas(root, bg=KEY_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.hide_job = None
        root.update_idletasks()
        self._click_through()
        root.withdraw()

    def _hwnd(self):
        return user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()

    def _click_through(self):
        GWL_EXSTYLE = -20
        WS_EX_LAYERED, WS_EX_TRANSPARENT = 0x00080000, 0x00000020
        WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x00000080, 0x08000000
        hwnd = self._hwnd()
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        )

    def _place(self, left: int, top: int, width: int, height: int):
        """Put the window exactly over the monitor, in real screen pixels.

        Done with the Win32 API: in a Tk geometry string, "-160" would mean
        "160 px from the bottom edge", which broke monitors with negative top.
        """
        HWND_TOPMOST = wintypes.HWND(-1)
        SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x0010, 0x0040
        user32.SetWindowPos(self._hwnd(), HWND_TOPMOST, left, top, width, height,
                            SWP_NOACTIVATE | SWP_SHOWWINDOW)

    def window_rect(self) -> tuple[int, int, int, int]:
        rect = wintypes.RECT()
        user32.GetWindowRect(self._hwnd(), ctypes.byref(rect))
        return rect.left, rect.top, rect.right, rect.bottom

    def hide(self):
        if self.hide_job:
            self.root.after_cancel(self.hide_job)
            self.hide_job = None
        self.canvas.delete("all")
        self.root.withdraw()
        self.root.update()

    def show(self, monitor: dict, result: ScreenSolution, hide_after: float):
        self.canvas.delete("all")
        w, h, left, top = monitor["width"], monitor["height"], monitor["left"], monitor["top"]
        self.root.geometry(f"{w}x{h}+{left}+{top}")  # "+-160" = negative coordinate

        # Status label just above the board (below it if there is no room),
        # never on top of the cells.
        anchor, label_x, label_y = "nw", 40, 40
        if result.ok:
            cell = result.cell_size
            radius = cell * 0.36
            width = max(2, int(cell * 0.05))
            for x, y in result.queens:
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                        outline=RING_COLOR, width=width)
                self.canvas.create_text(x, y, text="♛", fill=RING_COLOR,
                                        font=("Segoe UI Symbol", max(9, int(cell * 0.24))))
            xs = [q[0] for q in result.queens]
            ys = [q[1] for q in result.queens]
            board_left, board_top, board_bottom = min(xs) - cell / 2, min(ys) - cell / 2, max(ys) + cell / 2
            if board_top > 50:
                anchor, label_x, label_y = "sw", board_left, board_top - 10
            else:
                anchor, label_x, label_y = "nw", board_left, board_bottom + 10
        text = ("♛ " if result.ok else "✖ ") + result.message + "   ·   Ctrl+Alt+H : cacher"
        item = self.canvas.create_text(label_x + 8, label_y, text=text, anchor=anchor,
                                       fill="white", font=("Segoe UI", 10, "bold"))
        x1, y1, x2, y2 = self.canvas.bbox(item)
        self.canvas.create_rectangle(x1 - 8, y1 - 5, x2 + 8, y2 + 5,
                                     fill="#1f9d55" if result.ok else "#c0392b", outline="")
        self.canvas.tag_raise(item)

        game_window = user32.GetForegroundWindow()
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.update_idletasks()
        self._click_through()
        self._place(left, top, w, h)
        if game_window:  # keep the focus on Chrome, not on the overlay
            user32.SetForegroundWindow(game_window)
        if hide_after > 0:
            self.hide_job = self.root.after(int(hide_after * 1000), self.hide)


# ── main ─────────────────────────────────────────────────────────────────────
def save_debug(rgb: np.ndarray, result: ScreenSolution):
    import cv2

    DEBUG_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    marked = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    for x, y in result.queens:
        cv2.circle(marked, (int(x), int(y)), int(result.cell_size * 0.36), (107, 31, 255), 4)
    cv2.imwrite(str(DEBUG_DIR / f"{stamp}_capture.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(DEBUG_DIR / f"{stamp}_resultat.png"), marked)
    (DEBUG_DIR / f"{stamp}_grille.txt").write_text(
        result.message + "\n" + "\n".join(result.board) + "\n", encoding="utf-8"
    )
    print(f"  debug -> {DEBUG_DIR.resolve()}\\{stamp}_*")


def solve_now(overlay: Overlay, args) -> None:
    overlay.hide()  # never capture our own drawing
    time.sleep(0.05)
    with mss.mss() as sct:
        monitor = monitor_under_cursor(sct)
    rgb = grab(monitor)
    result = solve_screenshot(rgb)
    print(("OK   " if result.ok else "ÉCHEC ") + result.message)
    if args.debug:
        save_debug(rgb, result)
    overlay.show(monitor, result, args.hide_after)
    if args.debug:
        print(f"  écran capturé : x={monitor['left']} y={monitor['top']} "
              f"{monitor['width']}x{monitor['height']}  |  fenêtre overlay : {overlay.window_rect()}")


def main():
    parser = argparse.ArgumentParser(description="Queens overlay (Windows)")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--hide-after", type=float, default=30.0)
    parser.add_argument("--opacity", type=float, default=0.5)
    args = parser.parse_args()

    root = tk.Tk()
    overlay = Overlay(root, opacity=min(1.0, max(0.2, args.opacity)))

    if args.once:
        print(f"Capture dans {args.delay:.0f} s : affiche la grille Queens à l'écran…")
        root.after(int(args.delay * 1000), lambda: solve_now(overlay, args))
        root.after(int((args.delay + max(args.hide_after, 5)) * 1000), root.destroy)
        root.mainloop()
        return

    events: queue.Queue = queue.Queue()
    hotkeys = HotkeyThread(events)
    hotkeys.start()
    print("Prêt.  Ctrl+Alt+Q : résoudre   Ctrl+Alt+H : cacher   Ctrl+Alt+X : quitter")

    def poll():
        try:
            while True:
                kind, payload = events.get_nowait()
                if kind == "solve":
                    solve_now(overlay, args)
                elif kind == "hide":
                    overlay.hide()
                elif kind == "quit":
                    hotkeys.stop()
                    root.destroy()
                    return
                elif kind == "error":
                    print("ATTENTION : " + payload)
        except queue.Empty:
            pass
        root.after(40, poll)

    root.after(40, poll)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        hotkeys.stop()


if __name__ == "__main__":
    main()
