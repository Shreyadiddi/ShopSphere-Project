from pathlib import Path
import pandas as pd

def main(project_root=None):
    #Find the project folder

    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent
    else:
        project_root = Path(project_root)

    PROJECT_ROOT = project_root

    #Locate the customer data file
    data_file = PROJECT_ROOT / "data" / "customers_dirty.csv"


    if not data_file.exists():
        raise FileNotFoundError(
            f"Raw customer data file not found: {data_file}"
        )
    #Read the CSV into DataFrame
    customers = pd.read_csv(data_file)

    required_columns = {
        "customer_id",
        "customer_name",
        "city",
        "signup_date",
    }

    missing_columns = required_columns - set(customers.columns)

    if missing_columns:
        raise ValueError(
            f"Raw CSV is missing required columns: {sorted(missing_columns)}"
        )

    if customers.empty:
        raise ValueError("Raw CSV contains no customer records.")

    # Clean extra spaces from customer names
    customers["customer_name"] = (
        customers["customer_name"]
        .apply(lambda value: value.strip() if isinstance(value, str) else value)
    )

    # Clean extra spaces from city names
    customers["city"] =(
        customers["city"]
        .apply(
            lambda value: value.strip().title()
            if isinstance(value, str)
            else value
        )
    )

    print("\nCLEANED CUSTOMER NAMES")
    print(customers["customer_name"])

    print("\nCLEANED CITY NAMES")
    print(customers["city"])

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

    print("\n MISSING SIGNUP DATES")
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
    output_file = PROJECT_ROOT / "data" / "clean" / "customers_clean.csv"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    clean_customers.to_csv(output_file, index=False)

    print("\nCLEANED DATA SAVED")
    print("Output file:", output_file)

    # Create quarantine records and record why each row was rejected
    quarantine_reasons = {
        index: [] for index in customers.index
    }

    # Identify exact duplicate rows, keeping the first occurrence
    exact_duplicate_mask = customers.duplicated(keep="first")

    for index in customers.index[exact_duplicate_mask]:
        quarantine_reasons[index].append("exact_duplicate_row")

    # Identify missing customer names
    missing_name_mask = customers["customer_name"].isnull()

    for index in customers.index[missing_name_mask]:
        quarantine_reasons[index].append("missing_customer_name")

    # Identofy missing cities
    missing_city_mask = customers["city"].isnull()

    for index in customers.index[missing_city_mask]:
        quarantine_reasons[index].append("missing_city")

    # Identify missing or invalid signup dates
    parsed_dates = pd.to_datetime(
        customers["signup_date"],
        errors="coerce"
    )

    missing_date_mask = (
        customers["signup_date"].isnull()
        | customers["signup_date"].astype(str).str.strip().eq("")
    )

    invalid_date_mask = ~missing_date_mask & parsed_dates.isnull()

    for index in customers.index[missing_date_mask]:
        quarantine_reasons[index].append("missing_signup_date")

    for index in customers.index[invalid_date_mask]:
        quarantine_reasons[index].append("invalid_signup_date")

    # Select rows that have at least one quarantine reason
    quarantine_mask = pd.Series(
        [bool(quarantine_reasons[index]) for index in customers.index],
        index=customers.index
    )

    quarantine_customers = customers.loc[quarantine_mask].copy()

    # Add the reason or reasons for each quarantined row
    quarantine_customers["quarantine_reason"] = [
        "; ".join(quarantine_reasons[index])
        for index in quarantine_customers.index
    ]

    # Save the quarantine dataset
    quarantine_file = (
            PROJECT_ROOT / "data" / "quarantine" / "customers_quarantine.csv"
    )

    quarantine_file.parent.mkdir(parents=True, exist_ok=True)
    quarantine_customers.to_csv(quarantine_file, index=False)

    print("\nQUARANTINE DATA SAVED")
    print("Quarantined records:", len(quarantine_customers))
    print("output file:", quarantine_file)

    # Reconcile the raw, clean, and quarantined record counts
    raw_count = len(customers)
    clean_count = len(clean_customers)
    quarantine_count = len(quarantine_customers)

    print("\nRECORD RECONCILIATION")
    print("Raw records:", raw_count)
    print("Clean records:", clean_count)
    print("Quarantine records:", quarantine_count)
    print("Clean + quarantine:", clean_count + quarantine_count)

    if raw_count != clean_count + quarantine_count:
        raise ValueError(
            "Record Reconcilition failed: "
            "some records are missing or counted more than once."
        )
    print("Record count reconciliation passed!")

if __name__ == "__main__":
    main()