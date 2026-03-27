import requests
import certifi
import os
import sys
from config import BASE_URL, USERNAME, PASSWORD


def login():
    session = requests.Session()
    session.verify = certifi.where()
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
    return session


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload.py <path_to_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    session = login()

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
        print(f"Success: '{filename}' uploaded (ID: {data['id']}, {data['file_size']} bytes)")
    else:
        print(f"Failed to upload '{filename}' ({response.status_code}): {response.text}")
        sys.exit(1)
