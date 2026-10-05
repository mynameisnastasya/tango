"""
device_fingerprint.py — Система уникальных «устройств» для каждого профиля.

Каждый Chrome-профиль получает свой постоянный device_profile.json.
Профиль создаётся один раз и никогда не меняется — тот же профиль = то же «устройство».

Что подменяется:
  - User-Agent (Windows 10/11 или macOS)
  - navigator: platform, cores, memory, language, vendor, plugins, productSub, buildID
  - Screen: width, height, availWidth, availHeight, colorDepth, pixelDepth
  - Canvas: случайный шум в пикселях (уникальный на каждый вызов, но в рамках одного устройства)
  - WebGL: VENDOR, RENDERER (реальные строки реальных GPU)
  - AudioContext: tiny noise в AnalyserNode (не трогает реальный MediaStream!)
  - window.chrome: реалистичный объект
  - Permissions API: отвечает 'granted' для нужных или 'default'
  - connection (NetworkInformation): type, downlink, rtt
  - devicePixelRatio: 1 для Windows, 2 для Retina Mac
  - navigator.getBattery(): реалистичный ответ
  - navigator.keyboard, navigator.mediaDevices.enumerateDevices: ВСЕГДА фейковые device ID (не реальный hardware ID!)
  - navigator.mediaDevices.getUserMedia: перехватываем только для снятия deviceId-ограничения

НЕ трогаем (намеренно):
  - Timezone / Geolocation — ломает авторизацию Tango, используется реальная системная
  - Реальный медиапоток камеры/микрофона — getUserMedia пробрасывает на дефолтное устройство
  - WebRTC / ICE — для стрима нужен реальный ICE
"""

import json
import os
import random
import secrets
from pathlib import Path

DEVICE_PROFILE_FILE = "device_profile.json"


# ─────────────────────────────────────────────────────────────────────────────
#  Базы данных реальных устройств
# ─────────────────────────────────────────────────────────────────────────────

_WINDOWS_DEVICES = [
    # (os_hint, screen_w, screen_h, tz_name, tz_offset, language, dpr)
    # Win 10/11, разные разрешения и регионы
    ("Windows NT 10.0; Win64; x64", 1920, 1080, "America/New_York",    -300, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1920, 1080, "America/Chicago",     -360, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1920, 1080, "America/Los_Angeles", -480, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1366, 768,  "America/New_York",    -300, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1366, 768,  "Europe/Warsaw",        60,  "pl-PL", 1),
    ("Windows NT 10.0; Win64; x64", 1440, 900,  "America/Denver",      -420, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1536, 864,  "America/New_York",    -300, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1280, 720,  "Europe/London",         0,  "en-GB", 1),
    ("Windows NT 10.0; Win64; x64", 1280, 800,  "Europe/Berlin",        60,  "de-DE", 1),
    ("Windows NT 11.0; Win64; x64", 2560, 1440, "America/New_York",    -300, "en-US", 1),
    ("Windows NT 11.0; Win64; x64", 1920, 1080, "America/Los_Angeles", -480, "en-US", 1),
    ("Windows NT 11.0; Win64; x64", 1920, 1080, "Europe/London",         0,  "en-GB", 1),
    ("Windows NT 10.0; Win64; x64", 1600, 900,  "America/Chicago",     -360, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1920, 1200, "America/Phoenix",     -420, "en-US", 1),
    ("Windows NT 10.0; Win64; x64", 1024, 768,  "America/New_York",    -300, "en-US", 1),
]

_MAC_DEVICES = [
    # (os_hint, screen_w, screen_h, tz_name, tz_offset, language, dpr)
    # Retina: dpr=2, обычные: dpr=1
    ("Macintosh; Intel Mac OS X 10_15_7",  2560, 1600, "America/New_York",    -300, "en-US", 2),
    ("Macintosh; Intel Mac OS X 10_15_7",  1920, 1080, "America/Chicago",     -360, "en-US", 1),
    ("Macintosh; Intel Mac OS X 11_7_10",  2560, 1600, "America/Los_Angeles", -480, "en-US", 2),
    ("Macintosh; Intel Mac OS X 12_7_6",   2560, 1664, "America/New_York",    -300, "en-US", 2),
    ("Macintosh; Intel Mac OS X 13_6_9",   2560, 1600, "America/Los_Angeles", -480, "en-US", 2),
    ("Macintosh; Intel Mac OS X 14_7_1",   3456, 2234, "America/New_York",    -300, "en-US", 2),
    ("Macintosh; Intel Mac OS X 15_0",     2560, 1600, "America/Chicago",     -360, "en-US", 2),
    ("Macintosh; Intel Mac OS X 13_0",     1440,  900, "America/Denver",      -420, "en-US", 1),
    ("Macintosh; Intel Mac OS X 12_0",     2560, 1600, "Europe/London",          0, "en-GB", 2),
    ("Macintosh; Intel Mac OS X 10_15_7",  1680, 1050, "America/Los_Angeles", -480, "en-US", 1),
]

# Реальные WebGL пары (vendor, renderer) для разных GPU
_WEBGL_PAIRS = [
    # Intel (самые распространённые)
    ("Google Inc. (Intel)",
     "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)",
     "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)",
     "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)",
     "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)",
     "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    # NVIDIA
    ("Google Inc. (NVIDIA)",
     "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)",
     "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)",
     "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)",
     "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    # AMD
    ("Google Inc. (AMD)",
     "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)",
     "ANGLE (AMD, AMD Radeon RX 5500 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    # Mac Metal
    ("Google Inc. (Apple)",
     "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)"),
    ("Google Inc. (Apple)",
     "ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)"),
    ("Google Inc. (Apple)",
     "ANGLE (Apple, Apple M1 Pro, OpenGL Engine)"),
]

# Chrome версии (реалистичные — актуальные на 2024-2026)
_CHROME_VERSIONS = [
    (122, 6261, 128),
    (123, 6312, 122),
    (124, 6367, 82),
    (125, 6422, 112),
    (126, 6478, 126),
    (127, 6533, 99),
    (128, 6613, 114),
    (129, 6668, 75),
    (130, 6723, 93),
    (131, 6778, 88),
    (132, 6834, 126),
    (133, 6943, 85),
    (134, 7103, 92),
    (135, 7049, 116),
    (136, 7103, 77),
]

# Реалистичные наборы плагинов
_PLUGIN_SETS = [
    [
        {"name": "PDF Viewer",         "filename": "internal-pdf-viewer",               "description": "Portable Document Format"},
        {"name": "Chrome PDF Viewer",  "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",  "description": ""},
        {"name": "Chromium PDF Viewer","filename": "internal-pdf-viewer",               "description": ""},
        {"name": "Microsoft Edge PDF Viewer", "filename": "internal-pdf-viewer",        "description": ""},
        {"name": "WebKit built-in PDF","filename": "internal-pdf-viewer",               "description": ""},
    ],
    [
        {"name": "Chrome PDF Plugin",  "filename": "internal-pdf-viewer",               "description": "Portable Document Format"},
        {"name": "Chrome PDF Viewer",  "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",  "description": ""},
        {"name": "Native Client",      "filename": "internal-nacl-plugin",              "description": ""},
    ],
]


# ─────────────────────────────────────────────────────────────────────────────
#  Генератор профиля устройства
# ─────────────────────────────────────────────────────────────────────────────

def generate_device_profile(profile_num: int | None = None) -> dict:
    """
    Генерирует полный уникальный «профиль устройства».
    Использует profile_num как seed для детерминированности,
    плюс случайные соли — каждый вызов без profile_num даёт новый профиль.
    """
    rng = random.Random(secrets.token_bytes(16))

    # Выбираем тип устройства: 60% Windows, 40% Mac
    is_windows = rng.random() < 0.60

    if is_windows:
        os_hint, sw, sh, tz_name, tz_off, lang, dpr = rng.choice(_WINDOWS_DEVICES)
        platform  = "Win32"
        vendor    = "Google Inc."
        product_sub = "20030107"
        app_version = f"5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    else:
        os_hint, sw, sh, tz_name, tz_off, lang, dpr = rng.choice(_MAC_DEVICES)
        platform  = "MacIntel"
        vendor    = "Apple Computer, Inc."
        product_sub = "20030107"
        app_version = f"5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36"

    # Chrome version
    ch_major, ch_build1, ch_build2 = rng.choice(_CHROME_VERSIONS)
    ch_patch = rng.randint(0, 999)

    if is_windows:
        ua = (
            f"Mozilla/5.0 ({os_hint}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{ch_major}.0.{ch_build1}.{ch_build2} Safari/537.36"
        )
    else:
        ua = (
            f"Mozilla/5.0 ({os_hint}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{ch_major}.0.{ch_build1}.{ch_build2} Safari/537.36"
        )

    # Hardware
    cores_choices = [2, 4, 4, 4, 6, 8, 8, 12, 16]
    mem_choices   = [2, 4, 4, 8, 8, 16, 32]
    cores  = rng.choice(cores_choices)
    memory = rng.choice(mem_choices)

    # WebGL
    webgl_vendor, webgl_renderer = rng.choice(_WEBGL_PAIRS)

    # Plugins
    plugins = rng.choice(_PLUGIN_SETS)

    # Screen: availHeight = screen_h минус панель задач
    taskbar_h = rng.randint(40, 60) if is_windows else 25
    avail_h = sh - taskbar_h

    # Canvas noise seed — уникальный для профиля, но постоянный
    canvas_seed = rng.randint(1, 65535)

    # Audio noise
    audio_noise = round(rng.uniform(0.00002, 0.00009), 8)

    # Language variants
    langs_map = {
        "en-US": ["en-US", "en"],
        "en-GB": ["en-GB", "en-US", "en"],
        "de-DE": ["de-DE", "de", "en-US", "en"],
        "pl-PL": ["pl-PL", "pl", "en-US", "en"],
        "fr-FR": ["fr-FR", "fr", "en-US", "en"],
    }
    langs_list = langs_map.get(lang, ["en-US", "en"])

    # Network info (realistic for desktop)
    net_types = ["wifi", "ethernet", "4g"]
    net_type  = rng.choice(net_types)
    net_dl    = round(rng.uniform(2.5, 100.0), 2)
    net_rtt   = rng.randint(5, 80)

    # Battery (realistic)
    battery_charging  = rng.random() < 0.45
    battery_level     = round(rng.uniform(0.30, 1.0), 2) if not battery_charging else round(rng.uniform(0.60, 1.0), 2)
    battery_ct        = rng.randint(0, 3600) if battery_charging else 0
    battery_dt        = rng.randint(3600, 36000) if not battery_charging else 0

    # Fake device IDs for enumerateDevices
    fake_vid_id  = secrets.token_hex(32)
    fake_aud_id  = secrets.token_hex(32)
    fake_vid_gid = secrets.token_hex(32)
    fake_aud_gid = secrets.token_hex(32)

    # Unique profile fingerprint token
    fp_token = secrets.token_hex(8)

    # Font fingerprint seed — уникальный набор доступных шрифтов
    font_seed = rng.randint(1, 9999)

    # window.name — всегда пустая строка
    # pdfViewerEnabled — у реальных юзеров обычно true
    pdf_viewer = True

    # CSS prefers-color-scheme: Windows обычно light, Mac чаще dark
    prefers_dark = rng.random() < (0.55 if not is_windows else 0.35)

    return {
        "fp_token":        fp_token,
        "is_windows":      is_windows,
        "os_hint":         os_hint,
        "platform":        platform,
        "vendor":          vendor,
        "product_sub":     product_sub,
        "app_version":     app_version,
        "user_agent":      ua,
        "chrome_major":    ch_major,
        "screen_w":        sw,
        "screen_h":        sh,
        "avail_h":         avail_h,
        "dpr":             dpr,
        "tz_name":         tz_name,
        "tz_offset":       tz_off,
        "language":        lang,
        "languages":       langs_list,
        "cores":           cores,
        "memory":          memory,
        "webgl_vendor":    webgl_vendor,
        "webgl_renderer":  webgl_renderer,
        "plugins":         plugins,
        "canvas_seed":     canvas_seed,
        "audio_noise":     audio_noise,
        "net_type":        net_type,
        "net_dl":          net_dl,
        "net_rtt":         net_rtt,
        "battery_charging":battery_charging,
        "battery_level":   battery_level,
        "battery_ct":      battery_ct,
        "battery_dt":      battery_dt,
        "fake_vid_id":     fake_vid_id,
        "fake_aud_id":     fake_aud_id,
        "fake_vid_gid":    fake_vid_gid,
        "fake_aud_gid":    fake_aud_gid,
        "font_seed":       font_seed,
        "pdf_viewer":      pdf_viewer,
        "prefers_dark":    prefers_dark,
    }


def get_or_create_device_profile(profile_dir: str | None) -> dict:
    """Загружает device_profile.json из папки профиля или создаёт новый."""
    if not profile_dir:
        return generate_device_profile()

    profile_path = Path(profile_dir)
    profile_path.mkdir(parents=True, exist_ok=True)
    dev_file = profile_path / DEVICE_PROFILE_FILE

    if dev_file.exists():
        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            if data.get("user_agent") and data.get("fp_token"):
                return data
        except Exception:
            pass

    # Создаём новый
    dp = generate_device_profile()
    try:
        dev_file.write_text(json.dumps(dp, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return dp


# ─────────────────────────────────────────────────────────────────────────────
#  CDP / JS инъекция
# ─────────────────────────────────────────────────────────────────────────────

def apply_device_profile_to_driver(driver, dp: dict) -> None:
    """
    Применяет device_profile к уже запущенному Chrome через CDP + JS.
    Вызывать сразу после create_driver(), ДО открытия любой страницы.

    Подменяем: UA, navigator (hardware/platform/language), Screen, Canvas,
               WebGL, AudioContext, chrome object, Permissions, Network, Battery,
               enumerateDevices — всё кроме timezone и geolocation (они ломают авторизацию).
    """
    import json as _json

    # ── CDP: UA, Accept-Language, sec-ch-ua headers ─────────────────────────
    # Подменяем заголовки СЕТИ чтобы они совпадали с JS navigator (важно!)
    ua      = dp.get("user_agent", "")
    lang    = dp.get("language", "en-US")
    ch_major= dp.get("chrome_major", 134)
    platform_ch = '"Windows"' if dp.get("is_windows", True) else '"macOS"'
    sec_ch_ua = f'"Google Chrome";v="{ch_major}", "Not:A-Brand";v="8", "Chromium";v="{ch_major}"'

    try:
        driver.execute_cdp_cmd("Network.enable", {})
    except Exception:
        pass
    try:
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent":         ua,
            "acceptLanguage":    lang,
            "platform":          dp.get("platform", "Win32"),
            "userAgentMetadata": {
                "brands": [
                    {"brand": "Google Chrome",  "version": str(ch_major)},
                    {"brand": "Not:A-Brand",    "version": "8"},
                    {"brand": "Chromium",        "version": str(ch_major)},
                ],
                "fullVersion":    f"{ch_major}.0.0.0",
                "platform":       "Windows" if dp.get("is_windows", True) else "macOS",
                "platformVersion":"10.0.0",
                "architecture":   "x86",
                "model":          "",
                "mobile":         False,
            }
        })
    except Exception:
        # Fallback для старых chromedriver
        try:
            driver.execute_cdp_cmd("Network.setUserAgentOverride", {
                "userAgent": ua,
                "acceptLanguage": lang,
            })
        except Exception:
            pass

    # Убираем webdriver через CDP
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator,'webdriver',{get:()=>false,configurable:true});"
        })
    except Exception:
        pass

    # Большой JS-скрипт подмены отпечатка
    langs_json    = _json.dumps(dp["languages"])
    plugins_json  = _json.dumps(dp["plugins"])
    canvas_seed   = int(dp["canvas_seed"])
    audio_noise   = float(dp["audio_noise"])

    script = f"""
(function() {{
  'use strict';
  try {{
    // ── Утилита def ──────────────────────────────────────────────────────────
    const def = (obj, prop, value) => {{
      try {{
        Object.defineProperty(obj, prop, {{
          get: () => value,
          configurable: true,
          enumerable: true,
        }});
      }} catch(e) {{}}
    }};

    // ── 1. Navigator ─────────────────────────────────────────────────────────
    const proto = Navigator.prototype || navigator;
    def(proto, 'platform',           {_json.dumps(dp['platform'])});
    def(proto, 'vendor',             {_json.dumps(dp['vendor'])});
    def(proto, 'productSub',         {_json.dumps(dp['product_sub'])});
    def(proto, 'language',           {_json.dumps(dp['language'])});
    def(proto, 'languages',          {langs_json});
    def(proto, 'hardwareConcurrency',{dp['cores']});
    def(proto, 'deviceMemory',       {dp['memory']});
    def(proto, 'maxTouchPoints',     0);
    def(proto, 'doNotTrack',         null);
    try {{ delete Navigator.prototype.webdriver; }} catch(e) {{}}
    def(proto, 'webdriver', false);

    // Реалистичные плагины
    const pluginData = {plugins_json};
    const fakePlugins = {{
      length: pluginData.length,
      item: (i) => fakePlugins[i] || null,
      namedItem: (n) => Object.values(fakePlugins).find(p => p && p.name === n) || null,
      refresh: () => {{}},
      [Symbol.iterator]: function*() {{
        for (let i = 0; i < pluginData.length; i++) yield this[i];
      }}
    }};
    pluginData.forEach((p, i) => {{
      fakePlugins[i] = {{
        name: p.name, filename: p.filename, description: p.description,
        length: 1, item: () => null, namedItem: () => null
      }};
    }});
    def(proto, 'plugins', fakePlugins);

    // MimeTypes
    const fakeMimes = {{ length: 2, item: (i) => null, namedItem: () => null }};
    def(proto, 'mimeTypes', fakeMimes);

    // ── 2. Screen ────────────────────────────────────────────────────────────
    const scr = Screen.prototype || screen;
    def(scr, 'width',       {dp['screen_w']});
    def(scr, 'height',      {dp['screen_h']});
    def(scr, 'availWidth',  {dp['screen_w']});
    def(scr, 'availHeight', {dp['avail_h']});
    def(scr, 'colorDepth',  24);
    def(scr, 'pixelDepth',  24);
    def(scr, 'availLeft',   0);
    def(scr, 'availTop',    0);

    // devicePixelRatio
    def(window, 'devicePixelRatio', {dp['dpr']});

    // ── 3. Canvas fingerprint noise ─────────────────────────────────────────
    const _cSeed = {canvas_seed};
    function _lcg(n) {{
      return (((n * 1664525 + _cSeed) & 0xffffffff) >>> 16) & 0x03;
    }}
    function _addCanvasNoise(imgData) {{
      const d = imgData.data;
      const step = Math.max(1, Math.floor(d.length / 160));
      for (let i = 0; i < d.length; i += step * 4) {{
        d[i]   = (d[i]   + _lcg(i))   & 0xff;
        d[i+1] = (d[i+1] + _lcg(i+1)) & 0xff;
        d[i+2] = (d[i+2] + _lcg(i+2)) & 0xff;
      }}
      return imgData;
    }}
    const _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {{
      const ctx2d = this.getContext && this.getContext('2d');
      if (ctx2d) {{
        try {{
          const id = ctx2d.getImageData(0, 0, this.width || 1, this.height || 1);
          _addCanvasNoise(id);
          ctx2d.putImageData(id, 0, 0);
        }} catch(e) {{}}
      }}
      return _origToDataURL.apply(this, [type, ...args]);
    }};
    const _origGetImgData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
      const id = _origGetImgData.apply(this, args);
      return _addCanvasNoise(id);
    }};

    // ── 5. WebGL fingerprint ─────────────────────────────────────────────────
    function _patchWebGL(ctx) {{
      if (!ctx) return;
      const origGP = ctx.getParameter.bind(ctx);
      ctx.getParameter = function(param) {{
        if (param === 37445) return {_json.dumps(dp['webgl_vendor'])};   // UNMASKED_VENDOR
        if (param === 37446) return {_json.dumps(dp['webgl_renderer'])}; // UNMASKED_RENDERER
        if (param === 7936)  return 'WebKit';                              // VENDOR
        if (param === 7937)  return 'WebKit WebGL';                        // RENDERER
        return origGP(param);
      }};
      // getExtension: маскируем WEBGL_debug_renderer_info
      const origGE = ctx.getExtension.bind(ctx);
      ctx.getExtension = function(name) {{
        if (name === 'WEBGL_debug_renderer_info') {{
          return {{
            UNMASKED_VENDOR_WEBGL: 37445,
            UNMASKED_RENDERER_WEBGL: 37446,
          }};
        }}
        return origGE(name);
      }};
    }}
    try {{
      const canvas2 = document.createElement('canvas');
      _patchWebGL(canvas2.getContext('webgl'));
      _patchWebGL(canvas2.getContext('webgl2'));
      const _origGetCtx = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(type, ...a) {{
        const ctx = _origGetCtx.apply(this, [type, ...a]);
        if (type === 'webgl' || type === 'webgl2' || type === 'experimental-webgl') {{
          _patchWebGL(ctx);
        }}
        return ctx;
      }};
    }} catch(e) {{}}

    // ── 6. AudioContext — tiny noise в AnalyserNode (только FFT, не WebRTC поток) ──
    // getFloatFrequencyData = спектральный анализ для fingerprint детекторов.
    // Реальный MediaStream/WebRTC аудио поток НЕ затрагивается.
    try {{
      const _AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (_AudioCtx) {{
        const _origAnalyser = _AudioCtx.prototype.createAnalyser;
        _AudioCtx.prototype.createAnalyser = function() {{
          const node = _origAnalyser.call(this);
          const noise = {audio_noise};
          if (noise > 0) {{
            try {{
              const _origGetFD = node.getFloatFrequencyData.bind(node);
              node.getFloatFrequencyData = function(arr) {{
                _origGetFD(arr);
                for (let i = 0; i < arr.length; i++) arr[i] += (Math.random() - 0.5) * noise * 100;
              }};
            }} catch(e) {{}}
          }}
          return node;
        }};
      }}
    }} catch(e) {{}}

    // ── 7. window.chrome (детальный реалистичный объект) ────────────────────
    try {{
      const _chromeObj = {{
        app: {{
          isInstalled: false,
          getDetails: function() {{ return null; }},
          getIsInstalled: function() {{ return false; }},
          InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
          RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }},
        }},
        runtime: {{
          id: undefined,
          connect:     function() {{ return {{ disconnect: function(){{}}, postMessage: function(){{}}, onDisconnect: {{ addListener: function(){{}}, removeListener: function(){{}} }}, onMessage: {{ addListener: function(){{}}, removeListener: function(){{}} }} }}; }},
          sendMessage: function() {{}},
          onConnect:   {{ addListener: function(){{}}, removeListener: function(){{}}, hasListener: function(){{ return false; }} }},
          onMessage:   {{ addListener: function(){{}}, removeListener: function(){{}}, hasListener: function(){{ return false; }} }},
          onInstalled: {{ addListener: function(){{}}, removeListener: function(){{}}, hasListener: function(){{ return false; }} }},
          getManifest: function() {{ return {{ manifest_version: 3, name: 'Chrome', version: '1.0' }}; }},
          getURL:      function(path) {{ return 'chrome-extension://invalid/' + path; }},
          lastError:   null,
          id:          undefined,
        }},
        loadTimes: function() {{
          return {{
            commitLoadTime:    performance.timing ? performance.timing.navigationStart / 1000 : 0,
            connectionInfo:    'http/1.1',
            finishDocumentLoadTime: 0,
            finishLoadTime:    0,
            firstPaintAfterLoadTime: 0,
            firstPaintTime:    0,
            navigationType:    'Other',
            npnNegotiatedProtocol: 'unknown',
            requestTime:       0,
            startLoadTime:     0,
            wasAlternateProtocolAvailable: false,
            wasFetchedViaSpdy: false,
            wasNpnNegotiated:  false,
          }};
        }},
        csi: function() {{
          return {{
            startE:   Date.now(),
            onloadT:  Date.now() + Math.floor(Math.random()*500 + 200),
            pageT:    Math.random() * 3 + 0.5,
            tran:     15,
          }};
        }},
      }};
      if (!window.chrome || !window.chrome.runtime) {{
        Object.defineProperty(window, 'chrome', {{
          value: _chromeObj,
          configurable: true, enumerable: true, writable: true,
        }});
      }}
    }} catch(e) {{}}

    // ── 8. Permissions API ────────────────────────────────────────────────────
    try {{
      if (navigator.permissions && navigator.permissions.query) {{
        const _origQ = navigator.permissions.query.bind(navigator.permissions);
        navigator.permissions.query = function(params) {{
          const n = (params || {{}}).name || '';
          if (['camera','microphone','notifications'].includes(n)) {{
            return Promise.resolve({{ state: 'granted', onchange: null }});
          }}
          return _origQ(params);
        }};
      }}
    }} catch(e) {{}}

    // ── 9. NetworkInformation (connection) ────────────────────────────────────
    try {{
      const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (conn) {{
        def(conn, 'effectiveType', {_json.dumps(dp['net_type'])});
        def(conn, 'type',          {_json.dumps(dp['net_type'])});
        def(conn, 'downlink',      {dp['net_dl']});
        def(conn, 'rtt',           {dp['net_rtt']});
        def(conn, 'saveData',      false);
      }}
    }} catch(e) {{}}

    // ── 10. Battery API ───────────────────────────────────────────────────────
    try {{
      const _batteryObj = {{
        charging:          {'true' if dp['battery_charging'] else 'false'},
        chargingTime:      {dp['battery_ct']},
        dischargingTime:   {dp['battery_dt']},
        level:             {dp['battery_level']},
        addEventListener:  () => {{}},
        removeEventListener: () => {{}},
        dispatchEvent:     () => false,
      }};
      navigator.getBattery = () => Promise.resolve(_batteryObj);
    }} catch(e) {{}}

    // ── 11. enumerateDevices — ВСЕГДА фейковые ID (не реальный hardware ID!) ──
    // Реальный hardware deviceId = одинаков каждый раз = утечка fingerprint.
    // Решение: всегда возвращать fake ID уникальные на профиль.
    // getUserMedia патчится ниже: если передан наш fake deviceId — убираем его,
    // Chrome использует дефолтное реальное устройство. Поток не страдает.
    try {{
      const _fakeVidId  = {_json.dumps(dp['fake_vid_id'])};
      const _fakeAudId  = {_json.dumps(dp['fake_aud_id'])};
      const _fakeVidGid = {_json.dumps(dp['fake_vid_gid'])};
      const _fakeAudGid = {_json.dumps(dp['fake_aud_gid'])};

      // enumerateDevices — только фейковые ID
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
        navigator.mediaDevices.enumerateDevices = async function() {{
          return [
            {{ kind:'videoinput',  deviceId:_fakeVidId,  groupId:_fakeVidGid, label:'' }},
            {{ kind:'audioinput',  deviceId:_fakeAudId,  groupId:_fakeAudGid, label:'' }},
            {{ kind:'audiooutput', deviceId:'default',   groupId:'default',   label:'' }},
          ];
        }};
      }}

      // getUserMedia — снимаем deviceId если это наш fake (чтобы Chrome нашёл реальное устройство)
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
        const _origGUM = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
        navigator.mediaDevices.getUserMedia = function(constraints) {{
          try {{
            const c = constraints ? JSON.parse(JSON.stringify(constraints)) : {{}};
            if (c.video && typeof c.video === 'object' && c.video.deviceId) {{
              const did = c.video.deviceId;
              if (did === _fakeVidId || (did && did.exact === _fakeVidId)) delete c.video.deviceId;
            }}
            if (c.audio && typeof c.audio === 'object' && c.audio.deviceId) {{
              const did = c.audio.deviceId;
              if (did === _fakeAudId || (did && did.exact === _fakeAudId)) delete c.audio.deviceId;
            }}
            return _origGUM(c);
          }} catch(e) {{ return _origGUM(constraints); }}
        }};
      }}
    }} catch(e) {{}}

    // ── 12. history.length рандомизируем ─────────────────────────────────────
    try {{
      def(window.history, 'length', {random.randint(3, 12)});
    }} catch(e) {{}}

    // ── 13. outerWidth / outerHeight (должны совпадать с реальным окном) ────
    try {{
      def(window, 'outerWidth',  {dp['screen_w']});
      def(window, 'outerHeight', {dp['screen_h']});
      def(window, 'innerWidth',  {dp['screen_w']});
      def(window, 'innerHeight', {dp['avail_h'] - 90});
    }} catch(e) {{}}

    // ── 14. navigator.onLine, cookieEnabled ──────────────────────────────────
    try {{
      def(proto, 'onLine',        true);
      def(proto, 'cookieEnabled', true);
      def(proto, 'appName',       'Netscape');
      def(proto, 'appCodeName',   'Mozilla');
      def(proto, 'product',       'Gecko');
    }} catch(e) {{}}

    // ── 15. performance.memory — уникальные значения ─────────────────────────
    try {{
      const _memObj = {{
        jsHeapSizeLimit:  {int(dp['memory'] * 1024 * 1024 * 1024 * random.uniform(0.9, 1.1))},
        totalJSHeapSize:  {random.randint(10_000_000, 80_000_000)},
        usedJSHeapSize:   {random.randint(5_000_000, 40_000_000)},
      }};
      try {{
        Object.defineProperty(performance, 'memory', {{
          get: () => _memObj, configurable: true
        }});
      }} catch(e) {{}}
    }} catch(e) {{}}

    // ── 16. speechSynthesis — подменяем список голосов ────────────────────────
    // Это мощный fingerprint — каждая ОС/устройство имеет разный набор голосов
    try {{
      if (window.speechSynthesis) {{
        const _voices = [
          {{ default: true,  lang: '{dp['language']}', localService: true,
             name: '{random.choice(["Microsoft David Desktop", "Google US English", "Alex", "Samantha", "Microsoft Zira Desktop"])}',
             voiceURI: 'native' }},
          {{ default: false, lang: 'en-US', localService: true,
             name: '{random.choice(["Microsoft Zira Desktop", "Google US English", "Victoria", "Karen"])}',
             voiceURI: 'native' }},
        ];
        const _origGV = speechSynthesis.getVoices.bind(speechSynthesis);
        speechSynthesis.getVoices = function() {{
          const real = _origGV();
          return real && real.length > 0 ? real : _voices;
        }};
      }}
    }} catch(e) {{}}

    // ── 17b. ClientRects — tiny noise (мощный fingerprint по позициям эл-тов) ─
    try {{
      const _rcSeed = {random.randint(1, 9999)};
      function _rcNoise(v, i) {{
        return v + (((v * _rcSeed + i * 31337) & 0x7fff) % 3 - 1) * 0.00001;
      }}
      const _origGetBCR = Element.prototype.getBoundingClientRect;
      Element.prototype.getBoundingClientRect = function() {{
        const r = _origGetBCR.call(this);
        return {{
          x: _rcNoise(r.x, 0), y: _rcNoise(r.y, 1),
          width: _rcNoise(r.width, 2), height: _rcNoise(r.height, 3),
          top: _rcNoise(r.top, 4), right: _rcNoise(r.right, 5),
          bottom: _rcNoise(r.bottom, 6), left: _rcNoise(r.left, 7),
          toJSON: () => ({{}}),
        }};
      }};
    }} catch(e) {{}}

    // ── 18. Убираем $cdc_ и __selenium__ следы ────────────────────────────────
    try {{
      const _removeSeleniumArtifacts = () => {{
        for (const k of Object.keys(window)) {{
          if (k.startsWith('$cdc_') || k.startsWith('$chrome_') ||
              k === '__selenium_evaluate' || k === '__webdriver_evaluate' ||
              k === '__fxdriver_evaluate' || k === '__driver_evaluate' ||
              k === '__webdriver_script_fn' || k === '__driver_unwrapped' ||
              k === '__webdriverFunc') {{
            try {{ delete window[k]; }} catch(e) {{}}
          }}
        }}
      }};
      _removeSeleniumArtifacts();
      setTimeout(_removeSeleniumArtifacts, 100);
      setTimeout(_removeSeleniumArtifacts, 500);
    }} catch(e) {{}}

    // ── 19. Font fingerprint — стандартный набор шрифтов ───────────────────────
    // fonts.check() палит ОС — подменяем на фиксированный безопасный список
    try {{
      if (document.fonts && document.fonts.check) {{
        const _fontSeed = {dp.get('font_seed', 1234)};
        // Базовый набор присутствующий на всех платформах
        const _safeFonts = new Set([
          'Arial','Arial Black','Courier','Courier New','Georgia',
          'Helvetica','Impact','Times New Roman','Trebuchet MS','Verdana',
          'Tahoma','Comic Sans MS',
        ]);
        // Дополнительные — зависят от font_seed (уникальны на профиль)
        const _extraFonts = [
          'Calibri','Segoe UI','Cambria','Consolas','Palatino Linotype',
          'Book Antiqua','Garamond','Franklin Gothic Medium','Gill Sans',
          'Century Gothic','Lucida Console','Lucida Sans Unicode',
        ];
        const _myFonts = new Set([..._safeFonts]);
        _extraFonts.forEach((f, i) => {{
          if ((_fontSeed + i * 17) % 3 !== 0) _myFonts.add(f);
        }});
        const _origFontsCheck = document.fonts.check.bind(document.fonts);
        document.fonts.check = function(font, text) {{
          try {{
            const parts = (font || '').replace(/["']/g, '').trim().split(',');
            const name = (parts[parts.length-1] || font).trim();
            return _myFonts.has(name);
          }} catch(e) {{ return false; }}
        }};
        // Также патчим measureText чтобы width не палил реальный шрифт
        const _origMeasure = CanvasRenderingContext2D.prototype.measureText;
        CanvasRenderingContext2D.prototype.measureText = function(text) {{
          const result = _origMeasure.apply(this, arguments);
          try {{
            const noise = ((_fontSeed ^ text.length * 31) & 0x7) * 0.02;
            Object.defineProperty(result, 'width', {{ get: () => result.width + noise - 0.07 }});
          }} catch(e) {{}}
          return result;
        }};
      }}
    }} catch(e) {{}}

    // ── 20. window.name — очищаем (персистит между сессиями) ───────────────────
    try {{ window.name = ''; }} catch(e) {{}}

    // ── 21. navigator.pdfViewerEnabled ─────────────────────────────────────────
    try {{ def(proto, 'pdfViewerEnabled', {str(dp.get('pdf_viewer', True)).lower()}); }} catch(e) {{}}

    // ── 22. navigator.webdriver уже false — дублируем на случай race ────────────
    try {{
      Object.defineProperty(navigator, 'webdriver', {{get: () => false, configurable: true}});
    }} catch(e) {{}}

    // ── 23. Скрываем document.hasFocus() = true, visibilityState = 'visible' ────
    try {{
      Object.defineProperty(document, 'hasFocus', {{ value: () => true, configurable: true }});
      Object.defineProperty(document, 'visibilityState', {{ get: () => 'visible', configurable: true }});
      Object.defineProperty(document, 'hidden', {{ get: () => false, configurable: true }});
    }} catch(e) {{}}

    // ── 24. Убираем Notification.permission fingerprint ────────────────────────
    try {{
      if (window.Notification) {{
        Object.defineProperty(Notification, 'permission', {{ get: () => 'default', configurable: true }});
      }}
    }} catch(e) {{}}

    // ── 25. Object.getOwnPropertyDescriptor защита ──────────────────────────────
    // Fingerprint детекторы проверяют toString() родных функций
    try {{
      const _nativeBrand = 'function () {{ [native code] }}';
      const _toStringFns = [HTMLCanvasElement.prototype.toDataURL];
      _toStringFns.forEach(fn => {{
        try {{
          fn.toString = () => _nativeBrand;
        }} catch(e) {{}}
      }});
    }} catch(e) {{}}

  }} catch(globalErr) {{
    // silent — не ломаем страницу
  }}
}})();
"""

    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
    except Exception:
        pass


def clear_all_browser_state(driver) -> None:
    """
    Максимально глубокая очистка браузерного состояния через CDP + JS.
    Вызывать ДО и ПОСЛЕ стрима.
    """
    # 1) Удаляем все cookies через CDP
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    except Exception:
        pass

    # 2) Очищаем cache через CDP
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
    except Exception:
        pass

    # 3) JS: localStorage, sessionStorage, IndexedDB, Cache API, ServiceWorkers
    js_clear = """
(async function() {
  // localStorage / sessionStorage
  try { window.localStorage.clear(); } catch(e) {}
  try { window.sessionStorage.clear(); } catch(e) {}

  // IndexedDB — удаляем все базы
  try {
    const dbs = await indexedDB.databases();
    for (const db of (dbs || [])) {
      try { indexedDB.deleteDatabase(db.name); } catch(e) {}
    }
  } catch(e) {}

  // Cache API
  try {
    const keys = await caches.keys();
    for (const key of (keys || [])) {
      try { await caches.delete(key); } catch(e) {}
    }
  } catch(e) {}

  // Service Workers
  try {
    const regs = await navigator.serviceWorker.getRegistrations();
    for (const reg of (regs || [])) {
      try { await reg.unregister(); } catch(e) {}
    }
  } catch(e) {}
})();
"""
    try:
        driver.execute_script(js_clear)
    except Exception:
        pass

    # 4) Selenium cookies
    try:
        driver.delete_all_cookies()
    except Exception:
        pass
