import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import time
import os
import sys
import json
import re
import queue
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
STOP_REGER_FLAG = os.path.join(SETTINGS_DIR, "stop_reger.flag")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
STARTER_STATE_FILE = os.path.join(SETTINGS_DIR, "starter_state.json")
PROXY_FILE = os.path.join(SETTINGS_DIR, "proxy.txt")
DB_DIR = os.path.join(BASE_DIR, "db")
CASHOUT_DIR = os.path.join(BASE_DIR, "cashout")
WORK_DIR = os.path.join(BASE_DIR, "work")
REGER_SCRIPT = os.path.join(BASE_DIR, "reger.py")
VERSION = "3.0"

# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def ensure_dirs():
    for d in [SETTINGS_DIR, DB_DIR, CASHOUT_DIR, WORK_DIR,
              os.path.join(BASE_DIR, "logs"), os.path.join(BASE_DIR, "profiles"),
              os.path.join(BASE_DIR, "mails"), os.path.join(BASE_DIR, "avatar"),
              os.path.join(BASE_DIR, "videos")]:
        os.makedirs(d, exist_ok=True)

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e: print(f"[save_config] {e}")

def load_state():
    try:
        with open(STARTER_STATE_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def save_state(state):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(STARTER_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception: pass

def count_files(folder):
    try: return len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
    except Exception: return 0

def get_last_index():
    try:
        with open(os.path.join(DB_DIR, "last_index.txt"), "r") as f:
            return int(f.read().strip())
    except Exception: return 1

def read_proxies():
    try:
        if not os.path.exists(PROXY_FILE): return []
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    except Exception: return []

def fmt_time(sec):
    sec = int(sec)
    if sec < 60: return f"{sec}с"
    m, s = divmod(sec, 60)
    if m < 60: return f"{m}м {s:02d}с"
    h, m = divmod(m, 60)
    return f"{h}ч {m:02d}м"

# ═══════════════════════════════════════════════════════════════════════
#  Theme
# ═══════════════════════════════════════════════════════════════════════

_MAC = sys.platform == "darwin"
BG="#1c1c1e"; BG2="#2c2c2e"; BG3="#3a3a3c"
ACCENT="#ff453a"; ACCENT2="#64d2ff"; GREEN="#30d158"; YELLOW="#ffd60a"; RED="#ff453a"
TEXT="#f5f5f7"; TEXT_DIM="#98989d"; CARD="#2c2c2e"; BORDER="#48484a"; HDR="#000000"; ORANGE="#ff9f0a"

_F = "Helvetica Neue" if _MAC else "Segoe UI"
_M = "Menlo" if _MAC else "Consolas"
F12=(_F,12); F12B=(_F,12,"bold"); F11=(_F,11); FLOG=(_M,11)
F16B=(_F,16,"bold"); F13B=(_F,13,"bold"); F10=(_F,10)

# ═══════════════════════════════════════════════════════════════════════
#  Log
# ═══════════════════════════════════════════════════════════════════════

log_q: queue.Queue = queue.Queue()
LOG_CLR = {"SUCCESS":GREEN,"ERROR":RED,"WARNING":YELLOW,"INFO":ACCENT2,
           "OK":GREEN,"WARN":YELLOW,"GUI":TEXT_DIM,"DEFAULT":TEXT}

def log_level(line):
    m = re.search(r"\[(SUCCESS|ERROR|WARNING|INFO|OK|WARN|GUI)\]", line, re.IGNORECASE)
    return m.group(1).upper() if m else "DEFAULT"

# ═══════════════════════════════════════════════════════════════════════
#  Process pool
# ═══════════════════════════════════════════════════════════════════════

procs = []        # [(proc, thread, slot)]
procs_lock = threading.Lock()
launched = 0; finished = 0; errors = 0; success = 0
stats_lock = threading.Lock()
session_start = 0.0

_proxy_idx = 0
_proxy_lock = threading.Lock()

def next_proxy():
    global _proxy_idx
    px = read_proxies()
    if not px: return ""
    with _proxy_lock:
        i = _proxy_idx % len(px); _proxy_idx += 1
    return px[i]

def _read_output(proc, slot, pid):
    global finished, errors, success
    try:
        for raw in iter(proc.stdout.readline, b""):
            try: line = raw.decode("utf-8", errors="replace").rstrip()
            except Exception: line = repr(raw)
            if line:
                log_q.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}][#{slot}] {line}")
    except Exception: pass
    finally:
        rc = proc.wait()
        with stats_lock:
            if rc != 0: errors += 1
            else: success += 1
            finished += 1
        st = "OK" if rc == 0 else f"rc={rc}"
        log_q.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}][#{slot}] Завершён pid={pid} {st}")
        with procs_lock:
            procs[:] = [x for x in procs if x[0] is not proc]

def launch_one(slot, args):
    global launched
    cmd = [sys.executable, REGER_SCRIPT]
    cmd += [str(args.get("wait_time", 750))]
    cmd += [str(args.get("gift_option", ""))]
    cmd += ["1" if args.get("use_avatar") else "0"]
    cmd += ["1" if args.get("use_name")   else "0"]
    cmd += ["1" if args.get("use_bio")    else "0"]
    cmd += ["1" if args.get("activate_ai") else "0"]
    cmd += ["1" if args.get("block_dolboeba") else "0"]
    px = args.get("proxy_spec") or ""
    if px: cmd += ["--proxy", px]
    tot = args.get("total_target")
    if tot: cmd += ["--total", str(tot)]
    otp = args.get("otp_min_delay", 0)
    if otp and float(otp) > 0: cmd += ["--otp-delay", str(float(otp))]
    cmd += ["--vpn-country", _vpn_current_country()]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=BASE_DIR, env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"))
        t = threading.Thread(target=_read_output, args=(proc, slot, proc.pid), daemon=True)
        t.start()
        with procs_lock: procs.append((proc, t, slot))
        with stats_lock: launched += 1
        info = f" proxy={px[:35]}" if px else ""
        log_q.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}][#{slot}] Запущен pid={proc.pid}{info}")
        return True
    except Exception as e:
        log_q.put(f"[ERR][#{slot}] {e}"); return False

def stop_all():
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(STOP_REGER_FLAG, "w") as f: f.write("stop")
        log_q.put("[SYS] Стоп-флаг создан")
    except Exception as e: log_q.put(f"[ERR] {e}")

def clear_stop():
    try:
        if os.path.exists(STOP_REGER_FLAG):
            os.remove(STOP_REGER_FLAG); log_q.put("[SYS] Стоп-флаг снят")
    except Exception: pass

# ═══════════════════════════════════════════════════════════════════════
#  Worker — простая логика:
#    Запускаем до N параллельных стримов.
#    Каждый: регистрация → стрим (wait сек) → алмазы → конец.
#    Когда один освободился — на его место стартует следующий.
# ═══════════════════════════════════════════════════════════════════════

_running = False
_worker_thread = None

# ═══════════════════════════════════════════════════════════════════════
#  Windscribe VPN — автосмена каждые N профилей (только СНГ)
# ═══════════════════════════════════════════════════════════════════════

VPN_SWITCH_EVERY = 3   # менять страну каждые N профилей

VPN_CIS_LOCATIONS = [
    "Russia",
    "Ukraine",
    "Moldova",
    "Georgia",
    "Serbia",
    "Albania",
    "North Macedonia",
    "Bosnia",
    "Croatia",
    "Slovenia",
    "Bulgaria",
    "Romania",
    "Hungary",
    "Slovakia",
    "Czech Republic",
    "Poland",
    "Lithuania",
    "Latvia",
    "Estonia",
    "Cyprus",
    "Turkey",
]

_vpn_index = 0
_vpn_lock  = threading.Lock()

def _vpn_current_country() -> str:
    return VPN_CIS_LOCATIONS[_vpn_index % len(VPN_CIS_LOCATIONS)]

def switch_windscribe(country: str):
    """Переключает Windscribe на нужную страну через меню бара (AppleScript)."""
    script = f'''
tell application "System Events"
    tell process "Windscribe"
        set mbItem to menu bar item 1 of menu bar 2
        click mbItem
        delay 0.6
        tell menu 1 of mbItem
            tell menu item "Локации"
                click
                delay 0.5
                try
                    click menu item "{country}" of menu 1
                    delay 0.4
                    try
                        set subItems to every menu item of menu 1 of menu item "{country}" of menu 1
                        if (count of subItems) > 0 then
                            click item 1 of subItems
                        end if
                    end try
                on error
                    key code 53
                end try
            end tell
        end tell
    end tell
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            log_q.put(f"[VPN] ✅ Переключено на {country}")
        else:
            log_q.put(f"[VPN] ⚠️ Ошибка: {result.stderr.strip()[:80]}")
    except Exception as e:
        log_q.put(f"[VPN] ❌ {e}")

def _maybe_switch_vpn(profile_n: int):
    """Вызывается после каждого запуска профиля. Переключает VPN каждые VPN_SWITCH_EVERY профилей."""
    global _vpn_index
    if profile_n % VPN_SWITCH_EVERY != 0:
        return
    with _vpn_lock:
        _vpn_index = (_vpn_index + 1) % len(VPN_CIS_LOCATIONS)
        country = VPN_CIS_LOCATIONS[_vpn_index]
    log_q.put(f"[VPN] 🌍 Профилей запущено: {profile_n} → меняю страну на {country}")
    threading.Thread(target=switch_windscribe, args=(country,), daemon=True).start()

def _worker(parallel, total, args, on_done):
    global _running
    n = 0
    # Подключаемся к первой СНГ стране при старте
    log_q.put(f"[VPN] 🌍 Старт → подключаю {_vpn_current_country()}")
    threading.Thread(target=switch_windscribe, args=(_vpn_current_country(),), daemon=True).start()
    time.sleep(4)  # даём VPN подключиться
    try:
        while _running and n < total:
            with procs_lock: alive = len(procs)
            if alive >= parallel:
                time.sleep(1); continue
            n += 1
            la = {**args, "total_target": total}
            if args.get("proxy_mode") == "file":
                la["proxy_spec"] = next_proxy()
            launch_one(n, la)
            # Проверяем нужно ли менять VPN
            _maybe_switch_vpn(n)
            # Мелкая пауза чтобы не стартовали все в одну мс
            if n < total:
                time.sleep(2)
        # Ждём пока все доработают
        while _running:
            with procs_lock:
                if not procs: break
            time.sleep(2)
    finally:
        _running = False
        log_q.put("[SYS] Готово")
        try: on_done()
        except Exception: pass

# ═══════════════════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.title(f"Tango Starter v{VERSION}")
        w, h = (1200, 820) if _MAC else (1100, 780)
        self.geometry(f"{w}x{h}"); self.minsize(960, 660)
        self.configure(bg=BG)
        self.cfg = load_config(); self.st = load_state()
        self._imap_open = False
        self._build(); self._load_state()
        self._poll_log(); self._poll_stats()
        self._autosave()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind_all("<Command-Return>" if _MAC else "<Control-Return>", lambda e: self._start())
        self.bind_all("<Escape>", lambda e: self._stop())

    # ── Build ────────────────────────────────────────────────────────

    def _build(self):
        # Header
        h = tk.Frame(self, bg=HDR, pady=10); h.pack(fill="x")
        tk.Label(h, text=f"Tango Starter v{VERSION}", font=F16B, bg=HDR, fg=TEXT).pack(side="left", padx=20)

        self.btn_stop = tk.Button(h, text="  СТОП  ", font=(_F,13,"bold"),
            bg=RED, fg="white", activebackground="#b91c1c",
            relief="flat", bd=0, cursor="hand2", padx=16, pady=6,
            command=self._stop, state="disabled")
        self.btn_stop.pack(side="right", padx=12)

        self.btn_start = tk.Button(h, text="  СТАРТ  ", font=(_F,13,"bold"),
            bg=GREEN, fg="white", activebackground="#248a3d",
            relief="flat", bd=0, cursor="hand2", padx=16, pady=6,
            command=self._start)
        self.btn_start.pack(side="right", padx=4)

        self.lbl_session = tk.Label(h, text="", font=F11, bg=HDR, fg=ORANGE)
        self.lbl_session.pack(side="right", padx=8)
        self.lbl_clock = tk.Label(h, text="", font=F11, bg=HDR, fg=TEXT_DIM)
        self.lbl_clock.pack(side="right", padx=12)
        self._tick()

        # Pane
        pane = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=6, sashrelief="flat", bd=0)
        pane.pack(fill="both", expand=True, padx=8, pady=8)
        left = tk.Frame(pane, bg=BG, width=370); right = tk.Frame(pane, bg=BG)
        pane.add(left, minsize=310); pane.add(right, minsize=440)
        self._build_left(left); self._build_right(right)

    def _build_left(self, parent):
        c = tk.Canvas(parent, bg=BG, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); c.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(c, bg=BG)
        wid = c.create_window((0,0), window=inner, anchor="nw")
        def _cfg(e):
            c.configure(scrollregion=c.bbox("all")); c.itemconfig(wid, width=c.winfo_width())
        inner.bind("<Configure>", _cfg); c.bind("<Configure>", _cfg)
        def _sc(e):
            if _MAC: c.yview_scroll(int(-1*e.delta), "units")
            else: c.yview_scroll(int(-1*(e.delta/120)), "units")
        c.bind("<MouseWheel>", _sc); inner.bind("<MouseWheel>", _sc)
        def _bc(w):
            w.bind("<MouseWheel>", _sc)
            for ch in w.winfo_children(): _bc(ch)
        inner.bind("<Map>", lambda e: _bc(inner))

        p = dict(padx=12, pady=3)

        # ── Главное — запуск ──
        self._sec(inner, "Запуск")
        self._row(inner, "Потоков", "ent_threads", 5, val="1")
        self._row(inner, "Всего аккаунтов", "ent_total", 6, val="10")
        self._row(inner, "Длительность стрима (сек)", "ent_wait", 7, val="750")

        tk.Label(inner, text=(
            "Стрим запускается → идёт указанное время →\n"
            "алмазы записываются → следующий стартует.\n"
            "Потоков > 1 = несколько стримов параллельно."
        ), font=F10, bg=BG, fg=TEXT_DIM, justify="left").pack(fill="x", padx=14, pady=(0,8))

        # Подарок
        fg = tk.Frame(inner, bg=BG); fg.pack(fill="x", **p)
        tk.Label(fg, text="Подарок", font=F12, bg=BG, fg=TEXT, width=24, anchor="w").pack(side="left")
        self.var_gift = tk.StringVar(value="")
        ttk.Combobox(fg, textvariable=self.var_gift, values=["","99","299","499","999","1499"],
                      width=8, state="readonly").pack(side="left")

        # Прокси
        fp = tk.Frame(inner, bg=BG); fp.pack(fill="x", **p)
        tk.Label(fp, text="Прокси", font=F12, bg=BG, fg=TEXT, width=24, anchor="w").pack(side="left")
        self.var_proxy = tk.StringVar(value="none")
        for t,v in [("нет","none"),("файл","file"),("ручной","manual")]:
            tk.Radiobutton(fp, text=t, variable=self.var_proxy, value=v,
                bg=BG, fg=TEXT, selectcolor=BG3, activebackground=BG, font=F11).pack(side="left", padx=2)
        self._row(inner, "Прокси вручную", "ent_proxy", 25, placeholder="host:port:user:pass")

        # Профиль
        self._sec(inner, "Профиль")
        self.var_avatar = self._chk(inner, "Аватарка")
        self.var_name   = self._chk(inner, "Имя")
        self.var_bio    = self._chk(inner, "Bio")
        self.var_ai     = self._chk(inner, "AI")
        self.var_block  = self._chk(inner, "Блок (block.txt)")

        # ── Кнопки ──
        self._sec(inner, "Управление")
        fb = tk.Frame(inner, bg=BG); fb.pack(fill="x", **p)
        self._btn(fb, "Тест (1 запуск)", self._single, bg=BG3, fg=ACCENT2).pack(side="left", padx=(0,6))
        self._btn(fb, "Снять стоп", clear_stop, bg=BG2, fg=YELLOW).pack(side="left", padx=(0,6))
        self._btn(fb, "Сброс", self._reset, bg=BG2, fg=TEXT_DIM).pack(side="left")

        # ── Конфиг (сворачиваемый) ──
        self._toggle_sec(inner, "Конфиг (config.json)", "_cfg_open", "_cfg_frame")
        self._cfg_frame = tk.Frame(inner, bg=BG)
        self._row(self._cfg_frame, "Tango Ref URL", "ent_ref_url", 34)
        fd = tk.Frame(self._cfg_frame, bg=BG); fd.pack(fill="x", padx=12, pady=3)
        tk.Label(fd, text="Email домены (по строке)", font=F12, bg=BG, fg=TEXT, anchor="w").pack(anchor="w")
        self.txt_domains = tk.Text(fd, font=F12, bg=CARD, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=5, height=5, width=30, highlightthickness=1,
            highlightcolor=ACCENT2, highlightbackground=BORDER)
        self.txt_domains.pack(fill="x", pady=3)
        self._row(self._cfg_frame, "Префикс email", "ent_prefix", 10, val="soft")
        self._row(self._cfg_frame, "Таймаут OTP (сек)", "ent_otp_timeout", 6, val="240")
        self._row(self._cfg_frame, "Пауза OTP (сек)", "ent_otp_delay", 6, val="60")
        self.var_fakecam = self._chk(self._cfg_frame, "Видео вместо камеры")
        self.lbl_videos = tk.Label(self._cfg_frame, text="", font=F10, bg=BG, fg=TEXT_DIM, justify="left")
        self.lbl_videos.pack(fill="x", padx=14, pady=(0,4))
        self._update_video_count()
        self._btn(self._cfg_frame, "Сохранить config.json", self._save_cfg, bg=BG3, fg=ACCENT2).pack(fill="x", padx=12, pady=6)

        # ── IMAP (сворачиваемый) ──
        self._toggle_sec(inner, "IMAP", "_imap_open", "_imap_frame")
        self._imap_frame = tk.Frame(inner, bg=BG)
        self._row(self._imap_frame, "Сервер", "ent_imap_srv", 22, placeholder="imap.gmail.com")
        self._row(self._imap_frame, "Email", "ent_imap_email", 26, placeholder="you@gmail.com")
        self._row_pw(self._imap_frame, "Пароль", "ent_imap_pass", 20)
        self._row(self._imap_frame, "Порт", "ent_imap_port", 6, val="993")
        fi = tk.Frame(self._imap_frame, bg=BG); fi.pack(fill="x", padx=12, pady=3)
        self._btn(fi, "Сохранить", self._save_imap, bg=BG3, fg=ACCENT2).pack(side="left", padx=(0,8))
        self._btn(fi, "Тест", self._test_imap, bg=BG3, fg=YELLOW).pack(side="left")

        # ── Статистика ──
        self._sec(inner, "Статистика")
        self.s_launched  = self._stat(inner, "Запущено")
        self.s_running   = self._stat(inner, "Работает")
        self.s_finished  = self._stat(inner, "Завершено")
        self.s_ok        = self._stat(inner, "Успешно")
        self.s_err       = self._stat(inner, "Ошибок")
        self.s_cashout   = self._stat(inner, "Cashout")
        self.s_work      = self._stat(inner, "Work")
        self.s_idx       = self._stat(inner, "Индекс")
        self.s_domains   = self._stat(inner, "Доменов")
        self.s_proxies   = self._stat(inner, "Прокси")
        self.s_flag      = self._stat(inner, "Стоп-флаг")
        self.s_vpn       = self._stat(inner, "VPN страна")

        self.lbl_eta = tk.Label(inner, text="", font=F12B, bg=BG, fg=ORANGE, wraplength=280, justify="left")
        self.lbl_eta.pack(fill="x", padx=12, pady=2)

        fp2 = tk.Frame(inner, bg=BG); fp2.pack(fill="x", padx=12, pady=6)
        self.pbar = ttk.Progressbar(fp2, orient="horizontal", length=280, mode="determinate", maximum=100)
        self.pbar.pack(fill="x", pady=3)
        self.lbl_prog = tk.Label(fp2, text="", font=F11, bg=BG, fg=TEXT_DIM)
        self.lbl_prog.pack(anchor="w")

    def _build_right(self, parent):
        nb = ttk.Notebook(parent); nb.pack(fill="both", expand=True)

        # Лог
        lf = tk.Frame(nb, bg=BG2); nb.add(lf, text="  Лог  ")
        ct = tk.Frame(lf, bg=BG2); ct.pack(fill="x", padx=8, pady=6)
        self._btn(ct, "Очистить", self._clear_log, bg=BG3, fg=TEXT_DIM).pack(side="left", padx=4)
        self._btn(ct, "Сохранить", self._save_log, bg=BG3, fg=TEXT_DIM).pack(side="left", padx=4)
        self.var_scroll = tk.BooleanVar(value=True)
        tk.Checkbutton(ct, text="Автоскролл", variable=self.var_scroll,
            bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=F11).pack(side="left", padx=8)
        tk.Label(ct, text="Поиск:", font=F11, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(12,4))
        self.ent_search = tk.Entry(ct, font=F11, bg=CARD, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=3, width=16)
        self.ent_search.pack(side="left")
        self.ent_search.bind("<Return>", lambda e: self._find_log())
        self._btn(ct, ">>", self._find_log, bg=BG3, fg=ACCENT2).pack(side="left", padx=2)
        self._search_pos = "1.0"

        self.log = scrolledtext.ScrolledText(lf, font=FLOG, bg="#0d1117", fg=TEXT,
            insertbackground=TEXT, selectbackground=BG3, relief="flat", bd=0, wrap="word")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)
        for k,v in LOG_CLR.items(): self.log.tag_configure(k, foreground=v)
        self.log.tag_configure("SRCH", background="#44403c")

        # Config
        cf = tk.Frame(nb, bg=BG2); nb.add(cf, text="  config.json  ")
        self._btn(cf, "Обновить", self._reload_cfg, bg=BG3, fg=TEXT_DIM).pack(anchor="w", padx=8, pady=6)
        self.cfg_view = scrolledtext.ScrolledText(cf, font=FLOG, bg="#0d1117", fg=ACCENT2,
            insertbackground=TEXT, relief="flat", bd=0)
        self.cfg_view.pack(fill="both", expand=True, padx=6, pady=6)
        self._reload_cfg()

        # Прокси
        pf = tk.Frame(nb, bg=BG2); nb.add(pf, text="  Прокси  ")
        self._btn(pf, "Обновить", self._reload_px, bg=BG3, fg=TEXT_DIM).pack(anchor="w", padx=8, pady=6)
        self.px_view = scrolledtext.ScrolledText(pf, font=FLOG, bg="#0d1117", fg=YELLOW, relief="flat", bd=0)
        self.px_view.pack(fill="both", expand=True, padx=6, pady=6)
        self._reload_px()

    # ── Widgets ──────────────────────────────────────────────────────

    def _sec(self, p, title):
        f = tk.Frame(p, bg=BG); f.pack(fill="x", padx=8, pady=(14,3))
        tk.Label(f, text=title, font=F13B, bg=BG, fg=ACCENT2).pack(anchor="w")
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=8)

    def _toggle_sec(self, p, title, flag_attr, frame_attr):
        """Секция со сворачиванием."""
        setattr(self, flag_attr, False)
        f = tk.Frame(p, bg=BG); f.pack(fill="x", padx=8, pady=(14,3))
        lbl = tk.Label(f, text=f"▶ {title}", font=F13B, bg=BG, fg=ACCENT2, cursor="hand2")
        lbl.pack(anchor="w")
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=8)
        def toggle(e=None):
            opened = getattr(self, flag_attr)
            frame = getattr(self, frame_attr)
            if opened:
                frame.pack_forget(); lbl.config(text=f"▶ {title}")
            else:
                frame.pack(fill="x", after=f); lbl.config(text=f"▼ {title}")
            setattr(self, flag_attr, not opened)
        lbl.bind("<Button-1>", toggle)

    def _row(self, p, label, attr, width=14, val="", placeholder=""):
        f = tk.Frame(p, bg=BG); f.pack(fill="x", padx=12, pady=3)
        tk.Label(f, text=label, font=F12, bg=BG, fg=TEXT, width=24, anchor="w").pack(side="left")
        e = tk.Entry(f, font=F12, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", bd=5,
                     width=width, highlightthickness=1, highlightcolor=ACCENT2, highlightbackground=BORDER)
        if val: e.insert(0, val)
        elif placeholder:
            e.insert(0, placeholder); e.config(fg=TEXT_DIM)
            def fi(ev, e_=e, ph=placeholder):
                if e_.get()==ph: e_.delete(0,"end"); e_.config(fg=TEXT)
            def fo(ev, e_=e, ph=placeholder):
                if not e_.get(): e_.insert(0,ph); e_.config(fg=TEXT_DIM)
            e.bind("<FocusIn>", fi); e.bind("<FocusOut>", fo)
        e.pack(side="left"); setattr(self, attr, e)

    def _row_pw(self, p, label, attr, width=20):
        f = tk.Frame(p, bg=BG); f.pack(fill="x", padx=12, pady=3)
        tk.Label(f, text=label, font=F12, bg=BG, fg=TEXT, width=24, anchor="w").pack(side="left")
        e = tk.Entry(f, font=F12, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", bd=5,
                     width=width, highlightthickness=1, highlightcolor=ACCENT2, highlightbackground=BORDER, show="*")
        e.pack(side="left"); setattr(self, attr, e)
        tk.Button(f, text="👁", command=lambda: e.config(show="" if e.cget("show")=="*" else "*"),
                  font=F10, bg=BG3, fg=TEXT_DIM, relief="flat", bd=0, padx=4).pack(side="left", padx=4)

    def _btn(self, p, text, cmd, bg=BG3, fg=TEXT):
        return tk.Button(p, text=text, command=cmd, font=F12B, bg=bg, fg=fg,
            activebackground=ACCENT2, activeforeground="white", relief="flat", bd=0,
            cursor="hand2", pady=7, padx=12)

    def _chk(self, p, label):
        v = tk.BooleanVar(); f = tk.Frame(p, bg=BG); f.pack(fill="x", padx=12, pady=2)
        tk.Checkbutton(f, text=label, variable=v, font=F12, bg=BG, fg=TEXT,
            selectcolor=BG3, activebackground=BG, activeforeground=TEXT).pack(anchor="w")
        return v

    def _stat(self, p, label):
        f = tk.Frame(p, bg=BG); f.pack(fill="x", padx=12, pady=2)
        tk.Label(f, text=f"{label}:", font=F11, bg=BG, fg=TEXT_DIM, width=22, anchor="w").pack(side="left")
        l = tk.Label(f, text="—", font=F12B, bg=BG, fg=ACCENT2, anchor="w"); l.pack(side="left")
        return l

    # ── State ────────────────────────────────────────────────────────

    def _v(self, attr, default=""):
        w = getattr(self, attr, None)
        return (w.get().strip() or default) if w else default

    def _i(self, attr, default=0):
        try: return int(self._v(attr, str(default)))
        except Exception: return default

    def _domains(self):
        raw = self.txt_domains.get("1.0","end").strip()
        return [d.strip() for d in raw.splitlines() if d.strip()]

    def _update_video_count(self):
        vdir = os.path.join(BASE_DIR, "videos")
        exts = {".mp4", ".y4m", ".webm", ".mov", ".avi", ".mkv"}
        try:
            vids = [f for f in os.listdir(vdir)
                    if os.path.isfile(os.path.join(vdir, f)) and os.path.splitext(f)[1].lower() in exts]
        except Exception:
            vids = []
        if vids:
            names = ", ".join(sorted(vids)[:5])
            more = f" и ещё {len(vids)-5}" if len(vids) > 5 else ""
            self.lbl_videos.config(
                text=f"videos/: {len(vids)} файлов ({names}{more})\n"
                     f"Ротация по очереди. mp4 → y4m автоконверт.",
                fg=GREEN)
        else:
            self.lbl_videos.config(
                text="videos/: пусто. Положи .mp4 файлы в папку videos/\n"
                     "Без видео — Chrome покажет тест-паттерн.",
                fg=YELLOW)

    def _load_state(self):
        s, c = self.st, self.cfg
        def _s(attr, val):
            w = getattr(self, attr, None)
            if w and val is not None: w.delete(0,"end"); w.insert(0,str(val)); w.config(fg=TEXT)
        _s("ent_threads", str(s.get("threads",1)))
        _s("ent_total", str(s.get("total",10)))
        _s("ent_wait", str(s.get("wait",750)))
        _s("ent_proxy", s.get("proxy_manual",""))
        _s("ent_ref_url", c.get("tango_ref_url",""))
        domains = list(c.get("email_domains") or [])
        if not domains:
            for i in range(1,14):
                k = "email_domain" if i==1 else f"email_domain{i}"
                v = (c.get(k) or "").strip()
                if v: domains.append(v)
        self.txt_domains.delete("1.0","end")
        if domains: self.txt_domains.insert("1.0", "\n".join(domains))
        _s("ent_prefix", c.get("email_prefix","soft"))
        _s("ent_otp_timeout", str(c.get("email_check_timeout_sec",240)))
        _s("ent_otp_delay", str(s.get("otp_min_delay",60)))
        _s("ent_imap_srv", c.get("imap_server","imap.gmail.com"))
        _s("ent_imap_email", c.get("imap_email",""))
        _s("ent_imap_pass", c.get("imap_password",""))
        _s("ent_imap_port", str(c.get("imap_port",993)))
        self.var_gift.set(s.get("gift","")); self.var_proxy.set(s.get("proxy_mode","none"))
        self.var_avatar.set(s.get("use_avatar",True)); self.var_name.set(s.get("use_name",True))
        self.var_bio.set(s.get("use_bio",False)); self.var_ai.set(s.get("activate_ai",False))
        self.var_block.set(s.get("block_dolboeba",False))
        self.var_fakecam.set(c.get("fake_camera",False))

    def _save_st(self):
        save_state({"threads":self._i("ent_threads",1),"total":self._i("ent_total",10),
            "wait":self._i("ent_wait",750),"otp_min_delay":self._i("ent_otp_delay",60),
            "gift":self.var_gift.get(),"proxy_mode":self.var_proxy.get(),
            "proxy_manual":self._v("ent_proxy"),
            "use_avatar":self.var_avatar.get(),"use_name":self.var_name.get(),
            "use_bio":self.var_bio.get(),"activate_ai":self.var_ai.get(),
            "block_dolboeba":self.var_block.get()})

    def _args(self):
        px = ""
        mode = self.var_proxy.get()
        if mode == "manual": px = self._v("ent_proxy")
        elif mode == "file": px = next_proxy()
        return {"wait_time":self._i("ent_wait",750),"gift_option":self.var_gift.get(),
                "use_avatar":self.var_avatar.get(),"use_name":self.var_name.get(),
                "use_bio":self.var_bio.get(),"activate_ai":self.var_ai.get(),
                "block_dolboeba":self.var_block.get(),"proxy_spec":px,
                "proxy_mode":mode,"otp_min_delay":self._i("ent_otp_delay",60)}

    # ── Actions ──────────────────────────────────────────────────────

    def _ui_running(self, on):
        self.btn_start.config(state="disabled" if on else "normal")
        self.btn_stop.config(state="normal" if on else "disabled")

    def _start(self):
        global _running, _worker_thread, session_start
        if _running: return
        if not os.path.exists(REGER_SCRIPT):
            messagebox.showerror("","reger.py не найден"); return
        self._save_st(); clear_stop()
        n = max(1, self._i("ent_threads",1))
        total = max(1, self._i("ent_total",10))
        wait = self._i("ent_wait",750)
        a = self._args()
        _running = True; session_start = time.time()
        self._ui_running(True)
        def done():
            log_q.put("[SYS] Все аккаунты обработаны")
            self.after(0, lambda: self._ui_running(False))
        _worker_thread = threading.Thread(target=_worker, args=(n, total, a, done), daemon=True)
        _worker_thread.start()
        log_q.put(f"[SYS] Старт: {n} поток(ов), {total} акков, стрим={fmt_time(wait)}")

    def _stop(self):
        global _running
        if not _running and not procs: return
        _running = False; stop_all()
        k = 0
        with procs_lock:
            for p,_,_ in procs:
                try: p.terminate(); k += 1
                except Exception: pass
        if k: log_q.put(f"[SYS] Terminate {k}")
        self._ui_running(False)

    def _single(self):
        if not os.path.exists(REGER_SCRIPT):
            messagebox.showerror("","reger.py не найден"); return
        clear_stop()
        with stats_lock: slot = launched + 1
        launch_one(slot, {**self._args(), "total_target": None})

    def _reset(self):
        global launched, finished, errors, success, _proxy_idx, session_start
        if _running: messagebox.showwarning("","Нельзя во время работы"); return
        with stats_lock: launched=0; finished=0; errors=0; success=0
        with _proxy_lock: _proxy_idx=0
        with _adaptive_lock: _adaptive_history.clear()
        session_start = 0.0
        log_q.put("[SYS] Статистика сброшена")

    def _save_cfg(self):
        ref = self._v("ent_ref_url")
        if not ref: messagebox.showwarning("","Не заполнен Tango Ref URL!"); return
        self.cfg["tango_ref_url"] = ref
        doms = [d if d.startswith("@") else f"@{d}" for d in self._domains()]
        if not doms: messagebox.showwarning("","Укажи хотя бы один домен!"); return
        self.cfg["email_domains"] = doms; self.cfg["email_domain"] = doms[0]
        for i in range(2,14): self.cfg.pop(f"email_domain{i}", None)
        self.cfg.pop("domain_split", None)
        self.cfg["email_prefix"] = self._v("ent_prefix","soft")
        try: self.cfg["email_check_timeout_sec"] = int(self._v("ent_otp_timeout","240"))
        except: self.cfg["email_check_timeout_sec"] = 240
        self.cfg["fake_camera"] = self.var_fakecam.get()
        self.cfg.pop("fake_video_path", None)
        self.cfg.pop("vps_mode", None)
        self._save_imap_to_cfg(); save_config(self.cfg); self._reload_cfg()
        self.txt_domains.delete("1.0","end"); self.txt_domains.insert("1.0","\n".join(doms))
        log_q.put(f"[SYS] config.json сохранён ({len(doms)} доменов)")
        self._update_video_count()

    def _save_imap_to_cfg(self):
        s=self._v("ent_imap_srv").strip(); m=self._v("ent_imap_email").strip()
        p=self._v("ent_imap_pass").strip(); port=self._v("ent_imap_port","993")
        if s: self.cfg["imap_server"]=s
        if m: self.cfg["imap_email"]=m
        if p: self.cfg["imap_password"]=p
        try: self.cfg["imap_port"]=int(port)
        except: self.cfg["imap_port"]=993

    def _save_imap(self):
        self._save_imap_to_cfg(); save_config(self.cfg); self._reload_cfg()
        log_q.put("[SYS] IMAP сохранены")

    def _test_imap(self):
        s=self._v("ent_imap_srv").strip(); m=self._v("ent_imap_email").strip()
        p=self._v("ent_imap_pass").strip(); port=int(self._v("ent_imap_port","993") or 993)
        if not s or not m or not p:
            messagebox.showwarning("","Заполни сервер, email и пароль!"); return
        def run():
            import imaplib
            log_q.put(f"[SYS] IMAP тест: {s}:{port}...")
            try:
                i=imaplib.IMAP4_SSL(s,port); i.login(m,p)
                _,d=i.select("INBOX"); c=int(d[0]) if d and d[0] else 0; i.logout()
                log_q.put(f"[SYS] IMAP OK — {c} писем")
                self.after(0, lambda: messagebox.showinfo("IMAP",f"OK! Писем: {c}"))
            except Exception as e:
                log_q.put(f"[ERR] IMAP: {e}")
                self.after(0, lambda: messagebox.showerror("IMAP",str(e)))
        threading.Thread(target=run, daemon=True).start()

    def _clear_log(self):
        self.log.configure(state="normal"); self.log.delete("1.0","end"); self.log.configure(state="disabled")

    def _save_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
            initialfile=f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if path:
            try:
                with open(path,"w",encoding="utf-8") as f: f.write(self.log.get("1.0","end"))
                log_q.put(f"[SYS] Лог: {path}")
            except Exception as e: log_q.put(f"[ERR] {e}")

    def _find_log(self, _=None):
        q = self.ent_search.get().strip()
        if not q: return
        self.log.tag_remove("SRCH","1.0","end")
        pos = self.log.search(q, self._search_pos, nocase=True, stopindex="end")
        if not pos: pos = self.log.search(q, "1.0", nocase=True, stopindex="end")
        if pos:
            end = f"{pos}+{len(q)}c"
            self.log.tag_add("SRCH", pos, end); self.log.see(pos); self._search_pos = end
        else: self._search_pos = "1.0"

    def _reload_cfg(self):
        self.cfg_view.configure(state="normal"); self.cfg_view.delete("1.0","end")
        try:
            with open(CONFIG_FILE,"r",encoding="utf-8") as f: self.cfg_view.insert("end",f.read())
        except: self.cfg_view.insert("end","{}")
        self.cfg_view.configure(state="disabled")

    def _reload_px(self):
        self.px_view.configure(state="normal"); self.px_view.delete("1.0","end")
        try:
            if os.path.exists(PROXY_FILE):
                with open(PROXY_FILE,"r",encoding="utf-8") as f: self.px_view.insert("end",f.read())
            else: self.px_view.insert("end","# proxy.txt не найден\n")
        except Exception as e: self.px_view.insert("end",str(e))
        self.px_view.configure(state="disabled")

    # ── Loops ────────────────────────────────────────────────────────

    def _poll_log(self):
        lines = []
        try:
            while True: lines.append(log_q.get_nowait())
        except queue.Empty: pass
        if lines:
            self.log.configure(state="normal")
            for ln in lines: self.log.insert("end", ln+"\n", log_level(ln))
            if self.var_scroll.get(): self.log.see("end")
            self.log.configure(state="disabled")
            try:
                c = int(self.log.index("end-1c").split(".")[0])
                if c > 3000:
                    self.log.configure(state="normal"); self.log.delete("1.0",f"{c-2000}.0")
                    self.log.configure(state="disabled")
            except: pass
        self.after(150, self._poll_log)

    def _poll_stats(self):
        with stats_lock: l,fi,er,su = launched,finished,errors,success
        with procs_lock: run = len(procs)
        self.s_launched.config(text=str(l), fg=ACCENT2)
        self.s_running.config(text=str(run), fg=GREEN if run>0 else TEXT_DIM)
        self.s_finished.config(text=str(fi), fg=TEXT)
        self.s_ok.config(text=str(su), fg=GREEN if su>0 else TEXT_DIM)
        self.s_err.config(text=str(er), fg=RED if er>0 else TEXT_DIM)
        self.s_cashout.config(text=str(count_files(CASHOUT_DIR)), fg=GREEN)
        self.s_work.config(text=str(count_files(WORK_DIR)), fg=YELLOW)
        self.s_idx.config(text=str(get_last_index()), fg=TEXT_DIM)
        try: self.s_domains.config(text=str(len(self._domains())), fg=GREEN)
        except: pass
        np = len(read_proxies())
        self.s_proxies.config(text=str(np), fg=GREEN if np>0 else TEXT_DIM)
        fl = os.path.exists(STOP_REGER_FLAG)
        self.s_flag.config(text="ДА" if fl else "нет", fg=RED if fl else GREEN)
        self.s_vpn.config(text=_vpn_current_country(), fg=ACCENT2)

        # ETA
        try:
            tt = self._i("ent_total",0); wait = self._i("ent_wait",750)
            threads = max(1, self._i("ent_threads",1))
            if _running and tt > 0 and fi < tt:
                rem = tt - fi - run
                if rem > 0:
                    eta = rem * wait / threads
                    self.lbl_eta.config(text=f"ETA: ~{fmt_time(eta)}", fg=ORANGE)
                else:
                    self.lbl_eta.config(text="Дожидаемся завершения...", fg=ORANGE)
            else:
                self.lbl_eta.config(text="", fg=BG)
        except: self.lbl_eta.config(text="", fg=BG)

        # Progress
        try:
            tt = self._i("ent_total",0)
            if tt > 0 and l > 0:
                pct = min(100, int(fi*100/tt))
                self.pbar["value"] = pct; self.lbl_prog.config(text=f"{fi}/{tt} ({pct}%)")
            else: self.pbar["value"] = 0; self.lbl_prog.config(text="")
        except: pass

        self.after(1500, self._poll_stats)

    def _tick(self):
        self.lbl_clock.config(text=datetime.datetime.now().strftime("%H:%M:%S  %d.%m.%Y"))
        if session_start > 0:
            el = time.time() - session_start
            txt = f"Сессия: {fmt_time(el)}" if _running else f"Было: {fmt_time(el)}"
            self.lbl_session.config(text=txt)
        else: self.lbl_session.config(text="")
        self.after(1000, self._tick)

    def _autosave(self):
        try: self._save_st()
        except: pass
        self.after(30000, self._autosave)

    def _close(self):
        global _running
        _running = False; self._save_st()
        with procs_lock: alive = len(procs)
        if alive > 0:
            if not messagebox.askyesno("",f"Работает {alive}. Выйти?"): return
            stop_all()
        self.destroy()

# ═══════════════════════════════════════════════════════════════════════

def main():
    try:
        from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    s = ttk.Style()
    try: s.theme_use("aqua" if _MAC else "clam")
    except:
        try: s.theme_use("clam")
        except: pass
    s.configure("TNotebook", background=BG2, borderwidth=0)
    s.configure("TNotebook.Tab", background=BG3, foreground=TEXT, padding=[14,6], font=F12)
    s.map("TNotebook.Tab", background=[("selected",ACCENT2)], foreground=[("selected","black")])
    s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG2, arrowcolor=TEXT_DIM, borderwidth=0)
    s.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT)
    s.configure("TProgressbar", background=GREEN, troughcolor=BG3, borderwidth=0, lightcolor=GREEN, darkcolor=GREEN)
    App().mainloop()

if __name__ == "__main__":
    main()
