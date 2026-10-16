from pathlib import Path
import pandas as pd

#Find the project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#Locate the customer data file
data_file = PROJECT_ROOT / "data" / "customers_dirty.csv"

#Read the CSV into DataFrame
customers = pd.read_csv(data_file)

# Clean extra spaces from customer names
customers["customer_name"] = (
    customers["customer_name"].str.strip()
)

# Clean extra spaces from city names
customers["city"] =(
    customers["city"]
    .str.strip()
    .str.title()
) 

print("\nCLEANED CUSTOMER NAMES")
print(customers["customer_name"])

print("\nCLEANED CITY NAMES")
print(customers["city"])

#Display basic information
#print("\n Dataset shape:")
#print(customers.shape)
#print("\n Column names:")
#print(customers.columns.tolist())

# 1. Inspect missing values
print("MISSING VALUES")
print(customers.isnull().sum())

# 2. Inspect duplicate customer IDs
print("\n DUPLICATE CUSTTOMER IDs")
print(customers[customers.duplicated(subset="customer_id", keep=False)])

# 3. Detect invalid dates
raw_dates = customers["signup_date"].copy()

parsed_dates = pd.to_datetime(
    raw_dates,
    errors="coerce"
)

missing_dates = raw_dates.isna() | raw_dates.astype(str).str.strip().eq("")
invalid_dates = ~missing_dates & parsed_dates.isna()

print("\n MISSING SUGNUP DATES")
print(customers[missing_dates])

print("\n INVALID SIGNUP DATES")
print(customers[invalid_dates])

# 4. Inspect whitespce in customer names
print("\n NAMES WITH EXTRA SPACES")
print(
    customers[
        customers["customer_name"].fillna("")
        != customers["customer_name"].fillna("").str.strip()
    ]
)

# 5. Inspect city capitalisation
print("\n CITY VALUES")
print(customers["city"].dropna().unique())

# Identify customers with missing names
missing_name = customers["customer_name"].isnull()

#print("\n CUSTOMERS WITH MISSING NAMES")
#print(customers[missing_name])

# Separate records based on whether the customer name is missing
quarantine_customers = customers[missing_name].copy()
valid_customers = customers[~missing_name].copy()

print("\nCUSTOMER FOR REVIEW")
print(quarantine_customers)

print("\nCUSTOMERS WITH NAMES")
print(valid_customers)

print("\nRECORD COUNTS")
print("For review: ", len(quarantine_customers))
print("With names: ",len(valid_customers))

# Indentify all records with duplicate customer IDs
duplicate_ids = customers["customer_id"].duplicated(keep=False)

duplicate_customers = customers[duplicate_ids].copy()

print("\nDUPLICATE CUSTOMER RECORDS")
print(duplicate_customers)

print("\nNUMBER OF RECORDS WITH DUPLICATE IDs")
print(len(duplicate_customers))

# Check for completely identical rows
exact_duplicates = customers.duplicated(keep="first")

print("\nEXACT DUPLICATE ROWS")
print(customers[exact_duplicates])

print("\nNUMBER OF EXACT DUPLICATE ROWS")
print(exact_duplicates.sum())

# Remove exact duplicate rows from a separate DataFrame
customers_deduplicated = customers.drop_duplicates(keep="first").copy()

print("\nROWS BEFORE DEDUPLIACTION")
print(len(customers))

print("\nROWS AFTER DEDUPLICATION")
print(len(customers_deduplicated))

# Convert signup dates into proper datetime values
customers_deduplicated["signup_date"] = pd.to_datetime(
    customers_deduplicated["signup_date"],
    errors = "coerce"
)

# Identify records with invalid or missing signup dates
invalid_date_mask = customers_deduplicated["signup_date"].isnull()

invalid_date_customers = customers_deduplicated[
    invalid_date_mask
].copy()

valid_date_customers = customers_deduplicated[
    ~invalid_date_mask
].copy()

print("\nCUSTOMERS WITH INVALID OR MISSING DATES")
print(invalid_date_customers)

print("\nCUSTOMERS WITH VALID DATES")
print(valid_date_customers)

print("\nINVALID OR MISSING DATE COUNT")
print(len(invalid_date_customers))

# Identify customers woth msising cities
missing_city_mask = valid_date_customers["city"].isnull()

customers_missing_city = valid_date_customers[
    missing_city_mask
].copy()

customers_with_cities = valid_date_customers[
    ~missing_city_mask
].copy()

print("\nCUSTOMERS WITH MISSING CITIES")
print(customers_missing_city)

print("\nCUSTOMERS WITH CITIES")
print(customers_with_cities)

print("\nMISSING CITY COUNT")
print(len(customers_missing_city))

# Build the initial clean customers dataset
clean_customers = valid_date_customers[
    valid_date_customers["customer_name"].notnull()
    & valid_date_customers["city"].notnull()
].copy()

print("\nINITIAL CLEAN CUSTOMERS DATASET")
print(clean_customers)

print("\nCLEAN DATA SUMMARY")
print("Clean customers records:", len(clean_customers))
print("Missing customer names:",
clean_customers["customer_name"].isnull().sum())
print("Missing cities:", clean_customers["city"].isnull().sum())
print("Missing signup dates:", clean_customers["signup_date"].isnull().sum())

# Saave the cleaned dataset
output_file = "data/clean/customers_clean.csv"

clean_customers.to_csv(output_file, index=False)

print("\nCLEANED DATA SAVED")
print("Output file:", output_file)