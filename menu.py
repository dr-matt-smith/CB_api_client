import re
import os
import zipfile
from datetime import datetime
from urllib.parse import quote
from config import BASE_URL, AUTHOR
from api import make_session

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "files_to_upload")
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def connect():
    """Build a Workshop-Key session and confirm the key reaches the server."""
    session = make_session()
    url = f"{BASE_URL}/api/whoami"
    response = session.get(url)
    if response.status_code == 401:
        # The hook already printed the hint; stop here.
        exit(1)
    if response.status_code != 200:
        print(f"Could not reach the API ({response.status_code}): {response.text}")
        exit(1)
    try:
        who = response.json()
    except ValueError:
        who = {}
    org_name = who.get("organisation_name") or who.get("organisation") or "?"
    org_slug = who.get("organisation", "")
    author = who.get("author")
    where = f"{org_name} ({org_slug})" if org_slug else org_name
    print(f"Connected to Workshop {where} at {BASE_URL}.")
    if author:
        print(f"  Signed in as: {author}")
    print()
    return session


def get_packages(session):
    url = f"{BASE_URL}/api/packages/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve package list ({response.status_code}): {response.text}")
        return []
    try:
        return response.json()
    except ValueError:
        print("Server returned non-JSON response.")
        return []


def list_packages(session):
    packages = get_packages(session)
    if not packages:
        print("No packages found.")
        return
    print(f"\n{'Name':<30} {'Latest':>7} {'Vers':>5}  {'Author':<20} Uploaded")
    print("-" * 90)
    for p in packages:
        name = p.get("name", "?")
        latest = p.get("latest_version") or {}
        version = latest.get("version", "") if isinstance(latest, dict) else ""
        author = latest.get("author", "") if isinstance(latest, dict) else ""
        uploaded = (latest.get("date") or "")[:19].replace("T", " ") if isinstance(latest, dict) else ""
        count = p.get("versions_count", "")
        print(f"{name:<30} {str(version):>7} {str(count):>5}  {author:<20} {uploaded}")
    print()


def pick_package(session):
    packages = get_packages(session)
    if not packages:
        print("No packages available.")
        return None
    print()
    for i, p in enumerate(packages, 1):
        name = p.get("name", "?")
        latest = p.get("latest_version") or {}
        version = latest.get("version", "") if isinstance(latest, dict) else latest
        print(f"  {i}. {name} (latest v{version})")
    print()
    pick = input("Enter number (or press Enter to cancel): ").strip()
    if not pick:
        return None
    try:
        index = int(pick) - 1
        if index < 0 or index >= len(packages):
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input.")
        return None
    return packages[index].get("name")


def show_package_detail(session):
    name = pick_package(session)
    if not name:
        return
    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    try:
        data = response.json()
    except ValueError:
        print(response.text)
        return

    print(f"\nPackage: {data.get('name', name)}")
    created = (data.get("created_at") or "")[:19].replace("T", " ")
    if created:
        print(f"Created: {created}")
    versions = data.get("versions", [])
    if not versions:
        print("(no versions)")
    else:
        print(f"\n{'Ver':>4}  {'Author':<20} {'Uploaded':<22} {'Del':<5} Summary")
        print("-" * 90)
        for v in versions:
            ver = v.get("version", "?")
            author = v.get("author", "")
            uploaded = (v.get("date") or "")[:19].replace("T", " ")
            deleted = "yes" if v.get("deleted") else ""
            summary = (v.get("summary") or "").replace("\n", " ")
            if len(summary) > 40:
                summary = summary[:37] + "..."
            print(f"{str(ver):>4}  {author:<20} {uploaded:<22} {deleted:<5} {summary}")

    aliases = data.get("aliases", [])
    if aliases:
        print(f"\n{'Alias':<20} {'Version':>7}")
        print("-" * 30)
        for a in aliases:
            print(f"{a.get('name', '?'):<20} {str(a.get('version', '')):>7}")
    print()


def show_package_history(session):
    name = pick_package(session)
    if not name:
        return
    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/history/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    print()
    print(response.text)


def show_version_history(session):
    name = pick_package(session)
    if not name:
        return
    version_input = input("Enter version number (history as-of): ").strip()
    if not version_input:
        return
    try:
        version = int(version_input)
    except ValueError:
        print("Invalid version.")
        return
    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/{version}/history/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    print()
    print(response.text)


def list_package_versions(session):
    name = pick_package(session)
    if not name:
        return
    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    try:
        versions = response.json()
    except ValueError:
        print(response.text)
        return
    if not versions:
        print("(no versions)")
        return
    print(f"\n{'Ver':>4}  {'Author':<20} {'Uploaded':<22} {'Del':<5} Summary")
    print("-" * 90)
    for v in versions:
        ver = v.get("version", "?")
        author = v.get("author", "")
        uploaded = (v.get("date") or "")[:19].replace("T", " ")
        deleted = "yes" if v.get("deleted") else ""
        summary = (v.get("summary") or "").replace("\n", " ")
        if len(summary) > 40:
            summary = summary[:37] + "..."
        print(f"{str(ver):>4}  {author:<20} {uploaded:<22} {deleted:<5} {summary}")
    print()


def show_version_detail(session):
    name = pick_package(session)
    if not name:
        return
    version_input = input("Enter version number: ").strip()
    if not version_input:
        return
    try:
        version = int(version_input)
    except ValueError:
        print("Invalid version.")
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/{version}/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    try:
        v = response.json()
    except ValueError:
        print(response.text)
        return

    print()
    print(f"Package:    {name}")
    print(f"Version:    {v.get('version', '?')}")
    print(f"Author:     {v.get('author', '')}")
    uploaded = (v.get("date") or "")[:19].replace("T", " ")
    print(f"Uploaded:   {uploaded}")
    print(f"Deleted:    {'yes' if v.get('deleted') else 'no'}")
    if v.get("delete_reason"):
        print(f"Reason:     {v['delete_reason']}")
    if v.get("content_hash"):
        print(f"Hash:       {v['content_hash']}")
    base = v.get("base")
    if base:
        print(f"Base:       {base.get('name')}@{base.get('version')}")
    else:
        print("Base:       none")
    if v.get("summary"):
        print(f"Summary:    {v['summary']}")
    if v.get("description"):
        print(f"Description:\n{v['description']}")
    print()


def download_package_version(session):
    name = pick_package(session)
    if not name:
        return
    version_input = input("Enter version number to download: ").strip()
    if not version_input:
        return
    try:
        version = int(version_input)
    except ValueError:
        print("Invalid version.")
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/{version}/download/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code == 410:
        print(f"Version is deleted (410 Gone): {response.text}")
        return
    if response.status_code != 200:
        print(f"Download failed ({response.status_code}): {response.text}")
        return

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    dest_dir = os.path.join(DOWNLOADS_DIR, timestamp)
    os.makedirs(dest_dir, exist_ok=True)
    filename = f"{name}_v{version}.zip"
    dest = os.path.join(dest_dir, filename)
    with open(dest, "wb") as out:
        out.write(response.content)
    print(f"Downloaded: {filename}\n      -> {dest}")


def download_package_latest(session):
    name = pick_package(session)
    if not name:
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/latest/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code == 404:
        print(f"No published versions for '{name}'.")
        return
    if response.status_code != 200:
        print(f"Download failed ({response.status_code}): {response.text}")
        return

    version = None
    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r"-v(\d+)\.zip", disposition)
    if match:
        version = match.group(1)

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    dest_dir = os.path.join(DOWNLOADS_DIR, timestamp)
    os.makedirs(dest_dir, exist_ok=True)
    filename = f"{name}_v{version}.zip" if version else f"{name}_latest.zip"
    dest = os.path.join(dest_dir, filename)
    with open(dest, "wb") as out:
        out.write(response.content)
    print(f"Downloaded latest: {filename}\n      -> {dest}")


def _read_package_toml(zip_path):
    """Return (toml_text, error_message). On success error_message is None."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            toml_name = next(
                (n for n in zf.namelist()
                 if n == "package.toml" or n.endswith("/package.toml")),
                None,
            )
            if not toml_name:
                return None, "Invalid package: ZIP does not contain a 'package.toml' file."
            return zf.read(toml_name).decode("utf-8", errors="replace"), None
    except zipfile.BadZipFile:
        return None, f"Not a valid ZIP file: {zip_path}"


def _extract_package_name(toml_text):
    match = re.search(
        r"^\s*name\s*=\s*['\"]([^'\"]+)['\"]",
        toml_text,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def _choose_upload_file():
    """Pick a ZIP from files_to_upload/ or type a path. Returns a path or None."""
    print("\nUpload options:")
    print("  1 - Choose a file from the files_to_upload/ folder")
    print("  2 - Enter a file path manually")
    choice = input("Select option: ").strip()

    if choice == "1":
        files_in_dir = [f for f in os.listdir(UPLOADS_DIR)
                        if os.path.isfile(os.path.join(UPLOADS_DIR, f))]
        if not files_in_dir:
            print(f"No files found in {UPLOADS_DIR}")
            return None
        print()
        for i, fname in enumerate(files_in_dir, 1):
            print(f"  {i}. {fname}")
        print()
        pick = input("Enter number to upload (or press Enter to cancel): ").strip()
        if not pick:
            return None
        try:
            index = int(pick) - 1
            if index < 0 or index >= len(files_in_dir):
                print("Invalid selection.")
                return None
        except ValueError:
            print("Invalid input.")
            return None
        file_path = os.path.join(UPLOADS_DIR, files_in_dir[index])
    elif choice == "2":
        file_path = input("Enter full path to file: ").strip()
        if not file_path:
            return None
    else:
        print("Invalid option.")
        return None

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return None
    return file_path


def upload_package(session):
    file_path = _choose_upload_file()
    if not file_path:
        return

    toml_text, err = _read_package_toml(file_path)
    if err:
        print(err)
        return
    pkg_name = _extract_package_name(toml_text)
    if not pkg_name:
        print("Could not read package name from 'package.toml'.")
        return

    summary = input("Optional summary message (press Enter to skip): ").strip()

    filename = os.path.basename(file_path)
    url = f"{BASE_URL}/api/packages/{quote(pkg_name, safe='')}/versions/"
    print(f"  POST {url}")
    data = {}
    if summary:
        data["summary"] = summary
    if AUTHOR:
        data["author"] = AUTHOR
    with open(file_path, "rb") as f:
        response = session.post(
            url,
            files={"file": (filename, f, "application/zip")},
            data=data,
        )

    if response.status_code in (200, 201):
        try:
            payload = response.json()
        except ValueError:
            print(response.text)
            return
        name = payload.get("package", "?")
        version = payload.get("version", "?")
        author = payload.get("author", "")
        print(f"Uploaded: {name} v{version}" + (f" (author: {author})" if author else ""))
        download_url = payload.get("download_url")
        if download_url:
            full = download_url if download_url.startswith("http") else f"{BASE_URL}{download_url}"
            print(f"  Download: {full}")
        if payload.get("content_hash"):
            print(f"  Hash:     {payload['content_hash']}")
    else:
        print(f"Upload failed ({response.status_code}): {response.text}")


def delete_package(session):
    name = pick_package(session)
    if not name:
        return
    reason = input("Reason (optional): ").strip()
    confirm = input(
        f"Delete entire package '{name}'? This tombstones ALL versions and removes "
        "their ZIP files on the server. (y/N): "
    ).strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/"
    print(f"  DELETE {url}")
    response = session.delete(
        url,
        json={"reason": reason} if reason else {},
    )
    if response.status_code in (200, 204):
        print(f"Deleted package: {name}")
    else:
        print(f"Delete failed ({response.status_code}): {response.text}")


def list_aliases(session):
    name = pick_package(session)
    if not name:
        return
    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/aliases/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    try:
        aliases = response.json()
    except ValueError:
        print(response.text)
        return
    if not aliases:
        print("(no aliases)")
        return
    print(f"\n{'Alias':<20} {'Version':>7}  Updated")
    print("-" * 60)
    for a in aliases:
        updated = (a.get("updated_at") or "")[:19].replace("T", " ")
        print(f"{a.get('name', '?'):<20} {str(a.get('version', '')):>7}  {updated}")
    print()


def set_alias(session):
    name = pick_package(session)
    if not name:
        return
    alias = input("Alias name (lowercase kebab-case, e.g. 'stable'): ").strip()
    if not alias:
        return
    if alias.lower() == "latest":
        print("'latest' is a reserved keyword (server-resolved) and cannot be set.")
        return
    version_input = input("Point alias at version number: ").strip()
    if not version_input:
        return
    try:
        version = int(version_input)
    except ValueError:
        print("Invalid version.")
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/aliases/{quote(alias, safe='')}/"
    print(f"  PUT {url}")
    response = session.put(
        url,
        json={"version": version},
    )
    if response.status_code in (200, 201):
        print(f"Alias '{alias}' -> {name} v{version}")
    else:
        print(f"Set alias failed ({response.status_code}): {response.text}")


def delete_alias(session):
    name = pick_package(session)
    if not name:
        return
    alias = input("Alias name to remove: ").strip()
    if not alias:
        return
    if alias.lower() == "latest":
        print("'latest' is a reserved keyword (server-resolved) and cannot be removed.")
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/aliases/{quote(alias, safe='')}/"
    print(f"  DELETE {url}")
    response = session.delete(url)
    if response.status_code in (200, 204):
        print(f"Removed alias '{alias}' from {name}.")
    else:
        print(f"Delete alias failed ({response.status_code}): {response.text}")


def aliases_menu(session):
    while True:
        print("\n--- Aliases ---")
        print("  1 - List aliases for a package     (GET    /api/packages/{name}/aliases)")
        print("  2 - Set / move alias to a version  (PUT    /api/packages/{name}/aliases/{alias})")
        print("  3 - Remove an alias                (DELETE /api/packages/{name}/aliases/{alias})")
        print("  0 - Back")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            list_aliases(session)
        elif choice == "2":
            set_alias(session)
        elif choice == "3":
            delete_alias(session)
        elif choice == "0":
            return
        else:
            print("Invalid option, please try again.")


def _read_pages_toml(zip_path):
    """Return (publish_path, error_message). On success error_message is None.

    Reads the ``[publish] path`` value from the top-level page manifest in the
    ZIP. The server now accepts the singular ``page.toml`` (preferred) or the
    plural ``pages.toml``, so we look for either (case-insensitive). The server
    validates this too, but reading it client-side gives a clear up-front error
    and lets us show the path that will be published.
    """
    manifest_names = ("page.toml", "pages.toml")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            toml_name = next(
                (n for n in zf.namelist()
                 if n.lower() in manifest_names
                 or any(n.lower().endswith(f"/{m}") for m in manifest_names)),
                None,
            )
            if not toml_name:
                return None, "Invalid page bundle: ZIP does not contain a 'page.toml' file."
            text = zf.read(toml_name).decode("utf-8", errors="replace")
    except zipfile.BadZipFile:
        return None, f"Not a valid ZIP file: {zip_path}"

    match = re.search(r"^\s*path\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
    if not match:
        return None, "page.toml is missing the [publish] path value."
    return match.group(1), None


def get_pages(session):
    url = f"{BASE_URL}/api/pages"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page list ({response.status_code}): {response.text}")
        return []
    try:
        return response.json()
    except ValueError:
        print("Server returned non-JSON response.")
        return []


def list_pages(session):
    pages = get_pages(session)
    if not pages:
        print("No pages published.")
        return
    print(f"\n{'Path':<30} {'Published by':<16} {'Published at':<22} URL")
    print("-" * 100)
    for p in pages:
        path = p.get("path", "?")
        by = p.get("published_by") or ""
        when = (p.get("published_at") or "")[:19].replace("T", " ")
        url = p.get("url") or ""
        full = url if (not url or url.startswith("http")) else f"{BASE_URL}{url}"
        print(f"{path:<30} {by:<16} {when:<22} {full}")
    print()


def pick_page(session):
    pages = get_pages(session)
    if not pages:
        print("No pages published.")
        return None
    print()
    for i, p in enumerate(pages, 1):
        print(f"  {i}. {p.get('path', '?')}")
    print()
    pick = input("Enter number (or press Enter to cancel): ").strip()
    if not pick:
        return None
    try:
        index = int(pick) - 1
        if index < 0 or index >= len(pages):
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input.")
        return None
    return pages[index].get("path")


def publish_page(session):
    file_path = _choose_upload_file()
    if not file_path:
        return

    publish_path, err = _read_pages_toml(file_path)
    if err:
        print(err)
        return
    print(f"This bundle publishes to path: {publish_path}")

    filename = os.path.basename(file_path)
    url = f"{BASE_URL}/api/pages"
    print(f"  POST {url}")
    data = {"path": publish_path}
    if AUTHOR:
        data["author"] = AUTHOR
    with open(file_path, "rb") as f:
        response = session.post(
            url,
            files={"file": (filename, f, "application/zip")},
            data=data,
        )

    if response.status_code in (200, 201):
        try:
            data = response.json()
        except ValueError:
            print(response.text)
            return
        print(f"Published page: {data.get('path', publish_path)}")
        page = data.get("url")
        if page:
            full = page if page.startswith("http") else f"{BASE_URL}{page}"
            print(f"  Page: {full}")
        if data.get("content_hash"):
            print(f"  Hash: {data['content_hash']}")
    elif response.status_code == 409:
        print(f"Path conflict — overlaps an existing page: {response.text}")
    elif response.status_code == 422:
        print(f"Invalid page bundle: {response.text}")
    else:
        print(f"Publish failed ({response.status_code}): {response.text}")


def show_page_detail(session):
    path = pick_page(session)
    if not path:
        return
    url = f"{BASE_URL}/api/pages/{quote(path, safe='/')}"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code == 404:
        print(f"'{path}' is not currently published.")
        return
    if response.status_code != 200:
        print(f"Failed ({response.status_code}): {response.text}")
        return
    try:
        data = response.json()
    except ValueError:
        print(response.text)
        return
    published = (data.get("published_at") or "")[:19].replace("T", " ")
    print(f"\nPath:         {data.get('path', path)}")
    print(f"Published by: {data.get('published_by', '')}")
    print(f"Published at: {published}")
    page = data.get("url")
    if page:
        full = page if page.startswith("http") else f"{BASE_URL}{page}"
        print(f"URL:          {full}")
    if data.get("content_hash"):
        print(f"Hash:         {data['content_hash']}")
    print()


def unpublish_page(session):
    path = pick_page(session)
    if not path:
        return
    confirm = input(
        f"Unpublish '{path}'? This removes the served page files. (y/N): "
    ).strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    url = f"{BASE_URL}/api/pages/{quote(path, safe='/')}"
    print(f"  DELETE {url}")
    response = session.delete(url)
    if response.status_code in (200, 204):
        print(f"Unpublished: {path}")
    else:
        print(f"Unpublish failed ({response.status_code}): {response.text}")


def pages_menu(session):
    while True:
        print("\n--- Pages ---")
        print("  (pages are independent of packages: each page is its own ZIP upload")
        print("   containing a page.toml with [publish].path; served at /pages/<org>/<path>/)")
        print("  1 - Publish a page (upload ZIP)    (POST   /api/pages)")
        print("  2 - List published pages          (GET    /api/pages)")
        print("  3 - Show page detail              (GET    /api/pages/{path})")
        print("  4 - Unpublish a page              (DELETE /api/pages/{path})")
        print("  0 - Back")
        choice = input("\nSelect option: ").strip()
        if choice == "1":
            publish_page(session)
        elif choice == "2":
            list_pages(session)
        elif choice == "3":
            show_page_detail(session)
        elif choice == "4":
            unpublish_page(session)
        elif choice == "0":
            return
        else:
            print("Invalid option, please try again.")


def register_package(session):
    name = input("Package name: ").strip()
    if not name:
        return

    url = f"{BASE_URL}/api/packages/"
    print(f"  POST {url}")
    response = session.post(
        url,
        json={"name": name},
    )
    if response.status_code == 201:
        print(f"Registered: {name}")
    elif response.status_code == 409:
        print(f"Package '{name}' already exists.")
    else:
        print(f"Register failed ({response.status_code}): {response.text}")


def tombstone_version(session):
    name = pick_package(session)
    if not name:
        return
    version_input = input("Enter version number to tombstone: ").strip()
    if not version_input:
        return
    try:
        version = int(version_input)
    except ValueError:
        print("Invalid version.")
        return

    reason = input("Reason (optional but encouraged): ").strip()
    confirm = input(
        f"Tombstone {name} v{version}? This removes the ZIP file on the server. (y/N): "
    ).strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    url = f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/{version}/"
    print(f"  DELETE {url}")
    response = session.delete(
        url,
        json={"reason": reason} if reason else {},
    )
    if response.status_code in (200, 204):
        print(f"Tombstoned: {name} v{version}")
    else:
        print(f"Tombstone failed ({response.status_code}): {response.text}")


def packages_menu(session):
    while True:
        print("\n--- Packages ---")
        print("  1 - List all packages              (GET    /api/packages)")
        print("  2 - Show package metadata          (GET    /api/packages/{name})")
        print("  3 - Register a new (empty) package (POST   /api/packages)")
        print("  4 - Delete entire package          (DELETE /api/packages/{name})")
        print("  0 - Back")
        choice = input("\nSelect option: ").strip()
        if choice == "1":
            list_packages(session)
        elif choice == "2":
            show_package_detail(session)
        elif choice == "3":
            register_package(session)
        elif choice == "4":
            delete_package(session)
        elif choice == "0":
            return
        else:
            print("Invalid option, please try again.")


def versions_menu(session):
    while True:
        print("\n--- Versions ---")
        print("  1 - List versions of a package     (GET    /api/packages/{name}/versions)")
        print("  2 - Show single version detail     (GET    /api/packages/{name}/versions/{n})")
        print("  3 - Upload (publish) a new version (POST   /api/packages/{name}/versions)")
        print("  4 - Download a specific version    (GET    /api/packages/{name}/versions/{n}/download)")
        print("  5 - Tombstone a version            (DELETE /api/packages/{name}/versions/{n})")
        print("  0 - Back")
        choice = input("\nSelect option: ").strip()
        if choice == "1":
            list_package_versions(session)
        elif choice == "2":
            show_version_detail(session)
        elif choice == "3":
            upload_package(session)
        elif choice == "4":
            download_package_version(session)
        elif choice == "5":
            tombstone_version(session)
        elif choice == "0":
            return
        else:
            print("Invalid option, please try again.")


def history_menu(session):
    while True:
        print("\n--- History ---")
        print("  1 - Show full package history      (GET /api/packages/{name}/history)")
        print("  2 - Show history as-of a version   (GET /api/packages/{name}/versions/{n}/history)")
        print("  0 - Back")
        choice = input("\nSelect option: ").strip()
        if choice == "1":
            show_package_history(session)
        elif choice == "2":
            show_version_history(session)
        elif choice == "0":
            return
        else:
            print("Invalid option, please try again.")


def main():
    session = connect()

    while True:
        print("\n=== Packages API ===")
        print("  1 - Packages    (list / show / register / delete)")
        print("  2 - Versions    (list / detail / upload / download / tombstone)")
        print("  3 - Aliases     (list / set / remove)")
        print("  4 - History     (full / as-of-version)")
        print("  5 - Pages       (publish / list / detail / unpublish)")
        print("  6 - Download latest version        (GET  /api/packages/{name}/latest)")
        print("  7 - Upload a package               (POST /api/packages/{name}/versions)")
        print("  0 - Exit")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            packages_menu(session)
        elif choice == "2":
            versions_menu(session)
        elif choice == "3":
            aliases_menu(session)
        elif choice == "4":
            history_menu(session)
        elif choice == "5":
            pages_menu(session)
        elif choice == "6":
            download_package_latest(session)
        elif choice == "7":
            upload_package(session)
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please try again.")


if __name__ == "__main__":
    main()