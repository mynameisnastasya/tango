# Tango Local Launcher

A local web interface for launching a normal Chrome session with one persistent profile.

## Easiest way

### macOS
Double-click `start_web.command`.

If macOS blocks it the first time, open Terminal in this folder and run:

```bash
chmod +x start_web.command
./start_web.command
```

### Windows
Double-click `start_web.bat`.

The launcher installs the small Python dependencies and opens:

```text
http://127.0.0.1:8765
```

Then press **Запустить Tango**.

## Manual start

```bash
python -m pip install -r automation/requirements-safe.txt
python automation/web_launcher.py
```

## What it does

- gives you a browser-based local control panel;
- launches Google Chrome on the same computer;
- opens Tango;
- keeps one persistent Chrome profile in `automation/profiles/manual/`;
- lets you stop the Chrome session from the page.

The server listens only on `127.0.0.1`, so it is not exposed to the local network or Internet.

This launcher does not implement fingerprint spoofing, proxy/VPN rotation, OTP scraping, or automated account registration.
