#!/usr/bin/env python3

import argparse
from getpass import getpass
import http.cookiejar
import json
from pathlib import Path
import stat
import urllib.error
import urllib.request


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Create a temporary authenticated cookie jar for "
            "FieldLookers release smoke verification."
        )
    )
    parser.add_argument(
        "--base-url",
        default="https://jobflow.fieldlookers.com",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    base_url = arguments.base_url.rstrip("/")
    output = arguments.output.expanduser().resolve()

    email = input("Platform administrator email: ").strip().lower()
    password = getpass("Platform administrator password: ")

    if not email or not password:
        raise SystemExit("Email and password are required")

    cookie_jar = http.cookiejar.MozillaCookieJar(str(output))
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )

    payload = json.dumps(
        {
            "email": email,
            "password": password,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{base_url}/api/v1/auth/login",
        data=payload,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with opener.open(request, timeout=20) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"Authentication failed with HTTP {error.code}"
        ) from None
    except urllib.error.URLError as error:
        raise SystemExit(
            f"Authentication request failed: {error.reason}"
        ) from None

    if status != 200:
        raise SystemExit(
            f"Authentication failed with HTTP {status}"
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    cookie_jar.save(
        ignore_discard=True,
        ignore_expires=True,
    )
    output.chmod(
        stat.S_IRUSR
        | stat.S_IWUSR
    )

    print(
        "Authenticated smoke-session cookie created at "
        f"{output}"
    )
    print(
        "Delete this file immediately after release verification."
    )


if __name__ == "__main__":
    main()
