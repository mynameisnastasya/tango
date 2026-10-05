#!/usr/bin/env python3
from __future__ import annotations

import atexit
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request
from selenium.common.exceptions import WebDriverException

from safe_browser import build_driver

HOST = "127.0.0.1"
PORT = 8765
DEFAULT_URL = "https://www.tango.me/"

app = Flask(__name__)
_lock = threading.Lock()
_driver = None
_last_error = ""

PAGE = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Tango Local Launcher</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, system-ui, -apple-system, Segoe UI, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center;
      background: radial-gradient(circle at 20% 15%, #2b1747 0, transparent 35%),
                  radial-gradient(circle at 85% 80%, #112f4b 0, transparent 34%),
                  #090b12; color: #f7f7fb; }
    .card { width: min(92vw, 720px); padding: 28px; border-radius: 24px;
      background: rgba(18,20,30,.88); border: 1px solid rgba(255,255,255,.10);
      box-shadow: 0 28px 90px rgba(0,0,0,.42); backdrop-filter: blur(20px); }
    .top { display:flex; justify-content:space-between; gap:16px; align-items:center; }
    h1 { margin:0; font-size: clamp(28px, 5vw, 44px); letter-spacing:-.04em; }
    .sub { color:#a9adbd; line-height:1.55; margin:10px 0 24px; }
    .status { display:inline-flex; align-items:center; gap:8px; padding:8px 12px;
      border-radius:999px; background:#202333; color:#c7cad6; font-weight:700; }
    .dot { width:10px; height:10px; border-radius:50%; background:#777; }
    .status.on .dot { background:#35d07f; box-shadow:0 0 0 6px rgba(53,208,127,.12); }
    .status.on { color:#8ff0bc; }
    label { display:block; font-weight:700; margin-bottom:8px; }
    input { width:100%; padding:14px 16px; border-radius:14px; border:1px solid #303547;
      background:#0f111a; color:white; font-size:16px; outline:none; }
    input:focus { border-color:#7657ff; box-shadow:0 0 0 4px rgba(118,87,255,.14); }
    .buttons { display:grid; grid-template-columns: 1.4fr 1fr 1fr; gap:10px; margin-top:16px; }
    button, a.btn { border:0; border-radius:14px; padding:14px 16px; font-size:16px;
      font-weight:800; cursor:pointer; text-align:center; text-decoration:none; }
    .start { background:linear-gradient(135deg,#7c5cff,#4f8cff); color:white; }
    .stop { background:#2a1b22; color:#ff93a5; border:1px solid #55303a; }
    .open { background:#1b2930; color:#8fe3ff; border:1px solid #294955; }
    button:disabled { opacity:.5; cursor:not-allowed; }
    .msg { min-height:24px; margin-top:16px; color:#b9bdca; word-break:break-word; }
    .foot { margin-top:22px; padding-top:18px; border-top:1px solid #282c3a;
      color:#858a9c; font-size:13px; line-height:1.5; }
    code { color:#d3c9ff; }
    @media (max-width:640px){ .top{align-items:flex-start;flex-direction:column}.buttons{grid-template-columns:1fr} }
  </style>
</head>
<body>
  <main class="card">
    <div class="top">
      <div>
        <h1>Tango Launcher</h1>
        <div class="sub">Локальная веб-панель для обычного Chrome-профиля.</div>
      </div>
      <div id="status" class="status"><span class="dot"></span><span>проверяю…</span></div>
    </div>

    <label for="url">Адрес</label>
    <input id="url" value="https://www.tango.me/" autocomplete="off">

    <div class="buttons">
      <button id="start" class="start">▶ Запустить Tango</button>
      <button id="stop" class="stop">■ Остановить</button>
      <a id="open" class="btn open" href="https://www.tango.me/" target="_blank" rel="noopener">↗ Открыть сайт</a>
    </div>

    <div id="msg" class="msg"></div>
    <div class="foot">
      Панель доступна только на <code>127.0.0.1</code>, поэтому снаружи никто не сможет нажимать эти кнопки.
      Chrome использует постоянный локальный профиль <code>automation/profiles/manual</code>.
    </div>
  </main>

<script>
const $ = s => document.querySelector(s);
const statusEl = $('#status'), startBtn = $('#start'), stopBtn = $('#stop'),
      msg = $('#msg'), url = $('#url'), open = $('#open');

url.addEventListener('input', () => open.href = url.value || 'https://www.tango.me/');

async function api(path, opts={}) {
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || ('HTTP ' + r.status));
  return data;
}
async function refresh() {
  try {
    const s = await api('/api/status');
    statusEl.classList.toggle('on', !!s.running);
    statusEl.querySelector('span:last-child').textContent = s.running ? 'Chrome запущен' : 'остановлен';
    startBtn.disabled = !!s.running;
    stopBtn.disabled = !s.running;
    if (s.error) msg.textContent = s.error;
  } catch (e) { msg.textContent = e.message; }
}
startBtn.onclick = async () => {
  msg.textContent = 'Запускаю Chrome…';
  startBtn.disabled = true;
  try {
    const data = await api('/api/start', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({url:url.value})
    });
    msg.textContent = data.message || 'Запущено';
  } catch(e) { msg.textContent = e.message; }
  await refresh();
};
stopBtn.onclick = async () => {
  msg.textContent = 'Закрываю Chrome…';
  try {
    const data = await api('/api/stop', {method:'POST'});
    msg.textContent = data.message || 'Остановлено';
  } catch(e) { msg.textContent = e.message; }
  await refresh();
};
refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""


def _alive() -> bool:
    global _driver
    if _driver is None:
        return False
    try:
        _ = _driver.current_url
        return True
    except Exception:
        _driver = None
        return False


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.get("/api/status")
def status():
    with _lock:
        return jsonify(running=_alive(), error=_last_error)


@app.post("/api/start")
def start():
    global _driver, _last_error
    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url") or DEFAULT_URL).strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        return jsonify(error="URL должен начинаться с http:// или https://"), 400

    with _lock:
        if _alive():
            try:
                _driver.get(url)
                return jsonify(ok=True, running=True, message="Chrome уже работал — страница открыта.")
            except Exception as exc:
                _last_error = str(exc)
                return jsonify(error=_last_error), 500

        try:
            _last_error = ""
            _driver = build_driver(headless=False)
            _driver.get(url)
            return jsonify(ok=True, running=True, message="Chrome запущен.")
        except WebDriverException as exc:
            _driver = None
            _last_error = f"Не удалось запустить Chrome: {exc}"
            return jsonify(error=_last_error), 500
        except Exception as exc:
            _driver = None
            _last_error = str(exc)
            return jsonify(error=_last_error), 500


@app.post("/api/stop")
def stop():
    global _driver, _last_error
    with _lock:
        if _driver is not None:
            try:
                _driver.quit()
            except Exception:
                pass
        _driver = None
        _last_error = ""
    return jsonify(ok=True, running=False, message="Chrome остановлен.")


@atexit.register
def cleanup():
    global _driver
    try:
        if _driver is not None:
            _driver.quit()
    except Exception:
        pass


def main():
    threading.Timer(0.8, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    print(f"Tango Launcher: http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
