import requests
import os
from datetime import datetime
from config import BASE_URL, USERNAME, PASSWORD

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def login():
    session = requests.Session()
    session.verify = False
    session.auth = (USERNAME, PASSWORD)
    login_page = session.get(f"{BASE_URL}/admin/login/")
    csrf_token = session.cookies.get("csrftoken")
    response = session.post(f"{BASE_URL}/admin/login/", data={
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf_token,
        "next": "/admin/",
    })
    if "Log in" in response.text:
        print("Login failed. Check your credentials in config.py.")
        exit(1)
    print(f"Logged in as '{USERNAME}'.\n")
    return session


def get_files(session):
    url = f"{BASE_URL}/api/files/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve file list ({response.status_code})")
        return []
    return response.json()


def list_files(session):
    files = get_files(session)
    if not files:
        print("No files found.")
        return
    print(f"\n{'ID':<6} {'Size':>10}  {'Uploaded':<22}  Filename")
    print("-" * 70)
    for f in files:
        filename = os.path.basename(f["file"])
        size_kb = f["file_size"] / 1024
        uploaded = f["uploaded_at"][:19].replace("T", " ")
        print(f"{f['id']:<6} {size_kb:>9.1f}K  {uploaded:<22}  {filename}")
    print()


def download_file(session):
    files = get_files(session)
    if not files:
        print("No files available to download.")
        return

    print(f"\n{'#':<4} {'ID':<6} {'Size':>10}  Filename")
    print("-" * 50)
    for i, f in enumerate(files, 1):
        filename = os.path.basename(f["file"])
        size_kb = f["file_size"] / 1024
        print(f"{i:<4} {f['id']:<6} {size_kb:>9.1f}K  {filename}")
    print()

    choice = input("Enter number to download (or press Enter to cancel): ").strip()
    if not choice:
        return

    try:
        index = int(choice) - 1
        if index < 0 or index >= len(files):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return

    selected = files[index]
    filename = os.path.basename(selected["file"])

    url = f"{BASE_URL}/api/files/{selected['id']}/"
    print(f"  GET {url}")
    response = session.get(url)
    if response.status_code == 200:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        dest_dir = os.path.join(DOWNLOADS_DIR, timestamp)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)
        with open(dest, "wb") as out:
            out.write(response.content)
        print(f"Downloaded: {filename}\n      -> {dest}")
    else:
        print(f"Download failed ({response.status_code})")


def upload_file(session):
    print("\nUpload options:")
    print("  1 - Choose a file from the uploads/ folder")
    print("  2 - Enter a file path manually")
    choice = input("Select option: ").strip()

    if choice == "1":
        files_in_dir = [f for f in os.listdir(UPLOADS_DIR)
                        if os.path.isfile(os.path.join(UPLOADS_DIR, f))]
        if not files_in_dir:
            print(f"No files found in {UPLOADS_DIR}")
            return
        print()
        for i, name in enumerate(files_in_dir, 1):
            print(f"  {i}. {name}")
        print()
        pick = input("Enter number to upload (or press Enter to cancel): ").strip()
        if not pick:
            return
        try:
            index = int(pick) - 1
            if index < 0 or index >= len(files_in_dir):
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return
        file_path = os.path.join(UPLOADS_DIR, files_in_dir[index])

    elif choice == "2":
        file_path = input("Enter full path to file: ").strip()
        if not file_path:
            return
    else:
        print("Invalid option.")
        return

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    filename = os.path.basename(file_path)
    url = f"{BASE_URL}/api/upload/"
    print(f"  POST {url}")
    with open(file_path, "rb") as f:
        response = session.post(
            url,
            files={"file": (filename, f, "application/octet-stream")},
            headers={"X-CSRFToken": session.cookies.get("csrftoken")},
        )

    if response.status_code == 201:
        data = response.json()
        print(f"Uploaded: {filename} (ID: {data['id']}, {data['file_size']} bytes)")
    else:
        print(f"Upload failed ({response.status_code}): {response.text}")


def main():
    session = login()

    while True:
        print("\n--- File Upload API ---")
        print("  1 - List all files")
        print("  2 - Download a file")
        print("  3 - Upload a file")
        print("  0 - Exit")
        choice = input("\nSelect option: ").strip()

        if choice == "1":
            list_files(session)
        elif choice == "2":
            download_file(session)
        elif choice == "3":
            upload_file(session)
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid option, please try again.")


if __name__ == "__main__":
    main()