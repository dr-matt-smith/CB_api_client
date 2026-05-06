import argparse
import os
import re
import sys
import zipfile
from urllib.parse import quote

import certifi
import requests

from config import BASE_URL, PASSWORD, USERNAME


def login():
    session = requests.Session()
    session.verify = certifi.where()
    session.auth = (USERNAME, PASSWORD)
    session.get(f"{BASE_URL}/admin/login/")
    csrf_token = session.cookies.get("csrftoken")
    response = session.post(f"{BASE_URL}/admin/login/", data={
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf_token,
        "next": "/admin/",
    })
    if "Log in" in response.text:
        print("Login failed. Check your credentials in config.py.")
        sys.exit(1)
    return session


def read_package_name(zip_path):
    """Read the package name from package.toml inside the ZIP.

    The server enforces validation too, but reading client-side lets us
    construct the upload URL (which now requires the name) and gives a
    clearer error on a doomed file.
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            toml_name = next(
                (n for n in zf.namelist()
                 if n == "package.toml" or n.endswith("/package.toml")),
                None,
            )
            if not toml_name:
                print("Invalid package: ZIP does not contain a 'package.toml' file.")
                sys.exit(1)
            text = zf.read(toml_name).decode("utf-8", errors="replace")
    except zipfile.BadZipFile:
        print(f"Not a valid ZIP file: {zip_path}")
        sys.exit(1)

    match = re.search(r"^\s*name\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
    if not match:
        print("Could not read package name from 'package.toml'.")
        sys.exit(1)
    return match.group(1)


def upload_package(session, file_path, summary=None):
    filename = os.path.basename(file_path)
    pkg_name = read_package_name(file_path)
    url = f"{BASE_URL}/api/packages/{quote(pkg_name, safe='')}/versions/"
    print(f"  POST {url}")

    data = {}
    if summary:
        data["summary"] = summary

    with open(file_path, "rb") as f:
        response = session.post(
            url,
            files={"file": (filename, f, "application/zip")},
            data=data,
            headers={"X-CSRFToken": session.cookies.get("csrftoken")},
        )

    if response.status_code in (200, 201):
        print(f"Success ({response.status_code}):")
        try:
            payload = response.json()
        except ValueError:
            print(response.text)
            return

        name = payload.get("package") or payload.get("name")
        version = payload.get("version")
        author = payload.get("author")
        download_url = payload.get("download_url")
        public_url = payload.get("public_url")

        if name and version is not None:
            print(f"  {name} v{version}" + (f" (author: {author})" if author else ""))
        if download_url:
            full = download_url if download_url.startswith("http") else f"{BASE_URL}{download_url}"
            print(f"  Download: {full}")
        if public_url:
            full = public_url if public_url.startswith("http") else f"{BASE_URL}{public_url}"
            print(f"  Public:   {full}")
        if not (name or download_url):
            print(payload)
    else:
        print(f"Upload failed ({response.status_code}): {response.text}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Upload a package ZIP to the v4 /api/packages/<name>/versions/ endpoint."
    )
    parser.add_argument("file", help="Path to the package ZIP (must contain package.toml)")
    parser.add_argument(
        "--summary",
        "-m",
        help="Optional summary message for this version.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    session = login()
    upload_package(session, args.file, summary=args.summary)


if __name__ == "__main__":
    main()
