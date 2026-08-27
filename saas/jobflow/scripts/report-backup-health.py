#!/usr/bin/env python3
"""Send status only; never send database contents or logs."""
import argparse
import os
from pathlib import Path
import re
import stat
import sys
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def send(action, path):
    info = path.stat()
    if path.is_symlink() or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError("Unsafe credential permissions")
    url = path.read_text().strip()
    if not re.fullmatch(
        r"https://hc-ping\.com/[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
        url,
    ):
        raise ValueError("Invalid heartbeat URL")
    if action == "failure":
        url += "/fail"
    request = urllib.request.Request(url, data=b"", method="POST")
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("Heartbeat rejected")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("success", "failure"))
    args = parser.parse_args()
    try:
        send(args.action, Path.home() / ".config/fieldlookers/healthchecks-ping-url")
    except Exception as error:
        print("External backup heartbeat failed: " + type(error).__name__, file=sys.stderr)
        return 1
    print("External backup heartbeat accepted: " + args.action)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
