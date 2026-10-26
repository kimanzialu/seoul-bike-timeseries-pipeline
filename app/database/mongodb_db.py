import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/",
)

MONGO_DB = os.getenv(
    "MONGO_DB",
    "seoul_bike",
)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
)

database = client[MONGO_DB]


def check_mongodb_connection():
    return client.admin.command("ping")
