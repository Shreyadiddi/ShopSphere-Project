import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from the project's .env file
load_dotenv()

try:
    connection = psycopg2.connect(
        host = os.getenv("DB_HOST"),
        port = os.getenv("DB_PORT"),
        database = os.getenv("DB_NAME"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD")
    )

    print("Connected to postgresql successfully")

    connection.close()

except Exception as error:
    print("Connection failed:", error)