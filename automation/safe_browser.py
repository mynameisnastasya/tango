#!/usr/bin/env python3
"""
Safe manual browser launcher.

Opens Tango in a normal Chrome session using a persistent local profile.
No fingerprint spoofing, proxy rotation, VPN switching, OTP scraping,
or automated account registration is performed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / "profiles" / "manual"


def build_driver(headless: bool = False) -> webdriver.Chrome:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1440,1000")

    return webdriver.Chrome(options=options)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open Tango in a normal persistent Chrome profile."
    )
    parser.add_argument(
        "--url",
        default="https://www.tango.me/",
        help="Page to open (default: https://www.tango.me/)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome headlessly for a simple launch check.",
    )
    args = parser.parse_args()

    try:
        driver = build_driver(headless=args.headless)
    except WebDriverException as exc:
        print("Could not start Chrome.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(
            "\nCheck that Google Chrome is installed and run:\n"
            "  python -m pip install -U selenium",
            file=sys.stderr,
        )
        return 2

    try:
        driver.get(args.url)
        print(f"Opened: {driver.current_url}")
        print(f"Profile: {PROFILE_DIR}")
        if args.headless:
            print(f"Title: {driver.title}")
            return 0

        input("Browser is open. Work manually, then press Enter here to close it... ")
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
