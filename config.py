import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"].rstrip("/")
# v7 server: per-organisation API key, format `kpf_<prefix>_<secret>`.
# Issued once by the org admin and stored only as a salted hash server-side.
API_KEY = os.environ["API_KEY"]
