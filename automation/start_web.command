#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install -r requirements-safe.txt
python3 web_launcher.py
