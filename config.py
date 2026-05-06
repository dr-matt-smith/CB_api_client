import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"].rstrip("/")
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]