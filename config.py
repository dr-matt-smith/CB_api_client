import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"].rstrip("/")
# Workshop Key: per-organisation API key, format `cel_<prefix>_<secret>` (v11).
# Issued once by the org admin and stored only as a salted hash server-side.
# (Older `kpf_<prefix>_<secret>` keys are rejected by the v11 server — re-issue.)
API_KEY = os.environ["API_KEY"]

# Optional Workshop Author: sent as the multipart `author` form field on package
# and page publish so the server records who published (otherwise an org service
# key publishes as "service"). Leave unset to fall back to server-side defaults.
AUTHOR = os.environ.get("AUTHOR")
