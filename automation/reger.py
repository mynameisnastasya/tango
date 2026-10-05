import os
import shutil
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import datetime
import re
import colorama
from colorama import Fore, Style
import sys
import secrets
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
import threading
import random
from pathlib import Path

colorama.init(autoreset=True)


# === Device fingerprint (unique device per profile) ===
try:
    from device_fingerprint import (
        get_or_create_device_profile,
        generate_device_profile,
        apply_device_profile_to_driver,
        clear_all_browser_state,
    )
    _FP_OK = True
except ImportError:
    _FP_OK = False
    def generate_device_profile(profile_num=None):
        return {}
    def get_or_create_device_profile(profile_dir):
        return {}
    def apply_device_profile_to_driver(driver, dp):
        pass
    def clear_all_browser_state(driver):
        try:
            driver.delete_all_cookies()
        except Exception:
            pass
        try:
            driver.execute_script("window.localStorage.clear();window.sessionStorage.clear();")
        except Exception:
            pass


email_lock = threading.Lock()
VERSION = "1.5"

# ========================================================================================
#                               ПУТИ ПРОЕКТА
# ========================================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_DIR = os.path.join(BASE_DIR, "settings")
STOP_REGER_FLAG = os.path.join(SETTINGS_DIR, "stop_reger.flag")
_BYPASS_STOP = False

class StopRequested(Exception):
    pass


def stop_requested() -> bool:
    try:
        return os.path.exists(STOP_REGER_FLAG)
    except Exception:
        return False


def check_stop(where: str = ""):
    if _BYPASS_STOP:
        return
    if stop_requested():
        raise StopRequested(where or "stop_reger.flag")


_ORIG_SLEEP = time.sleep

def safe_sleep(seconds: float, granularity: float = 0.25):
    end = time.time() + float(seconds)
    while True:
        check_stop("sleep")
        remaining = end - time.time()
        if remaining <= 0:
            return
        _ORIG_SLEEP(min(granularity, remaining))

time.sleep = safe_sleep


def clear_and_type(driver, element, text_value: str, *, click_first: bool = True, verify: bool = True):
    if text_value is None:
        return
    text_value = str(text_value)
    try:
        element.clear()
    except Exception:
        pass
    try:
        if click_first:
            element.click()
            time.sleep(0.15)
        mod = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL
        element.send_keys(mod, "a")
        time.sleep(0.1)
        element.send_keys(Keys.BACKSPACE)
        time.sleep(0.15)
    except Exception:
        pass
    if verify:
        try:
            val = element.get_attribute("value")
        except Exception:
            val = None
        if val:
            try:
                driver.execute_script(
                    """const el = arguments[0];
                         if ('value' in el) { el.value = ''; } else { el.textContent = ''; }
                         el.dispatchEvent(new Event('input', {bubbles:true}));
                         el.dispatchEvent(new Event('change', {bubbles:true}));""",
                    element
                )
                time.sleep(0.1)
            except Exception:
                pass
    try:
        element.send_keys(text_value)
    except Exception:
        try:
            driver.execute_script(
                """const el = arguments[0];
                     if ('value' in el) { el.value = arguments[1]; } else { el.textContent = arguments[1]; }
                     el.dispatchEvent(new Event('input', {bubbles:true}));
                     el.dispatchEvent(new Event('change', {bubbles:true}));""",
                element,
                text_value
            )
        except Exception:
            raise


PATH_DB = os.path.join(BASE_DIR, "db")
PATH_LOGS = os.path.join(BASE_DIR, "logs")
PATH_PROFILES = os.path.join(BASE_DIR, "profiles")
PATH_MAILS = os.path.join(BASE_DIR, "mails")
PATH_PULSZ_MAILS = os.path.join(PATH_MAILS, "pulsz")
LOCK_FILE     = os.path.join(BASE_DIR, "register.lock")
OTP_LOCK_FILE = os.path.join(BASE_DIR, "otp.lock")
OTP_GATE_FILE = os.path.join(BASE_DIR, "settings", "otp_gate.json")

LOG_PATH = os.path.join(PATH_LOGS, "run.log")
DB_INDEX = os.path.join(PATH_DB, "last_index.txt")
USED_EMAILS = os.path.join(PATH_DB, "used_emails.txt")


_log_lock = threading.Lock()
_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _rotate_log_if_needed():
    try:
        if os.path.getsize(LOG_PATH) < _LOG_MAX_BYTES:
            return
        backup = LOG_PATH + ".1"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(LOG_PATH, backup)
    except Exception:
        pass


def log(message, level="INFO"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {message}"
    colors = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW,
    }
    is_tty = False
    try:
        is_tty = sys.stdout.isatty()
    except Exception:
        pass

    if is_tty:
        # Терминал — цветной вывод
        try:
            print(colors.get(level, "") + line + Style.RESET_ALL, flush=True)
        except Exception:
            try:
                print(line, flush=True)
            except Exception:
                pass
    else:
        # Под starter.py — только [GUI] префикс, без дублирования
        lvl_map = {"SUCCESS": "OK", "WARNING": "WARN", "ERROR": "ERROR", "INFO": "INFO"}
        try:
            print(f"[GUI][{lvl_map.get(level, 'INFO')}] {line}", flush=True)
        except Exception:
            pass

    # Файл (с ротацией, thread-safe)
    try:
        os.makedirs(PATH_LOGS, exist_ok=True)
        with _log_lock:
            _rotate_log_if_needed()
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


def gui(msg: str, level: str | None = None):
    try:
        if level:
            print(f"[GUI][{level}] {msg}", flush=True)
        else:
            print(f"[GUI] {msg}", flush=True)
    except Exception:
        pass


# ========================================================================================
#                           ФАЙЛОВАЯ БАЗА EMAIL ИНДЕКСОВ
# ========================================================================================

def _tg_parse_proxy(proxy_str: str) -> dict | None:
    """
    Разбирает строку прокси в разных форматах:
      host:port
      host:port:user:pass
      socks5://user:pass@host:port
      http://user:pass@host:port
    Возвращает dict с ключами: scheme, host, port, user, password
    """
    if not proxy_str:
        return None
    s = proxy_str.strip()
    try:
        # Формат с схемой: socks5://... или http://...
        if "://" in s:
            from urllib.parse import urlparse as _up
            p = _up(s)
            return {
                "scheme":   (p.scheme or "http").lower(),
                "host":     p.hostname or "",
                "port":     int(p.port or 1080),
                "user":     p.username or "",
                "password": p.password or "",
            }
        # Формат host:port или host:port:user:pass
        parts = s.split(":")
        if len(parts) == 2:
            return {"scheme": "http", "host": parts[0], "port": int(parts[1]), "user": "", "password": ""}
        if len(parts) >= 4:
            return {"scheme": "http", "host": parts[0], "port": int(parts[1]), "user": parts[2], "password": ":".join(parts[3:])}
        if len(parts) == 3:
            # Может быть host:port:user (без пароля) или IPv6 — обрабатываем как host:port
            try:
                return {"scheme": "http", "host": parts[0], "port": int(parts[1]), "user": parts[2], "password": ""}
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_public_ip() -> str:
    """Получает публичный IP-адрес через несколько сервисов (fallback цепочка)."""
    services = [
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
    ]
    import ssl as _ssl_ip
    ctx = _ssl_ip.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl_ip.CERT_NONE
    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                ip = resp.read().decode("utf-8", errors="ignore").strip()
                if ip and len(ip) <= 45:  # IPv4 макс 15, IPv6 макс 45
                    return ip
        except Exception:
            continue
    return "неизвестен"


def tg_send_message(cfg: dict, text: str) -> bool:
    import ssl as _ssl
    import json as _json
    try:
        tg = (cfg or {}).get("telegram") or {}
        if not tg.get("enabled"):
            return False
        token = (tg.get("bot_token") or "").strip()
        chat_id = (tg.get("chat_id") or "").strip()
        if not token or not chat_id:
            log("Telegram: не заполнены bot_token/chat_id в config.json", "WARNING")
            return False
        prefix = (tg.get("message_prefix") or "").strip()
        msg = f"{prefix}{text}" if prefix else text
        payload = {"chat_id": chat_id, "text": msg}
        parse_mode = (tg.get("parse_mode") or "").strip()
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if "disable_web_page_preview" in tg:
            payload["disable_web_page_preview"] = bool(tg.get("disable_web_page_preview"))
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode(payload).encode("utf-8")
        timeout = float(tg.get("timeout_sec", 10))
        _ctx = _ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = _ssl.CERT_NONE

        # ── Прокси: сначала telegram.proxy, потом общий прокси из конфига ──
        proxy_str = (tg.get("proxy") or "").strip()
        if not proxy_str:
            # Пробуем взять из общего конфига (proxy_spec или proxy)
            proxy_str = (cfg.get("proxy_spec") or cfg.get("proxy") or "").strip()
        proxy_info = _tg_parse_proxy(proxy_str) if proxy_str else None

        if proxy_info:
            scheme = proxy_info["scheme"]
            host   = proxy_info["host"]
            port   = proxy_info["port"]
            user   = proxy_info["user"]
            pwd    = proxy_info["password"]

            if scheme.startswith("socks"):
                # SOCKS5/SOCKS4 через requests (если установлен) или socks-обёртка
                try:
                    import requests as _req
                    import requests.packages.urllib3 as _u3
                    _u3.disable_warnings()
                    proxy_url = f"{scheme}://"
                    if user:
                        proxy_url += f"{urllib.parse.quote(user, safe='')}:{urllib.parse.quote(pwd, safe='')}@"
                    proxy_url += f"{host}:{port}"
                    proxies = {"https": proxy_url, "http": proxy_url}
                    resp = _req.post(url, data=payload, proxies=proxies, timeout=timeout, verify=False)
                    result = resp.json()
                    if result.get("ok"):
                        log("Telegram: сообщение отправлено ✓ (socks прокси)", "SUCCESS")
                        return True
                    err_code = result.get("error_code", "?")
                    description = result.get("description", "нет описания")
                    log(f"Telegram API error {err_code}: {description}", "WARNING")
                    return False
                except ImportError:
                    log("Telegram: SOCKS прокси требует библиотеку requests (pip install requests[socks])", "WARNING")
                    return False
            else:
                # HTTP прокси через ProxyHandler
                proxy_url = f"http://"
                if user:
                    proxy_url += f"{urllib.parse.quote(user, safe='')}:{urllib.parse.quote(pwd, safe='')}@"
                proxy_url += f"{host}:{port}"
                proxy_handler = urllib.request.ProxyHandler({"https": proxy_url, "http": proxy_url})
                opener = urllib.request.build_opener(proxy_handler)
                req = urllib.request.Request(url, data=data, method="POST")
                with opener.open(req, timeout=timeout) as resp:
                    raw = resp.read()
        else:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as resp:
                raw = resp.read()

        try:
            result = _json.loads(raw)
            if result.get("ok"):
                log("Telegram: сообщение отправлено ✓", "SUCCESS")
                return True
            else:
                err_code = result.get("error_code", "?")
                description = result.get("description", "нет описания")
                log(f"Telegram API error {err_code}: {description}", "WARNING")
                return False
        except Exception:
            log(f"Telegram: ответ получен, но не распарсился: {raw[:200]}", "WARNING")
            return False
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            parsed = _json.loads(body)
            description = parsed.get("description", body[:200])
            log(f"Telegram HTTP {e.code}: {description}", "WARNING")
        except Exception:
            log(f"Telegram HTTP ошибка {e.code}: {e.reason}", "WARNING")
        return False
    except Exception as e:
        log(f"Telegram: не удалось отправить: {e}", "WARNING")
        return False


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_SPREADSHEET_ID = "1N7jfAKO1lezlZrWkYh3Z-ZFfaMEPjelk4mV2YvMdVIs"
DEFAULT_SHEET_NAME = "АККАУНТЫ"


def append_gsheets_row(cfg, account: str, diamonds, note: str = "алмазы после стрима", profile_url: str = "", vpn_country: str = "", ip: str = ""):
    try:
        import datetime as dt
        import gspread
        from google.oauth2.service_account import Credentials
    except Exception as e:
        log(f"GSHEETS: библиотеки не установлены/не импортируются: {e}", "ERROR")
        return False
    creds_path = None
    try:
        gs_cfg = (cfg or {}).get("google_sheets", {})
        creds_path = (gs_cfg.get("credentials_json") or gs_cfg.get("credentials_path")
                       or gs_cfg.get("creds"))
    except Exception:
        gs_cfg = {}
        creds_path = None
    if not creds_path:
        cand1 = os.path.join(BASE_DIR, "settings", "credentials.json")
        cand2 = os.path.join(BASE_DIR, "credentials.json")
        creds_path = cand1 if os.path.exists(cand1) else cand2
    spreadsheet_id = (gs_cfg.get("spreadsheet") or gs_cfg.get("spreadsheet_id") or gs_cfg.get("spreadsheetId")
                      or gs_cfg.get("spreadsheet_url") or DEFAULT_SPREADSHEET_ID)
    if isinstance(spreadsheet_id, str) and "docs.google.com" in spreadsheet_id and "/d/" in spreadsheet_id:
        try:
            spreadsheet_id = spreadsheet_id.split("/d/")[1].split("/")[0]
        except Exception:
            spreadsheet_id = DEFAULT_SPREADSHEET_ID
    sheet_name = gs_cfg.get("sheet") or gs_cfg.get("sheet_name") or DEFAULT_SHEET_NAME
    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        gc = gspread.authorize(creds)
        ws = gc.open_by_key(spreadsheet_id).worksheet(sheet_name)
        now = dt.datetime.now()
        # Колонки: Аккаунт | Алмазы | Статус | Страна | IP | Дата | Время | Заметка | Профиль
        status = "cashout" if (diamonds is not None and str(diamonds).isdigit() and int(diamonds) >= 3000) else "новый"
        row = [
            account,
            str(diamonds),
            status,
            vpn_country or "—",
            ip or "—",
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            note,
            profile_url or "",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        log(f"GSHEETS: OK appended row -> {row}", "SUCCESS")
        return True
    except Exception as e:
        log(f"GSHEETS: ошибка записи: {e}", "ERROR")
        return False


def notify_my_service(cfg: dict, payload: dict, event: str = "event", retries: int = 2) -> bool:
    try:
        ms = (cfg or {}).get("my_service") or {}
        url = (ms.get("webhook_url") or "").strip()
        if not url:
            return False
        token = (ms.get("token") or "").strip()
        timeout = float(ms.get("timeout_sec") or 10)
        body = {
            "event": event,
            "ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "payload": payload or {},
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8", "User-Agent": "LegalAutomation/1.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        last_err = None
        for i in range(max(0, int(retries)) + 1):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    code = getattr(resp, "status", 200)
                    return 200 <= int(code) < 300
            except Exception as e:
                last_err = e
                time.sleep(0.6 * (i + 1))
        return False
    except Exception:
        return False


def init_db():
    os.makedirs(PATH_DB, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "cashout"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "work"),    exist_ok=True)
    if not os.path.exists(DB_INDEX):
        with open(DB_INDEX, "w") as f:
            f.write("1")


def get_next_email(total_target: int | None = None):
    cfg = load_config()

    # ── Сбор доменов (до 13 штук) ────────────────────────────────────────────
    _raw_list = cfg.get("email_domains") or []
    if not _raw_list:
        _raw_list = []
        for _i in range(1, 14):
            _key = "email_domain" if _i == 1 else f"email_domain{_i}"
            _val = (cfg.get(_key) or "").strip()
            if _val:
                _raw_list.append(_val)
    domains = [d.strip() for d in _raw_list if d and d.strip()]

    if not domains:
        gui('❌ В config.json отсутствует email_domain', 'ERROR')
        log('В config.json отсутствует email_domain', 'ERROR')
        raise SystemExit(1)

    prefix = cfg.get("email_prefix", "soft")
    os.makedirs(PATH_DB, exist_ok=True)

    # ── Файловый лок — защищает счётчик при мультипроцессном запуске ────────
    _idx_lock_path = os.path.join(PATH_DB, "index.lock")

    def _acquire_idx_lock():
        deadline = time.time() + 30
        while True:
            try:
                fd = os.open(_idx_lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(_idx_lock_path)
                    if age > 15:
                        os.remove(_idx_lock_path)
                        continue  # retry — не входим без лока
                except Exception:
                    pass
                if time.time() > deadline:
                    # Принудительно ломаем зависший лок и пробуем ещё раз
                    try:
                        os.remove(_idx_lock_path)
                    except Exception:
                        pass
                    continue  # retry, а не return
                _ORIG_SLEEP(0.1)

    def _release_idx_lock():
        try:
            os.remove(_idx_lock_path)
        except Exception:
            pass

    email = None
    try:
        _acquire_idx_lock()

        if not os.path.exists(DB_INDEX):
            with open(DB_INDEX, "w") as f:
                f.write("1")
        with open(DB_INDEX, "r") as f:
            idx = int(f.read().strip())

        # Поочерёдная ротация: idx=1→domain[0], idx=2→domain[1], …
        use_domain = domains[(idx - 1) % len(domains)]
        log(f'Домен #{(idx - 1) % len(domains) + 1}/{len(domains)}, idx={idx}: {use_domain}', 'INFO')

        import string as _str
        _noise_chars = _str.ascii_lowercase + _str.digits
        _sfx_len = random.randint(3, 5)
        _sfx = "".join(random.choice(_noise_chars) for _ in range(_sfx_len))
        _pfx_extra = random.choice(_str.ascii_lowercase) if random.random() < 0.4 else ""
        email = f"{prefix}{_pfx_extra}{idx}{_sfx}{use_domain}"

        with open(DB_INDEX, "w") as f:
            f.write(str(idx + 1))
        with open(USED_EMAILS, "a", encoding="utf-8") as f:
            f.write(email + "\n")
    finally:
        _release_idx_lock()

    log(f"Сгенерирована почта: {email} (домен: {use_domain})", "INFO")
    try:
        trim_used_emails(max_lines=3000)
    except Exception:
        pass
    return email


def infer_profile_num_from_email(email: str | None) -> int | None:
    """
    Извлекаем числовой индекс из email.
    Email вида softa17xyz3k@d.com — ищем первое число после букв (это idx).
    """
    if not email:
        return None
    local_part = str(email).split("@", 1)[0]
    nums = re.findall(r"\d+", local_part)
    if not nums:
        return None
    try:
        return int(nums[0])
    except Exception:
        return None


def parse_runtime_args(argv: list[str]) -> dict:
    args = {
        "wait_time": 750,
        "gift_option": "",
        "use_avatar": False,
        "use_name": False,
        "use_bio": False,
        "activate_ai": False,
        "block_dolboeba": False,
        "proxy_spec": None,
        "email": None,
        "profile_num": None,
        "total_target": None,
        "otp_min_delay": 0.0,   # минимальная пауза между вводами OTP (сек) через gate
    }
    pos = []
    i = 1
    while i < len(argv):
        tok = argv[i]
        if tok == "--proxy" and i + 1 < len(argv):
            args["proxy_spec"] = argv[i + 1]
            i += 2
            continue
        if tok == "--email" and i + 1 < len(argv):
            args["email"] = argv[i + 1].strip()
            i += 2
            continue
        if tok == "--profile-num" and i + 1 < len(argv):
            try:
                args["profile_num"] = int(argv[i + 1])
            except Exception:
                args["profile_num"] = None
            i += 2
            continue
        if tok == "--total" and i + 1 < len(argv):
            try:
                args["total_target"] = int(argv[i + 1])
            except Exception:
                args["total_target"] = None
            i += 2
            continue
        if tok == "--otp-delay" and i + 1 < len(argv):
            try:
                args["otp_min_delay"] = float(argv[i + 1])
            except Exception:
                args["otp_min_delay"] = 0.0
            i += 2
            continue
        if tok == "--vpn-country" and i + 1 < len(argv):
            args["vpn_country"] = argv[i + 1].strip()
            i += 2
            continue
        pos.append(tok)
        i += 1
    if len(pos) > 0:
        try:
            args["wait_time"] = int(pos[0])
        except Exception:
            pass
    if len(pos) > 1:
        args["gift_option"] = str(pos[1]).strip()
    if len(pos) > 2:
        args["use_avatar"] = str(pos[2]).strip() == "1"
    if len(pos) > 3:
        args["use_name"] = str(pos[3]).strip() == "1"
    if len(pos) > 4:
        args["use_bio"] = str(pos[4]).strip() == "1"
    if len(pos) > 5:
        args["activate_ai"] = str(pos[5]).strip() == "1"
    if len(pos) > 6:
        args["block_dolboeba"] = str(pos[6]).strip() == "1"
    if args["profile_num"] is None:
        args["profile_num"] = infer_profile_num_from_email(args["email"])
    return args


def _extract_latest_otp_from_lines(lines, expected_lengths=(4, 6)):
    """
    Ищем OTP-код в файле письма.
    Стратегия (от самого точного к широкому):
      1. Subject: строка — берём число нужной длины
      2. Строка, где есть ключевые слова (code, код, otp, verify, подтвер)
      3. Строка только из цифр нужной длины (самый точный паттерн)
      4. Любое число нужной длины в любой строке (fallback)
    Ищем с конца файла — последнее письмо важнее старых.
    """
    if not lines:
        return None, None

    # Нормализуем длины — сортируем по убыванию (сначала ищем 6-значный, потом 4)
    lengths = sorted(set(int(l) for l in expected_lengths), reverse=True)

    # 1. Subject строка
    for line in reversed(lines):
        stripped = (line or "").strip()
        if re.match(r"(?i)^(subject|subj)\s*:", stripped):
            after = stripped.split(":", 1)[1].strip()
            for ln in lengths:
                m = re.search(rf"(?<!\d)(\d{{{ln}}})(?!\d)", after)
                if m:
                    return m.group(1), f"subject:{ln}"

    # 2. Строки с ключевыми словами
    keywords = re.compile(
        r"(?i)(verification|verify|код|code|otp|one.time|подтвер|confirm|passcode|pin\b|access code)",
        re.IGNORECASE
    )
    for line in reversed(lines):
        stripped = (line or "").strip()
        if not stripped:
            continue
        if keywords.search(stripped):
            for ln in lengths:
                m = re.search(rf"(?<!\d)(\d{{{ln}}})(?!\d)", stripped)
                if m:
                    return m.group(1), f"keyword:{ln}"

    # 3. Строка целиком из цифр нужной длины
    for line in reversed(lines):
        stripped = (line or "").strip()
        for ln in lengths:
            if re.fullmatch(rf"\d{{{ln}}}", stripped):
                return stripped, f"exact:{ln}"

    # 4. Любое число нужной длины в любой строке (fallback, последние 100 строк)
    for line in reversed(lines[-100:]):
        stripped = (line or "").strip()
        if not stripped:
            continue
        for ln in lengths:
            m = re.search(rf"(?<!\d)(\d{{{ln}}})(?!\d)", stripped)
            if m:
                return m.group(1), f"fallback:{ln}"

    return None, "not-found"


def wait_for_code_from_file(filepath, *, timeout=240, poll_interval=5, expected_lengths=(4, 6), channel_name="mail"):
    log(f"Ожидаем OTP в файле [{channel_name}]: {filepath}", "INFO")
    start = time.time()
    last_size = None
    while time.time() - start < timeout:
        if os.path.exists(filepath):
            try:
                size = os.path.getsize(filepath)
                if size != last_size:
                    log(f"Файл {os.path.basename(filepath)} обновился: {size} bytes", "INFO")
                    last_size = size
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                code, source = _extract_latest_otp_from_lines(lines, expected_lengths=expected_lengths)
                if code:
                    log(f"OTP найден [{channel_name}] ({source}) в {os.path.basename(filepath)}: {code}", "SUCCESS")
                    return code
                log(f"OTP пока не найден [{channel_name}] ({source}). Ждём...", "WARNING")
            except Exception as e:
                log(f"Ошибка чтения файла {os.path.basename(filepath)}: {e}", "ERROR")
        else:
            log(f"Файл {os.path.basename(filepath)} пока не найден. Ждём...", "INFO")
        _ORIG_SLEEP(poll_interval)
    log(f"OTP не найден в файле {os.path.basename(filepath)} за {timeout} сек.", "ERROR")
    return None


# ========================================================================================
#                               SELENIUM: ЗАПУСК С ПРОФИЛЕМ
# ========================================================================================

def parse_proxy_spec(spec: str):
    if not spec:
        return None
    s = str(spec).strip()
    if not s:
        return None
    try:
        if "://" in s:
            from urllib.parse import urlparse
            u = urlparse(s)
            scheme = (u.scheme or "").lower()
            if scheme in ("socks5", "socks5h", "socks"):
                host = u.hostname
                port = int(u.port) if u.port else None
                if not host or not port:
                    return None
                user = u.username or ""
                pwd = u.password or ""
                return {"scheme": "socks5", "host": host, "port": port, "user": user, "pass": pwd}
    except Exception:
        pass
    if s.lower().startswith("socks5 "):
        s = s.split(None, 1)[1].strip()
    parts = s.split(":")
    if len(parts) < 2:
        return None
    host = parts[0].strip()
    try:
        port = int(parts[1].strip())
    except Exception:
        return None
    user = parts[2].strip() if len(parts) >= 3 else ""
    pwd = parts[3].strip() if len(parts) >= 4 else ""
    return {"scheme": "socks5", "host": host, "port": port, "user": user, "pass": pwd}


def build_proxy_extension(px: dict) -> str | None:
    try:
        if not px:
            return None
        host = px.get("host")
        port = int(px.get("port") or 0)
        user = px.get("user") or ""
        pwd = px.get("pass") or ""
        scheme = (px.get("scheme") or "socks5").lower()
        if scheme not in ("socks5", "socks"):
            scheme = "socks5"
        if not host or not port:
            return None
        ext_root = os.path.join(BASE_DIR, "_proxy_ext")
        os.makedirs(ext_root, exist_ok=True)
        ext_dir = os.path.join(ext_root, f"px_{int(time.time())}_{secrets.token_hex(4)}")
        os.makedirs(ext_dir, exist_ok=True)
        manifest = {
            "name": "AuthProxy", "version": "1.0.0", "manifest_version": 3,
            "permissions": ["proxy", "storage", "webRequest", "webRequestAuthProvider"],
            "host_permissions": ["<all_urls>"],
            "background": {"service_worker": "background.js"},
        }
        background = f"""chrome.runtime.onInstalled.addListener(() => {{
  chrome.proxy.settings.set({{value:{{mode:"fixed_servers",rules:{{singleProxy:{{scheme:"{scheme}",host:"{host}",port:{port}}},bypassList:["localhost","127.0.0.1"]}}}},scope:"regular"}});
}});
chrome.proxy.settings.set({{value:{{mode:"fixed_servers",rules:{{singleProxy:{{scheme:"{scheme}",host:"{host}",port:{port}}},bypassList:["localhost","127.0.0.1"]}}}},scope:"regular"}});
const USERNAME={json.dumps(user)};const PASSWORD={json.dumps(pwd)};
chrome.webRequest.onAuthRequired.addListener((details,callback)=>{{if(USERNAME||PASSWORD){{callback({{authCredentials:{{username:USERNAME,password:PASSWORD}}}});}}else{{callback();}}}},({{urls:["<all_urls>"]}}),["asyncBlocking"]);
"""
        with open(os.path.join(ext_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        with open(os.path.join(ext_dir, "background.js"), "w", encoding="utf-8") as f:
            f.write(background)
        return ext_dir
    except Exception:
        return None


def _pick_random_nonempty_line(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.read().splitlines()]
        lines = [ln for ln in lines if ln and not ln.startswith("#")]
        return secrets.choice(lines) if lines else ""
    except Exception:
        return ""


def _pick_random_image_file(folder: str) -> str | None:
    try:
        if not os.path.isdir(folder):
            return None
        exts = (".jpg", ".jpeg", ".png", ".webp")
        files = [os.path.join(folder, fn) for fn in os.listdir(folder) if fn.lower().endswith(exts)]
        return secrets.choice(files) if files else None
    except Exception:
        return None


PROFILE_UA_FILE = "user_agent.txt"
PROFILE_META_FILE = "profile_meta.json"
PROFILE_NUM_WIDTH = 6


def format_profile_num(num: int | None) -> str | None:
    try:
        if num is None:
            return None
        return f"{int(num):0{PROFILE_NUM_WIDTH}d}"
    except Exception:
        return None


def profile_dir_for_runtime(profile_num: int | None, email: str | None) -> str:
    if profile_num is not None:
        formatted = format_profile_num(profile_num) or str(profile_num)
        return os.path.join(PATH_PROFILES, f"profile_{formatted}")
    safe_profile = str(email or "profile_unknown").replace("@", "_").replace(".", "_")
    return os.path.join(PATH_PROFILES, safe_profile)


def write_profile_metadata(profile_path: str, *, email: str | None, profile_num: int | None):
    try:
        os.makedirs(profile_path, exist_ok=True)
        meta = {
            "profile_num": int(profile_num) if profile_num is not None else None,
            "profile_num_padded": format_profile_num(profile_num),
            "email": str(email or "").strip(),
            "profile_dir": profile_path,
            "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        with open(os.path.join(profile_path, PROFILE_META_FILE), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Не удалось сохранить profile_meta.json: {e}", "WARNING")


def generate_mac_user_agent() -> str:
    chrome_major = random.randint(120, 134)
    chrome_build1 = random.randint(1000, 9999)
    chrome_build2 = random.randint(0, 200)
    if random.random() < 0.5:
        win_versions = ["10.0; Win64; x64", "10.0; Win64; x64", "11.0; Win64; x64"]
        win_ver = random.choice(win_versions)
        return (
            f"Mozilla/5.0 (Windows NT {win_ver}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_major}.0.{chrome_build1}.{chrome_build2} Safari/537.36"
        )
    else:
        mac_versions = ["10_15_7", "11_7_10", "12_7_6", "13_6_9", "14_7_1", "15_0"]
        mac_ver = random.choice(mac_versions)
        return (
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_ver}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_major}.0.{chrome_build1}.{chrome_build2} Safari/537.36"
        )


def get_or_create_profile_user_agent(profile_dir: str | None) -> str | None:
    if not profile_dir:
        return None
    try:
        profile_path = Path(profile_dir)
        profile_path.mkdir(parents=True, exist_ok=True)
        ua_file = profile_path / PROFILE_UA_FILE
        if ua_file.exists():
            ua = ua_file.read_text(encoding="utf-8").strip()
            if ua:
                return ua
        ua = generate_mac_user_agent()
        ua_file.write_text(ua, encoding="utf-8")
        return ua
    except Exception as e:
        log(f"Не удалось получить/сохранить user-agent для профиля {profile_dir}: {e}", "WARNING")
        return generate_mac_user_agent()


def wipe_profile_for_fresh_start(profile_path: str) -> None:
    """
    Глубокая очистка Chrome-профиля перед регистрацией нового аккаунта.
    Сохраняем: только profile_meta.json (device_profile.json и user_agent.txt — сбрасываются для нового отпечатка)
    """
    if not profile_path or not os.path.isdir(profile_path):
        return
    lock_names = {"SingletonLock", "SingletonCookie", "SingletonSocket", "DevToolsActivePort", "lockfile"}
    for name in lock_names:
        try:
            p = os.path.join(profile_path, name)
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    wipe_targets = [
        "Default", "GrShaderCache", "ShaderCache", "blob_storage",
        "File System", "IndexedDB", "databases", "Local Storage",
        "Session Storage", "Cache", "Code Cache", "Network",
    ]
    # НЕ сохраняем device_profile.json — сбрасываем отпечаток при каждом запуске
    keep_files = {"profile_meta.json"}
    for target in wipe_targets:
        full = os.path.join(profile_path, target)
        if os.path.isdir(full):
            try:
                shutil.rmtree(full, ignore_errors=True)
                log(f"🧹 Wipe профиля: удалена папка {target}/", "INFO")
            except Exception as e:
                log(f"🧹 Wipe профиля: не удалось удалить {target}: {e}", "WARNING")
        elif os.path.isfile(full):
            try:
                os.remove(full)
            except Exception:
                pass
    try:
        for item in os.listdir(profile_path):
            if item in keep_files:
                continue
            full = os.path.join(profile_path, item)
            try:
                if os.path.isfile(full):
                    os.remove(full)
            except Exception:
                pass
    except Exception:
        pass
    log(f"✅ Профиль вайпнут под свежий аккаунт: {profile_path}", "INFO")


def reset_device_fingerprint(profile_path: str) -> dict:
    """
    Полностью сбрасывает отпечаток устройства для профиля:
    удаляем device_profile.json и user_agent.txt -> генерируем новые.
    Вызывать ПЕРЕД запуском браузера, после wipe_profile_for_fresh_start.
    """
    if not profile_path:
        return get_or_create_device_profile(None)
    for fname in ('device_profile.json', 'user_agent.txt'):
        fpath = os.path.join(profile_path, fname)
        try:
            if os.path.exists(fpath):
                os.remove(fpath)
                log(f'Отпечаток: удалён {fname}', 'INFO')
        except Exception as e:
            log(f'Не удалось удалить {fname}: {e}', 'WARNING')
    dp = get_or_create_device_profile(profile_path)
    log(
        f'Новый отпечаток: token={dp.get("fp_token","?")}, '
        f'OS={"Windows" if dp.get("is_windows") else "Mac"}, '
        f'screen={dp.get("screen_w")}x{dp.get("screen_h")}, '
        f'UA={str(dp.get("user_agent",""))[:60]}',
        'INFO'
    )
    return dp



def cleanup_profile(profile_path: str) -> None:
    """Удаляем Chrome-профиль полностью после завершения стрима — он больше не нужен."""
    if not profile_path or not os.path.isdir(profile_path):
        return
    try:
        shutil.rmtree(profile_path, ignore_errors=True)
        log(f"🗑 Профиль удалён: {profile_path}", "INFO")
    except Exception as e:
        log(f"🗑 Не удалось удалить профиль {profile_path}: {e}", "WARNING")


def cleanup_mail_file(email: str) -> None:
    """Удаляем mail-файл с OTP сразу после того как код прочитан и использован."""
    if not email:
        return
    local_part = email.split("@")[0]
    for path in [
        os.path.join(PATH_MAILS, f"{local_part}.txt"),
        os.path.join(PATH_PULSZ_MAILS, f"{local_part}.txt"),
    ]:
        if os.path.exists(path):
            try:
                os.remove(path)
                log(f"🗑 Mail-файл удалён: {os.path.basename(path)}", "INFO")
            except Exception as e:
                log(f"🗑 Не удалось удалить mail-файл {path}: {e}", "WARNING")


def cleanup_proxy_ext_old(max_age_sec: float = 3600) -> None:
    """Удаляем старые папки _proxy_ext/ — они нужны только пока жив браузер."""
    ext_root = os.path.join(BASE_DIR, "_proxy_ext")
    if not os.path.isdir(ext_root):
        return
    now = time.time()
    removed = 0
    try:
        for name in os.listdir(ext_root):
            full = os.path.join(ext_root, name)
            if not os.path.isdir(full):
                continue
            try:
                age = now - os.path.getmtime(full)
                if age > max_age_sec:
                    shutil.rmtree(full, ignore_errors=True)
                    removed += 1
            except Exception:
                pass
    except Exception:
        pass
    if removed:
        log(f"🗑 Удалено {removed} старых proxy_ext папок", "INFO")


def trim_used_emails(max_lines: int = 3000) -> None:
    """Ротация used_emails.txt — оставляем только последние max_lines строк."""
    try:
        if not os.path.exists(USED_EMAILS):
            return
        with open(USED_EMAILS, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) <= max_lines:
            return
        keep = lines[-max_lines:]
        with open(USED_EMAILS, "w", encoding="utf-8") as f:
            f.writelines(keep)
        log(f"🗑 used_emails.txt обрезан: {len(lines)} → {len(keep)} строк", "INFO")
    except Exception as e:
        log(f"🗑 trim_used_emails: {e}", "WARNING")


def inject_fingerprint_randomization(driver):
    """
    Fallback fingerprint (если device_fingerprint.py не найден).
    Меняем только железо/UA — БЕЗ timezone и geolocation,
    чтобы не ломать авторизацию на Tango.
    """
    cores    = random.choice([2, 4, 6, 8, 10, 12])
    memory   = random.choice([4, 8, 16, 32])
    lang     = random.choice(["en-US", "en-US", "en-GB"])
    platform = random.choice(["Win32", "Win32", "Win32", "MacIntel"])
    webgl_vendors   = ["Google Inc. (Intel)", "Google Inc. (NVIDIA)", "Google Inc. (AMD)", "Google Inc."]
    webgl_renderers = [
        "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    ]
    webgl_vendor   = random.choice(webgl_vendors)
    webgl_renderer = random.choice(webgl_renderers)
    screen_widths  = [1280, 1366, 1440, 1536, 1600, 1920]
    screen_heights = [720,  768,  900,  864,  900,  1080]
    sw_idx = random.randint(0, len(screen_widths) - 1)
    sw = screen_widths[sw_idx]
    sh = screen_heights[sw_idx]
    avail_h = sh - random.randint(40, 80)
    langs_json = '["en-US","en"]' if "en" in lang else f'["{lang}","en-US","en"]'

    script = f"""
(function() {{
  try {{
    const def_ = (obj, prop, value) => {{
      try {{ Object.defineProperty(obj, prop, {{get: () => value, configurable: true, enumerable: true}}); }} catch(e) {{}}
    }};
    if (window.Navigator && Navigator.prototype) {{
      def_(Navigator.prototype, 'hardwareConcurrency', {cores});
      def_(Navigator.prototype, 'deviceMemory', {memory});
      def_(Navigator.prototype, 'platform', '{platform}');
      def_(Navigator.prototype, 'language', '{lang}');
      def_(Navigator.prototype, 'languages', {langs_json});
      def_(Navigator.prototype, 'vendor', 'Google Inc.');
      try {{ delete Navigator.prototype.webdriver; }} catch(e) {{}}
      def_(Navigator.prototype, 'webdriver', false);
    }}
    if (window.Screen && Screen.prototype) {{
      def_(Screen.prototype, 'width', {sw});
      def_(Screen.prototype, 'height', {sh});
      def_(Screen.prototype, 'availWidth', {sw});
      def_(Screen.prototype, 'availHeight', {avail_h});
      def_(Screen.prototype, 'colorDepth', 24);
      def_(Screen.prototype, 'pixelDepth', 24);
    }}
    const origGetParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {{
      if (param === 37445) return '{webgl_vendor}';
      if (param === 37446) return '{webgl_renderer}';
      return origGetParam.call(this, param);
    }};
    if (!window.chrome) {{
      window.chrome = {{
        app: {{isInstalled: false}},
        runtime: {{
          onConnect: {{addListener: () => {{}}}},
          onMessage: {{addListener: () => {{}}}}
        }},
        loadTimes: function() {{ return {{}}; }},
        csi: function() {{ return {{}}; }}
      }};
    }}
  }} catch(e) {{}}
}})();
"""
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
        log(f"🎭 Fingerprint fallback: cores={cores}, mem={memory}GB, lang={lang}, screen={sw}x{sh}", "INFO")
    except Exception as e:
        log(f"Не удалось инжектнуть fingerprint spoof: {e}", "WARNING")





def create_driver(profile_path=None, proxy_spec: str | None = None, device_profile: dict | None = None):
    """
    Запускает Chrome с полной имитацией уникального устройства.
    device_profile берётся из profile_path/device_profile.json
    (device_profile генерируется заново при каждом запуске через reset_device_fingerprint).
    """
    # Загружаем профиль устройства
    # device_profile должен быть передан из main() через reset_device_fingerprint().
    # Если не передан (например, checker mode) — генерируем свежий, не читаем старый файл.
    dp = device_profile if device_profile else generate_device_profile()
    if not dp:
        dp = {}

    # user_agent берём из dp или из старого ua-файла (fallback)
    user_agent = dp.get("user_agent")
    if not user_agent and profile_path:
        user_agent = get_or_create_profile_user_agent(profile_path)

    options = Options()

    # ── Основные флаги (незаметные для fingerprint-детекторов) ─────────────
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    # --no-sandbox и --disable-dev-shm-usage нужны только на Linux (Docker/CI)
    # На macOS они могут вызывать краш Chrome
    if sys.platform.startswith("linux"):
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    # Медиастрим — нужен для стрима
    options.add_argument("--use-fake-ui-for-media-stream")

    # ── WebRTC IP leak prevention ─────────────────────────────────────────────
    # default_public_interface_only: блокирует утечку локального IP через STUN,
    # но сохраняет работоспособность WebRTC стрима через публичный интерфейс.
    options.add_argument("--webrtc-ip-handling-policy=default_public_interface_only")

    # ── Anti-detection Chrome flags ───────────────────────────────────────────
    # Отключаем фичи которые репортят метрики / палят автоматизацию
    options.add_argument(
        "--disable-features="
        "ChromeWhatsNewUI,"
        "PrivacySandboxSettings4,"
        "AutofillServerCommunication,"
        "UserAgentClientHint,"
        "OptimizationHints,"
        "MediaRouter,"
        "DialMediaRouteProvider"
    )
    options.add_argument("--disable-component-update")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--no-pings")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-client-side-phishing-detection")

    # ── Снижение нагрузки на CPU / RAM / GPU ──────────────────────────────────
    # GPU: рендерим через CPU (softw. raster) — меньше VRAM, нет GPU-процесса
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-gpu-compositing")
    options.add_argument("--disable-gpu-rasterization")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--disable-accelerated-jpeg-decoding")
    options.add_argument("--disable-accelerated-mjpeg-decode")
    options.add_argument("--disable-accelerated-video-decode")
    options.add_argument("--disable-software-rasterizer")
    # Память: ограничиваем JS-heap и кэши
    options.add_argument("--js-flags=--max-old-space-size=512")
    options.add_argument("--memory-pressure-thresholds=critical=0.9,moderate=0.8")
    options.add_argument("--disk-cache-size=1")          # кэш диска — минимум
    options.add_argument("--media-cache-size=1")         # медиа-кэш — минимум
    # Фоновые процессы: убираем всё лишнее
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-breakpad")           # нет crash reporter
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-in-process-stack-traces")
    options.add_argument("--disable-renderer-accessibility")
    options.add_argument("--disable-speech-api")         # нет speech synthesis
    options.add_argument("--disable-spell-checking")     # нет проверки орфографии
    options.add_argument("--disable-logging")            # нет внутр. логов Chrome
    options.add_argument("--log-level=3")                # только FATAL в консоль
    options.add_argument("--silent")
    options.add_argument("--mute-audio")                 # аудио-вывод тихий
    # Изображения: НЕ отключаем — нужны для превью аватарки в форме

    # Язык из device_profile
    lang = dp.get("language", "en-US")
    options.add_argument(f"--lang={lang}")

    # Небольшой шум к размеру окна
    _win_noise_w = random.randint(-2, 2)

    # Размер окна = экран устройства + минимальный шум (как реальный chrome)
    sw = int(dp.get("screen_w") or random.randint(1200, 1920))
    sh = int(dp.get("screen_h") or random.randint(800, 1080))
    win_w = sw + _win_noise_w
    win_h = sh - random.randint(80, 120)   # taskbar + chrome UI
    options.add_argument(f"--window-size={win_w},{win_h}")

    # Убираем явные automation маркеры
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    # Chrome prefs — как у реального пользователя
    prefs = {
        # Медиа — разрешаем без диалога
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 2,  # 2=block popups spam
        "profile.default_content_settings.popups": 0,
        # Пароли — реальный юзер обычно не сохраняет на новых сайтах
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        # Язык
        "intl.accept_languages": lang,
        # Не предлагать перевод
        "translate_whitelists": {},
        "translate.enabled": False,
        # Tango — разрешения на камеру и микрофон
        "profile.content_settings.exceptions.media_stream_camera": {
            "https://tango.me,*": {"setting": 1},
        },
        "profile.content_settings.exceptions.media_stream_mic": {
            "https://tango.me,*": {"setting": 1},
        },
    }
    options.add_experimental_option("prefs", prefs)

    # Прокси
    if proxy_spec:
        try:
            px = parse_proxy_spec(proxy_spec)
            if px:
                host = px["host"]
                port = int(px["port"])
                user_p = (px.get("user") or "").strip()
                pwd_p  = (px.get("pass") or "").strip()
                if user_p or pwd_p:
                    ext_dir = build_proxy_extension(px)
                    if ext_dir:
                        options.add_argument(f"--disable-extensions-except={ext_dir}")
                        options.add_argument(f"--load-extension={ext_dir}")
                        log(f"Прокси применена (auth): socks5 {host}:{port}", "INFO")
                    else:
                        options.add_argument(f"--proxy-server=socks5://{host}:{port}")
                        log(f"Прокси применена (fallback без auth): socks5 {host}:{port}", "WARNING")
                else:
                    options.add_argument(f"--proxy-server=socks5://{host}:{port}")
                    log(f"Прокси применена: socks5 {host}:{port}", "INFO")
        except Exception as e:
            log(f"Не смогли применить прокси ({proxy_spec}): {e}", "WARNING")

    if profile_path:
        os.makedirs(profile_path, exist_ok=True)
        options.add_argument(f"user-data-dir={profile_path}")
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")

    os_label = "Windows" if dp.get("is_windows", True) else "Mac"
    log(
        f"Запуск Chrome: профиль={profile_path}, OS={os_label}, "
        f"screen={sw}x{sh}, lang={lang}, UA={str(user_agent or '')[:60]}",
        "INFO"
    )
    # Чистим старые proxy-extension папки (старше 1 часа)
    try:
        cleanup_proxy_ext_old(max_age_sec=3600)
    except Exception:
        pass

    driver = webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(120)
        driver.set_script_timeout(120)
    except Exception:
        pass
    # CDP: задаём точные метрики viewport + DPR (совпадает с JS screen.*)
    try:
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width":             win_w,
            "height":            win_h,
            "deviceScaleFactor": float(dp.get("dpr", 1)),
            "mobile":            False,
        })
    except Exception:
        pass

    # CDP: убираем navigator.webdriver
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator,'webdriver',{get:()=>false,configurable:true});"
        })
    except Exception:
        pass

    # CDP: CSS media prefers-color-scheme (matching device profile)
    try:
        _scheme = "dark" if dp.get("prefers_dark", False) else "light"
        driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {
            "features": [{"name": "prefers-color-scheme", "value": _scheme}]
        })
    except Exception:
        pass

    # CDP: блокируем WebRTC device enumeration через Policy (двойная защита)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": (
                "// Запрещаем сохранять deviceId в localStorage (Tango fingerprint)\n"
                "try { const _origSetItem = localStorage.setItem.bind(localStorage);"
                "localStorage.setItem = function(k,v) {"
                "  if (k && (k.includes('device') || k.includes('finger') || k.includes('fp'))) return;"
                "  return _origSetItem(k,v); }; } catch(e) {}"
            )
        })
    except Exception:
        pass

    # Применяем полный fingerprint из device_profile
    if dp and _FP_OK:
        apply_device_profile_to_driver(driver, dp)
    else:
        inject_fingerprint_randomization(driver)

    log(
        f"🎭 Device: token={dp.get('fp_token','?')}, "
        f"cores={dp.get('cores')}, mem={dp.get('memory')}GB, "
        f"tz={dp.get('tz_name')}, "
        f"webgl={str(dp.get('webgl_renderer',''))[:40]}…",
        "INFO"
    )

    return driver


# ========================================================================================
#                         УНИВЕРСАЛЬНЫЕ СЕЛЕНИУМ ФУНКЦИИ
# ========================================================================================



def _pid_alive(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(int(pid))
    except Exception:
        try:
            pid = int(pid)
            if pid <= 0:
                return False
            os.kill(pid, 0)
            return True
        except Exception:
            return False


def acquire_register_lock():
    me = os.getpid()
    created_at = time.time()
    payload = {"pid": me, "created_at": created_at}
    payload_raw = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8", "ignore")
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                os.write(fd, payload_raw)
            finally:
                os.close(fd)
            log("Получен lock на регистрацию (register.lock)", "INFO")
            return
        except FileExistsError:
            try:
                if os.path.exists(LOCK_FILE):
                    mtime = os.path.getmtime(LOCK_FILE)
                    age = time.time() - mtime
                    owner_pid = None
                    try:
                        with open(LOCK_FILE, "r", encoding="utf-8", errors="ignore") as f:
                            raw = f.read().strip()
                        if raw:
                            data = json.loads(raw)
                            owner_pid = int(data.get("pid") or 0)
                    except Exception:
                        owner_pid = None
                    if owner_pid and not _pid_alive(owner_pid):
                        log(f"Lock принадлежит pid={owner_pid}, но процесс не найден — удаляем lock", "WARNING")
                        try:
                            os.remove(LOCK_FILE)
                        except Exception:
                            pass
                        continue
                    if owner_pid is None and age > 1800:
                        log("Lock старше 30 минут и без pid — удаляем", "WARNING")
                        try:
                            os.remove(LOCK_FILE)
                        except Exception:
                            pass
                        continue
            except Exception as e:
                log(f"Ошибка проверки lock-файла: {e}", "WARNING")
            log("Ждём освобождения lock регистрации...", "INFO")
            time.sleep(5)


def release_register_lock():
    me = os.getpid()
    try:
        if not os.path.exists(LOCK_FILE):
            return
        owner_pid = None
        try:
            with open(LOCK_FILE, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read().strip()
            if raw:
                data = json.loads(raw)
                owner_pid = int(data.get("pid") or 0)
        except Exception:
            owner_pid = None
        if owner_pid is None or owner_pid == me:
            os.remove(LOCK_FILE)
            log("Освобождён lock регистрации", "INFO")
        else:
            log(f"Не удаляем lock: владелец pid={owner_pid}, текущий pid={me}", "WARNING")
    except Exception as e:
        log(f"Не удалось удалить lock файл регистрации: {e}", "WARNING")




# ========================================================================================
#   OTP GATE — межпроцессный семафор + минимальная пауза между вводами кода
# ========================================================================================

def acquire_otp_gate(min_delay_sec: float = 0.0) -> None:
    """
    Перед вводом OTP-кода процесс должен взять этот гейт.
    Гарантирует что между вводами кодов разных потоков выдержан минимальный интервал.

    Алгоритм:
      1. Ждём файл-замок otp.lock (только один процесс проходит через гейт одновременно)
      2. Читаем время последнего прохода из otp_gate.json
      3. Если прошло меньше min_delay_sec — спим остаток
      4. Входим (файл замка держим ДО окончания ввода кода, затем release_otp_gate())
    """
    me = os.getpid()
    min_delay_sec = max(0.0, float(min_delay_sec))

    # ── 1. Занимаем файл-замок otp.lock ──────────────────────────────────────
    while True:
        check_stop("otp_gate:waiting_for_lock")
        try:
            fd = os.open(OTP_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.write(fd, str(me).encode())
            os.close(fd)
            break  # замок взят
        except FileExistsError:
            # Проверяем не умер ли хозяин
            try:
                with open(OTP_LOCK_FILE, "r") as f:
                    owner = int(f.read().strip() or 0)
                if owner and not _pid_alive(owner):
                    log(f"OTP gate: pid={owner} мёртв, сбрасываем otp.lock", "WARNING")
                    try:
                        os.remove(OTP_LOCK_FILE)
                    except Exception:
                        pass
                    continue
            except Exception:
                pass
            log(f"OTP gate: ждём (другой поток вводит код)...", "INFO")
            _ORIG_SLEEP(3.0)
        except Exception as e:
            log(f"OTP gate: ошибка lock: {e}", "WARNING")
            _ORIG_SLEEP(3.0)

    # ── 2. Соблюдаем минимальную паузу ───────────────────────────────────────
    if min_delay_sec > 0:
        last_ts = 0.0
        try:
            if os.path.exists(OTP_GATE_FILE):
                with open(OTP_GATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                last_ts = float(data.get("last_otp_ts", 0.0))
        except Exception:
            last_ts = 0.0

        elapsed = time.time() - last_ts
        wait_for = min_delay_sec - elapsed
        if wait_for > 0:
            log(f"OTP gate: пауза {wait_for:.1f}с (мин. интервал {min_delay_sec:.0f}с)", "INFO")
            waited = 0.0
            while waited < wait_for:
                check_stop("otp_gate:delay")
                chunk = min(2.0, wait_for - waited)
                _ORIG_SLEEP(chunk)
                waited += chunk

    log(f"OTP gate: ✅ проходим (pid={me})", "INFO")


def release_otp_gate() -> None:
    """Записываем timestamp прохода и освобождаем otp.lock."""
    # Записываем время
    try:
        os.makedirs(os.path.dirname(OTP_GATE_FILE), exist_ok=True)
        with open(OTP_GATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_otp_ts": time.time()}, f)
    except Exception as e:
        log(f"OTP gate: не удалось записать timestamp: {e}", "WARNING")
    # Снимаем замок
    try:
        if os.path.exists(OTP_LOCK_FILE):
            os.remove(OTP_LOCK_FILE)
    except Exception as e:
        log(f"OTP gate: не удалось удалить otp.lock: {e}", "WARNING")


# ========================================================================================
#                           IMAP — получение OTP прямо из почты
# ========================================================================================

def _imap_fetch_otp(cfg: dict, email_to: str, *, timeout: int = 240,
                    poll_interval: int = 10, expected_lengths=(4, 6),
                    stop_event: threading.Event | None = None) -> str | None:
    """
    Подключается к IMAP, ждёт письмо для email_to, извлекает OTP.
    После нахождения — сохраняет код в mails/<local>.txt.
    Поддерживает Gmail и любые другие IMAP-серверы.
    """
    import imaplib
    import email as _email_mod
    import email.header as _hdr

    imap_server   = (cfg.get("imap_server")   or "").strip()
    imap_email    = (cfg.get("imap_email")     or "").strip()
    imap_password = (cfg.get("imap_password")  or "").strip()
    imap_port     = int(cfg.get("imap_port", 993))

    if not imap_server or not imap_email or not imap_password:
        log("IMAP не настроен в config.json — пропускаем", "WARNING")
        return None

    local_part = email_to.split("@")[0].lower()

    def _decode_part(part) -> str:
        charset = part.get_content_charset() or "utf-8"
        payload = part.get_payload(decode=True)
        if not payload:
            return ""
        for enc in (charset, "utf-8", "latin-1"):
            try:
                return payload.decode(enc, errors="ignore")
            except Exception:
                pass
        return ""

    def _extract_text(msg) -> str:
        """Достаём весь текст письма: subject + plain + html."""
        parts = []
        # Subject
        raw_subj = msg.get("Subject", "")
        try:
            chunks = _hdr.decode_header(raw_subj)
            subj = " ".join(
                b.decode(enc or "utf-8", errors="ignore") if isinstance(b, bytes) else str(b)
                for b, enc in chunks
            )
        except Exception:
            subj = raw_subj
        parts.append(f"Subject: {subj}")
        # Body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ("text/plain", "text/html"):
                    parts.append(_decode_part(part))
        else:
            parts.append(_decode_part(msg))
        return "\n".join(parts)

    def _is_for_us(msg) -> bool:
        """
        Строго проверяем что письмо адресовано НАШЕМУ email.
        Важно при параллельных потоках — не воруем OTP чужого аккаунта.
        """
        checked_any = False
        for hdr in ("To", "Delivered-To", "X-Original-To", "Envelope-To", "X-Forwarded-To"):
            val = (msg.get(hdr) or "").lower()
            if not val:
                continue
            checked_any = True
            if local_part in val or email_to.lower() in val:
                return True
        # Заголовки совсем не найдены — нетипичная ситуация, принимаем письмо
        if not checked_any:
            log(f"IMAP: письмо без To-заголовков — принимаем (email={email_to})", "WARNING")
            return True
        # Заголовки есть, но наш email не найден — чужое письмо
        return False

    def _save_email_to_file(full_text: str, code: str):
        """
        Сохраняем ПОЛНЫЙ текст письма в mails/<local_part>.txt.
        Это позволяет file-watcher-у читать из файла с полным контентом.
        Первая строка — Subject (для быстрого поиска кода),
        далее — весь body, в конце — явная строка с кодом.
        """
        try:
            os.makedirs(PATH_MAILS, exist_ok=True)
            fpath = os.path.join(PATH_MAILS, f"{local_part}.txt")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(full_text)
                f.write(f"\n\n--- extracted code: {code} ---\n{code}\n")
            log(f"IMAP: письмо сохранено в файл: {fpath} (код={code})", "INFO")
        except Exception as e:
            log(f"IMAP: не удалось сохранить письмо в файл: {e}", "WARNING")

    start_time = time.time()
    seen_uids: set = set()
    imap = None

    def _connect():
        nonlocal imap
        imap = imaplib.IMAP4_SSL(imap_server, imap_port)
        imap.login(imap_email, imap_password)
        imap.select("INBOX")

    try:
        log(f"IMAP: подключаемся к {imap_server}:{imap_port} как {imap_email}", "INFO")
        try:
            _connect()
        except Exception as e:
            log(f"IMAP: не удалось подключиться/авторизоваться: {e}", "ERROR")
            return None
        log("IMAP: авторизация OK", "SUCCESS")

        # Запоминаем существующие UIDs — старые письма не трогаем
        _, existing = imap.uid("search", None, "ALL")
        if existing and existing[0]:
            for uid in (existing[0] or b"").split():
                seen_uids.add(uid)
        log(f"IMAP: существующих писем: {len(seen_uids)} (будут проигнорированы)", "INFO")

        while time.time() - start_time < timeout:
            # Внешний stop_event (другой поток нашёл код раньше)
            if stop_event and stop_event.is_set():
                log("IMAP: stop_event — другой поток уже нашёл код", "INFO")
                return None

            try:
                imap.select("INBOX")
                _, data = imap.uid("search", None, "ALL")
                all_uids = (data[0] or b"").split() if data else []
                new_uids = [u for u in all_uids if u not in seen_uids]

                for uid in reversed(new_uids):  # самые новые первыми
                    if stop_event and stop_event.is_set():
                        return None
                    try:
                        _, msg_data = imap.uid("fetch", uid, "(RFC822)")
                        seen_uids.add(uid)  # помечаем сразу чтоб не читать повторно
                        if not msg_data or not msg_data[0]:
                            continue
                        raw = msg_data[0][1]
                        msg = _email_mod.message_from_bytes(raw)

                        if not _is_for_us(msg):
                            subj_skip = (msg.get("Subject") or "")[:50]
                            to_skip = (msg.get("To") or msg.get("Delivered-To") or "")[:60]
                            log(f"IMAP: uid={uid.decode()} — чужое письмо (To={to_skip!r}) пропускаем", "INFO")
                            continue

                        text = _extract_text(msg)
                        # Логируем письмо для отладки
                        subj_line = next((l for l in text.splitlines() if l.startswith("Subject:")), "")
                        frm = (msg.get("From") or "")[:60]
                        to_hdr = (msg.get("To") or msg.get("Delivered-To") or "")[:60]
                        log(f"IMAP: 📩 uid={uid.decode()} | From={frm!r} | To={to_hdr!r} | {subj_line[:80]}", "INFO")

                        lines = text.splitlines()
                        code, source = _extract_latest_otp_from_lines(lines, expected_lengths=expected_lengths)
                        if code:
                            log(f"IMAP: ✅ OTP найден ({source}) uid={uid.decode()}: {code}", "SUCCESS")
                            _save_email_to_file(text, code)
                            return code

                        # Письмо наше, но кода нет — сохраняем для отладки
                        log(f"IMAP: письмо uid={uid.decode()} без OTP-кода, сохраняем для отладки", "WARNING")
                        try:
                            debug_path = os.path.join(PATH_MAILS, f"{local_part}_debug_{uid.decode()}.txt")
                            with open(debug_path, "w", encoding="utf-8") as f:
                                f.write(text)
                        except Exception:
                            pass

                    except Exception as e:
                        log(f"IMAP: ошибка чтения uid={uid}: {e}", "WARNING")

            except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as e:
                log(f"IMAP: соединение разорвано ({e}), переподключаемся...", "WARNING")
                try:
                    imap.logout()
                except Exception:
                    pass
                _ORIG_SLEEP(2)
                try:
                    _connect()
                except Exception as e2:
                    log(f"IMAP: переподключение не удалось: {e2}", "ERROR")
                    return None
            except Exception as e:
                log(f"IMAP: ошибка поиска: {e}", "WARNING")

            elapsed = int(time.time() - start_time)
            log(f"IMAP: ждём письмо для {email_to}... ({elapsed}с / {timeout}с)", "INFO")
            _ORIG_SLEEP(poll_interval)

        log(f"IMAP: OTP не получен за {timeout} сек", "ERROR")
        return None

    finally:
        try:
            if imap:
                imap.logout()
        except Exception:
            pass


def get_tango_code(cfg: dict, email: str, timeout: int = 240, poll_interval: int = 5) -> str | None:
    """
    Получаем OTP для Tango двумя способами параллельно:
      1. IMAP — подключается к Gmail, ждёт письмо, сохраняет ПОЛНЫЙ текст
             в mails/<local_part>.txt, возвращает код напрямую
      2. file-watcher — ждёт появления/обновления mails/<local_part>.txt
             (подхватит файл записанный IMAP или внешним скриптом)
    Первый нашедший код побеждает, второй поток останавливается.
    """
    local_part = email.split("@")[0]
    filepath = os.path.join(PATH_MAILS, f"{local_part}.txt")

    imap_configured = bool(
        (cfg.get("imap_server") or "").strip() and
        (cfg.get("imap_email") or "").strip() and
        (cfg.get("imap_password") or "").strip()
    )

    result_box: list = []          # [(source, code)]
    done_event = threading.Event() # сигнал "код найден"

    def _file_worker():
        code = wait_for_code_from_file(
            filepath, timeout=timeout, poll_interval=poll_interval,
            expected_lengths=(4, 6), channel_name="file"
        )
        if code and not done_event.is_set():
            result_box.append(("file", code))
            done_event.set()

    def _imap_worker():
        code = _imap_fetch_otp(
            cfg, email,
            timeout=timeout,
            poll_interval=int(cfg.get("imap_poll_interval", 10)),
            expected_lengths=(4, 6),
            stop_event=done_event,
        )
        if code and not done_event.is_set():
            result_box.append(("imap", code))
            done_event.set()

    # file-watcher всегда — даже если IMAP не настроен или упал
    t_file = threading.Thread(target=_file_worker, daemon=True, name=f"file-{local_part}")
    t_file.start()

    if imap_configured:
        log(f"📬 IMAP+file-watcher запущены параллельно для: {email}", "INFO")
        log(f"   Файл ожидания: {filepath}", "INFO")
        t_imap = threading.Thread(target=_imap_worker, daemon=True, name=f"imap-{local_part}")
        t_imap.start()
    else:
        log(f"📂 IMAP не настроен — только file-watcher: {filepath}", "INFO")

    got = done_event.wait(timeout=timeout + 20)
    if not got:
        log(f"OTP не получен ни одним способом за {timeout + 20} сек", "ERROR")

    if result_box:
        source, code = result_box[0]
        log(f"✅ OTP получен через [{source}]: {code}", "SUCCESS")
        return code

    return None


def get_tango_code_from_file(email, timeout=240, poll_interval=5):
    """Обратная совместимость — вызывает get_tango_code без IMAP."""
    local_part = email.split("@")[0]
    filepath = os.path.join(PATH_MAILS, f"{local_part}.txt")
    return wait_for_code_from_file(
        filepath, timeout=timeout, poll_interval=poll_interval,
        expected_lengths=(4, 6), channel_name="tango",
    )




def get_pulsz_code_from_file(email, timeout=240, poll_interval=5):
    local_part = email.split("@")[0]
    filename = f"{local_part}.txt"
    try:
        os.makedirs(PATH_PULSZ_MAILS, exist_ok=True)
    except Exception:
        pass
    filepath = os.path.join(PATH_PULSZ_MAILS, filename)
    return wait_for_code_from_file(
        filepath, timeout=timeout, poll_interval=poll_interval,
        expected_lengths=(4, 6), channel_name="pulsz",
    )


def send_gift(driver, gift_key):
    if not gift_key:
        log("Подарок не выбран (gift_key пустой), пропускаем отправку подарка", "INFO")
        return
    gift_map = {
        "99":   "gift-ssSY6hLfSmA2LtZcdXmNKw",
        "299":  "gift-xoyWTZnoSPniXnntiYCi_A",
        "499":  "gift-nzZP2cjNuMJK_Unhj7S50Q",
        "999":  "gift-d2S2xYdFtnec3j02HdOcBg",
        "1499": "gift-MVxFsvBeag7vYRWLKHYaoA",
    }
    gift_key = str(gift_key)
    gift_testid = gift_map.get(gift_key)
    if not gift_testid:
        log(f"Неизвестный тип подарка: {gift_key}, пропускаем отправку", "WARNING")
        return
    gift_txt_path = os.path.join(BASE_DIR, "settings/gift.txt")
    gift_text = ""
    try:
        if os.path.exists(gift_txt_path):
            with open(gift_txt_path, "r", encoding="utf-8") as f:
                gift_text = f.read().strip()
    except Exception as e:
        log(f"Ошибка чтения gift.txt: {e}", "ERROR")
    try:
        log("Стрим запущен, ждём 60 секунд перед отправкой подарка", "INFO")
        time.sleep(60)
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='broadcast-stickers-button']"))
        ).click()
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='sticker-GIFT']"))
        ).click()
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='{gift_testid}']"))
        ).click()
        text_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-testid='add-text-input'], textarea[data-testid='add-text-input']"))
        )
        if gift_text:
            try:
                text_input.clear()
            except Exception:
                pass
            text_input.send_keys(gift_text)
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='done']"))
        ).click()
        log(f"Подарок {gift_key} успешно отправлен", "SUCCESS")
    except Exception as e:
        log(f"Ошибка при отправке подарка {gift_key}: {e}", "ERROR")


def get_diamonds(driver):
    """Возвращает (diamonds: int, profile_url: str | None)."""
    url = "https://tango.me/live/recommended"
    profile_url = None
    try:
        log(f"Открываем страницу с алмазами: {url}", "INFO")
        driver.get(url)
        time.sleep(3)
        driver.refresh()
        time.sleep(3)
        try:
            avatars = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='avatar']"))
            )
        except TimeoutException:
            log("Не нашли ни одного avatar на странице, алмазы = 0", "WARNING")
            return 0, None
        if not avatars:
            log("Список avatar пуст, алмазы = 0", "WARNING")
            return 0, None
        avatars[0].click()
        log("Клик по первому avatar", "INFO")
        time.sleep(3)

        # Извлекаем ссылку на профиль из текущего URL
        try:
            cur_url = driver.current_url or ""
            if "/profile/" in cur_url or "tango.me" in cur_url:
                profile_url = cur_url
                log(f"Профиль URL: {profile_url}", "INFO")
        except Exception:
            pass

        # Пробуем несколько способов получить текст алмазов
        # Способ 1: старый JS с известным классом
        script_known = """
        const container = document.querySelector("div.ZzHP7.Y3IN4.DN33Y");
        if (!container) return null;
        for (const node of container.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                const t = (node.textContent || "").trim();
                if (t) return t;
            }
        }
        return null;
        """
        # Способ 2: ищем data-testid с алмазами
        script_testid = """
        const els = document.querySelectorAll("[data-testid*='diamond'], [data-testid*='balance'], [data-testid*='coin']");
        for (const el of els) {
            const t = (el.textContent || el.innerText || "").trim();
            if (t && /\\d/.test(t)) return t;
        }
        return null;
        """
        # Способ 3: ищем aria-label с алмазами
        script_aria = """
        const els = document.querySelectorAll("[aria-label*='diamond' i], [aria-label*='balance' i], [title*='diamond' i]");
        for (const el of els) {
            const t = (el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || "").trim();
            if (t && /\\d/.test(t)) return t;
        }
        return null;
        """
        # Способ 4: ищем число рядом со значком алмаза (SVG + текст)
        script_near_svg = """
        const svgs = document.querySelectorAll("svg");
        for (const svg of svgs) {
            const parent = svg.parentElement;
            if (!parent) continue;
            const txt = (parent.textContent || "").trim();
            if (/^[\\d,. ]+$/.test(txt) && txt.length <= 10) return txt;
            const sib = parent.nextElementSibling;
            if (sib) {
                const t = (sib.textContent || "").trim();
                if (/^[\\d,. ]+$/.test(t) && t.length <= 10) return t;
            }
        }
        return null;
        """

        raw_text = None
        for i, script in enumerate([script_known, script_testid, script_aria, script_near_svg], 1):
            try:
                raw_text = driver.execute_script(script)
                if raw_text:
                    log(f"Алмазы найдены способом #{i}: '{raw_text}'", "INFO")
                    break
            except Exception:
                pass

        if not raw_text:
            # Последний шанс — ищем любое число от 0 до 9999999 на странице в нужном контексте
            try:
                page_src = driver.page_source
                # Ищем паттерн вроде "diamonds":1234 или "balance":1234
                m = re.search(r'"(?:diamonds?|balance|coins?|tokens?)"\s*:\s*(\d+)', page_src, re.IGNORECASE)
                if m:
                    raw_text = m.group(1)
                    log(f"Алмазы найдены в page source: '{raw_text}'", "INFO")
            except Exception:
                pass

        if not raw_text:
            log("Не нашли количество алмазов ни одним способом, возвращаю 0", "WARNING")
            return 0, profile_url

        digits_only = re.sub(r"[^\d]", "", str(raw_text))
        if not digits_only:
            log("Не удалось выделить цифры из текста алмазов, возвращаю 0", "WARNING")
            return 0, profile_url
        diamonds = int(digits_only)
        log(f"Получено алмазов: {diamonds}", "SUCCESS")
        return diamonds, profile_url
    except WebDriverException as e:
        msg = str(e).splitlines()[0]
        log(f"WebDriver ошибка при получении алмазов: {msg}", "ERROR")
        return 0, profile_url
    except Exception as e:
        msg = str(e).splitlines()[0]
        log(f"Не удалось получить алмазы: {msg}", "ERROR")
        return 0, profile_url


# ========================================================================================
#   ЧЕЛОВЕЧЕСКОЕ ПОВЕДЕНИЕ — скрываем автоматизацию от поведенческих анализаторов
# ========================================================================================

def _human_sleep(min_ms: int, max_ms: int):
    """Пауза с нормальным распределением (не равномерным — как у людей)."""
    mean = (min_ms + max_ms) / 2
    std  = (max_ms - min_ms) / 6
    ms   = max(min_ms, min(max_ms, random.gauss(mean, std)))
    _ORIG_SLEEP(ms / 1000.0)


def human_type(element, text: str, allow_typos: bool = False):
    """
    Вводит текст посимвольно с нечеловечески случайными паузами.
    allow_typos=False — точный ввод (для email/OTP).
    allow_typos=True  — иногда делает опечатку и исправляет её (для имён/ников).
    """
    from selenium.webdriver.common.keys import Keys
    try:
        element.click()
    except Exception:
        pass
    _human_sleep(80, 200)

    for i, ch in enumerate(text):
        # Опечатки только если явно разрешено — никогда при вводе email/кода
        if allow_typos and i > 0 and random.random() < 0.06 and len(text) > 4:
            typo_ch = random.choice("qwertyuiopasdfghjklzxcvbnm")
            try:
                element.send_keys(typo_ch)
                _human_sleep(40, 120)
                element.send_keys(Keys.BACK_SPACE)
                _human_sleep(60, 180)
            except Exception:
                pass

        try:
            element.send_keys(ch)
        except Exception:
            pass

        # Пауза после символа — нормальное распределение ~80-180ms
        # Длиннее после пробела, запятой, точки
        if ch in (' ', '.', ',', '@', '-', '_'):
            _human_sleep(120, 320)
        else:
            _human_sleep(45, 190)


def human_move_and_click(driver, element):
    """
    Плавно подводим курсор к элементу через ActionChains и кликаем.
    Добавляет небольшой оффсет от центра (человек не кликает точно в центр).
    """
    from selenium.webdriver.common.action_chains import ActionChains
    try:
        # Случайный оффсет от центра элемента
        size = element.size
        off_x = random.randint(-max(1, size.get('width', 20) // 4),
                                max(1, size.get('width', 20) // 4))
        off_y = random.randint(-max(1, size.get('height', 8) // 3),
                                max(1, size.get('height', 8) // 3))
        ActionChains(driver)            .move_to_element_with_offset(element, off_x, off_y)            .pause(random.uniform(0.05, 0.15))            .click()            .perform()
    except Exception:
        try:
            element.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", element)
            except Exception:
                pass


def purge_profile_tracking_data(profile_path: str):
    """
    Удаляем файлы Chrome-профиля, которые могут хранить tracking-данные
    между сессиями: History, Cookies, Local Storage, IndexedDB, Cache, Service Workers.
    Вызывать ПЕРЕД запуском Chrome для данного профиля.
    device_profile.json уже сброшен на этом этапе — здесь только tracking-данные.
    """
    if not profile_path or not os.path.isdir(profile_path):
        return

    # Папки внутри Default/ которые чистим полностью
    dirs_to_clear = [
        "Default/Cache",
        "Default/Code Cache",
        "Default/Service Worker",
        "Default/GPUCache",
        "Default/IndexedDB",
        "Default/Local Storage",
        "Default/Session Storage",
        "Default/databases",
        "Default/BudgetDatabase",
        "Default/File System",
        "Default/blob_storage",
    ]
    # Отдельные файлы-следы
    files_to_remove = [
        "Default/History",
        "Default/History-journal",
        "Default/Cookies",
        "Default/Cookies-journal",
        "Default/Login Data",
        "Default/Login Data-journal",
        "Default/Web Data",
        "Default/Web Data-journal",
        "Default/Visited Links",
        "Default/Last Session",
        "Default/Last Tabs",
        "Default/Current Session",
        "Default/Current Tabs",
        "Default/Shortcuts",
        "Default/Favicons",
        "Default/Top Sites",
        "Default/Network Action Predictor",
        "Default/QuotaManager",
        "Default/QuotaManager-journal",
        "Default/Extension Cookies",
    ]

    removed_dirs  = 0
    removed_files = 0

    for rel in dirs_to_clear:
        full = os.path.join(profile_path, rel)
        if os.path.isdir(full):
            try:
                shutil.rmtree(full, ignore_errors=True)
                removed_dirs += 1
            except Exception:
                pass

    for rel in files_to_remove:
        full = os.path.join(profile_path, rel)
        if os.path.isfile(full):
            try:
                os.remove(full)
                removed_files += 1
            except Exception:
                pass

    # ── Патчим Preferences — сбрасываем device_id_salt и created_time ────────
    # media.device_id_salt → Tango использует его для постоянного device ID через MediaDevices
    # profile.created_time  → Chrome сообщает когда создан профиль
    prefs_path = os.path.join(profile_path, "Default", "Preferences")
    if os.path.isfile(prefs_path):
        try:
            import json as _json2
            with open(prefs_path, "r", encoding="utf-8", errors="ignore") as f:
                prefs_data = _json2.load(f)
            changed = False
            # Сбрасываем соль MediaDevices (новая соль = новые device IDs)
            media = prefs_data.get("media", {})
            import secrets as _sec
            new_salt = _sec.token_hex(16)
            if media.get("device_id_salt") != new_salt:
                prefs_data.setdefault("media", {})["device_id_salt"] = new_salt
                changed = True
            # Сбрасываем время создания профиля на случайное прошлое
            import random as _rnd2, time as _time2
            fake_created = _time2.time() - _rnd2.randint(60*60*24*30, 60*60*24*365)
            prefs_data.setdefault("profile", {})["creation_time"] = int(fake_created * 1e6)
            prefs_data["profile"]["created_time"] = int(fake_created * 1e6)
            # Убираем Google account следы
            for k in ("google", "gaia_cookie", "account_info", "signin"):
                prefs_data.pop(k, None)
            changed = True
            if changed:
                with open(prefs_path, "w", encoding="utf-8") as f:
                    _json2.dump(prefs_data, f, ensure_ascii=False, separators=(',', ':'))
                log(f"🔑 Preferences пропатчены: device_id_salt сброшен", "INFO")
        except Exception as _pe:
            # Если не смогли распарсить — удаляем (Chrome пересоздаст)
            try:
                os.remove(prefs_path)
                log(f"🧹 Preferences удалены (Chrome пересоздаст)", "INFO")
            except Exception:
                pass

    # ── Явно удаляем Local State (machine-level IDs: hardware_id, session stats) ──
    # Chrome пересоздаст его при следующем запуске со свежими значениями
    for ls_name in ("Local State", "Local State-journal"):
        ls_path = os.path.join(profile_path, ls_name)
        if os.path.isfile(ls_path):
            try:
                os.remove(ls_path)
                log(f"🧹 Удалён {ls_name} (machine-level IDs)", "INFO")
            except Exception:
                pass

    # ── Service Worker папка (регистрации персистируют между сессиями) ──────
    for sw_path in [
        "Default/Service Worker",
        "Default/ServiceWorkerCache",
        "Default/CacheStorage",
        "Default/Storage",
    ]:
        full_sw = os.path.join(profile_path, sw_path)
        if os.path.isdir(full_sw):
            try:
                shutil.rmtree(full_sw, ignore_errors=True)
                removed_dirs += 1
            except Exception:
                pass

    # ── Также чистим Network папку (HSTS, certificate pins) ─────────────────
    for net_item in ["Default/Network", "Default/Reporting and NEL",
                     "Default/GCM Store", "Default/Platform Notifications"]:
        full = os.path.join(profile_path, net_item)
        if os.path.isdir(full):
            try:
                shutil.rmtree(full, ignore_errors=True)
                removed_dirs += 1
            except Exception:
                pass
        elif os.path.isfile(full):
            try:
                os.remove(full)
                removed_files += 1
            except Exception:
                pass

    if removed_dirs or removed_files:
        log(f"🧹 Профиль очищен ({profile_path}): "
            f"{removed_dirs} папок, {removed_files} файлов удалено", "INFO")
    else:
        log(f"🧹 Профиль уже чист: {profile_path}", "INFO")


def clear_browser_data(driver):
    """Очистка состояния браузера через CDP + JS."""
    # CDP cookies + cache
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    except Exception:
        pass
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
    except Exception:
        pass
    # Selenium cookies
    try:
        driver.delete_all_cookies()
    except Exception as e:
        log(f"Не удалось удалить cookies: {e}", "WARNING")
    # localStorage / sessionStorage
    try:
        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
    except Exception as e:
        log(f"Не удалось очистить localStorage/sessionStorage: {e}", "WARNING")


def perform_email_login(driver, cfg, email):
    check_stop("perform_email_login:start")
    # Случайная пауза перед открытием (анти-паттерн: все стримы стартуют мгновенно)
    _pre_delay = random.uniform(1.5, 6.0)
    _ORIG_SLEEP(_pre_delay)
    if not _safe_navigate(driver, cfg["tango_ref_url"], timeout=120, retries=3, label="login"):
        log("Не удалось открыть Tango ref URL", "ERROR")
        return False
    log("Открыта ссылка Tango", "INFO")
    # Ждём загрузки и немного скроллим — как живой пользователь
    _human_sleep(800, 1800)
    try:
        scroll_px = random.randint(80, 300)
        driver.execute_script(f"window.scrollBy({{top: {scroll_px}, left: 0, behavior: 'smooth'}});")
        _human_sleep(400, 900)
        driver.execute_script(f"window.scrollBy({{top: -{scroll_px // 2}, left: 0, behavior: 'smooth'}});")
        _human_sleep(300, 700)
    except Exception:
        pass
    try:
        log("Пробуем нажать JOIN NOW", "INFO")
        btn_join = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.join-now"))
        )
        try:
            btn_join.click()
        except (ElementClickInterceptedException, StaleElementReferenceException, WebDriverException):
            driver.execute_script("arguments[0].click();", btn_join)
        log("Нажата Join Now", "SUCCESS")
    except Exception as e:
        log(f"JOIN NOW не нажата (может её и нет): {e}", "WARNING")
    check_stop("perform_email_login:before_email_otp")
    try:
        btn_email = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='EMAIL_OTP']"))
        )
        try:
            btn_email.click()
        except (ElementClickInterceptedException, StaleElementReferenceException, WebDriverException):
            driver.execute_script("arguments[0].click();", btn_email)
        log("Нажата EMAIL_OTP", "SUCCESS")
        _human_sleep(1500, 2800)
        inp = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email']"))
        )
        # Вводим email через JS — без посимвольного ввода (autocorrect на Mac портит текст)
        for _attempt in range(3):
            try:
                inp.click()
            except Exception:
                pass
            try:
                inp.clear()
            except Exception:
                pass
            _human_sleep(80, 150)

            # Всегда JS — надёжно на Mac и Windows, без риска autocorrect
            _injected = False
            try:
                driver.execute_script(
                    "const el = arguments[0]; const val = arguments[1];"
                    "const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                    "setter.call(el, val);"
                    "el.dispatchEvent(new Event('input', {bubbles:true}));"
                    "el.dispatchEvent(new Event('change', {bubbles:true}));",
                    inp, email
                )
                _injected = True
            except Exception:
                pass

            if not _injected:
                # Fallback — send_keys целиком (не посимвольно)
                try:
                    inp.send_keys(email)
                except Exception:
                    pass

            _human_sleep(150, 250)
            val = ""
            try:
                val = inp.get_attribute("value") or ""
            except Exception:
                pass
            if email.lower() in val.lower() or val.lower() in email.lower():
                break
            _human_sleep(100, 200)
        log(f"Введена почта: {email}", "INFO")
    except Exception as e:
        log(f"Ошибка EMAIL_OTP / ввод email: {e}", "ERROR")
        return False
    check_stop("perform_email_login:before_continue")
    cont_sel = "button[data-testid='login-with-email-continue-button']"
    otp_sel = "input[data-testid='digit-input-0']"

    def otp_is_present() -> bool:
        try:
            return bool(driver.find_elements(By.CSS_SELECTOR, otp_sel))
        except Exception:
            return False

    def click_continue(label: str) -> bool:
        try:
            btn = None
            for b in driver.find_elements(By.CSS_SELECTOR, cont_sel)[::-1]:
                try:
                    if b.is_displayed() and b.is_enabled():
                        btn = b
                        break
                except Exception:
                    continue
            if not btn:
                raise TimeoutException("Continue button not found/visible")
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            except Exception:
                pass
            try:
                btn.click()
            except (ElementClickInterceptedException, StaleElementReferenceException, WebDriverException):
                driver.execute_script("arguments[0].click();", btn)
            log(label, "SUCCESS")
            return True
        except Exception as e:
            log(f"{label} — не получилось: {e}", "WARNING")
            return False

    if not click_continue("Нажата Continue после ввода почты (1/2)"):
        return False
    _human_sleep(5000, 9000)   # ждём пока Tango обработает запрос OTP
    if otp_is_present():
        return True
    log("OTP поле не появилось — пробуем Continue ещё раз", "WARNING")
    for attempt in range(3):
        check_stop(f"perform_email_login:continue_retry_{attempt+1}")
        click_continue(f"Нажата Continue после ввода почты (2/2), попытка {attempt+1}")
        try:
            WebDriverWait(driver, 4).until(lambda d: bool(d.find_elements(By.CSS_SELECTOR, otp_sel)))
            break
        except Exception:
            pass
    if otp_is_present():
        return True
    try:
        inp = None
        for sel in ("input[type='email']", "input[name='email']", "input[data-testid*='email']"):
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                inp = els[0]
                break
        if inp:
            try:
                inp.click()
            except Exception:
                pass
            inp.send_keys(Keys.ENTER)
            log("Отправили Enter в поле email (fallback)", "WARNING")
            WebDriverWait(driver, 4).until(lambda d: bool(d.find_elements(By.CSS_SELECTOR, otp_sel)))
    except Exception as e:
        log(f"Enter fallback не сработал: {e}", "WARNING")
    if not otp_is_present():
        log("После повторного Continue OTP так и не появился — возможно капча/лаг", "ERROR")
        return False
    return True


def setup_profile(driver, use_avatar=True, use_name=True, use_bio=True):
    """
    Порядок: фото → ник → био → done-edit-profile-button
    Возвращает profile_url (str | None).
    """
    try:
        avatar_dir = os.path.join(BASE_DIR, "avatar")

        # --- Файл с никами ---
        nick_path = os.path.join(avatar_dir, "nickname.txt")
        if not os.path.exists(nick_path):
            nick_path = os.path.join(avatar_dir, "nicknames.txt")
        name_path = nick_path if os.path.exists(nick_path) else os.path.join(avatar_dir, "name.txt")
        bio_path  = os.path.join(avatar_dir, "bio.txt")

        name_text  = ""
        bio_text   = ""
        photo_path = None

        if use_name and os.path.exists(name_path):
            name_text = _pick_random_nonempty_line(name_path)
            if name_text:
                log(f"Выбран ник: {name_text}", "INFO")

        if use_bio and os.path.exists(bio_path):
            bio_text = _pick_random_nonempty_line(bio_path)
            if bio_text:
                log(f"Выбрано био ({len(bio_text)} симв.): '{bio_text[:60] + (chr(8230) if len(bio_text)>60 else "")}'", "INFO")

        if use_avatar and os.path.isdir(avatar_dir):
            photo_path = _pick_random_image_file(avatar_dir)
            if photo_path:
                log(f"Выбрали аватарку: {photo_path}", "INFO")

        if not any([name_text, bio_text, photo_path]):
            log("Нет данных для изменения профиля, setup_profile пропускается", "INFO")
            return None

        # --- Клик по аватарке ---
        try:
            avatar_btn = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='avatar']"))
            )
            avatar_btn.click()
            log("Клик по avatar", "SUCCESS")
            time.sleep(3)
        except Exception as e:
            log(f"Не удалось кликнуть avatar: {e}", "ERROR")
            return None

        # --- userinfo → берём ссылку на профиль ---
        profile_url = None
        try:
            userinfo_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='userinfo']"))
            )
            userinfo_btn.click()
            log("Клик по userinfo", "SUCCESS")
            time.sleep(2)
            try:
                cur_url = driver.current_url or ""
                if "tango.me" in cur_url:
                    profile_url = cur_url
                    log(f"Ссылка на профиль: {profile_url}", "SUCCESS")
            except Exception:
                pass
        except Exception as e:
            log(f"userinfo не найден: {e}", "WARNING")

        # --- edit-profile ---
        try:
            edit_btn = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='edit-profile']"))
            )
            edit_btn.click()
            log("Клик по edit-profile", "SUCCESS")
            time.sleep(4)
        except Exception as e:
            log(f"edit-profile не найден: {e}", "WARNING")
            time.sleep(2)

        # --- Фото ---
        if photo_path:
            try:
                file_input = WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                file_input.send_keys(photo_path)
                log(f"Фото отправлено: {photo_path}", "INFO")
                try:
                    set_btn = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='set-photo-profile-button']"))
                    )
                    set_btn.click()
                    gui("Фото установлено", "OK")
                    log("Фото профиля установлено", "SUCCESS")
                    time.sleep(3)
                except Exception as e:
                    log(f"set-photo-profile-button: {e}", "WARNING")
            except Exception as e:
                log(f"input[type=file]: {e}", "WARNING")

        # --- Ник ---
        if name_text:
            try:
                name_input = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.ID, "name-field"))
                )
                time.sleep(0.5)

                def _set_nick_via_clipboard(text):
                    """Копирует текст в буфер через системную утилиту и вставляет Cmd/Ctrl+V.
                    Единственный 100% способ вставить эмодзи через Selenium."""
                    try:
                        import subprocess as _sp
                        if sys.platform == "darwin":
                            _sp.run("pbcopy", input=text.encode("utf-8"), check=True)
                        else:
                            # Linux: xclip или xdotool
                            try:
                                _sp.run(["xclip", "-selection", "clipboard"],
                                        input=text.encode("utf-8"), check=True)
                            except FileNotFoundError:
                                _sp.run(["xdotool", "type", "--clearmodifiers", text], check=True)
                                return True  # xdotool сам вводит, paste не нужен
                        name_input.click()
                        time.sleep(0.15)
                        mod = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL
                        name_input.send_keys(mod, "a")
                        time.sleep(0.1)
                        name_input.send_keys(Keys.BACKSPACE)
                        time.sleep(0.1)
                        name_input.send_keys(mod, "v")
                        time.sleep(0.4)
                        return True
                    except Exception as _ce:
                        log(f"clipboard вставка: {_ce}", "WARNING")
                        return False

                # Шаг 1: clipboard (pbcopy/xclip) — 100% эмодзи
                _nick_ok = False
                if _set_nick_via_clipboard(name_text):
                    _actual = name_input.get_attribute("value") or ""
                    if _actual.strip():
                        log(f"Ник через clipboard: '{_actual}'", "SUCCESS")
                        _nick_ok = True

                # Шаг 2: clear_and_type (обычный текст без эмодзи)
                if not _nick_ok:
                    clear_and_type(driver, name_input, name_text)
                    time.sleep(0.3)
                    _actual = name_input.get_attribute("value") or ""
                    if _actual.strip():
                        log(f"Ник через clear_and_type: '{_actual}'", "SUCCESS")
                        _nick_ok = True

                # Шаг 3: JS nativeSetter — последний шанс
                if not _nick_ok:
                    try:
                        driver.execute_script(
                            "arguments[0].focus();"
                            "var s=Object.getOwnPropertyDescriptor("
                            "window.HTMLInputElement.prototype,'value').set;"
                            "s.call(arguments[0],arguments[1]);"
                            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));"
                            "arguments[0].dispatchEvent(new KeyboardEvent('keyup',{bubbles:true}));",
                            name_input, name_text
                        )
                        time.sleep(0.3)
                        _actual = name_input.get_attribute("value") or ""
                        if _actual.strip():
                            log(f"Ник через JS nativeSetter: '{_actual}'", "SUCCESS")
                            _nick_ok = True
                    except Exception as _je:
                        log(f"JS nativeSetter: {_je}", "WARNING")

                if _nick_ok:
                    gui(f"Никнейм установлен: {name_text}", "OK")
                else:
                    log(f"Не удалось вставить ник '{name_text}' ни одним способом", "ERROR")
                time.sleep(0.5)
            except Exception as e:
                log(f"Не удалось установить никнейм: {e}", "ERROR")

        # --- Био ---
        if bio_text:
            try:
                bio_input = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "about-me-field"))
                )
                time.sleep(0.5)
                clear_and_type(driver, bio_input, bio_text)
                log("Био установлено", "SUCCESS")
                gui("Био установлено", "OK")
                time.sleep(1)
            except Exception as e:
                log(f"Ошибка установки био: {e}", "ERROR")

        # --- Сохранение (до 3 попыток) ---
        for _attempt in range(1, 4):
            try:
                done_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='done-edit-profile-button']"))
                )
                try:
                    done_btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", done_btn)
                log(f"Нажата done-edit-profile-button (попытка {_attempt})", "SUCCESS")
                gui("Профиль сохранён", "OK")
                time.sleep(2)
                break
            except Exception as e:
                log(f"done-edit-profile-button попытка {_attempt}/3: {e}", "WARNING")
                time.sleep(2)
        log("Настройка профиля завершена", "INFO")
        return profile_url

    except Exception as e:
        log(f"Глобальная ошибка setup_profile: {e}", "ERROR")
        return None


def Block_Dolboeba(driver, block_file_path=None) -> bool:
    """Блокировка пользователей из settings/block.txt.

    Открывает собственную отдельную вкладку, по очереди заходит по ссылкам,
    жмёт more-menu-profile → profile-block-menu-item → confirm, закрывает вкладку.
    """
    block_path = block_file_path or os.path.join(SETTINGS_DIR, "block.txt")

    try:
        if not os.path.exists(block_path):
            log(f"Block_Dolboeba: файл не найден: {block_path}", "WARNING")
            return False

        with open(block_path, "r", encoding="utf-8") as f:
            links = [s.strip() for s in f.read().splitlines()
                     if s.strip() and not s.strip().startswith("#")]

        if not links:
            log("Block_Dolboeba: список пуст (settings/block.txt)", "INFO")
            return True

    except Exception as e:
        log(f"Block_Dolboeba: не смог прочитать settings/block.txt: {e}", "ERROR")
        return False

    def wait_loaded(timeout: int = 25) -> bool:
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except Exception:
            return False

    original_handle = None
    block_handle = None

    try:
        original_handle = driver.current_window_handle
        before = set(driver.window_handles)

        driver.execute_script("window.open('about:blank','_blank');")
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > len(before))
        after = [h for h in driver.window_handles if h not in before]
        block_handle = after[-1] if after else driver.window_handles[-1]
        driver.switch_to.window(block_handle)

        gui(f"Block_Dolboeba: начинаю блок ({len(links)} ссылок)", "INFO")
        log(f"Block_Dolboeba: открыта вкладка -> {len(links)} ссылок", "INFO")

        ok_all = True

        for i, url in enumerate(links, start=1):
            check_stop("Block_Dolboeba loop")
            try:
                log(f"Block_Dolboeba: [{i}/{len(links)}] {url}", "INFO")
                driver.get(url)
                wait_loaded(25)

                if not safe_click(driver, "[data-testid='more-menu-profile']", timeout=15, desc="more-menu-profile"):
                    ok_all = False
                    log(f"Block_Dolboeba: не нашёл more-menu-profile на {url}", "WARNING")
                    continue

                if not safe_click(driver, "[data-testid='profile-block-menu-item']", timeout=15, desc="profile-block-menu-item"):
                    ok_all = False
                    log(f"Block_Dolboeba: не нашёл profile-block-menu-item на {url}", "WARNING")
                    continue

                if not safe_click(driver, "[data-testid='confirm']", timeout=15, desc="confirm"):
                    ok_all = False
                    log(f"Block_Dolboeba: не нашёл confirm на {url}", "WARNING")
                    continue

                log(f"Block_Dolboeba [{i}/{len(links)}]: ✅ заблокировали", "SUCCESS")
                time.sleep(1)

            except StopRequested:
                raise
            except Exception as e:
                ok_all = False
                log(f"Block_Dolboeba: ошибка на {url}: {e}", "ERROR")
                continue

        gui("Block_Dolboeba: готово", "SUCCESS" if ok_all else "WARNING")
        log("Block_Dolboeba: завершено", "SUCCESS" if ok_all else "WARNING")
        return ok_all

    except StopRequested:
        log("Block_Dolboeba: стоп-флаг во время блока", "WARNING")
        return False
    except Exception as e:
        log(f"Block_Dolboeba: критическая ошибка: {e}", "ERROR")
        return False
    finally:
        try:
            if block_handle and block_handle in driver.window_handles:
                driver.switch_to.window(block_handle)
                driver.close()
        except Exception:
            pass
        try:
            if original_handle and original_handle in driver.window_handles:
                driver.switch_to.window(original_handle)
        except Exception:
            pass





def change_profile_late(driver, use_avatar, use_name, use_bio, block_dolboeba=False):
    """Возвращает profile_url (str | None) если setup_profile его нашёл."""
    profile_url = None
    if not any([use_avatar, use_name, use_bio, block_dolboeba]):
        return profile_url

    # Если нужна только блокировка — лишняя вкладка с tango.me не нужна,
    # Block_Dolboeba сам управляет своей вкладкой
    if not any([use_avatar, use_name, use_bio]):
        if block_dolboeba:
            try:
                Block_Dolboeba(driver)
            except Exception as e:
                log(f"Ошибка в Block_Dolboeba: {e}", "ERROR")
        return profile_url

    orig_handle = None
    new_handle  = None
    try:
        orig_handle = driver.current_window_handle
        before = set(driver.window_handles)
        driver.execute_script("window.open('https://tango.me', '_blank');")
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > len(before))
        new_handles = [h for h in driver.window_handles if h not in before]
        if not new_handles:
            log("Не удалось найти новую вкладку для профиля", "ERROR")
            return profile_url
        new_handle = new_handles[0]
        driver.switch_to.window(new_handle)
        # Ждём загрузки страницы — через медленный VPN может занять >5 сек
        try:
            WebDriverWait(driver, 40).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception:
            pass
        # Дополнительно ждём появления avatar на странице (индикатор полной загрузки)
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='avatar']"))
            )
            log("Страница tango.me загружена (avatar найден)", "INFO")
        except Exception:
            log("avatar не появился за 30с — пробуем всё равно", "WARNING")
        time.sleep(2)
        if any([use_avatar, use_name, use_bio]):
            profile_url = setup_profile(driver, use_avatar=use_avatar, use_name=use_name, use_bio=use_bio)
        if block_dolboeba:
            Block_Dolboeba(driver)
        time.sleep(3)
        log("Закрыли вкладку профиля, вернулись к стриму", "SUCCESS")
    except Exception as e:
        log(f"Ошибка в change_profile_late: {e}", "ERROR")
    finally:
        # Гарантируем закрытие вкладки и возврат к основной
        try:
            if new_handle and new_handle in driver.window_handles:
                driver.switch_to.window(new_handle)
                driver.close()
        except Exception:
            pass
        try:
            if orig_handle and orig_handle in driver.window_handles:
                driver.switch_to.window(orig_handle)
        except Exception:
            pass
    return profile_url


def _js_click(driver, el):
    try:
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        return False


def safe_click(driver, css: str, timeout: int = 15, *, desc: str = "", allow_js: bool = True) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
        try:
            el.click()
            return True
        except Exception:
            return _js_click(driver, el) if allow_js else False
    except Exception as e:
        if desc:
            log(f"Не удалось кликнуть {desc}: {e}", "WARNING")
        return False


def safe_type(driver, css: str, text: str, timeout: int = 15, *, desc: str = "") -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
        try:
            el.click()
        except Exception:
            _js_click(driver, el)
        try:
            el.clear()
        except Exception:
            pass
        el.send_keys(text)
        return True
    except Exception as e:
        if desc:
            log(f"Не удалось ввести {desc}: {e}", "ERROR")
        return False


def scroll_down(driver, times: int = 8, pause: float = 0.6):
    for _ in range(max(1, times)):
        try:
            driver.execute_script("window.scrollBy(0, Math.max(400, window.innerHeight * 0.8));")
        except Exception:
            pass
        time.sleep(pause)


def close_stream_with_confirm(driver, *, timeout_btn: int = 30, timeout_confirm: int = 20, where: str = "") -> bool:
    ok = safe_click(driver, "button[data-testid='close-stream-button']", timeout=timeout_btn, desc=f"close-stream-button ({where})")
    if not ok:
        return False
    confirm_selectors = [
        "button[data-testid='confirm']",
        "button[data-testid='confirm-button']",
        "button[data-testid='confirm-close-stream']",
        "button[data-testid='modal-confirm']",
    ]
    for sel in confirm_selectors:
        if safe_click(driver, sel, timeout=timeout_confirm, desc=f"confirm ({where})", allow_js=True):
            return True
    try:
        btn = WebDriverWait(driver, timeout_confirm).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[normalize-space()='Confirm' or normalize-space()='Yes' or normalize-space()='OK' or normalize-space()='Да' or normalize-space()='ОК']"
            ))
        )
        try:
            btn.click()
        except Exception:
            _js_click(driver, btn)
        return True
    except Exception:
        log(f"Не нашли кнопку подтверждения закрытия стрима ({where})", "WARNING")
        return False


def pulsz_login_by_email(driver, email: str, cfg: dict) -> bool:
    driver.get('https://www.pulsz.tv/')
    time.sleep(20)
    clicked_join = safe_click(driver, "[data-testid='join-now']", timeout=10, desc='join-now')
    time.sleep(1)
    if not safe_click(driver, "button[data-testid='EMAIL_OTP']", timeout=15, desc='EMAIL_OTP'):
        return False
    if not safe_type(driver, "input[data-testid='login-with-email-input-email']", email, timeout=15, desc='email (pulsz)'):
        return False
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, "button[data-testid='login-with-email-continue-button']").click()
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='digit-input-0']")))
    except Exception as e:
        log(f'Не дождались полей кода на pulsz: {e}', 'ERROR')
        return False
    code = get_pulsz_code_from_file(email, timeout=cfg.get('email_check_timeout_sec', 240))
    if not code:
        log('Код для pulsz не получен', 'ERROR')
        return False
    digits = list(code.strip())
    for idx, d in enumerate(digits):
        sel = f"input[data-testid='digit-input-{idx}']"
        try:
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).send_keys(d)
        except Exception as e:
            log(f'Ошибка ввода кода pulsz: {e}', 'ERROR')
            return False
    time.sleep(2)
    gui(f'Pulsz: авторизация успешна для {email}', 'OK')
    return True


def pulsz_start_and_close_broadcast(driver) -> bool:
    driver.get("https://www.pulsz.tv/broadcast")
    try:
        WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
    except Exception:
        pass
    time.sleep(4)
    safe_click(driver, "button[data-testid='permission-confirm-button']", timeout=10, desc="permission-confirm-button (pulsz)")
    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='audio-button']")))
    except Exception:
        time.sleep(5)
    if not safe_click(driver, "button[data-testid='audio-button']", timeout=15, desc="audio-button (pulsz)"):
        return False
    time.sleep(2)
    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='go-live-button']")))
    except Exception:
        pass
    if not safe_click(driver, "button[data-testid='go-live-button']", timeout=20, desc="go-live-button (pulsz)"):
        return False
    gui("Pulsz: стрим начат", "INFO")
    time.sleep(60)
    close_stream_with_confirm(driver, where="pulsz")
    gui("Pulsz: стрим завершён", "INFO")
    return True


def tango_enable_ai_settings(driver) -> bool:
    from selenium.webdriver.common.action_chains import ActionChains
    driver.get("https://tango.me/settings")
    time.sleep(3)
    try:
        el = driver.find_element(By.CSS_SELECTOR, "div.y3eBY")
        try:
            el.click()
        except Exception:
            _js_click(driver, el)
        time.sleep(1)
    except Exception as e:
        log(f"Не нашли div.y3eBY: {e}", "WARNING")

    def _space_scroll(times: int = 12, pause: float = 0.7):
        for _ in range(times):
            try:
                ActionChains(driver).send_keys(Keys.SPACE).perform()
            except Exception:
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)
                except Exception:
                    pass
            time.sleep(pause)

    _space_scroll(times=12, pause=0.7)
    log("Ждём 40 секунд на прогрузку настроек (AI)", "INFO")
    time.sleep(40)
    try:
        driver.refresh()
    except Exception:
        pass
    time.sleep(3)
    _space_scroll(times=12, pause=0.7)
    toggles = []
    try:
        container = driver.find_element(By.CSS_SELECTOR, "div.c5IBi")
        toggles = container.find_elements(By.CSS_SELECTOR, "[role='switch'][aria-checked='false'][data-testid='']")
        if not toggles:
            toggles = container.find_elements(By.CSS_SELECTOR, "[aria-checked='false'][data-testid='']")
        if not toggles:
            toggles = container.find_elements(By.CSS_SELECTOR, "[role='switch'][aria-checked='false']")
        if not toggles:
            toggles = container.find_elements(By.CSS_SELECTOR, "[aria-checked='false']")
    except Exception as e:
        log(f"Не нашли контейнер c5IBi: {e}", "WARNING")
        toggles = []
    if toggles:
        try:
            toggles[0].click()
        except Exception:
            _js_click(driver, toggles[0])
        log("AI тумблер включён", "SUCCESS")
        gui("AI: включили тумблер", "OK")
        time.sleep(2)
    else:
        log("Не нашли AI тумблер — возможно уже включён", "WARNING")
    opened = safe_click(driver, "button[data-testid='button-ai-advanced-settings']", timeout=10, desc="button-ai-advanced-settings")
    if not opened:
        opened = safe_click(driver, "div.fqdMq", timeout=10, desc="div.fqdMq (AI settings)")
    if not opened:
        log("Не удалось открыть AI advanced settings", "ERROR")
        return False
    time.sleep(2)
    try:
        plus_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='plus-button']")
    except Exception:
        plus_buttons = []
    if len(plus_buttons) < 2:
        log(f"Ожидали 2 кнопки plus-button, нашли: {len(plus_buttons)}", "WARNING")
    else:
        plus_buttons_sorted = sorted(plus_buttons, key=lambda el: el.location.get('y', 0))
        top_btn = plus_buttons_sorted[0]
        bottom_btn = plus_buttons_sorted[-1]
        for _ in range(4):
            try:
                top_btn.click()
            except Exception:
                _js_click(driver, top_btn)
            time.sleep(0.25)
        for _ in range(8):
            try:
                bottom_btn.click()
            except Exception:
                _js_click(driver, bottom_btn)
            time.sleep(0.25)
        log("AI advanced settings: +4 сверху и +8 снизу", "SUCCESS")
        gui("AI: advanced settings настроены", "OK")
    safe_click(driver, "button[data-testid='button-ai-advanced-settings-close']", timeout=10, desc="button-ai-advanced-settings-close")
    time.sleep(1)
    gui("AI: настройки применены", "OK")
    return True


def _wait_page_fully_loaded(driver, timeout: float = 90.0, label: str = ""):
    """
    Ждёт полной загрузки страницы: readyState=complete.
    Толерантна к медленному VPN/прокси — не крашится, просто ждёт.
    """
    pfx = f"[{label}] " if label else ""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = driver.execute_script("return document.readyState")
            if state == "complete":
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        log(f"{pfx}readyState не стал complete за {timeout}с — продолжаем", "WARNING")


def _wait_media_ready(driver, timeout: float = 60.0, label: str = ""):
    """
    Ждёт готовности камеры/микрофона (video.srcObject.active).
    Если камера не загрузилась за timeout — предупреждает, но продолжает.
    """
    pfx = f"[{label}] " if label else ""
    check_script = """
    try {
        var videos = document.querySelectorAll('video');
        for (var i = 0; i < videos.length; i++) {
            var v = videos[i];
            if (v.srcObject && v.srcObject.active && v.readyState >= 2) return 'ready';
            if (v.srcObject && v.srcObject.active) return 'loading';
        }
        return videos.length > 0 ? 'waiting' : 'none';
    } catch(e) { return 'error'; }
    """
    last_state = ""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = driver.execute_script(check_script)
            if state != last_state:
                log(f"{pfx}Медиа: {state}", "INFO")
                last_state = state
            if state == "ready":
                log(f"{pfx}Камера/видео готова", "SUCCESS")
                return True
        except Exception:
            pass
        time.sleep(1.5)
    log(f"{pfx}Медиа не стала ready за {timeout}с — продолжаем", "WARNING")
    return False


def _safe_navigate(driver, url: str, timeout: float = 120.0, retries: int = 3, label: str = "") -> bool:
    """
    Навигация с ретраями при TimeoutException / WebDriverException.
    Если страница частично загружена (readyState=interactive) — считаем ОК.
    """
    pfx = f"[{label}] " if label else ""
    for attempt in range(1, retries + 1):
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            _wait_page_fully_loaded(driver, timeout=min(timeout, 60), label=label)
            return True
        except TimeoutException:
            log(f"{pfx}Таймаут загрузки {url} (попытка {attempt}/{retries})", "WARNING")
            try:
                state = driver.execute_script("return document.readyState")
                if state in ("interactive", "complete"):
                    log(f"{pfx}Страница частично загружена (readyState={state}) — продолжаем", "INFO")
                    return True
            except Exception:
                pass
            if attempt < retries:
                time.sleep(3)
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
                time.sleep(2)
        except WebDriverException as e:
            log(f"{pfx}WebDriver ошибка навигации: {e} (попытка {attempt}/{retries})", "ERROR")
            if attempt < retries:
                time.sleep(5)
        except Exception as e:
            log(f"{pfx}Ошибка навигации: {e}", "ERROR")
            if attempt < retries:
                time.sleep(3)
    return False


def tango_start_stream_from_broadcast(driver) -> float | None:
    if not _safe_navigate(driver, "https://tango.me/broadcast", timeout=120, retries=3, label="broadcast"):
        log("tango_start_stream: не открылся /broadcast после всех попыток", "ERROR")
        return None
    time.sleep(5)  # увеличено с 3 до 5 — VPN замедляет загрузку страницы
    safe_click(driver, "button[data-testid='permission-confirm-button']", timeout=40, desc="permission-confirm-button (tango)")
    try:
        WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='audio-button']")))
    except Exception:
        time.sleep(5)
    # Ждём готовности камеры (не блокирует если камера уже готова)
    _wait_media_ready(driver, timeout=30, label="pre-stream")
    # Звук НЕ выключаем
    time.sleep(2)
    try:
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='go-live-button']")))
    except Exception:
        pass
    if not safe_click(driver, "button[data-testid='go-live-button']", timeout=20, desc="go-live-button (tango)"):
        return None
    return time.time()


def run_ai_activation_flow(driver, email: str, cfg: dict, pause_timer, resume_timer) -> bool:
    base_handle = driver.current_window_handle
    pulsz_handle = None
    pause_timer()
    gui("AI: старт процедуры Pulsz → Tango AI", "INFO")
    try:
        try:
            driver.execute_script("window.open('about:blank', '_blank');")
            WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) >= 2)
            handles = driver.window_handles
            pulsz_handle = [h for h in handles if h != base_handle][-1]
        except Exception as e:
            log(f"AI: не удалось открыть вкладку для pulsz: {e}", "ERROR")
            return False
        driver.switch_to.window(pulsz_handle)
        log("AI: пробуем логин в pulsz.tv", "INFO")
        if not pulsz_login_by_email(driver, email, cfg):
            log("AI: pulsz login не удался — продолжаем стрим Tango", "WARNING")
            try:
                driver.close()
            except Exception:
                pass
            try:
                driver.switch_to.window(base_handle)
            except Exception:
                pass
            return False
        log("AI: pulsz login OK", "SUCCESS")
        gui("AI: Pulsz авторизация OK", "OK")
        driver.switch_to.window(base_handle)
        log("AI: закрываем текущий Tango-стрим", "INFO")
        if not close_stream_with_confirm(driver, where="tango"):
            log("AI: не удалось закрыть Tango-стрим", "ERROR")
            try:
                if pulsz_handle and pulsz_handle in driver.window_handles:
                    driver.switch_to.window(pulsz_handle)
                    driver.close()
            except Exception:
                pass
            try:
                driver.switch_to.window(base_handle)
            except Exception:
                pass
            return False
        try:
            driver.switch_to.window(pulsz_handle)
            log("AI: запускаем pulsz broadcast", "INFO")
            try:
                pulsz_start_and_close_broadcast(driver)
            except Exception as e:
                log(f"AI: pulsz broadcast не удался: {e}", "WARNING")
        finally:
            try:
                driver.close()
            except Exception:
                pass
        driver.switch_to.window(base_handle)
        log("AI: включаем AI в Tango settings", "INFO")
        try:
            tango_enable_ai_settings(driver)
        except Exception as e:
            log(f"AI: не удалось включить AI в настройках: {e}", "WARNING")
        log("AI: запускаем новый стрим на tango", "INFO")
        new_start = tango_start_stream_from_broadcast(driver)
        if not new_start:
            try:
                driver.refresh()
                time.sleep(3)
            except Exception:
                pass
            new_start = tango_start_stream_from_broadcast(driver)
        if not new_start:
            log("AI: так и не удалось запустить новый стрим", "ERROR")
            return False
        log("AI: новый Tango-стрим запущен", "SUCCESS")
        gui("AI: повторный стрим Tango запущен", "OK")
        return True
    finally:
        try:
            resume_timer()
        except Exception:
            pass


# ========================================================================================
#                                       MAIN
# ========================================================================================

def load_config():
    cfg_path = os.path.join(BASE_DIR, "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        try:
            gui(f"❌ Не удалось прочитать config.json: {e}", "ERROR")
        except Exception:
            pass
        log(f"Не удалось прочитать config.json ({cfg_path}): {e}", "ERROR")
        raise SystemExit(1)


def click_if_present(driver, selector: str, timeout: float = 2.5) -> bool:
    end = time.time() + float(timeout)
    while True:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in els[::-1]:
                try:
                    if not el.is_displayed() or not el.is_enabled():
                        continue
                    try:
                        el.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", el)
                        except Exception:
                            continue
                    return True
                except Exception:
                    continue
        except Exception:
            pass
        if time.time() >= end:
            return False
        time.sleep(0.15)


def dismiss_onetrust(driver) -> None:
    """Закрывает OneTrust/GDPR cookie banner — он перекрывает кнопки на европейских локалях."""
    try:
        _ot_btn = driver.find_element(
            By.CSS_SELECTOR,
            "#onetrust-accept-btn-handler, #onetrust-reject-all-handler, "
            ".onetrust-close-btn-handler, button#accept-recommended-btn-handler"
        )
        driver.execute_script("arguments[0].click();", _ot_btn)
        log("OneTrust banner закрыт (кнопка)", "INFO")
        time.sleep(0.5)
    except Exception:
        pass
    try:
        driver.execute_script(
            "['onetrust-banner-sdk','onetrust-button-group-parent',"
            "'onetrust-consent-sdk','onetrust-pc-sdk'].forEach(function(id){"
            "  var el=document.getElementById(id); if(el) el.style.display='none';"
            "});"
        )
    except Exception:
        pass


def dismiss_email_marketing(driver, timeout: float = 8.0, log_prefix: str = "") -> bool:
    # Сначала убираем OneTrust если висит
    try:
        dismiss_onetrust(driver)
    except Exception:
        pass
    selectors = [
        "button[data-testid='email-marketing-confirm-cancel']",
        "[data-testid='email-marketing-confirm-cancel']",
        "button[aria-label*='No thanks' i]",
        "button[aria-label*='Not now' i]",
        "button[aria-label*='Skip' i]",
        "button:has(svg)",
    ]
    overlay_selectors = [
        "button[data-testid='email-marketing-confirm-cancel']",
        "[data-testid='email-marketing-confirm-cancel']",
        "[data-testid='email-marketing-confirm']",
        "div[role='dialog']",
    ]
    deadline = time.time() + float(timeout)
    while time.time() < deadline:
        for selector in selectors:
            if click_if_present(driver, selector, timeout=0.6):
                end_confirm = time.time() + 2.5
                while time.time() < end_confirm:
                    still_visible = False
                    try:
                        for ov in overlay_selectors:
                            els = driver.find_elements(By.CSS_SELECTOR, ov)
                            if any(getattr(el, 'is_displayed', lambda: False)() for el in els):
                                still_visible = True
                                break
                    except Exception:
                        pass
                    if not still_visible:
                        log(f"Нажата отмена маркетинга ({selector})", "SUCCESS")
                        return True
                    time.sleep(0.15)
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.25)
    log("Email marketing cancel не закрылся — обновляю страницу", "INFO")
    try:
        driver.refresh()
        time.sleep(2)
    except Exception as e:
        log(f"Не удалось обновить страницу после маркетинга: {e}", "WARNING")
    return False


def cleanup_before_start():
    """
    Очистка рабочих папок перед стартом нового цикла.
    Удаляет: profiles/, mails/, work/, _proxy_ext/, logs/run.log.1
    НЕ удаляет: cashout/ (ценные аккаунты), settings/, avatar/, db/
    """
    cleanup_dirs = [
        PATH_PROFILES,                             # profiles/
        PATH_MAILS,                                # mails/
        os.path.join(PATH_MAILS, "pulsz"),         # mails/pulsz/
        os.path.join(BASE_DIR, "work"),            # work/
        os.path.join(BASE_DIR, "_proxy_ext"),      # _proxy_ext/
    ]
    total_removed = 0
    for dirpath in cleanup_dirs:
        if not os.path.isdir(dirpath):
            continue
        try:
            items = os.listdir(dirpath)
            for item in items:
                full = os.path.join(dirpath, item)
                try:
                    if os.path.isdir(full):
                        shutil.rmtree(full, ignore_errors=True)
                        total_removed += 1
                    elif os.path.isfile(full):
                        os.remove(full)
                        total_removed += 1
                except Exception:
                    pass
        except Exception:
            pass
    # Удаляем старый backup лога
    try:
        backup_log = LOG_PATH + ".1"
        if os.path.exists(backup_log):
            os.remove(backup_log)
    except Exception:
        pass
    if total_removed:
        log(f"🧹 Очистка перед стартом: удалено {total_removed} файлов/папок", "INFO")
    else:
        log("🧹 Очистка перед стартом: нечего удалять", "INFO")


def main():
    global _BYPASS_STOP
    driver = None
    email = None
    lock_acquired = False
    otp_gate_acquired = False

    def safe_release_lock():
        nonlocal lock_acquired
        if lock_acquired:
            try:
                release_register_lock()
            except Exception:
                pass
            lock_acquired = False

    def safe_release_otp_gate():
        nonlocal otp_gate_acquired
        if otp_gate_acquired:
            try:
                release_otp_gate()
            except Exception:
                pass
            otp_gate_acquired = False

    cfg = load_config()
    profile_url = ""   # будет обновляться по ходу, используется во всех уведомлениях

    # ── Очистка рабочих папок перед стартом ──────────────────────────────────
    try:
        cleanup_before_start()
    except Exception as _clean_err:
        log(f"Ошибка очистки: {_clean_err}", "WARNING")

    runtime_preview = parse_runtime_args(sys.argv)
    if not runtime_preview.get("email"):
        acquire_register_lock()
        lock_acquired = True

    if not (cfg.get('tango_ref_url') or '').strip():
        gui('❌ В config.json отсутствует tango_ref_url', 'ERROR')
        log('В config.json отсутствует tango_ref_url', 'ERROR')
        raise SystemExit(1)
    if not (cfg.get('email_domain') or '').strip():
        # Проверяем также новый формат email_domains (до 13 штук)
        _domains_check = list(cfg.get('email_domains') or [])
        if not _domains_check:
            for _ci in range(1, 14):
                _ck = "email_domain" if _ci == 1 else f"email_domain{_ci}"
                if (cfg.get(_ck) or '').strip():
                    _domains_check.append(cfg[_ck])
        if not _domains_check:
            gui('❌ В config.json отсутствует email_domain', 'ERROR')
            log('В config.json отсутствует email_domain', 'ERROR')
            raise SystemExit(1)
    if 'email_check_timeout_sec' not in cfg:
        cfg['email_check_timeout_sec'] = 240
        log('email_check_timeout_sec не задан — использую 240 сек', 'WARNING')

    runtime = runtime_preview  # reuse already-parsed args (no duplicate parse)

    wait_time       = int(runtime.get("wait_time") or 750)
    profile_change_delay = 5
    gift_option     = str(runtime.get("gift_option") or "").strip()
    use_avatar      = bool(runtime.get("use_avatar"))
    use_name        = bool(runtime.get("use_name"))
    use_bio         = bool(runtime.get("use_bio"))
    activate_ai     = bool(runtime.get("activate_ai"))
    block_dolboeba  = bool(runtime.get("block_dolboeba"))
    proxy_spec      = runtime.get("proxy_spec")
    profile_num     = runtime.get("profile_num")
    otp_min_delay   = float(runtime.get("otp_min_delay") or 0.0)
    vpn_country     = str(runtime.get("vpn_country") or "").strip() or "—"

    log(f"Время ожидания: {wait_time} секунд", "INFO")
    if gift_option:
        log(f"Тип подарка: {gift_option}", "INFO")
    log(f"Настройки профиля: avatar={use_avatar}, name={use_name}, bio={use_bio}, ai={activate_ai}, block={block_dolboeba}, profile_num={profile_num}", "INFO")

    block_done = False

    try:
        if any([use_avatar, use_name, use_bio, block_dolboeba]) and int(wait_time) < int(profile_change_delay) + 20:
            new_delay = max(5, min(30, int(int(wait_time) * 0.3)))
            if new_delay != profile_change_delay:
                profile_change_delay = new_delay
    except Exception:
        pass

    forced_email = str(runtime.get("email") or "").strip()
    if forced_email:
        email = forced_email
        log(f"Использую email из аргумента: {email}", "INFO")
    else:
        email = get_next_email(total_target=runtime.get("total_target"))

    if profile_num is None:
        profile_num = infer_profile_num_from_email(email)

    check_stop("after_email")
    safe_release_lock()

    profile_path = profile_dir_for_runtime(profile_num, email)
    write_profile_metadata(profile_path, email=email, profile_num=profile_num)

    padded = format_profile_num(profile_num)
    if padded:
        gui(f"Профиль #{profile_num} ({padded}): {profile_path}", "INFO")

    # Вайп профиля — device_profile.json и user_agent.txt удаляются (новый отпечаток каждый раз)
    wipe_profile_for_fresh_start(profile_path)
    log("🧹 Профиль вайпнут", "INFO")

    # Загружаем / создаём device_profile ДО запуска браузера
    device_profile = reset_device_fingerprint(profile_path)  # Новый отпечаток при каждом запуске
    if device_profile:
        _os_hint = "Windows" if device_profile.get("is_windows") else "Mac"
        log(
            f"🎭 Device profile: OS={_os_hint}, token={device_profile.get('fp_token','?')}, "
            f"tz={device_profile.get('tz_name')}, lang={device_profile.get('language')}, "
            f"screen={device_profile.get('screen_w')}x{device_profile.get('screen_h')}, "
            f"cores={device_profile.get('cores')}, mem={device_profile.get('memory')}GB",
            "INFO"
        )
        gui(
            f"Device: {_os_hint} | "
            f"{device_profile.get('screen_w')}x{device_profile.get('screen_h')} | "
            f"{device_profile.get('tz_name')} | {device_profile.get('language')}",
            "INFO"
        )
    else:
        device_profile = None

    # ── Глубокая очистка файлов профиля ДО запуска Chrome ─────────────────
    # Удаляем History, Cookies, LocalStorage, IndexedDB, Cache — всё что
    # могло остаться от предыдущей сессии (tracking токены, fingerprints)
    try:
        purge_profile_tracking_data(profile_path)
    except Exception as _ppe:
        log(f"purge_profile: {_ppe}", "WARNING")

    # Запускаем Chrome с device_profile
    driver = create_driver(profile_path, proxy_spec=proxy_spec, device_profile=device_profile)

    # === Очищаем браузерное состояние через CDP + JS (тройная защита) ===
    try:
        driver.get("about:blank")
        _ORIG_SLEEP(0.5)
        clear_all_browser_state(driver)
        log("🧹 Браузерное состояние очищено (CDP+JS)", "INFO")
    except Exception as _ce:
        log(f"Очистка браузера перед стримом: {_ce}", "WARNING")
    # CDP Storage.clearDataForOrigin (удаляет IndexedDB/Cache/SW на уровне CDP)
    for _origin in ["https://tango.me", "https://www.tango.me"]:
        try:
            driver.execute_cdp_cmd("Storage.clearDataForOrigin", {
                "origin": _origin,
                "storageTypes": "all"
            })
        except Exception:
            pass

    def is_dead():
        try:
            alert = driver.find_elements(By.CSS_SELECTOR, "[data-testid='alert-modal']")
            suspended = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='user-suspended-view']")
            if alert or suspended:
                log("Обнаружены признаки смерти аккаунта!", "ERROR")
                return True
        except Exception as e:
            log(f"Ошибка проверки статуса: {e}", "ERROR")
        return False

    try:
        ok = perform_email_login(driver, cfg, email)
        if not ok:
            log("Первая попытка логина провалена", "ERROR")
            safe_release_lock()
            driver.quit()
            return

        otp_ready = False
        for attempt in range(2):
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='digit-input-0']"))
                )
                log(f"Окно ввода кода появилось (попытка {attempt+1})", "SUCCESS")
                otp_ready = True
                break
            except Exception as e:
                log(f"Окно ввода кода не появилось (попытка {attempt+1}): {e}", "WARNING")
                if attempt == 0:
                    clear_browser_data(driver)
                    ok = perform_email_login(driver, cfg, email)
                    if not ok:
                        log("Повторный логин не удался", "ERROR")
                        safe_release_lock()
                        driver.quit()
                        return
                else:
                    log("После двух попыток OTP не появился. Выходим.", "ERROR")
                    safe_release_lock()
                    driver.quit()
                    return

        if not otp_ready:
            safe_release_lock()
            driver.quit()
            return

        # ── OTP GATE: занимаем слот и ждём минимального интервала ──────────
        log(f"OTP gate: запрашиваем слот (мин. пауза {otp_min_delay:.0f}с)...", "INFO")
        try:
            acquire_otp_gate(otp_min_delay)
            otp_gate_acquired = True
        except StopRequested:
            safe_release_lock()
            driver.quit()
            return
        except Exception as _og_err:
            log(f"OTP gate ошибка: {_og_err}", "WARNING")
            # Не блокируем — продолжаем без гейта

        log("Ожидаем код из почты (IMAP + file)...", "INFO")
        code = get_tango_code(cfg, email, timeout=cfg.get('email_check_timeout_sec', 240))
        if not code:
            log("Код не получен", "ERROR")
            safe_release_otp_gate()
            safe_release_lock()
            driver.quit()
            return

        # Чистим код от лишнего (пробелы, дефисы)
        code_clean = re.sub(r"[^0-9]", "", code.strip())
        digits = list(code_clean)
        log(f"Вводим код: {digits} (из '{code.strip()}', длина={len(digits)})", "INFO")

        if not digits:
            log("Код пустой после очистки — выходим", "ERROR")
            safe_release_lock()
            driver.quit()
            return

        # Ждём появления первого поля — убеждаемся что форма готова
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='digit-input-0']"))
            )
        except Exception:
            log("Поля digit-input не найдены перед вводом кода", "WARNING")

        try:
            for idx, digit in enumerate(digits):
                # Не пытаемся вводить за пределы длины кода
                selector = f"input[data-testid='digit-input-{idx}']"
                els = driver.find_elements(By.CSS_SELECTOR, selector)
                if not els:
                    log(f"Поле digit-input-{idx} не найдено — код введён частично ({idx} цифр)", "WARNING")
                    break
                inp_d = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                # Кликаем по-человечески (случайный оффсет от центра)
                try:
                    human_move_and_click(driver, inp_d)
                except Exception:
                    try:
                        inp_d.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", inp_d)
                _human_sleep(80, 160)
                try:
                    inp_d.clear()
                except Exception:
                    pass
                # Вводим цифру с человеческой паузой (как будто читаем код)
                _human_sleep(120, 350)
                inp_d.send_keys(digit)
                # Проверяем что цифра вписалась
                _human_sleep(60, 100)
                try:
                    val = inp_d.get_attribute("value")
                    if val != digit:
                        driver.execute_script(
                            "arguments[0].value=arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                            inp_d, digit
                        )
                except Exception:
                    pass
                # Пауза между цифрами — нормальное распределение
                _human_sleep(90, 220)
        except Exception as e:
            log(f"Ошибка ввода кода: {e}", "ERROR")
            safe_release_lock()
            driver.quit()
            return

        time.sleep(1)
        # ── Освобождаем OTP gate — следующий поток может вводить код ────────
        safe_release_otp_gate()
        gui(f"[READY_NEXT] Код введён для {email}", "OK")
        time.sleep(2)

        marketing_cancel_clicked = dismiss_email_marketing(driver, timeout=8.0)

        time.sleep(1)
        gui(f"[ACCOUNT_CREATED] Создали аккаунт {email}", "OK")

        # Закрываем OneTrust/cookie consent banner если перекрывает кнопки
        try:
            _ot_btn = driver.find_element(
                By.CSS_SELECTOR,
                "#onetrust-accept-btn-handler, #onetrust-reject-all-handler, "
                ".onetrust-close-btn-handler, button#accept-recommended-btn-handler"
            )
            driver.execute_script("arguments[0].click();", _ot_btn)
            log("OneTrust banner закрыт (кнопка)", "INFO")
            time.sleep(1)
        except Exception:
            pass
        # Принудительно скрываем OneTrust через JS (на случай если кнопка не сработала)
        try:
            driver.execute_script(
                "['onetrust-banner-sdk','onetrust-button-group-parent',"
                "'onetrust-consent-sdk','onetrust-pc-sdk'].forEach(function(id){"
                "  var el=document.getElementById(id); if(el) el.style.display='none';"
                "});"
            )
        except Exception:
            pass

        try:
            btn_sidebar = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-testid='broadcast-button-sidebar']"))
            )
            try:
                btn_sidebar.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn_sidebar)
            log("Нажата broadcast-button-sidebar", "SUCCESS")
            # Вход подтверждён — mail-файл точно больше не нужен
            try:
                cleanup_mail_file(email)
            except Exception:
                pass
        except Exception as e:
            log(f"broadcast-button-sidebar ERROR: {e}", "ERROR")
            driver.quit()
            return

        try:
            WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except Exception:
            pass
        time.sleep(4)

        # Кнопка разрешений камеры/микрофона
        # Ждём до 50 сек — через VPN страница грузится дольше, кнопка может появиться позже
        try:
            _perm_btn = WebDriverWait(driver, 50).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='permission-confirm-button']"))
            )
            try:
                _perm_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", _perm_btn)
            log("Разрешение камеры/микрофона подтверждено", "SUCCESS")
            time.sleep(1)
        except Exception:
            log("permission-confirm-button не появилась — разрешения уже выданы или не требуются", "INFO")

        # Ждём audio-button — индикатор что страница трансляции готова
        try:
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='audio-button']"))
            )
            log("Страница трансляции готова (audio-button)", "INFO")
        except Exception:
            log("audio-button не появился за 30с — продолжаем", "WARNING")
            time.sleep(5)

        # Звук НЕ выключаем — оставляем микрофон включённым

        time.sleep(2)

        # Ждём готовности камеры перед go-live
        _wait_media_ready(driver, timeout=40, label="main-pre-stream")

        # Ждём go-live-button
        try:
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='go-live-button']"))
            )
        except Exception:
            pass

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='go-live-button']"))
            ).click()
            log("Нажата go-live-button, стрим начинается", "SUCCESS")
            gui(f"Начали стрим для {email}", "OK")
        except Exception as e:
            log(f"go-live-button ERROR: {e}", "ERROR")
            driver.quit()
            return

        stream_clock_start = time.time()
        stream_pause_total = 0.0
        stream_pause_started_at = None
        ai_in_progress = False
        ai_attempted = False
        profile_ops_lock = threading.Lock()

        def pause_stream_timer():
            nonlocal stream_pause_started_at
            if stream_pause_started_at is None:
                stream_pause_started_at = time.time()

        def resume_stream_timer():
            nonlocal stream_pause_total, stream_pause_started_at
            if stream_pause_started_at is not None:
                stream_pause_total += time.time() - stream_pause_started_at
                stream_pause_started_at = None

        def elapsed_stream():
            now = time.time()
            extra = (now - stream_pause_started_at) if stream_pause_started_at is not None else 0.0
            return now - stream_clock_start - stream_pause_total - extra

        safe_release_lock()
        time.sleep(40)

        send_gift(driver, gift_option)

        if activate_ai and (not ai_attempted):
            log("activate_ai=True: ждём 700 секунд стрима и активируем AI", "INFO")
            while True:
                if elapsed_stream() >= 700:
                    break
                if is_dead():
                    log("Аккаунт умер до AI-активации", "ERROR")
                    try:
                        driver.quit()
                    except:
                        pass
                    return
                time.sleep(30)
            ai_attempted = True
            ai_in_progress = True
            with profile_ops_lock:
                ok_ai = run_ai_activation_flow(driver, email, cfg, pause_stream_timer, resume_stream_timer)
            ai_in_progress = False
            if ok_ai:
                log("AI: активация завершена успешно", "SUCCESS")
                send_gift(driver, gift_option)
            else:
                log("AI: не удались — продолжаем стрим без остановки", "WARNING")

        log(f"Ждём {wait_time} секунд (от старта стрима)", "INFO")
        profile_changed = False
        _profile_url_from_setup = None  # ссылка из setup_profile → userinfo
        loop_tick = 10
        while True:
            elapsed = elapsed_stream()
            if (not profile_changed) and (not ai_in_progress) and any([use_avatar, use_name, use_bio, block_dolboeba]) and elapsed >= profile_change_delay:
                log(f"Прошло ≥ {profile_change_delay} сек, меняем профиль в новой вкладке", "INFO")
                with profile_ops_lock:
                    _profile_url_from_setup = change_profile_late(driver, use_avatar, use_name, use_bio, (block_dolboeba and (not block_done)))
                # Помечаем как выполненное только если не была критическая ошибка вкладок
                profile_changed = True
                if block_dolboeba and (not block_done):
                    block_done = True
            if elapsed >= wait_time:
                break
            time.sleep(loop_tick)
            if is_dead():
                log("Аккаунт умер во время ожидания", "ERROR")
                try:
                    driver.quit()
                except:
                    pass
                return

        log("Ожидание стрима завершено, аккаунт жив.", "SUCCESS")

        diamonds, profile_url = get_diamonds(driver)
        # Приоритет: ссылка из setup_profile (userinfo) > ссылка из get_diamonds (avatar)
        profile_url = _profile_url_from_setup or profile_url
        gui(f"Получили алмазы для {email}: {diamonds}", "INFO")

        try:
            if diamonds >= 3000:
                target_dir = os.path.join(BASE_DIR, "cashout")
                log(f"Алмазов {diamonds} ≥ 3000, сохраняем в cashout", "SUCCESS")
            else:
                target_dir = os.path.join(BASE_DIR, "work")
                log(f"Алмазов {diamonds} < 3000, сохраняем в work", "INFO")
            os.makedirs(target_dir, exist_ok=True)
            safe_email = re.sub(r'[\\/:*?"<>|]', "_", email)
            fname = f"{safe_email}_{diamonds}.txt"
            fpath = os.path.join(target_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(email)
            log(f"Создан файл аккаунта: {fpath}", "SUCCESS")
            try:
                from datetime import datetime as _dt
                acc = (email.strip() if email else "unknown")
                folder_icon = "💰" if os.path.basename(target_dir) == "cashout" else "📁"
                now_str = _dt.now().strftime("%d.%m.%Y %H:%M")
                _link_line = f"🔗 <b>Профиль:</b> {profile_url}\n" if profile_url else ""
                tg_send_message(cfg,
                    f"✅ <b>Стрим завершён!</b>\n━━━━━━━━━━━━━━━━━━\n"
                    f"📧 <b>Аккаунт:</b> <code>{acc}</code>\n"
                    f"💎 <b>Алмазы:</b> {diamonds}\n"
                    f"{_link_line}"
                    f"{folder_icon} <b>Папка:</b> {target_dir}\n"
                    f"🌍 <b>VPN страна:</b> {vpn_country}\n"
                    f"🌐 <b>IP:</b> <code>{get_public_ip()}</code>\n"
                    f"🕐 <b>Время:</b> {now_str}"
                )
            except Exception:
                pass
            try:
                acc = (email.strip() if email else "unknown")
                append_gsheets_row(cfg, acc, diamonds, note="алмазы после стрима", profile_url=(profile_url or ""), vpn_country=(vpn_country or ""), ip=get_public_ip())
            except Exception as e:
                log(f"GSHEETS: ошибка записи: {e}", "ERROR")
            try:
                notify_my_service(cfg, {"email": (email or ""), "diamonds": diamonds, "profile": profile_num}, event="stream_finished", retries=2)
            except Exception:
                pass
        except Exception as e:
            log(f"Ошибка создания файла результата: {e}", "ERROR")

        # === Очистка ПОСЛЕ стрима ===
        try:
            clear_all_browser_state(driver)
            log("🧹 Браузерное состояние очищено после стрима", "INFO")
        except Exception as _ce2:
            log(f"Очистка после стрима: {_ce2}", "WARNING")

        log("Ждём 10 секунд перед закрытием...", "INFO")
        time.sleep(10)
        try:
            driver.quit()
        except:
            pass
        # Профиль отработал — удаляем, освобождаем место на диске
        try:
            cleanup_profile(profile_path)
        except Exception:
            pass
        # ── Случайная пауза между стримами (анти-паттерн частоты) ────────
        # Если в конфиге задан inter_stream_delay_sec — ждём ± 20% рандом
        try:
            _cfg2 = load_config()
            _isd  = float(_cfg2.get("inter_stream_delay_sec", 0))
            if _isd > 0:
                _jitter = _isd * random.uniform(-0.20, 0.20)
                _wait   = max(5.0, _isd + _jitter)
                log(f"⏳ Пауза между стримами: {_wait:.0f} сек (base={_isd:.0f})", "INFO")
                time.sleep(_wait)
        except Exception:
            pass
        return

    except StopRequested as e:
        log(f"⛔ Остановка запрошена: {e}", "WARNING")
        try:
            global _BYPASS_STOP
            _BYPASS_STOP = True
        except Exception:
            pass
        try:
            if driver is not None:
                try:
                    diamonds, profile_url = get_diamonds(driver)
                except Exception as e2:
                    log(f"Не смог получить алмазы после стопа: {e2}", "ERROR")
                    diamonds = None
                    profile_url = None
                if diamonds is not None and email:
                    try:
                        gui(f"Получили алмазы для {email}: {diamonds}", "INFO")
                        try:
                            if int(diamonds) >= 3000:
                                target_dir = os.path.join(BASE_DIR, "cashout")
                            else:
                                target_dir = os.path.join(BASE_DIR, "work")
                        except Exception:
                            target_dir = os.path.join(BASE_DIR, "work")
                        os.makedirs(target_dir, exist_ok=True)
                        safe_email = re.sub(r'[\\/:*?"<>|]', "_", email)
                        fname = f"{safe_email}_{diamonds}.txt"
                        fpath = os.path.join(target_dir, fname)
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(email)
                        log(f"Создан файл аккаунта: {fpath}", "SUCCESS")
                        try:
                            from datetime import datetime as _dt
                            acc = (email.strip() if email else "unknown")
                            folder_icon = "💰" if os.path.basename(target_dir) == "cashout" else "📁"
                            now_str = _dt.now().strftime("%d.%m.%Y %H:%M")
                            _link_line = f"🔗 <b>Профиль:</b> {profile_url}\n" if profile_url else ""
                            tg_send_message(cfg,
                                f"⛔ <b>Стрим остановлен (собраны алмазы)</b>\n━━━━━━━━━━━━━━━━━━\n"
                                f"📧 <b>Аккаунт:</b> <code>{acc}</code>\n"
                                f"💎 <b>Алмазы:</b> {diamonds}\n"
                                f"{_link_line}"
                                f"{folder_icon} <b>Папка:</b> {target_dir}\n"
                                f"🌍 <b>VPN страна:</b> {vpn_country}\n"
                                f"🌐 <b>IP:</b> <code>{get_public_ip()}</code>\n"
                                f"🕐 <b>Время:</b> {now_str}"
                            )
                        except Exception:
                            pass
                        try:
                            acc = (email.strip() if email else "unknown")
                            append_gsheets_row(cfg, acc, diamonds, note="алмазы после стрима (stop)", profile_url=(profile_url or ""), vpn_country=(vpn_country or ""), ip=get_public_ip())
                        except Exception as e4:
                            log(f"GSHEETS: ошибка записи при стопе: {e4}", "ERROR")
                        try:
                            notify_my_service(cfg, {"email": (email or ""), "diamonds": diamonds, "profile": profile_num, "reason": "stop"}, event="stream_stopped", retries=1)
                        except Exception:
                            pass
                    except Exception as e3:
                        log(f"Ошибка сохранения результата после стопа: {e3}", "ERROR")
                elif email:
                    gui(f"Стоп: email={email}, алмазы не удалось получить", "WARN")
                    try:
                        notify_my_service(cfg, {"email": (email or ""), "diamonds": None, "profile": profile_num, "reason": "diamonds_unavailable"}, event="stream_failed", retries=1)
                    except Exception:
                        pass
        finally:
            try:
                if driver is not None:
                    driver.quit()
            except Exception:
                pass
            # Профиль отработал — удаляем
            try:
                cleanup_profile(profile_path)
            except Exception:
                pass
            if lock_acquired:
                try:
                    safe_release_lock()
                except Exception:
                    pass
        return

    except Exception as e:
        log(f"КРИТИЧЕСКАЯ ошибка в main: {e}", "ERROR")
        try:
            driver.quit()
        except:
            pass
        if lock_acquired:
            safe_release_lock()


# ========================================================================================
#                                 CHECKER MODE
# ========================================================================================

STOP_CHECKER_FLAG = os.path.join(SETTINGS_DIR, "stop_checker.flag")


def _checker_use_own_stop_flag():
    global STOP_REGER_FLAG
    STOP_REGER_FLAG = STOP_CHECKER_FLAG


def _checker_clear_stop_flag():
    try:
        if os.path.exists(STOP_CHECKER_FLAG):
            os.remove(STOP_CHECKER_FLAG)
    except Exception:
        pass


def _checker_is_banned(driver) -> bool:
    try:
        alert = driver.find_elements(By.CSS_SELECTOR, "[data-testid='alert-modal']")
        suspended = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='user-suspended-view']")
        if alert or suspended:
            return True
    except Exception:
        pass
    return False


def _checker_wait_present(driver, css: str, timeout: float = 25.0, poll: float = 0.5):
    end = time.time() + float(timeout)
    while True:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, css)
            if els:
                return els[0]
        except Exception:
            pass
        if time.time() >= end:
            return None
        time.sleep(min(poll, max(0.05, end - time.time())))


def _checker_wait_clickable(driver, css: str, timeout: float = 25.0, poll: float = 0.5) -> bool:
    end = time.time() + float(timeout)
    while True:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, css)
            for el in els[::-1]:
                try:
                    if el.is_displayed() and el.is_enabled():
                        try:
                            el.click()
                        except Exception:
                            try:
                                driver.execute_script("arguments[0].click();", el)
                            except Exception:
                                return False
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        if time.time() >= end:
            return False
        time.sleep(min(poll, max(0.05, end - time.time())))


def tango_login_existing_account(driver, cfg: dict, email: str) -> tuple[bool, str]:
    try:
        driver.get("https://tango.me/live/recommended")
    except Exception:
        pass
    time.sleep(3)
    if driver.find_elements(By.CSS_SELECTOR, "a[data-testid='broadcast-button-sidebar']"):
        return True, "already"
    ok = perform_email_login(driver, cfg, email)
    if not ok:
        if driver.find_elements(By.CSS_SELECTOR, "a[data-testid='broadcast-button-sidebar']"):
            return True, "already"
        return False, "login_failed"
    otp0 = _checker_wait_present(driver, "input[data-testid='digit-input-0']", timeout=70)
    if not otp0:
        if _checker_is_banned(driver):
            return False, "ban"
        return False, "otp_not_shown"
    code = get_tango_code_from_file(email, timeout=cfg.get('email_check_timeout_sec', 240))
    if not code:
        return False, "no_code"
    digits = list(str(code).strip())
    try:
        for idx, d in enumerate(digits):
            el = _checker_wait_present(driver, f"input[data-testid='digit-input-{idx}']", timeout=15)
            if not el:
                raise RuntimeError("otp input not found")
            el.send_keys(d)
    except Exception:
        return False, "otp_input_fail"
    time.sleep(2)
    try:
        dismiss_email_marketing(driver, timeout=6.0, log_prefix="[checker]")
    except Exception:
        pass
    ok_sidebar = bool(_checker_wait_present(driver, "a[data-testid='broadcast-button-sidebar']", timeout=25))
    if ok_sidebar:
        return True, "ok"
    if _checker_is_banned(driver):
        return False, "ban"
    return False, "ban"


def tango_prepare_to_go_live(driver) -> bool:
    if not _safe_navigate(driver, "https://tango.me/broadcast", timeout=120, retries=2, label="checker-broadcast"):
        return False
    time.sleep(10)
    try:
        _checker_wait_clickable(driver, "button[data-testid='permission-confirm-button']", timeout=6)
    except Exception:
        pass
    time.sleep(5)
    if not _checker_wait_clickable(driver, "button[data-testid='audio-button']", timeout=25):
        return False
    time.sleep(2)
    btn = _checker_wait_present(driver, "button[data-testid='go-live-button']", timeout=35)
    return bool(btn)


def check_single_account(email: str, proxy_spec: str | None = None) -> dict:
    cfg = load_config()
    if not (cfg.get('tango_ref_url') or '').strip():
        return {"email": email, "status": "ошибка", "diamonds": None, "note": "no tango_ref_url"}
    if 'email_check_timeout_sec' not in cfg:
        cfg['email_check_timeout_sec'] = 240
    safe_profile = email.replace("@", "_").replace(".", "_")
    profile_path = f"{PATH_PROFILES}/{safe_profile}"
    max_attempts = 3
    last_reason = ""
    driver = None
    try:
        ok = False
        reason = ""
        for attempt in range(1, max_attempts + 1):
            try:
                driver = create_driver(profile_path, proxy_spec=proxy_spec)
            except Exception as e:
                last_reason = f"driver_err:{e}"
                driver = None
                ok = False
                reason = "driver_err"
            if driver is None:
                if attempt < max_attempts:
                    try:
                        shutil.rmtree(profile_path, ignore_errors=True)
                    except Exception:
                        pass
                    time.sleep(1)
                    continue
                return {"email": email, "status": "не удалось войти", "diamonds": None, "note": last_reason or "driver_err"}
            ok, reason = tango_login_existing_account(driver, cfg, email)
            last_reason = reason
            if ok:
                break
            if reason == "ban":
                return {"email": email, "status": "бан", "diamonds": None, "note": reason}
            try:
                driver.quit()
            except Exception:
                pass
            driver = None
            if attempt < max_attempts:
                try:
                    shutil.rmtree(profile_path, ignore_errors=True)
                except Exception:
                    pass
                time.sleep(1)
                continue
        if not ok:
            return {"email": email, "status": "не удалось войти", "diamonds": None, "note": last_reason or "login_failed"}
        try:
            diamonds, _profile_url = get_diamonds(driver)
        except Exception as e:
            return {"email": email, "status": "ошибка", "diamonds": None, "note": f"diamonds_err:{e}"}
        try:
            diamonds_i = int(diamonds)
        except Exception:
            diamonds_i = None
        if diamonds_i is None:
            return {"email": email, "status": "ошибка", "diamonds": None, "note": "diamonds_parse_err"}
        status = "вывод" if diamonds_i >= 3000 else "новый"
        prepared = False
        if diamonds_i >= 3000:
            try:
                prepared = tango_prepare_to_go_live(driver)
            except Exception:
                prepared = False
        return {
            "email": email, "status": status, "diamonds": diamonds_i,
            "prepared_go_live": prepared, "note": last_reason or "ok",
        }
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass


def _run_checker_cli():
    _checker_use_own_stop_flag()
    try:
        email = sys.argv[sys.argv.index("--check-single") + 1]
    except Exception:
        print("[RESULT] {}", flush=True)
        return 2
    proxy_spec = None
    if "--proxy" in sys.argv:
        try:
            proxy_spec = sys.argv[sys.argv.index("--proxy") + 1]
        except Exception:
            proxy_spec = None
    res = check_single_account(email, proxy_spec=proxy_spec)
    print("[RESULT] " + json.dumps(res, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    if "--check-single" in sys.argv:
        raise SystemExit(_run_checker_cli())
    main()
