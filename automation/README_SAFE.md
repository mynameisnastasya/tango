# Safe local browser mode

This folder contains the uploaded automation sources plus a separate safe/manual launcher.

## What the safe launcher does

`safe_browser.py` opens Tango in a normal Chrome session and keeps one persistent local Chrome profile in:

```text
automation/profiles/manual/
```

It does **not** spoof browser/device fingerprints, rotate proxies or VPN locations, scrape OTP codes, or automate account registration.

## Requirements

- Python 3.10+
- Google Chrome
- Selenium 4.6+

Install Selenium:

```bash
python -m pip install -U selenium
```

## Run

From the repository root:

```bash
python automation/safe_browser.py
```

Or from the `automation` directory:

```bash
python safe_browser.py
```

Selenium Manager will normally download/resolve the matching ChromeDriver automatically.

## Quick launch check

```bash
python automation/safe_browser.py --headless
```

A successful run prints the opened URL and page title.

## Troubleshooting

If Chrome does not start:

```bash
python --version
python -m pip show selenium
python -m pip install -U selenium
```

Make sure Google Chrome itself is installed and can be opened normally.
