"""
GPS-Based City Route Finder
Problem 11 – AI Problem Solving Assignment
Algorithm: A* Search (with optional BFS/UCS comparison)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import heapq
import math
import time
import random

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0a0f1e"
PANEL_BG  = "#111827"
ACCENT    = "#00d4ff"
GREEN     = "#00ff88"
RED       = "#ff4757"
ORANGE    = "#ffa502"
PURPLE    = "#a855f7"
YELLOW    = "#ffd700"
TEXT      = "#e2e8f0"
MUTED     = "#64748b"
BORDER    = "#1e293b"
NODE_CLR  = "#1e3a5f"
EDGE_CLR  = "#1e293b"

# ── A* Algorithm ──────────────────────────────────────────────────────────────

def astar(graph, heuristic, start, goal):
    """Returns (path, total_cost, nodes_explored)."""
    open_set = []
    heapq.heappush(open_set, (0 + heuristic.get(start, 0), 0, start, [start]))
    visited = {}
    explored = []

    while open_set:
        f, g, node, path = heapq.heappop(open_set)
        if node in visited:
            continue
        visited[node] = g
        explored.append(node)
        if node == goal:
            return path, g, explored
        for neighbor, cost in graph.get(node, []):
            if neighbor not in visited:
                ng = g + cost
                nf = ng + heuristic.get(neighbor, 0)
                heapq.heappush(open_set, (nf, ng, neighbor, path+[neighbor]))
    return None, float('inf'), explored


def ucs(graph, start, goal):
    open_set = []
    heapq.heappush(open_set, (0, start, [start]))
    visited = {}
    explored = []

    while open_set:
        g, node, path = heapq.heappop(open_set)
        if node in visited:
            continue
        visited[node] = g
        explored.append(node)
        if node == goal:
            return path, g, explored
        for neighbor, cost in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(open_set, (g+cost, neighbor, path+[neighbor]))
    return None, float('inf'), explored


def bfs_unweighted(graph, start, goal):
    from collections import deque
    queue = deque([(start, [start])])
    visited = {start}
    explored = []

    while queue:
        node, path = queue.popleft()
        explored.append(node)
        if node == goal:
            return path, explored
        for neighbor, _ in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path+[neighbor]))
    return None, explored

# ── Sample Cities ─────────────────────────────────────────────────────────────

SAMPLE_CITIES = {
    "A": (120, 80),  "B": (260, 60),  "C": (400, 90),
    "D": (180, 200), "E": (320, 190), "F": (460, 210),
    "G": (140, 330), "H": (280, 320), "I": (420, 340),
    "J": (220, 440), "K": (360, 430), "L": (500, 390),
}

SAMPLE_EDGES = [
    ("A","B",4), ("A","D",6), ("B","C",3), ("B","E",5),
    ("C","F",4), ("D","E",3), ("D","G",5), ("E","F",4),
    ("E","H",4), ("F","I",3), ("G","H",4), ("G","J",6),
    ("H","I",5), ("H","K",4), ("I","L",4), ("J","K",3),
    ("K","L",3),
]

def euclidean_heuristic(positions, goal):
    gx, gy = positions[goal]
    return {n: math.hypot(x-gx, y-gy)/40 for n, (x,y) in positions.items()}

# ── Main App ──────────────────────────────────────────────────────────────────

class GPSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GPS City Route Finder  ·  A* Algorithm")
        self.configure(bg=BG)
        self.resizable(True, True)

        self.positions = {}   # node -> (canvas_x, canvas_y)
        self.edges     = []   # (u, v, weight)
        self.graph     = {}   # adjacency list
        self.start_node = tk.StringVar()
        self.goal_node  = tk.StringVar()
        self.algo       = tk.StringVar(value="A*")
        self.drag_node  = None
        self.add_edge_first = None

        self._build_ui()
        self._load_sample()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🗺️  GPS City Route Finder",
                 font=("Courier New",20,"bold"), fg=ACCENT, bg=BG).pack()
        tk.Label(hdr, text="A* Search Algorithm  ·  AI Problem Solving Assignment",
                 font=("Courier New",10), fg=MUTED, bg=BG).pack()

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0,14))

        # ── Control Panel ─────────────────────────────────────────────────────
        ctrl = tk.Frame(body, bg=PANEL_BG, padx=14, pady=14,
                        highlightbackground=BORDER, highlightthickness=1,
                        width=220)
        ctrl.pack(side="left", fill="y", padx=(0,14))
        ctrl.pack_propagate(False)

        self._section(ctrl, "START / GOAL")
        nodes = list(self.positions.keys()) or ["—"]
        tk.Label(ctrl, text="Start City:", fg=MUTED, bg=PANEL_BG,
                 font=("Courier New",9)).pack(anchor="w")
        self.start_cb = ttk.Combobox(ctrl, textvariable=self.start_node,
                                     font=("Courier New",10), width=16,
                                     state="readonly")
        self.start_cb.pack(fill="x", pady=(0,6))
        tk.Label(ctrl, text="Goal City:", fg=MUTED, bg=PANEL_BG,
                 font=("Courier New",9)).pack(anchor="w")
        self.goal_cb = ttk.Combobox(ctrl, textvariable=self.goal_node,
                                    font=("Courier New",10), width=16,
                                    state="readonly")
        self.goal_cb.pack(fill="x", pady=(0,6))

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=8)
        self._section(ctrl, "ALGORITHM")
        for a in ["A*","UCS","BFS","Compare All"]:
            tk.Radiobutton(ctrl, text=a, variable=self.algo, value=a,
                           fg=TEXT, bg=PANEL_BG, selectcolor=ACCENT,
                           activebackground=PANEL_BG, activeforeground=TEXT,
                           font=("Courier New",10)).pack(anchor="w", pady=1)

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=8)
        self._section(ctrl, "ACTIONS")
        for lbl, cmd, col in [
            ("▶  FIND ROUTE", self._run, GREEN),
            ("➕  ADD NODE",   self._add_node, ACCENT),
            ("🔗  ADD EDGE",   self._start_add_edge, PURPLE),
            ("🗑  CLEAR EDGE", self._clear_edges, ORANGE),
            ("🔄  RESET",      self._load_sample, RED),
        ]:
            tk.Button(ctrl, text=lbl, command=cmd,
                      bg=col, fg=BG, font=("Courier New",9,"bold"),
                      relief="flat", cursor="hand2", pady=5).pack(fill="x", pady=2)

        tk.Frame(ctrl, height=1, bg=BORDER).pack(fill="x", pady=8)
        self._section(ctrl, "LEGEND")
        for sym, desc, col in [
            ("●","City Node", NODE_CLR),
            ("●","Start City", GREEN),
            ("●","Goal City", RED),
            ("—","Road (weighted)", EDGE_CLR),
            ("—","Explored Path", PURPLE),
            ("—","Optimal Route", YELLOW),
        ]:
            row = tk.Frame(ctrl, bg=PANEL_BG)
            row.pack(anchor="w")
            tk.Label(row, text=sym, fg=col, bg=PANEL_BG,
                     font=("Courier New",14)).pack(side="left")
            tk.Label(row, text=f" {desc}", fg=MUTED, bg=PANEL_BG,
                     font=("Courier New",9)).pack(side="left")

        # ── Right: canvas + results ───────────────────────────────────────────
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        cv_frame = tk.Frame(right, bg=PANEL_BG,
                            highlightbackground=BORDER, highlightthickness=1)
        cv_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(cv_frame, bg=BG, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.canvas.bind("<Button-1>",   self._canvas_click)
        self.canvas.bind("<B1-Motion>",  self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)

        # Results panel
        res = tk.Frame(right, bg=PANEL_BG,
                       highlightbackground=BORDER, highlightthickness=1)
        res.pack(fill="x", pady=(10,0))

        self.stat_labels = {}
        cols_info = [("Algorithm","—"),("Path","—"),
                     ("Cost","—"),("Explored","—"),("Time (ms)","—")]
        for i,(key,default) in enumerate(cols_info):
            tk.Label(res, text=key, fg=MUTED, bg=PANEL_BG,
                     font=("Courier New",8)).grid(row=0, column=i, padx=14, pady=(6,2))
            lbl = tk.Label(res, text=default, fg=ACCENT, bg=PANEL_BG,
                           font=("Courier New",11,"bold"))
            lbl.grid(row=1, column=i, padx=14, pady=(0,6))
            self.stat_labels[key] = lbl

        # Log
        self.log = tk.Text(right, height=5, bg=PANEL_BG, fg=TEXT,
                           font=("Courier New",9), relief="flat",
                           state="disabled", wrap="word")
        self.log.pack(fill="x", pady=(10,0))

    def _section(self, parent, text):
        tk.Label(parent, text=text, fg=MUTED, bg=PANEL_BG,
                 font=("Courier New",8)).pack(anchor="w", pady=(6,2))

    # ── Graph Building ────────────────────────────────────────────────────────

    def _load_sample(self):
        self.positions = dict(SAMPLE_CITIES)
        self.edges = list(SAMPLE_EDGES)
        self._rebuild_graph()
        self._refresh_combos()
        self.start_node.set("A")
        self.goal_node.set("L")
        self.add_edge_first = None
        self._draw_all()
        self._log("Sample city map loaded. Click ▶ FIND ROUTE to begin.", MUTED)

    def _rebuild_graph(self):
        self.graph = {}
        for u, v, w in self.edges:
            self.graph.setdefault(u, []).append((v, w))
            self.graph.setdefault(v, []).append((u, w))

    def _refresh_combos(self):
        nodes = sorted(self.positions.keys())
        self.start_cb["values"] = nodes
        self.goal_cb["values"]  = nodes

    def _add_node(self):
        name = simpledialog.askstring("Add City", "Enter city name:",
                                      parent=self)
        if not name or name in self.positions:
            if name in self.positions:
                messagebox.showwarning("Exists", "City already exists!")
            return
        # place randomly on canvas
        cw = self.canvas.winfo_width() or 600
        ch = self.canvas.winfo_height() or 450
        x = random.randint(60, cw-60)
        y = random.randint(60, ch-60)
        self.positions[name] = (x, y)
        self._rebuild_graph()
        self._refresh_combos()
        self._draw_all()
        self._log(f"Added city '{name}' at ({x},{y})", ACCENT)

    def _start_add_edge(self):
        if len(self.positions) < 2:
            messagebox.showwarning("Need nodes", "Add at least 2 cities first.")
            return
        self.add_edge_first = None
        self._log("Click a city node to start adding an edge…", PURPLE)

    def _clear_edges(self):
        self.edges = []
        self._rebuild_graph()
        self._draw_all()
        self._log("All edges cleared.", ORANGE)

    # ── Canvas Interaction ────────────────────────────────────────────────────

    def _find_node_at(self, x, y, radius=18):
        for name, (nx, ny) in self.positions.items():
            if math.hypot(x-nx, y-ny) <= radius:
                return name
        return None

    def _canvas_click(self, event):
        node = self._find_node_at(event.x, event.y)
        if self.add_edge_first is not None:
            if node and node != self.add_edge_first:
                w = simpledialog.askinteger("Edge Weight",
                    f"Distance from {self.add_edge_first} to {node}:",
                    minvalue=1, maxvalue=999, parent=self)
                if w:
                    self.edges.append((self.add_edge_first, node, w))
                    self._rebuild_graph()
                    self._draw_all()
                    self._log(f"Edge {self.add_edge_first}↔{node} (cost={w}) added.", PURPLE)
            self.add_edge_first = None
            return
        if node:
            self.drag_node = node

    def _canvas_drag(self, event):
        if self.drag_node:
            self.positions[self.drag_node] = (event.x, event.y)
            self._draw_all(preserve_path=False)

    def _canvas_release(self, event):
        self.drag_node = None
        # If add_edge mode, pick first node
        node = self._find_node_at(event.x, event.y)
        if self.add_edge_first is None and node and not self.drag_node:
            pass  # handled in click

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_all(self, path=None, explored=None, preserve_path=True):
        self.canvas.delete("all")

        # edges
        for u, v, w in self.edges:
            if u not in self.positions or v not in self.positions:
                continue
            x1,y1 = self.positions[u]
            x2,y2 = self.positions[v]
            self.canvas.create_line(x1,y1,x2,y2, fill="#1e3a5f",
                                    width=2, tags="edge")
            mx, my = (x1+x2)//2, (y1+y2)//2
            self.canvas.create_text(mx, my-8, text=str(w),
                                    fill=MUTED, font=("Courier New",8),
                                    tags="weight")

        # explored edges
        if explored and len(explored) > 1:
            for i in range(len(explored)-1):
                u,v = explored[i], explored[i+1]
                if u in self.positions and v in self.positions:
                    x1,y1 = self.positions[u]
                    x2,y2 = self.positions[v]
                    self.canvas.create_line(x1,y1,x2,y2,fill=PURPLE,
                                            width=2,dash=(4,3))

        # path edges
        if path and len(path) > 1:
            for i in range(len(path)-1):
                u,v = path[i], path[i+1]
                if u in self.positions and v in self.positions:
                    x1,y1 = self.positions[u]
                    x2,y2 = self.positions[v]
                    self.canvas.create_line(x1,y1,x2,y2,fill=YELLOW,
                                            width=4)

        # nodes
        for name, (x, y) in self.positions.items():
            r = 18
            col = NODE_CLR
            txt_col = ACCENT
            if name == self.start_node.get():
                col, txt_col = GREEN, BG
            elif name == self.goal_node.get():
                col, txt_col = RED, BG
            elif path and name in path:
                col = "#2d2a00"
                txt_col = YELLOW
            elif explored and name in explored:
                col = "#1e1040"
                txt_col = PURPLE
            self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                    fill=col, outline=BORDER, width=2)
            self.canvas.create_text(x, y, text=name, fill=txt_col,
                                    font=("Courier New",11,"bold"))

    # ── Run ───────────────────────────────────────────────────────────────────

    def _run(self):
        s = self.start_node.get()
        g = self.goal_node.get()
        if not s or not g:
            messagebox.showwarning("Missing", "Select start and goal cities!")
            return
        if s == g:
            messagebox.showwarning("Same", "Start and Goal must differ!")
            return

        algo = self.algo.get()
        h = euclidean_heuristic(self.positions, g)

        if algo == "Compare All":
            self._compare_all(s, g, h)
            return

        if algo == "A*":
            t0 = time.perf_counter()
            path, cost, explored = astar(self.graph, h, s, g)
            elapsed = (time.perf_counter()-t0)*1000
        elif algo == "UCS":
            t0 = time.perf_counter()
            path, cost, explored = ucs(self.graph, s, g)
            elapsed = (time.perf_counter()-t0)*1000
        else:  # BFS
            t0 = time.perf_counter()
            path, explored = bfs_unweighted(self.graph, s, g)
            elapsed = (time.perf_counter()-t0)*1000
            cost = "N/A (unweighted)"

        self._draw_all(path=path, explored=explored)
        if path:
            route = " → ".join(path)
            self._update_stats(algo, route, str(cost), len(explored), f"{elapsed:.2f}")
            self._log(f"[{algo}] Route: {route}  |  Cost: {cost}  |  "
                      f"Explored: {len(explored)} cities  |  Time: {elapsed:.2f} ms", GREEN)
        else:
            self._update_stats(algo, "No path", "∞", len(explored), f"{elapsed:.2f}")
            self._log(f"[{algo}] ❌ No path found between {s} and {g}.", RED)

    def _compare_all(self, s, g, h):
        results = {}
        h_map = euclidean_heuristic(self.positions, g)

        t0 = time.perf_counter()
        p, c, e = astar(self.graph, h_map, s, g)
        results["A*"] = (p, c, e, (time.perf_counter()-t0)*1000)

        t0 = time.perf_counter()
        p2, c2, e2 = ucs(self.graph, s, g)
        results["UCS"] = (p2, c2, e2, (time.perf_counter()-t0)*1000)

        t0 = time.perf_counter()
        p3, e3 = bfs_unweighted(self.graph, s, g)
        results["BFS"] = (p3, "N/A", e3, (time.perf_counter()-t0)*1000)

        # show A* path visually
        best_path = results["A*"][0]
        self._draw_all(path=best_path, explored=results["A*"][2])

        self._log("── Comparison Results ─────────────────", ACCENT)
        for alg, (p, c, e, t) in results.items():
            route = " → ".join(p) if p else "No path"
            self._log(f"[{alg}]  Route: {route}  |  Cost: {c}  |  "
                      f"Explored: {len(e)}  |  Time: {t:.3f} ms", TEXT)

        # show A* in stats
        ap, ac, ae, at = results["A*"]
        self._update_stats("A* (best)", " → ".join(ap) if ap else "—",
                           str(ac), len(ae), f"{at:.2f}")

    def _update_stats(self, algo, path, cost, exp, t):
        self.stat_labels["Algorithm"].config(text=algo)
        self.stat_labels["Path"].config(text=path[:35]+"…" if len(path)>35 else path)
        self.stat_labels["Cost"].config(text=cost)
        self.stat_labels["Explored"].config(text=str(exp))
        self.stat_labels["Time (ms)"].config(text=t)

    def _log(self, msg, color=TEXT):
        self.log.config(state="normal")
        self.log.insert("end", f"› {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")


# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = GPSApp()
    app.mainloop()
