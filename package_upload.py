import argparse
import os
import re
import sys
import zipfile
from urllib.parse import quote

from config import BASE_URL
from api import make_session


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
        )

    if response.status_code in (200, 201):
        print(f"Success ({response.status_code}):")
        try:
            payload = response.json()
        except ValueError:
            print(response.text)
            return

        name = payload.get("package")
        version = payload.get("version")
        author = payload.get("author")
        download_url = payload.get("download_url")
        content_hash = payload.get("content_hash")

        if name and version is not None:
            print(f"  {name} v{version}" + (f" (author: {author})" if author else ""))
        if download_url:
            full = download_url if download_url.startswith("http") else f"{BASE_URL}{download_url}"
            print(f"  Download: {full}")
        if content_hash:
            print(f"  Hash:     {content_hash}")
        if not (name or download_url):
            print(payload)
    else:
        print(f"Upload failed ({response.status_code}): {response.text}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Upload a package ZIP to the /api/packages/<name>/versions/ endpoint."
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

    session = make_session()
    upload_package(session, args.file, summary=args.summary)


if __name__ == "__main__":
    main()
