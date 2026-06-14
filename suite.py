import tkinter as tk
import threading
from tkinter import ttk, filedialog, messagebox, colorchooser
import os, json, platform, subprocess, threading, math, hashlib, base64, re, shutil, zipfile
from datetime import datetime

threading.Thread(target=lambda: __import__('pandas'), daemon=True).start()
threading.Thread(target=lambda: __import__('PIL'), daemon=True).start()


# ── Pillow ──
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── pandas ──
try:
    import pandas as pd
    PD_OK = True
except ImportError:
    PD_OK = False

# ── tkcalendar ──
try:
    from tkcalendar import Calendar
    CAL_OK = True
except ImportError:
    CAL_OK = False

# ── cryptography ──
try:
    from cryptography.fernet import Fernet
    CRYPT_OK = True
except ImportError:
    CRYPT_OK = False

# ════════════════════════════════════════════════════════════
#  DESIGN TOKENS
# ════════════════════════════════════════════════════════════
C = {
    "bg":        "#F7F7F8",
    "white":     "#FFFFFF",
    "black":     "#111111",
    "text":      "#1A1A1A",
    "muted":     "#6B7280",
    "border":    "#E5E7EB",
    "hover":     "#F3F4F6",
    "blue":      "#2563EB",
    "blue_lt":   "#EFF6FF",
    "blue_text": "#1D4ED8",
    "green":     "#16A34A",
    "green_lt":  "#F0FDF4",
    "red":       "#DC2626",
    "red_lt":    "#FEF2F2",
    "amber":     "#D97706",
    "amber_lt":  "#FFFBEB",
    "purple":    "#7C3AED",
    "purple_lt": "#F5F3FF",
    "sidebar":   "#FFFFFF",
    "selected":  "#EFF6FF",
}

FONT_UI   = ("SF Pro Display", 11) if platform.system()=="Darwin" else ("Segoe UI", 11)
FONT_MONO = ("SF Mono", 11)        if platform.system()=="Darwin" else ("Consolas", 11)
FONT_H1   = (FONT_UI[0], 18, "bold")
FONT_H2   = (FONT_UI[0], 13, "bold")
FONT_SM   = (FONT_UI[0], 10)
FONT_BOLD = (FONT_UI[0], 11, "bold")

# ════════════════════════════════════════════════════════════
#  ROOT
# ════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("Studio Suite")
root.geometry("1280x760")
root.minsize(900, 600)
root.configure(bg=C["bg"])

# ── ttk style ──
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame",       background=C["bg"])
style.configure("White.TFrame", background=C["white"])
style.configure("Sidebar.TFrame",background=C["sidebar"])

style.configure("TScrollbar", background=C["border"], troughcolor=C["bg"],
                bordercolor=C["border"], arrowcolor=C["muted"], relief="flat")

style.configure("Treeview", background=C["white"], foreground=C["text"],
                fieldbackground=C["white"], rowheight=30, font=FONT_UI,
                borderwidth=0, relief="flat")
style.configure("Treeview.Heading", background=C["bg"], foreground=C["muted"],
                font=(FONT_UI[0], 10, "bold"), relief="flat", borderwidth=0)
style.map("Treeview", background=[("selected", C["selected"])],
          foreground=[("selected", C["blue_text"])])

style.configure("TEntry", fieldbackground=C["white"], foreground=C["text"],
                bordercolor=C["border"], lightcolor=C["border"],
                darkcolor=C["border"], relief="solid", padding=6)

# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════
def card(parent, **kw):
    f = tk.Frame(parent, bg=C["white"],
                 highlightbackground=C["border"], highlightthickness=1, **kw)
    return f

def label(parent, text, font=None, color=None, **kw):
    return tk.Label(parent, text=text,
                    font=font or FONT_UI,
                    fg=color or C["text"],
                    bg=kw.pop("bg", parent.cget("bg")), **kw)

def btn(parent, text, cmd, style_="normal", **kw):
    styles = {
        "normal": dict(bg=C["white"],   fg=C["text"],      ab=C["hover"],   af=C["text"]),
        "primary":dict(bg=C["blue"],    fg=C["white"],     ab="#1D4ED8",    af=C["white"]),
        "danger": dict(bg=C["red_lt"],  fg=C["red"],       ab="#FEE2E2",    af=C["red"]),
        "success":dict(bg=C["green_lt"],fg=C["green"],     ab="#DCFCE7",    af=C["green"]),
        "ghost":  dict(bg=C["bg"],      fg=C["muted"],     ab=C["border"],  af=C["text"]),
    }
    s = styles.get(style_, styles["normal"])
    b = tk.Button(parent, text=text, command=cmd,
                  bg=s["bg"], fg=s["fg"],
                  activebackground=s["ab"], activeforeground=s["af"],
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  font=FONT_UI,
                  highlightbackground=C["border"], highlightthickness=1,
                  **kw)
    return b

def sep(parent, orient="h", **kw):
    if orient == "h":
        return tk.Frame(parent, height=1, bg=C["border"], **kw)
    return tk.Frame(parent, width=1, bg=C["border"], **kw)

def scrolled_text(parent, **kw):
    f = tk.Frame(parent, bg=C["white"])
    t = tk.Text(f, bg=C["white"], fg=C["text"],
                insertbackground=C["blue"],
                selectbackground=C["selected"],
                selectforeground=C["blue_text"],
                relief="flat", bd=0,
                font=FONT_MONO, wrap="none", **kw)
    sy = ttk.Scrollbar(f, orient="vertical",   command=t.yview)
    sx = ttk.Scrollbar(f, orient="horizontal", command=t.xview)
    t.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    sy.pack(side="right",  fill="y")
    sx.pack(side="bottom", fill="x")
    t.pack(side="left", fill="both", expand=True)
    return f, t

# ════════════════════════════════════════════════════════════
#  LEFT SIDEBAR NAV
# ════════════════════════════════════════════════════════════
main_pane = tk.PanedWindow(root, orient="horizontal",
                            bg=C["bg"], sashwidth=1,
                            sashrelief="flat", sashpad=0)
main_pane.pack(fill="both", expand=True)

sidebar = tk.Frame(main_pane, bg=C["sidebar"], width=190)
sidebar.pack_propagate(False)
main_pane.add(sidebar, minsize=160)

content = tk.Frame(main_pane, bg=C["bg"])
main_pane.add(content, minsize=600)

# App title
title_bar = tk.Frame(sidebar, bg=C["sidebar"], pady=16)
title_bar.pack(fill="x", padx=16)
label(title_bar, "Studio", font=(FONT_UI[0], 15, "bold"), color=C["black"],
      bg=C["sidebar"]).pack(side="left")
label(title_bar, "Suite",  font=(FONT_UI[0], 15),         color=C["blue"],
      bg=C["sidebar"]).pack(side="left")

sep(sidebar).pack(fill="x")

TABS = [
    ("📁", "Files",      "#2563EB"),
    ("✏️", "Editor",     "#7C3AED"),
    ("🎵", "Media",      "#D97706"),
    ("🖼", "Images",     "#16A34A"),
    ("📊", "CSV",        "#0891B2"),
    ("📝", "Notes",      "#EA580C"),
    ("🖩", "Calculator", "#6B7280"),
    ("⏰", "Pomodoro",   "#DC2626"),
    ("📅", "Calendar",   "#9333EA"),
    ("🔐", "Passwords",  "#065F46"),
    ("🎨", "Colors",     "#C026D3"),
    ("💻", "Terminal",   "#111827"),
]

pages = {}
nav_buttons = {}
current_tab = tk.StringVar(value="Files")

nav_frame = tk.Frame(sidebar, bg=C["sidebar"])
nav_frame.pack(fill="both", expand=True, pady=8)

def show_tab(name):
    current_tab.set(name)
    for n, b in nav_buttons.items():
        if n == name:
            b.configure(bg=C["selected"], fg=C["blue_text"],
                        font=(FONT_UI[0], 11, "bold"))
        else:
            b.configure(bg=C["sidebar"], fg=C["text"],
                        font=FONT_UI)
    for n, p in pages.items():
        if n == name:
            p.lift()

def make_nav_btn(icon, name, color):
    f = tk.Frame(nav_frame, bg=C["sidebar"])
    f.pack(fill="x", padx=8, pady=1)
    b = tk.Button(f, text=f"  {icon}  {name}",
                  command=lambda n=name: show_tab(n),
                  bg=C["sidebar"], fg=C["text"],
                  relief="flat", anchor="w",
                  cursor="hand2", padx=4, pady=7,
                  font=FONT_UI,
                  activebackground=C["selected"],
                  activeforeground=C["blue_text"])
    b.pack(fill="x")
    nav_buttons[name] = b

for icon, name, color in TABS:
    make_nav_btn(icon, name, color)

# page stack
page_stack = tk.Frame(content, bg=C["bg"])
page_stack.pack(fill="both", expand=True)

def make_page(name):
    p = tk.Frame(page_stack, bg=C["bg"])
    p.place(relwidth=1, relheight=1)
    pages[name] = p
    return p

# ════════════════════════════════════════════════════════════
#  PAGE HEADER helper
# ════════════════════════════════════════════════════════════
def page_header(parent, title, subtitle=""):
    h = tk.Frame(parent, bg=C["bg"], pady=0)
    h.pack(fill="x", padx=24, pady=(20, 0))
    label(h, title,    font=FONT_H1, color=C["black"], bg=C["bg"]).pack(side="left")
    if subtitle:
        label(h, f"  {subtitle}", font=FONT_SM, color=C["muted"],
              bg=C["bg"]).pack(side="left", pady=(6,0))
    sep(parent).pack(fill="x", padx=24, pady=(12,0))
    return h

# ════════════════════════════════════════════════════════════
#  1. FILE MANAGER
# ════════════════════════════════════════════════════════════
pg_files = make_page("Files")
page_header(pg_files, "File Manager", "— browse, open, manage")

fm_ctrl = tk.Frame(pg_files, bg=C["bg"])
fm_ctrl.pack(fill="x", padx=24, pady=10)

fm_path = tk.StringVar(value=os.path.expanduser("~"))

def fm_refresh():
    fm_tree.delete(*fm_tree.get_children())
    path = fm_path.get()
    fm_path_entry.delete(0, "end")
    fm_path_entry.insert(0, path)
    try:
        entries = sorted(os.listdir(path),
            key=lambda x: (not os.path.isdir(os.path.join(path,x)), x.lower()))
        for name in entries:
            full = os.path.join(path, name)
            is_dir = os.path.isdir(full)
            ext = os.path.splitext(name)[1].upper()
            ico = "📁" if is_dir else (
                "🖼" if ext in [".PNG",".JPG",".JPEG",".GIF",".BMP"] else
                "🎵" if ext in [".MP3",".WAV",".OGG",".FLAC"] else
                "💻" if ext in [".PY",".JS",".HTML",".CSS",".TS"] else
                "📊" if ext in [".CSV",".XLSX"] else "📄")
            size = "—" if is_dir else _fmtsize(full)
            modified = datetime.fromtimestamp(
                os.path.getmtime(full)).strftime("%b %d, %Y") if os.path.exists(full) else "—"
            fm_tree.insert("", "end",
                values=(f"{ico}  {name}", size, ext.lstrip(".") or "Folder", modified))
    except PermissionError:
        pass

def _fmtsize(p):
    try:
        s = os.path.getsize(p)
        for u in ["B","KB","MB","GB"]:
            if s < 1024: return f"{s:.0f} {u}"
            s /= 1024
        return f"{s:.1f} TB"
    except: return "—"

def fm_up():
    p = os.path.dirname(fm_path.get())
    if p != fm_path.get():
        fm_path.set(p); fm_refresh()

def fm_home():
    fm_path.set(os.path.expanduser("~")); fm_refresh()

def fm_browse():
    d = filedialog.askdirectory()
    if d: fm_path.set(d); fm_refresh()

def fm_enter(e=None):
    fm_path.set(fm_path_entry.get()); fm_refresh()

def fm_dblclick(e):
    sel = fm_tree.focus()
    if not sel: return
    raw = fm_tree.item(sel, "values")[0]
    name = raw.split("  ", 1)[-1].strip()
    full = os.path.join(fm_path.get(), name)
    if os.path.isdir(full):
        fm_path.set(full); fm_refresh()
    else:
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                te_text.delete("1.0","end")
                te_text.insert("1.0", f.read())
            te_file.set(full)
            show_tab("Editor")
        except: pass

def fm_delete():
    sel = fm_tree.focus()
    if not sel: return
    raw = fm_tree.item(sel, "values")[0]
    name = raw.split("  ",1)[-1].strip()
    full = os.path.join(fm_path.get(), name)
    if messagebox.askyesno("Delete", f"Delete '{name}'?"):
        try:
            if os.path.isdir(full): shutil.rmtree(full)
            else: os.remove(full)
            fm_refresh()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

def fm_new_folder():
    win = tk.Toplevel(root); win.title("New Folder")
    win.configure(bg=C["white"]); win.resizable(False,False)
    label(win,"Folder name:", bg=C["white"]).pack(padx=20,pady=(16,4))
    e = tk.Entry(win, font=FONT_UI, bg=C["bg"], fg=C["text"],
                 relief="solid", bd=1)
    e.pack(padx=20,fill="x")
    def mk():
        nm = e.get().strip()
        if nm:
            os.makedirs(os.path.join(fm_path.get(), nm), exist_ok=True)
            fm_refresh(); win.destroy()
    btn(win,"Create", mk, "primary").pack(pady=12)
    e.focus()

# toolbar
for text, cmd, st in [("↑ Up",fm_up,"ghost"),("⌂ Home",fm_home,"ghost"),
                       ("Browse",fm_browse,"normal"),("+ Folder",fm_new_folder,"success"),
                       ("Delete",fm_delete,"danger")]:
    b = btn(fm_ctrl, text, cmd, st)
    b.pack(side="left", padx=3)

fm_path_entry = tk.Entry(fm_ctrl, font=FONT_SM, bg=C["white"], fg=C["muted"],
                          relief="solid", bd=1, width=55)
fm_path_entry.pack(side="left", padx=(12,0), ipady=5)
fm_path_entry.insert(0, fm_path.get())
fm_path_entry.bind("<Return>", fm_enter)

# tree
fm_body = tk.Frame(pg_files, bg=C["white"],
                   highlightbackground=C["border"], highlightthickness=1)
fm_body.pack(fill="both", expand=True, padx=24, pady=(0,20))

cols = ("Name","Size","Type","Modified")
fm_tree = ttk.Treeview(fm_body, columns=cols, show="headings", selectmode="browse")
for c,w in zip(cols,[400,90,80,130]):
    fm_tree.heading(c, text=c)
    fm_tree.column(c, width=w, anchor="w" if c=="Name" else "center")

fm_sb = ttk.Scrollbar(fm_body, orient="vertical", command=fm_tree.yview)
fm_tree.configure(yscrollcommand=fm_sb.set)
fm_sb.pack(side="right", fill="y")
fm_tree.pack(fill="both", expand=True)
fm_tree.bind("<Double-1>", fm_dblclick)
fm_refresh()

# ════════════════════════════════════════════════════════════
#  2. TEXT EDITOR
# ════════════════════════════════════════════════════════════
pg_edit = make_page("Editor")
page_header(pg_edit, "Text Editor", "— code & notes")

te_file   = tk.StringVar(value="Untitled")
te_status = tk.StringVar(value="Ready")

te_tb = tk.Frame(pg_edit, bg=C["bg"])
te_tb.pack(fill="x", padx=24, pady=8)

def te_new():
    te_text.delete("1.0","end"); te_file.set("Untitled"); te_status.set("New file")
def te_open():
    p = filedialog.askopenfilename(
        filetypes=[("All text","*.txt *.py *.js *.ts *.html *.css *.md *.json *.csv"),
                   ("All files","*.*")])
    if p:
        with open(p,"r",encoding="utf-8",errors="replace") as f:
            te_text.delete("1.0","end"); te_text.insert("1.0",f.read())
        te_file.set(p); te_status.set(os.path.basename(p))
def te_save():
    p = te_file.get()
    if p == "Untitled": te_save_as(); return
    with open(p,"w",encoding="utf-8") as f: f.write(te_text.get("1.0","end-1c"))
    te_status.set(f"Saved — {datetime.now().strftime('%H:%M')}")
def te_save_as():
    p = filedialog.asksaveasfilename(defaultextension=".txt")
    if p: te_file.set(p); te_save()
def te_find():
    win = tk.Toplevel(root); win.title("Find & Replace")
    win.configure(bg=C["white"]); win.resizable(False,False)
    for i,lbl in enumerate(["Find","Replace"]):
        label(win, lbl+":", bg=C["white"]).grid(row=i,column=0,padx=16,pady=6,sticky="e")
    fv = tk.StringVar(); rv = tk.StringVar()
    tk.Entry(win,textvariable=fv,width=28,bg=C["bg"],fg=C["text"],
             relief="solid",bd=1,font=FONT_UI).grid(row=0,column=1,padx=10,pady=6)
    tk.Entry(win,textvariable=rv,width=28,bg=C["bg"],fg=C["text"],
             relief="solid",bd=1,font=FONT_UI).grid(row=1,column=1,padx=10,pady=6)
    def do():
        c = te_text.get("1.0","end-1c").replace(fv.get(),rv.get())
        te_text.delete("1.0","end"); te_text.insert("1.0",c); win.destroy()
    btn(win,"Replace All",do,"primary").grid(row=2,column=1,pady=10,sticky="e",padx=10)

for txt,cmd,st in [("New",te_new,"ghost"),("Open",te_open,"normal"),
                    ("Save",te_save,"primary"),("Save As",te_save_as,"ghost"),
                    ("Find & Replace",te_find,"ghost")]:
    btn(te_tb,txt,cmd,st).pack(side="left",padx=3)

tk.Label(te_tb, textvariable=te_status, bg=C["bg"], fg=C["muted"],
         font=FONT_SM).pack(side="right")

te_wrap = tk.Frame(pg_edit, bg=C["white"],
                   highlightbackground=C["border"], highlightthickness=1)
te_wrap.pack(fill="both", expand=True, padx=24, pady=(0,20))

te_ln = tk.Text(te_wrap, width=4, bg=C["bg"], fg=C["muted"],
                font=FONT_MONO, relief="flat", state="disabled",
                padx=6, pady=6, takefocus=0)
te_ln.pack(side="left", fill="y")
sep(te_wrap, "v").pack(side="left", fill="y")

_, te_text = scrolled_text(te_wrap, padx=8, pady=6)
te_text.master.pack(side="left", fill="both", expand=True)

def _update_ln(e=None):
    te_ln.configure(state="normal"); te_ln.delete("1.0","end")
    n = int(te_text.index("end-1c").split(".")[0])
    te_ln.insert("1.0","\n".join(str(i) for i in range(1,n+1)))
    te_ln.configure(state="disabled")
te_text.bind("<KeyRelease>", _update_ln); _update_ln()

# ════════════════════════════════════════════════════════════
#  3. MEDIA PLAYER
# ════════════════════════════════════════════════════════════
pg_media = make_page("Media")
page_header(pg_media, "Media Player", "— audio & video")

mp_playlist = []
mp_proc     = None
mp_playing  = False
mp_cur      = tk.StringVar(value="Nothing playing")
mp_stat     = tk.StringVar(value="Stopped")

mp_body = tk.Frame(pg_media, bg=C["bg"])
mp_body.pack(fill="both", expand=True, padx=24, pady=10)

# now playing
np = card(mp_body)
np.pack(fill="x", pady=(0,12))
tk.Label(np, text="🎧", font=("Helvetica",52), bg=C["white"]).pack(pady=(20,4))
label(np, "", textvariable=mp_cur, font=FONT_H2, color=C["blue"],
      bg=C["white"]).pack()
label(np, "", textvariable=mp_stat, font=FONT_SM, color=C["muted"],
      bg=C["white"]).pack(pady=(2,16))

ctrl = tk.Frame(np, bg=C["white"])
ctrl.pack(pady=(0,18))

def mp_play_path(path):
    global mp_proc, mp_playing
    mp_stop()
    sys = platform.system()
    try:
        if sys=="Darwin":   mp_proc = subprocess.Popen(["afplay",path])
        elif sys=="Linux":
            for pl in ["mpv","vlc","mplayer","aplay"]:
                if subprocess.run(["which",pl],capture_output=True).returncode==0:
                    mp_proc = subprocess.Popen([pl,path],
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); break
        elif sys=="Windows": os.startfile(path)
        mp_playing=True; mp_stat.set("▶  Playing")
        mp_cur.set(os.path.basename(path))
    except Exception as ex: mp_stat.set(f"Error: {ex}")

def mp_play():
    sel = mp_lb.curselection()
    idx = sel[0] if sel else 0
    if mp_playlist: mp_play_path(mp_playlist[idx])

def mp_stop():
    global mp_proc, mp_playing
    if mp_proc: mp_proc.terminate(); mp_proc=None
    mp_playing=False; mp_stat.set("⏹  Stopped")

def mp_next():
    sel = mp_lb.curselection()
    idx = (sel[0]+1) if sel else 0
    if idx < len(mp_playlist):
        mp_lb.selection_clear(0,"end"); mp_lb.selection_set(idx)
        mp_play_path(mp_playlist[idx])

def mp_prev():
    sel = mp_lb.curselection()
    idx = max(0,(sel[0]-1)) if sel else 0
    if mp_playlist:
        mp_lb.selection_clear(0,"end"); mp_lb.selection_set(idx)
        mp_play_path(mp_playlist[idx])

def mp_add():
    files = filedialog.askopenfilenames(
        filetypes=[("Media","*.mp3 *.wav *.ogg *.flac *.m4a *.mp4 *.avi *.mkv *.mov")])
    for f in files:
        if f not in mp_playlist:
            mp_playlist.append(f); mp_lb.insert("end", os.path.basename(f))

def mp_remove():
    sel = mp_lb.curselection()
    if sel: mp_lb.delete(sel[0]); mp_playlist.pop(sel[0])

for txt,cmd,st in [("⏮",mp_prev,"ghost"),("⏹ Stop",mp_stop,"danger"),
                    ("▶ Play",mp_play,"primary"),("⏭",mp_next,"ghost")]:
    btn(ctrl,txt,cmd,st).pack(side="left",padx=4)

# playlist
pl = card(mp_body)
pl.pack(fill="both", expand=True, pady=(0,0))
hdr = tk.Frame(pl, bg=C["white"]); hdr.pack(fill="x", padx=12, pady=8)
label(hdr,"Playlist",font=FONT_BOLD,color=C["black"],bg=C["white"]).pack(side="left")
btn(hdr,"+ Add",mp_add,"primary").pack(side="right",padx=(4,0))
btn(hdr,"Remove",mp_remove,"danger").pack(side="right")
sep(pl).pack(fill="x")
mp_lb = tk.Listbox(pl, bg=C["white"], fg=C["text"], relief="flat",
                    font=FONT_UI, selectbackground=C["selected"],
                    selectforeground=C["blue_text"], activestyle="none",
                    highlightthickness=0)
mp_lb.pack(fill="both", expand=True, padx=2)
mp_lb.bind("<Double-1>", lambda e: mp_play())

# ════════════════════════════════════════════════════════════
#  4. IMAGE VIEWER
# ════════════════════════════════════════════════════════════
pg_img = make_page("Images")
page_header(pg_img, "Image Viewer", "— open, zoom, inspect")

iv_img_ref = None
iv_orig    = None
iv_zoom    = 1.0
iv_file    = tk.StringVar(value="No image loaded")

iv_tb = tk.Frame(pg_img, bg=C["bg"]); iv_tb.pack(fill="x", padx=24, pady=8)

def iv_open():
    global iv_orig, iv_zoom
    if not PIL_OK: messagebox.showinfo("Missing","pip install Pillow"); return
    p = filedialog.askopenfilename(
        filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.bmp *.webp")])
    if p:
        iv_orig = Image.open(p); iv_zoom=1.0
        iv_file.set(os.path.basename(p)); iv_render()

def iv_render():
    global iv_img_ref
    if not iv_orig: return
    w = int(iv_orig.width*iv_zoom); h = int(iv_orig.height*iv_zoom)
    img = iv_orig.resize((max(1,w),max(1,h)), Image.LANCZOS)
    iv_img_ref = ImageTk.PhotoImage(img)
    iv_canvas.configure(scrollregion=(0,0,w,h))
    iv_canvas.delete("all")
    iv_canvas.create_image(w//2, h//2, image=iv_img_ref)
    iv_zoom_lbl.configure(text=f"{int(iv_zoom*100)}%")

def iv_zin():  global iv_zoom; iv_zoom=min(iv_zoom+0.25,5.0); iv_render()
def iv_zout(): global iv_zoom; iv_zoom=max(iv_zoom-0.25,0.1); iv_render()
def iv_fit():
    global iv_zoom
    if not iv_orig: return
    cw = iv_canvas.winfo_width() or 800
    ch = iv_canvas.winfo_height() or 600
    iv_zoom = min(cw/iv_orig.width, ch/iv_orig.height)*0.95; iv_render()

iv_zoom_lbl = tk.Label(iv_tb, text="100%", bg=C["bg"], fg=C["muted"], font=FONT_SM)

for txt,cmd,st in [("Open Image",iv_open,"primary"),("Zoom In",iv_zin,"normal"),
                    ("Zoom Out",iv_zout,"normal"),("Fit",iv_fit,"ghost")]:
    btn(iv_tb,txt,cmd,st).pack(side="left",padx=3)
iv_zoom_lbl.pack(side="left", padx=10)
label(iv_tb,"",textvariable=iv_file,font=FONT_SM,color=C["muted"],
      bg=C["bg"]).pack(side="right")

iv_body = tk.Frame(pg_img, bg=C["white"],
                   highlightbackground=C["border"], highlightthickness=1)
iv_body.pack(fill="both", expand=True, padx=24, pady=(0,20))
iv_canvas = tk.Canvas(iv_body, bg=C["bg"], highlightthickness=0)
iv_sx = ttk.Scrollbar(iv_body, orient="horizontal", command=iv_canvas.xview)
iv_sy = ttk.Scrollbar(iv_body, orient="vertical",   command=iv_canvas.yview)
iv_canvas.configure(xscrollcommand=iv_sx.set, yscrollcommand=iv_sy.set)
iv_sx.pack(side="bottom", fill="x"); iv_sy.pack(side="right", fill="y")
iv_canvas.pack(fill="both", expand=True)
iv_canvas.create_text(400,300, text="Open an image to view it",
                       fill=C["muted"], font=FONT_H2)

# ════════════════════════════════════════════════════════════
#  5. CSV VIEWER
# ════════════════════════════════════════════════════════════
pg_csv = make_page("CSV")
page_header(pg_csv, "CSV Viewer", "— spreadsheets & data")

csv_info = tk.StringVar(value="No file loaded")
csv_tb = tk.Frame(pg_csv, bg=C["bg"]); csv_tb.pack(fill="x", padx=24, pady=8)

def csv_open():
    if not PD_OK: messagebox.showinfo("Missing","pip install pandas"); return
    p = filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("Excel","*.xlsx")])
    if not p: return
    df = pd.read_csv(p) if p.endswith(".csv") else pd.read_excel(p)
    csv_tree.delete(*csv_tree.get_children())
    csv_tree["columns"] = list(df.columns)
    csv_tree["show"] = "headings"
    for c in df.columns:
        csv_tree.heading(c, text=c)
        csv_tree.column(c, width=max(80, min(200, len(str(c))*12)))
    for _, row in df.iterrows():
        csv_tree.insert("","end", values=list(row))
    csv_info.set(f"{os.path.basename(p)}  •  {len(df)} rows × {len(df.columns)} cols")

btn(csv_tb,"Open CSV / Excel",csv_open,"primary").pack(side="left",padx=3)
label(csv_tb,"",textvariable=csv_info,font=FONT_SM,color=C["muted"],
      bg=C["bg"]).pack(side="left",padx=12)

csv_body = tk.Frame(pg_csv, bg=C["white"],
                    highlightbackground=C["border"], highlightthickness=1)
csv_body.pack(fill="both", expand=True, padx=24, pady=(0,20))
csv_tree = ttk.Treeview(csv_body, show="headings")
csv_sbx = ttk.Scrollbar(csv_body, orient="horizontal", command=csv_tree.xview)
csv_sby = ttk.Scrollbar(csv_body, orient="vertical",   command=csv_tree.yview)
csv_tree.configure(xscrollcommand=csv_sbx.set, yscrollcommand=csv_sby.set)
csv_sbx.pack(side="bottom",fill="x"); csv_sby.pack(side="right",fill="y")
csv_tree.pack(fill="both", expand=True)

# ════════════════════════════════════════════════════════════
#  6. STICKY NOTES
# ════════════════════════════════════════════════════════════
pg_notes = make_page("Notes")
page_header(pg_notes, "Sticky Notes", "— save quick thoughts")

NOTES_FILE = os.path.join(os.path.expanduser("~"), ".studio_notes.json")
notes_data = []

def notes_load():
    global notes_data
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE) as f: notes_data = json.load(f)
    notes_render()

def notes_save():
    with open(NOTES_FILE,"w") as f: json.dump(notes_data, f)

def notes_render():
    for w in notes_grid.winfo_children(): w.destroy()
    for i, note in enumerate(notes_data):
        colors = {"yellow":("#FFFBEB","#D97706"),
                  "blue":("#EFF6FF","#2563EB"),
                  "green":("#F0FDF4","#16A34A"),
                  "pink":("#FDF2F8","#9333EA")}
        bg, acc = colors.get(note.get("color","yellow"),
                              colors["yellow"])
        c = tk.Frame(notes_grid, bg=bg,
                     highlightbackground=acc, highlightthickness=1)
        c.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="nsew")
        tk.Label(c, text=note.get("title","Note"),
                 bg=bg, fg=acc, font=FONT_BOLD,
                 anchor="w").pack(fill="x", padx=10, pady=(8,2))
        tk.Label(c, text=note.get("text",""),
                 bg=bg, fg=C["text"], font=FONT_UI,
                 anchor="nw", justify="left",
                 wraplength=200).pack(fill="x", padx=10, pady=(0,8))
        tk.Label(c, text=note.get("date",""),
                 bg=bg, fg=acc, font=FONT_SM).pack(anchor="e", padx=8, pady=4)
        tk.Button(c, text="✕", command=lambda idx=i: notes_delete(idx),
                  bg=bg, fg=acc, relief="flat", cursor="hand2",
                  font=FONT_SM, padx=4).pack(anchor="ne")

def notes_delete(idx):
    notes_data.pop(idx); notes_save(); notes_render()

def notes_add():
    win = tk.Toplevel(root); win.title("New Note")
    win.configure(bg=C["white"]); win.geometry("340x300")
    label(win,"Title:", bg=C["white"]).pack(anchor="w",padx=20,pady=(16,2))
    tv = tk.StringVar()
    tk.Entry(win, textvariable=tv, bg=C["bg"], fg=C["text"],
             relief="solid", bd=1, font=FONT_UI).pack(fill="x",padx=20)
    label(win,"Note:", bg=C["white"]).pack(anchor="w",padx=20,pady=(10,2))
    ta = tk.Text(win, height=6, bg=C["bg"], fg=C["text"],
                 relief="solid", bd=1, font=FONT_UI)
    ta.pack(fill="x", padx=20)
    cv = tk.StringVar(value="yellow")
    cf = tk.Frame(win, bg=C["white"]); cf.pack(pady=8)
    label(cf,"Color:", bg=C["white"]).pack(side="left",padx=8)
    for col in ["yellow","blue","green","pink"]:
        tk.Radiobutton(cf, text=col, variable=cv, value=col,
                       bg=C["white"], fg=C["text"],
                       selectcolor=C["white"]).pack(side="left",padx=4)
    def save_note():
        notes_data.append({"title":tv.get() or "Note",
                            "text":ta.get("1.0","end-1c"),
                            "color":cv.get(),
                            "date":datetime.now().strftime("%b %d")})
        notes_save(); notes_render(); win.destroy()
    btn(win,"Save Note",save_note,"primary").pack(pady=8)

nt = tk.Frame(pg_notes, bg=C["bg"]); nt.pack(fill="x", padx=24, pady=8)
btn(nt,"+ New Note",notes_add,"primary").pack(side="left")

notes_canvas = tk.Canvas(pg_notes, bg=C["bg"], highlightthickness=0)
notes_canvas.pack(fill="both", expand=True, padx=24, pady=(0,12))
notes_grid = tk.Frame(notes_canvas, bg=C["bg"])
notes_canvas.create_window((0,0), window=notes_grid, anchor="nw")
for i in range(3): notes_grid.columnconfigure(i, weight=1, minsize=220)
notes_load()

# ════════════════════════════════════════════════════════════
#  7. CALCULATOR
# ════════════════════════════════════════════════════════════
pg_calc = make_page("Calculator")
page_header(pg_calc, "Calculator", "— scientific mode")

calc_expr = tk.StringVar(value="")
calc_disp = tk.StringVar(value="0")

calc_center = tk.Frame(pg_calc, bg=C["bg"])
calc_center.pack(expand=True)

calc_card = card(calc_center)
calc_card.pack(padx=40, pady=10, ipadx=4, ipady=4)

# display
disp = tk.Frame(calc_card, bg=C["white"]); disp.pack(fill="x")
tk.Label(disp, textvariable=calc_expr, bg=C["white"], fg=C["muted"],
         font=FONT_SM, anchor="e").pack(fill="x", padx=16, pady=(12,0))
tk.Label(disp, textvariable=calc_disp, bg=C["white"], fg=C["black"],
         font=(FONT_UI[0],36), anchor="e").pack(fill="x", padx=16, pady=(0,12))
sep(calc_card).pack(fill="x")

CALC_BTNS = [
    [("C","clr"),("±","sign"),("%","pct"),("÷","op")],
    [("7","7"),("8","8"),("9","9"),("×","op")],
    [("4","4"),("5","5"),("6","6"),("−","op")],
    [("1","1"),("2","2"),("3","3"),("+","op")],
    [("sin","fn"),("cos","fn"),("√","fn"),("=","eq")],
    [("0","wide"),(".","dot"),("(","par"),("π","pi")],
]

calc_buf   = ""
calc_last  = ""
calc_new   = True

def calc_press(val, kind):
    global calc_buf, calc_new
    disp_val = calc_disp.get()
    if kind in ("0","1","2","3","4","5","6","7","8","9"):
        if calc_new: calc_buf = val; calc_new=False
        else: calc_buf = ("" if calc_buf=="0" else calc_buf) + val
        calc_disp.set(calc_buf)
    elif kind == "dot":
        if "." not in calc_buf: calc_buf += "."; calc_disp.set(calc_buf)
    elif kind == "op":
        op = {"÷":"/","×":"*","−":"-","+":"+"}[val]
        calc_expr.set(f"{calc_disp.get()} {val}")
        calc_buf = calc_disp.get() + op; calc_new=True
    elif kind == "eq":
        try:
            res = eval(calc_buf + calc_disp.get() if calc_new else calc_buf)
            calc_expr.set(f"{calc_buf}{calc_disp.get()} =")
            calc_disp.set(str(round(res, 10)).rstrip("0").rstrip(".") or "0")
            calc_buf=""; calc_new=True
        except: calc_disp.set("Error"); calc_buf=""; calc_new=True
    elif kind == "clr":
        calc_buf=""; calc_disp.set("0"); calc_expr.set(""); calc_new=True
    elif kind == "sign":
        v = float(calc_disp.get())*-1
        calc_disp.set(str(v)); calc_buf=str(v)
    elif kind == "pct":
        v = float(calc_disp.get())/100
        calc_disp.set(str(v)); calc_buf=str(v)
    elif kind == "fn":
        v = float(calc_disp.get())
        res = {"sin":math.sin(math.radians(v)),
               "cos":math.cos(math.radians(v)),
               "√":math.sqrt(v)}.get(val, v)
        calc_disp.set(str(round(res,8))); calc_buf=str(res); calc_new=True
    elif kind == "pi":
        calc_buf=str(math.pi); calc_disp.set(str(math.pi)); calc_new=True
    elif kind == "par":
        calc_buf += "("; calc_new=False

btn_grid = tk.Frame(calc_card, bg=C["white"])
btn_grid.pack(padx=8, pady=8)
for row in CALC_BTNS:
    rf = tk.Frame(btn_grid, bg=C["white"]); rf.pack()
    for val, kind in row:
        is_op = kind=="op"; is_eq=kind=="eq"; is_clr=kind=="clr"
        bg = C["blue"] if is_eq else C["amber_lt"] if is_op else C["red_lt"] if is_clr else C["bg"]
        fg = C["white"] if is_eq else C["amber"] if is_op else C["red"] if is_clr else C["text"]
        w = 100 if kind=="wide" else 60
        tk.Button(rf, text=val,
                  command=lambda v=val,k=kind: calc_press(v,k),
                  bg=bg, fg=fg, width=4,
                  font=(FONT_UI[0],13),
                  relief="flat", cursor="hand2", pady=10,
                  activebackground=C["border"],
                  activeforeground=fg).pack(side="left", padx=3, pady=3, ipadx=4)

# ════════════════════════════════════════════════════════════
#  8. POMODORO TIMER
# ════════════════════════════════════════════════════════════
pg_pomo = make_page("Pomodoro")
page_header(pg_pomo, "Pomodoro Timer", "— focus & break cycles")

pomo_secs    = 25*60
pomo_left    = pomo_secs
pomo_running = False
pomo_session = tk.StringVar(value="Focus")
pomo_count   = 0
pomo_timer_id= None

pomo_center = tk.Frame(pg_pomo, bg=C["bg"])
pomo_center.pack(expand=True)

pomo_card = card(pomo_center); pomo_card.pack(padx=60, pady=10)

pomo_mode_var = tk.StringVar(value="focus")

def pomo_set_mode(mode):
    global pomo_secs, pomo_left
    pomo_stop()
    if mode=="focus":   pomo_secs=25*60; pomo_session.set("Focus 🎯")
    elif mode=="short": pomo_secs=5*60;  pomo_session.set("Short Break ☕")
    else:               pomo_secs=15*60; pomo_session.set("Long Break 🌿")
    pomo_left=pomo_secs; pomo_update_display()

def pomo_update_display():
    m,s = divmod(pomo_left,60)
    pomo_time_lbl.configure(text=f"{m:02d}:{s:02d}")
    pct = pomo_left/pomo_secs
    arc = int(pct*359.9)
    pomo_canvas.delete("arc")
    pomo_canvas.create_arc(20,20,180,180, start=90, extent=-arc,
                            outline=C["blue"], width=8, style="arc", tags="arc")

def pomo_tick():
    global pomo_left, pomo_running, pomo_count, pomo_timer_id
    if pomo_running and pomo_left > 0:
        pomo_left -= 1; pomo_update_display()
        pomo_timer_id = root.after(1000, pomo_tick)
    elif pomo_running and pomo_left == 0:
        pomo_count += 1; pomo_running=False
        pomo_stat_lbl.configure(text=f"Sessions done: {pomo_count}")
        messagebox.showinfo("Pomodoro", f"{pomo_session.get()} done! 🎉")

def pomo_start():
    global pomo_running
    if not pomo_running:
        pomo_running=True; pomo_tick()
        pomo_btn_start.configure(text="Pause")
    else:
        pomo_running=False
        pomo_btn_start.configure(text="Resume")

def pomo_stop():
    global pomo_running, pomo_left
    pomo_running=False; pomo_left=pomo_secs
    pomo_btn_start.configure(text="Start")
    pomo_update_display()

# mode selector
mf = tk.Frame(pomo_card, bg=C["white"]); mf.pack(pady=16)
for txt,md in [("Focus","focus"),("Short Break","short"),("Long Break","long")]:
    tk.Button(mf, text=txt, command=lambda m=md: pomo_set_mode(m),
              bg=C["bg"], fg=C["muted"], relief="flat",
              cursor="hand2", padx=10, pady=5, font=FONT_SM,
              activebackground=C["selected"],
              activeforeground=C["blue"]).pack(side="left",padx=4)

label(pomo_card, "", textvariable=pomo_session,
      font=FONT_H2, color=C["blue"], bg=C["white"]).pack()

# ring
pomo_canvas = tk.Canvas(pomo_card, width=200, height=200,
                          bg=C["white"], highlightthickness=0)
pomo_canvas.pack(pady=8)
pomo_canvas.create_oval(20,20,180,180, outline=C["border"], width=8)
pomo_time_lbl = tk.Label(pomo_canvas, text="25:00", bg=C["white"],
                           fg=C["black"], font=(FONT_UI[0],34,"bold"))
pomo_canvas.create_window(100,100, window=pomo_time_lbl)
pomo_update_display()

cf2 = tk.Frame(pomo_card, bg=C["white"]); cf2.pack(pady=8)
pomo_btn_start = btn(cf2,"Start",pomo_start,"primary")
pomo_btn_start.pack(side="left",padx=6)
btn(cf2,"Reset",pomo_stop,"ghost").pack(side="left",padx=6)

pomo_stat_lbl = label(pomo_card,f"Sessions done: 0",
                       font=FONT_SM, color=C["muted"], bg=C["white"])
pomo_stat_lbl.pack(pady=(4,16))

# ════════════════════════════════════════════════════════════
#  9. CALENDAR
# ════════════════════════════════════════════════════════════
pg_cal = make_page("Calendar")
page_header(pg_cal, "Calendar", "— view & add events")

cal_events = {}
EVENTS_FILE = os.path.join(os.path.expanduser("~"), ".studio_events.json")

def cal_load():
    global cal_events
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE) as f: cal_events = json.load(f)

def cal_save_f():
    with open(EVENTS_FILE,"w") as f: json.dump(cal_events, f)

cal_load()

cal_body = tk.Frame(pg_cal, bg=C["bg"])
cal_body.pack(fill="both", expand=True, padx=24, pady=8)
cal_body.columnconfigure(0, weight=1)
cal_body.columnconfigure(1, weight=2)

# left — calendar widget
cal_left = card(cal_body); cal_left.grid(row=0,column=0,sticky="nsew",padx=(0,8))

if CAL_OK:
    cal_widget = Calendar(cal_left, selectmode="day",
                           year=datetime.now().year,
                           month=datetime.now().month,
                           day=datetime.now().day,
                           background=C["white"],
                           foreground=C["text"],
                           selectbackground=C["blue"],
                           headersbackground=C["bg"],
                           headersforeground=C["muted"],
                           bordercolor=C["border"],
                           othermonthforeground=C["muted"],
                           font=FONT_UI)
    cal_widget.pack(padx=12, pady=12)
else:
    label(cal_left,"pip install tkcalendar",font=FONT_SM,color=C["muted"],
          bg=C["white"]).pack(padx=20,pady=40)

# right — events list + add
cal_right = tk.Frame(cal_body, bg=C["bg"])
cal_right.grid(row=0,column=1,sticky="nsew")

cal_ev_card = card(cal_right); cal_ev_card.pack(fill="both",expand=True)
label(cal_ev_card,"Events",font=FONT_BOLD,color=C["black"],
      bg=C["white"]).pack(anchor="w",padx=12,pady=(12,4))
sep(cal_ev_card).pack(fill="x")

cal_lb = tk.Listbox(cal_ev_card, bg=C["white"], fg=C["text"],
                     relief="flat", font=FONT_UI,
                     selectbackground=C["selected"],
                     selectforeground=C["blue_text"],
                     activestyle="none", highlightthickness=0)
cal_lb.pack(fill="both",expand=True,padx=4,pady=4)

def cal_show_events():
    cal_lb.delete(0,"end")
    date = cal_widget.get_date() if CAL_OK else ""
    evs = cal_events.get(date, [])
    if not evs: cal_lb.insert("end","  No events")
    for ev in evs: cal_lb.insert("end", f"  • {ev}")

def cal_add_event():
    if not CAL_OK: return
    date = cal_widget.get_date()
    win = tk.Toplevel(root); win.title(f"Add Event — {date}")
    win.configure(bg=C["white"]); win.resizable(False,False)
    label(win,"Event:", bg=C["white"]).pack(padx=20,pady=(16,4))
    ev = tk.Entry(win, bg=C["bg"], fg=C["text"],
                  relief="solid", bd=1, font=FONT_UI, width=32)
    ev.pack(padx=20); ev.focus()
    def save():
        txt = ev.get().strip()
        if txt:
            cal_events.setdefault(date,[]).append(txt)
            cal_save_f(); cal_show_events(); win.destroy()
    btn(win,"Add",save,"primary").pack(pady=12)

def cal_delete():
    sel = cal_lb.curselection()
    if not sel or not CAL_OK: return
    date = cal_widget.get_date()
    idx = sel[0]
    evs = cal_events.get(date,[])
    if 0 <= idx < len(evs):
        evs.pop(idx); cal_save_f(); cal_show_events()

cal_btns = tk.Frame(cal_ev_card, bg=C["white"])
cal_btns.pack(fill="x", padx=8, pady=8)
btn(cal_btns,"+ Add Event",cal_add_event,"primary").pack(side="left",padx=4)
btn(cal_btns,"Delete",cal_delete,"danger").pack(side="left",padx=4)
if CAL_OK:
    cal_widget.bind("<<CalendarSelected>>", lambda e: cal_show_events())
    cal_show_events()

# ════════════════════════════════════════════════════════════
#  10. PASSWORD MANAGER
# ════════════════════════════════════════════════════════════
pg_pw = make_page("Passwords")
page_header(pg_pw, "Password Manager", "— encrypted local vault")

PW_FILE = os.path.join(os.path.expanduser("~"), ".studio_vault.json")
pw_entries  = []
pw_key      = None
pw_unlocked = False

def pw_derive_key(master):
    h = hashlib.sha256(master.encode()).digest()
    return base64.urlsafe_b64encode(h)

def pw_unlock_ui():
    for w in pw_main.winfo_children(): w.destroy()
    f = tk.Frame(pw_main, bg=C["bg"]); f.pack(expand=True)
    lk = card(f); lk.pack(padx=60,pady=20,ipadx=8,ipady=8)
    tk.Label(lk,text="🔐",font=("Helvetica",52),bg=C["white"]).pack(pady=(20,4))
    label(lk,"Enter master password:",font=FONT_BOLD,color=C["black"],
          bg=C["white"]).pack()
    pv = tk.StringVar()
    pe = tk.Entry(lk,textvariable=pv,show="●",bg=C["bg"],fg=C["text"],
                  relief="solid",bd=1,font=FONT_UI,width=28)
    pe.pack(padx=20,pady=8); pe.focus()
    def unlock(e=None):
        global pw_key, pw_unlocked, pw_entries
        pw_key = pw_derive_key(pv.get())
        if os.path.exists(PW_FILE):
            try:
                with open(PW_FILE) as f2: raw=json.load(f2)
                if CRYPT_OK:
                    fn = Fernet(pw_key)
                    pw_entries = json.loads(fn.decrypt(raw["data"].encode()).decode())
                else: pw_entries = raw.get("data",[])
            except: pw_entries=[]
        pw_unlocked=True; pw_vault_ui()
    pe.bind("<Return>",unlock)
    btn(lk,"Unlock",unlock,"primary").pack(pady=(0,20))

def pw_vault_save():
    if not pw_key: return
    if CRYPT_OK:
        fn = Fernet(pw_key)
        enc = fn.encrypt(json.dumps(pw_entries).encode()).decode()
        with open(PW_FILE,"w") as f: json.dump({"data":enc},f)
    else:
        with open(PW_FILE,"w") as f: json.dump({"data":pw_entries},f)

def pw_vault_ui():
    for w in pw_main.winfo_children(): w.destroy()
    tb = tk.Frame(pw_main, bg=C["bg"]); tb.pack(fill="x",padx=24,pady=8)
    btn(tb,"+ Add Entry",pw_add_entry,"primary").pack(side="left",padx=3)
    btn(tb,"Delete",pw_delete,"danger").pack(side="left",padx=3)
    btn(tb,"🔒 Lock",pw_lock,"ghost").pack(side="right",padx=3)
    body = tk.Frame(pw_main,bg=C["white"],
                    highlightbackground=C["border"],highlightthickness=1)
    body.pack(fill="both",expand=True,padx=24,pady=(0,20))
    cols=("Site","Username","Password","Notes")
    global pw_tree
    pw_tree = ttk.Treeview(body,columns=cols,show="headings",selectmode="browse")
    for c,w in zip(cols,[200,180,160,200]):
        pw_tree.heading(c,text=c); pw_tree.column(c,width=w)
    sb=ttk.Scrollbar(body,orient="vertical",command=pw_tree.yview)
    pw_tree.configure(yscrollcommand=sb.set)
    sb.pack(side="right",fill="y"); pw_tree.pack(fill="both",expand=True)
    pw_refresh_tree()

def pw_refresh_tree():
    pw_tree.delete(*pw_tree.get_children())
    for e in pw_entries:
        pw_tree.insert("","end",values=(
            e.get("site",""), e.get("user",""),
            "●"*len(e.get("pass","")), e.get("notes","")))

def pw_add_entry():
    win=tk.Toplevel(root); win.title("Add Password")
    win.configure(bg=C["white"]); win.geometry("360x320")
    fields={}
    for lbl,key,show in [("Site","site",False),("Username","user",False),
                           ("Password","pass",True),("Notes","notes",False)]:
        label(win,lbl+":",bg=C["white"]).pack(anchor="w",padx=20,pady=(10,2))
        v=tk.StringVar()
        tk.Entry(win,textvariable=v,show="●" if show else "",
                 bg=C["bg"],fg=C["text"],relief="solid",bd=1,
                 font=FONT_UI).pack(fill="x",padx=20)
        fields[key]=v
    def save():
        pw_entries.append({k:v.get() for k,v in fields.items()})
        pw_vault_save(); pw_refresh_tree(); win.destroy()
    btn(win,"Save",save,"primary").pack(pady=12)

def pw_delete():
    sel=pw_tree.focus()
    if not sel: return
    idx=pw_tree.index(sel)
    pw_entries.pop(idx); pw_vault_save(); pw_refresh_tree()

def pw_lock():
    global pw_unlocked, pw_key, pw_entries
    pw_unlocked=False; pw_key=None; pw_entries=[]; pw_unlock_ui()

pw_main = tk.Frame(pg_pw, bg=C["bg"]); pw_main.pack(fill="both",expand=True)
pw_unlock_ui()

# ════════════════════════════════════════════════════════════
#  11. COLOR PICKER
# ════════════════════════════════════════════════════════════
pg_color = make_page("Colors")
page_header(pg_color, "Color Picker", "— hex, rgb, hsl")

cp_hex  = tk.StringVar(value="#2563EB")
cp_r    = tk.StringVar(value="37")
cp_g    = tk.StringVar(value="99")
cp_b    = tk.StringVar(value="235")
cp_hist = []

cp_center = tk.Frame(pg_color, bg=C["bg"]); cp_center.pack(expand=True)
cp_card   = card(cp_center); cp_card.pack(padx=40,pady=10,ipadx=8)

def cp_update(source="hex"):
    try:
        if source=="hex":
            h = cp_hex.get().lstrip("#")
            if len(h)==6:
                r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
                cp_r.set(str(r)); cp_g.set(str(g)); cp_b.set(str(b))
        else:
            r,g,b=int(cp_r.get()),int(cp_g.get()),int(cp_b.get())
            cp_hex.set(f"#{r:02X}{g:02X}{b:02X}")
        h=cp_hex.get()
        cp_preview.configure(bg=h)
        lum=0.299*int(cp_r.get())+0.587*int(cp_g.get())+0.114*int(cp_b.get())
        cp_hex_lbl.configure(fg="white" if lum<128 else C["black"])
    except: pass

def cp_pick():
    color = colorchooser.askcolor(color=cp_hex.get())
    if color[1]:
        cp_hex.set(color[1].upper()); cp_update("hex")

def cp_copy():
    root.clipboard_clear(); root.clipboard_append(cp_hex.get())

def cp_add_hist():
    h=cp_hex.get()
    if h not in cp_hist: cp_hist.append(h)
    if len(cp_hist)>10: cp_hist.pop(0)
    hist_render()

def hist_render():
    for w in hist_frame.winfo_children(): w.destroy()
    for h in reversed(cp_hist):
        f=tk.Frame(hist_frame,bg=h,width=36,height=36,cursor="hand2",
                   highlightbackground=C["border"],highlightthickness=1)
        f.pack(side="left",padx=4,pady=4)
        f.bind("<Button-1>",lambda e,hx=h: (cp_hex.set(hx),cp_update("hex")))

cp_preview = tk.Label(cp_card, text="", bg=cp_hex.get(),
                       width=30, height=5)
cp_preview.pack(fill="x", padx=12, pady=(12,0))
cp_hex_lbl = tk.Label(cp_preview, textvariable=cp_hex,
                       bg=cp_hex.get(), fg=C["white"],
                       font=(FONT_UI[0],16,"bold"))
cp_hex_lbl.place(relx=0.5,rely=0.5,anchor="center")

rf = tk.Frame(cp_card, bg=C["white"]); rf.pack(fill="x",padx=12,pady=10)
for lbl,var,ch in [("R",cp_r,"red"),("G",cp_g,"green"),("B",cp_b,"blue")]:
    row=tk.Frame(rf,bg=C["white"]); row.pack(fill="x",pady=2)
    tk.Label(row,text=lbl,bg=C["white"],fg=C["muted"],
             font=FONT_BOLD,width=2).pack(side="left",padx=(0,6))
    sl=tk.Scale(row,from_=0,to=255,orient="horizontal",variable=var,
                command=lambda v,_=None: cp_update("rgb"),
                bg=C["white"],troughcolor=C["border"],
                highlightthickness=0,showvalue=False,
                length=200,sliderlength=16)
    sl.pack(side="left",fill="x",expand=True)
    tk.Entry(row,textvariable=var,width=4,bg=C["bg"],
             fg=C["text"],relief="solid",bd=1,
             font=FONT_UI).pack(side="left",padx=6)

bf=tk.Frame(cp_card,bg=C["white"]); bf.pack(padx=12,pady=(4,8))
btn(bf,"Open Picker",cp_pick,"primary").pack(side="left",padx=4)
btn(bf,"Copy Hex",cp_copy,"normal").pack(side="left",padx=4)
btn(bf,"Save",cp_add_hist,"success").pack(side="left",padx=4)

label(cp_card,"Saved colors:",font=FONT_SM,color=C["muted"],
      bg=C["white"]).pack(anchor="w",padx=12)
hist_frame=tk.Frame(cp_card,bg=C["white"]); hist_frame.pack(fill="x",padx=12,pady=(0,12))

cp_r.trace_add("write",lambda *a: cp_update("rgb"))
cp_g.trace_add("write",lambda *a: cp_update("rgb"))
cp_b.trace_add("write",lambda *a: cp_update("rgb"))
cp_update()

# ════════════════════════════════════════════════════════════
#  12. TERMINAL
# ════════════════════════════════════════════════════════════
pg_term = make_page("Terminal")
page_header(pg_term, "Terminal", "— run shell commands")

term_cwd = os.path.expanduser("~")
term_history = []
term_hist_idx = 0

term_body = tk.Frame(pg_term, bg=C["black"],
                     highlightbackground=C["border"],
                     highlightthickness=1)
term_body.pack(fill="both",expand=True,padx=24,pady=(8,20))

term_out = tk.Text(term_body, bg="#0D0D0D", fg="#E5E7EB",
                    font=FONT_MONO, relief="flat", bd=0,
                    insertbackground="#fff",
                    selectbackground="#374151",
                    state="disabled", padx=10, pady=8)
term_sb = ttk.Scrollbar(term_body,orient="vertical",command=term_out.yview)
term_out.configure(yscrollcommand=term_sb.set)
term_sb.pack(side="right",fill="y"); term_out.pack(fill="both",expand=True)

term_in_frame = tk.Frame(term_body, bg="#0D0D0D")
term_in_frame.pack(fill="x")
tk.Label(term_in_frame,text="$",bg="#0D0D0D",fg="#10B981",
         font=FONT_MONO,padx=10).pack(side="left")
term_entry = tk.Entry(term_in_frame, bg="#0D0D0D", fg="#E5E7EB",
                       insertbackground="#fff", relief="flat",
                       font=FONT_MONO)
term_entry.pack(fill="x",side="left",expand=True,ipady=8)
term_entry.focus()

def term_write(text, color="#E5E7EB"):
    term_out.configure(state="normal")
    term_out.insert("end", text)
    term_out.see("end")
    term_out.configure(state="disabled")

def term_run(e=None):
    global term_cwd, term_hist_idx
    cmd = term_entry.get().strip()
    if not cmd: return
    term_history.append(cmd); term_hist_idx=len(term_history)
    term_entry.delete(0,"end")
    term_write(f"\n$ {cmd}\n", "#10B981")
    if cmd.startswith("cd "):
        try:
            d = os.path.expanduser(cmd[3:].strip())
            if not os.path.isabs(d): d=os.path.join(term_cwd,d)
            os.chdir(d); term_cwd=d
            term_write(f"→ {term_cwd}\n","#6B7280")
        except Exception as ex: term_write(f"Error: {ex}\n","#EF4444")
    elif cmd=="clear":
        term_out.configure(state="normal"); term_out.delete("1.0","end")
        term_out.configure(state="disabled")
    else:
        def run_bg():
            try:
                res=subprocess.run(cmd,shell=True,capture_output=True,
                                   text=True,cwd=term_cwd,timeout=30)
                if res.stdout: root.after(0,lambda: term_write(res.stdout))
                if res.stderr: root.after(0,lambda: term_write(res.stderr,"#EF4444"))
            except subprocess.TimeoutExpired:
                root.after(0,lambda: term_write("Timeout\n","#EF4444"))
            except Exception as ex:
                root.after(0,lambda: term_write(f"Error: {ex}\n","#EF4444"))
        threading.Thread(target=run_bg,daemon=True).start()

def term_hist_up(e):
    global term_hist_idx
    if term_hist_idx>0:
        term_hist_idx-=1; term_entry.delete(0,"end")
        term_entry.insert(0,term_history[term_hist_idx])
def term_hist_dn(e):
    global term_hist_idx
    if term_hist_idx<len(term_history)-1:
        term_hist_idx+=1; term_entry.delete(0,"end")
        term_entry.insert(0,term_history[term_hist_idx])
    else: term_hist_idx=len(term_history); term_entry.delete(0,"end")

term_entry.bind("<Return>",term_run)
term_entry.bind("<Up>",term_hist_up)
term_entry.bind("<Down>",term_hist_dn)
term_write(f"Studio Suite Terminal\nDirectory: {term_cwd}\nType any command and press Enter.\n\n")

# ════════════════════════════════════════════════════════════
#  INIT
# ════════════════════════════════════════════════════════════
show_tab("Files")
root.mainloop()