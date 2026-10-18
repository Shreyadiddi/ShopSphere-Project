import os
from pathlib import Path
import logging
import pandas as pd
import psycopg2 
from dotenv import load_dotenv

logging.basicConfig(
    filename="shopsphere.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Validate required columns
def validate_columns(customers):
    required_columns = [
        "customer_id",
        "customer_name",
        "city",
        "signup_date"
    ]

    missing_columns = set(required_columns) - set(customers.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    logging.info("Required columns validation passed!")

# Validate missing values in required columns
def validate_missing_values(customers):
    required_columns = [
        "customer_id",
        "customer_name",
        "city",
        "signup_date"
    ]

    missing_values = customers[required_columns].isnull().sum()

    if missing_values.any():
        raise ValueError(
            f"Missing values found:\n{missing_values[missing_values > 0]}"
    )
  
    logging.info("Missing value validation passed")

# Validate unique customer IDs
def validate_unique_ids(customers):
    duplicate_ids = customers.loc[
        customers["customer_id"].duplicated(keep=False),
        "customer_id"
    ]

    if not duplicate_ids.empty:
        raise ValueError(
            f"Duplicate customer IDs found: {duplicate_ids.tolist}"
        )

    logging.info("Unique customer ID validation passed!")

# Validate signup dates
def validate_signup_dates(customers):
    parsed_dates = pd.to_datetime(
        customers["signup_date"],
        errors="coerce"
    )

    invalid_dates = parsed_dates.isnull()

    if invalid_dates.any():
        bad_rows = customers.loc[
            invalid_dates, ["customer_id", "signup_date"]
        ]

        raise ValueError(
            f"Invalid signup dates found:\n{bad_rows}"
        )

    logging.info("Signup date validation passed!")

# Find the project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load database credentials from .env
load_dotenv(PROJECT_ROOT / ".env")

# Locate the cleaned customer data
data_file = PROJECT_ROOT / "data" / "clean" / "customers_clean.csv"

# Read the cleaned CSV
customers = pd.read_csv(data_file)

print("Cleaned customer data loaded:")
print(customers)

print("\nNumber of customer records:", len(customers))

validate_columns(customers)
validate_missing_values(customers)
validate_unique_ids(customers)
validate_signup_dates(customers)

# Connect to PostgreSQL
try:
    connection = psycopg2.connect(
        host = os.getenv("DB_HOST"),
        port = os.getenv("DB_PORT"),
        database = os.getenv("DB_NAME"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD")
    )

    cursor = connection.cursor()

    insert_query = """ 
        INSERT INTO public.shopsphere_customers
            (customer_id, customer_name, city, signup_date)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (customer_id) DO NOTHING;
    """
    inserted_count = 0
    skipped_count = 0
    
    for _, row in customers.iterrows():
        cursor.execute(
            insert_query,
            (
                int(row["customer_id"]),
                row["customer_name"],
                row["city"],
                row["signup_date"]
            )
        )

        if cursor.rowcount == 1:
            inserted_count += 1
        else:
            skipped_count += 1

    logging.info(f"Records inserted: {inserted_count}")
    logging.info(f"Records skipped: {skipped_count}")

    connection.commit()
    print("\nCustomer records loaded successfully!")

except Exception as error:
    if "connection" in locals():
        connection.rollback()
    logging.error("Data load failed:", error)

finally:
    if "cursor" in locals():
        cursor.close()
    if "connection" in locals():
        connection.close()