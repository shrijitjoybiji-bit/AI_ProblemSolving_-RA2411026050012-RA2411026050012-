

import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import time
import threading
 
BG        = "#0d1117"
PANEL_BG  = "#161b22"
ACCENT    = "#58a6ff"
GREEN     = "#3fb950"
RED       = "#f85149"
ORANGE    = "#d29922"
PURPLE    = "#bc8cff"
TEXT      = "#e6edf3"
MUTED     = "#8b949e"
BORDER    = "#30363d"
CELL_FREE = "#1f2937"
CELL_WALL = "#374151"

CELL_SIZE  = 52
ANIM_DELAY = 0.06   # seconds between animation steps

# ── Algorithms ───────────────────────────────────────────────────────────────

def bfs(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    queue = deque([(start, [start])])
    visited = {start}
    explored = []

    while queue:
        (r, c), path = queue.popleft()
        explored.append((r, c))
        if (r, c) == goal:
            return path, explored
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in visited and grid[nr][nc] == 0:
                visited.add((nr,nc))
                queue.append(((nr,nc), path+[(nr,nc)]))
    return None, explored


def dfs(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    stack = [(start, [start])]
    visited = set()
    explored = []

    while stack:
        (r, c), path = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        explored.append((r, c))
        if (r, c) == goal:
            return path, explored
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in visited and grid[nr][nc] == 0:
                stack.append(((nr,nc), path+[(nr,nc)]))
    return None, explored

# ── Main App ──────────────────────────────────────────────────────────────────

class DroneApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Drone Delivery Path Finder")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.rows = 8
        self.cols = 10
        self.grid_data = [[0]*self.cols for _ in range(self.rows)]
        self.start = None
        self.goal  = None
        self.mode  = tk.StringVar(value="wall")   # wall | start | goal
        self.algo  = tk.StringVar(value="BFS")
        self.running = False

        self._build_ui()
        self._draw_grid()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🚁  Drone Delivery Path Finder",
                 font=("Courier New", 20, "bold"),
                 fg=ACCENT, bg=BG).pack()
        tk.Label(hdr, text="BFS vs DFS  ·  AI Problem Solving Assignment",
                 font=("Courier New", 10), fg=MUTED, bg=BG).pack()

        body = tk.Frame(self, bg=BG)
        body.pack(padx=16, pady=(0,16))

        # Left panel – controls
        ctrl = tk.Frame(body, bg=PANEL_BG, padx=14, pady=14,
                        highlightbackground=BORDER, highlightthickness=1)
        ctrl.grid(row=0, column=0, sticky="nsew", padx=(0,14))

        self._section(ctrl, "DRAW MODE")
        for lbl, val in [("🧱  Wall / Obstacle","wall"),
                         ("🟢  Start (Warehouse)","start"),
                         ("🔴  Goal (Customer)","goal")]:
            tk.Radiobutton(ctrl, text=lbl, variable=self.mode, value=val,
                           fg=TEXT, bg=PANEL_BG, selectcolor=ACCENT,
                           activebackground=PANEL_BG, activeforeground=TEXT,
                           font=("Courier New", 10)).pack(anchor="w", pady=2)

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=10)
        self._section(ctrl, "ALGORITHM")
        for a in ["BFS","DFS","Both"]:
            tk.Radiobutton(ctrl, text=a, variable=self.algo, value=a,
                           fg=TEXT, bg=PANEL_BG, selectcolor=ACCENT,
                           activebackground=PANEL_BG, activeforeground=TEXT,
                           font=("Courier New", 10)).pack(anchor="w", pady=2)

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=10)
        self._section(ctrl, "GRID SIZE")
        size_row = tk.Frame(ctrl, bg=PANEL_BG)
        size_row.pack(fill="x", pady=4)
        tk.Label(size_row, text="Rows:", fg=MUTED, bg=PANEL_BG,
                 font=("Courier New",9)).pack(side="left")
        self.row_spin = tk.Spinbox(size_row, from_=4, to=14, width=3,
                                   font=("Courier New",10), bg=CELL_WALL,
                                   fg=TEXT, buttonbackground=BORDER,
                                   command=self._resize)
        self.row_spin.delete(0,"end"); self.row_spin.insert(0,self.rows)
        self.row_spin.pack(side="left", padx=4)
        tk.Label(size_row, text="Cols:", fg=MUTED, bg=PANEL_BG,
                 font=("Courier New",9)).pack(side="left")
        self.col_spin = tk.Spinbox(size_row, from_=4, to=18, width=3,
                                   font=("Courier New",10), bg=CELL_WALL,
                                   fg=TEXT, buttonbackground=BORDER,
                                   command=self._resize)
        self.col_spin.delete(0,"end"); self.col_spin.insert(0,self.cols)
        self.col_spin.pack(side="left", padx=4)

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=10)

        for lbl, cmd, color in [
            ("▶  RUN", self._run, GREEN),
            ("🔄  RESET", self._reset, ORANGE),
            ("🎲  RANDOM", self._random_grid, PURPLE),
        ]:
            tk.Button(ctrl, text=lbl, command=cmd,
                      bg=color, fg=BG, font=("Courier New",10,"bold"),
                      relief="flat", cursor="hand2", pady=6).pack(fill="x", pady=3)

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=10)
        self._section(ctrl, "LEGEND")
        for sym, desc in [("🟦","Free Path"),("⬛","Obstacle"),
                          ("🟢","Start"),("🔴","Goal"),
                          ("🔵","Explored"),("🟡","Path")]:
            tk.Label(ctrl, text=f"{sym} {desc}", fg=MUTED, bg=PANEL_BG,
                     font=("Courier New",9)).pack(anchor="w")

        # Right panel – canvas + stats
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        self.canvas = tk.Canvas(right, bg=BG, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<Button-1>",  self._cell_click)
        self.canvas.bind("<B1-Motion>", self._cell_drag)

        # Stats row
        self.stats_frame = tk.Frame(right, bg=PANEL_BG,
                                    highlightbackground=BORDER,
                                    highlightthickness=1)
        self.stats_frame.pack(fill="x", pady=(10,0))
        self.stat_labels = {}
        for col_idx, key in enumerate(["Algorithm","Path Length","Explored","Time (ms)"]):
            tk.Label(self.stats_frame, text=key,
                     fg=MUTED, bg=PANEL_BG,
                     font=("Courier New",8)).grid(row=0, column=col_idx,
                                                   padx=18, pady=(6,2))
            lbl = tk.Label(self.stats_frame, text="—",
                           fg=ACCENT, bg=PANEL_BG,
                           font=("Courier New",12,"bold"))
            lbl.grid(row=1, column=col_idx, padx=18, pady=(0,8))
            self.stat_labels[key] = lbl

        # Log box
        self.log = tk.Text(right, height=6, bg=PANEL_BG, fg=TEXT,
                           font=("Courier New",9), relief="flat",
                           state="disabled", wrap="word",
                           insertbackground=ACCENT)
        self.log.pack(fill="x", pady=(10,0))

    def _section(self, parent, text):
        tk.Label(parent, text=text, fg=MUTED, bg=PANEL_BG,
                 font=("Courier New",8)).pack(anchor="w", pady=(4,2))

    # ── Canvas ────────────────────────────────────────────────────────────────

    def _canvas_size(self):
        w = self.cols * CELL_SIZE + 1
        h = self.rows * CELL_SIZE + 1
        self.canvas.config(width=w, height=h)

    def _draw_grid(self):
        self._canvas_size()
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c, color=None, text="", text_color=TEXT):
        x0 = c * CELL_SIZE + 1
        y0 = r * CELL_SIZE + 1
        x1 = x0 + CELL_SIZE - 2
        y1 = y0 + CELL_SIZE - 2
        if color is None:
            color = CELL_WALL if self.grid_data[r][c] == 1 else CELL_FREE
        if (r, c) == self.start:
            color, text, text_color = GREEN, "S", BG
        elif (r, c) == self.goal:
            color, text, text_color = RED, "G", BG
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=color,
                                     outline=BORDER, width=1,
                                     tags=f"cell_{r}_{c}")
        if text:
            self.canvas.create_text((x0+x1)//2, (y0+y1)//2,
                                    text=text, fill=text_color,
                                    font=("Courier New",14,"bold"))

    def _px_to_cell(self, x, y):
        r = y // CELL_SIZE
        c = x // CELL_SIZE
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None, None

    def _cell_click(self, event):
        if self.running: return
        r, c = self._px_to_cell(event.x, event.y)
        if r is None: return
        m = self.mode.get()
        if m == "wall":
            self.grid_data[r][c] ^= 1
            if (r,c) == sel.start: self.start = None
            if (r,c) == self.goal:  self.goal  = None
        elif m == "start":
            self.start = (r, c)
            self.grid_data[r][c] = 0
        elif m == "goal":
            self.goal  = (r, c)
            self.grid_data[r][c] = 0
        self._draw_grid()

    def _cell_drag(self, event):
        if self.running or self.mode.get() != "wall": return
        r, c = self._px_to_cell(event.x, event.y)
        if r is None: return
        self.grid_data[r][c] = 1
        if (r,c) == self.start: self.start = None
        if (r,c) == self.goal:  self.goal  = None
        self._draw_grid()

    # ── Controls ──────────────────────────────────────────────────────────────

    def _resize(self):
        try:
            self.rows = int(self.row_spin.get())
            self.cols = int(self.col_spin.get())
        except ValueError:
            return
        self.grid_data = [[0]*self.cols for _ in range(self.rows)]
        self.start = self.goal = None
        self._draw_grid()
        self._log("Grid resized. Place start and goal.", MUTED)

    def _reset(self):
        self.grid_data = [[0]*self.cols for _ in range(self.rows)]
        self.start = self.goal = None
        self._draw_grid()
        for v in self.stat_labels.values(): v.config(text="—")
        self._log("Grid cleared.", MUTED)

    def _random_grid(self):
        import random
        self._reset()
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid_data[r][c] = 1 if random.random() < 0.28 else 0
        self.start = (0, 0)
        self.goal  = (self.rows-1, self.cols-1)
        self.grid_data[0][0] = 0
        self.grid_data[self.rows-1][self.cols-1] = 0
        self._draw_grid()
        self._log("Random grid generated.", MUTED)

    def _run(self):
        if self.running: return
        if not self.start or not self.goal:
            messagebox.showwarning("Missing", "Set start (🟢) and goal (🔴) first!")
            return
        self.running = True
        algo = self.algo.get()
        self._draw_grid()

        def worker():
            if algo in ("BFS", "Both"):
                self._animate_algo("BFS")
            if algo in ("DFS", "Both"):
                time.sleep(0.3)
                self._draw_grid()
                self._animate_algo("DFS")
            self.running = False

        threading.Thread(target=worker, daemon=True).start()

    def _animate_algo(self, algo_name):
        fn = bfs if algo_name == "BFS" else dfs
        t0 = time.perf_counter()
        path, explored = fn(self.grid_data, self.start, self.goal)
        elapsed = (time.perf_counter() - t0) * 1000

        # animate explored cells
        exp_color = "#1e3a5f" if algo_name == "BFS" else "#2d1b4e"
        for step, (r, c) in enumerate(explored):
            if (r,c) in (self.start, self.goal): continue
            self._color_cell(r, c, exp_color)
            time.sleep(ANIM_DELAY)

        # animate path
        if path:
            for (r, c) in path:
                if (r,c) in (self.start, self.goal): continue
                self._color_cell(r, c, ORANGE)
                time.sleep(ANIM_DELAY * 0.7)
            result_msg = (f"{algo_name}: Path found! Length={len(path)-1} steps, "
                          f"Explored={len(explored)} cells, Time={elapsed:.2f} ms")
        else:
            result_msg = f"{algo_name}: ❌ No path found! Explored {len(explored)} cells."

        # update stats on main thread
        self.after(0, lambda: self._update_stats(
            algo_name,
            len(path)-1 if path else "N/A",
            len(explored),
            f"{elapsed:.1f}"
        ))
        self.after(0, lambda: self._log(result_msg, GREEN if path else RED))

    def _color_cell(self, r, c, color):
        self.canvas.after(0, lambda r=r, c=c, col=color: self._draw_cell(r, c, col))

    def _update_stats(self, algo, pl, exp, t):
        self.stat_labels["Algorithm"].config(text=algo)
        self.stat_labels["Path Length"].config(text=str(pl))
        self.stat_labels["Explored"].config(text=str(exp))
        self.stat_labels["Time (ms)"].config(text=t)

    def _log(self, msg, color=TEXT):
        self.log.config(state="normal")
        self.log.insert("end", f"› {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = DroneApp()
    app.mainloop()
