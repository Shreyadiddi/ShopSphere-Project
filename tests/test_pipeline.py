from unittest.mock import patch
import pytest
from src import run_pipeline
from pathlib import Path
import pandas as pd

def test_pipeline_stops_if_cleaning_fails():
    with patch.object(
        run_pipeline,
        "clean_data",
        side_effect = ValueError("Simulated cleaning failure"),
    ) as mock_clean, patch.object(
        run_pipeline,
        "load_data",
    ) as mock_load:

        with pytest.raises(ValueError, match="Simulated cleaning failure"):
            run_pipeline.main()

        mock_clean.assert_called_once()
        mock_load.assert_not_called()


def test_pipeline_reports_load_failure(capsys):
    with patch.object(run_pipeline, "clean_data") as mock_clean, \
        patch.object(
            run_pipeline,
            "load_data",
            side_effect=RuntimeError("Simulated database failure"),
        ) as mock_load:

        with pytest.raises(
            RuntimeError,
            match="Simulated database failure",
        ):

            run_pipeline.main()

        mock_clean.assert_called_once()
        mock_load.assert_called_once()

    output = capsys.readouterr().out
    assert "pipeline FAILED" in output
    assert "Completed Successfully" not in output

def test_cleaning_fails_if_raw_is_missing(tmp_path):
    from src import inspect_data

    with pytest.raises(
        FileNotFoundError,
        match="Raw customer data file not found",
    ):
        inspect_data.main(project_root=tmp_path)

def test_cleaning_fails_if_required_column_is_missing(tmp_path):
    import pandas as pd
    from src import inspect_data

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    #Create a CSV missing the signup_date column
    customers = pd.DataFrame({
        "customer_id": [201],
        "customer_name": ["Riya Sharma"],
        "city": ["Mumbai",]
    })

    customers.to_csv(data_dir / "customers_dirty.csv", index=False)

    with pytest.raises(
        ValueError,
        match="Raw CSV is missing required columns",
    ):
        inspect_data.main(project_root=tmp_path)

def test_cleaning_fails_if_csv_is_empty(tmp_path):
    import pandas as pd
    from src import inspect_data

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    # Create a CSV with the required columns but no rows
    customers = pd.DataFrame(columns=[
        "customer_id",
        "customer_name",
        "city",
        "signup_date",
    ])

    customers.to_csv(
        data_dir / "customers_dirty.csv",
        index=False,
    )

    with pytest.raises(
        ValueError,
        match="Raw CSV contains no customer records",
    ):
        inspect_data.main(project_root=tmp_path)

def test_cleaning_quarantines_invalid_signup_date(tmp_path):
    import pandas as pd
    from src import inspect_data

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    customers = pd.DataFrame({
        "customer_id": [203],
        "customer_name": ["Ananya Rao"],
        "city": ["Delhi"],
        "signup_date": ["2025-02-30"],
    })

    customers.to_csv(
        data_dir / "customers_dirty.csv",
        index=False,
    )

    inspect_data.main(project_root=tmp_path)

    quarantine_file = (
        data_dir / "quarantine" / "customers_quarantine.csv"
    )
    quarantine = pd.read_csv(quarantine_file)

    assert len(quarantine) == 1
    assert quarantine.loc[0, "customer_id"] == 203
    assert quarantine.loc[0, "quarantine_reason"] == "invalid_signup_date"

def test_cleaning_quarantines_duplicate_records(tmp_path):
    import pandas as pd
    from src import inspect_data

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    customers = pd.DataFrame({
        "customer_id": [201, 201],
        "customer_name": ["Riya Sharma", "Riya Sharma"],
        "city": ["Mumbai", "Mumbai"],
        "signup_date": ["2025-01-10", "2025-01-10"],
    })

    customers.to_csv(
        data_dir / "customers_dirty.csv",
        index=False,
    )

    inspect_data.main(project_root=tmp_path)

    clean_file = data_dir / "clean" / "customers_clean.csv"
    quarantine_file = (
        data_dir / "quarantine" / "customers_quarantine.csv"
    )

    clean = pd.read_csv(clean_file)
    quarantine = pd.read_csv(quarantine_file)

    assert len(clean) == 1
    assert len(quarantine) == 1
    assert quarantine.loc[0, "quarantine_reason"] == "exact_duplicate_row"

def test_cleaning_quarantines_missing_customer_name(tmp_path):
    import pandas as pd
    from src import inspect_data

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    customers = pd.DataFrame({
        "customer_id": [204],
        "customer_name": [None],
        "city": ["Hyderabad"],
        "signup_date": ["2025-03-12"],
    })

    customers.to_csv(
        data_dir / "customers_dirty.csv",
        index=False,
    )

    inspect_data.main(project_root=tmp_path)

    quarantine_file = (
        data_dir / "quarantine" / "customers_quarantine.csv"
    )
    quarantine = pd.read_csv(quarantine_file)

    assert len(quarantine) == 1
    assert quarantine.loc[0, "customer_id"] == 204
    assert "missing_customer_name" in quarantine.loc[0, "quarantine_reason"]

def test_cleaning_quarantines_missing_city(tmp_path):
    import pandas as pd
    from src import inspect_data

    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    customers = pd.DataFrame({
        "customer_id": [205],
        "customer_name": ["Dev Mehta"],
        "city": [None],
        "signup_date": ["2025-04-01"],
    })

    customers.to_csv(
        data_dir / "customers_dirty.csv",
        index=False,
    )

    inspect_data.main(project_root=tmp_path)

    quarantine_file = (
        data_dir / "quarantine" / "customers_quarantine.csv"
    )
    quarantine = pd.read_csv(quarantine_file)

    assert len(quarantine) == 1
    assert quarantine.loc[0, "customer_id"] == 205
    assert quarantine["quarantine_reason"].notna().all()

def test_loader_rejects_invalid_signup_date():
    import pandas as pd
    from src.load_customers import validate_signup_dates

    customers = pd.DataFrame({
        "customer_id": [301],
        "signup_date": ["2025-02-30"],
    })

    with pytest.raises(ValueError, match="Invalid signup dates found"):
        validate_signup_dates(customers)

def test_loader_rejects_missing_customer_name():
    import pandas as pd
    from src.load_customers import validate_missing_values

    customers = pd.DataFrame({
        "customer_id": [302],
        "customer_name": [None],
        "city": ["Pune"],
        "signup_date": ["2025-05-10"],
    })

    with pytest.raises(
        ValueError,
        match="Missing values found",
    ):
        validate_missing_values(customers)

def test_loader_rejects_missing_city():
    import pandas as pd
    from src.load_customers import validate_missing_values

    customers = pd.DataFrame({
        "customer_id": [303],
        "customer_name": ["Aarav Shah"],
        "city": [None],
        "signup_date": ["2025-05-12"],
    })

    with pytest.raises(
        ValueError,
        match="Missing values found",
    ):
        validate_missing_values(customers)

def test_loader_rolls_back_if_insert_fails(tmp_path):
    from unittest.mock import MagicMock, patch
    from src import load_customers

    # Use a temporary project directory
    data_dir = tmp_path / "data" / "clean"
    data_dir.mkdir(parents=True)

    # Provide one valid customer record
    customers = pd.DataFrame({
        "customer_id": [401],
        "customer_name": ["Test Customer"],
        "city": ["Pune"],
        "signup_date": ["2025-05-10"],
    })
    customers.to_csv(
        data_dir / "customers_clean.csv",
        index=False,
    )

    mock_connection = MagicMock()
    mock_cursor = mock_connection.cursor.return_value
    mock_cursor.execute.side_effect = RuntimeError("Simulated insert failure")

    with patch.object(load_customers, "load_dotenv"), \
         patch.object(load_customers.psycopg2, "connect",
                      return_value=mock_connection):
        with pytest.raises(RuntimeError, match="Simulated insert failure"):
            load_customers.main()

    mock_connection.rollback.assert_called_once()
    mock_connection.close.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_loader_rejects_missing_database_credentials(tmp_path):
    from unittest.mock import patch
    from src import load_customers

    # Create a temporary project with a valid clean CSV
    data_dir = tmp_path / "data" / "clean"
    data_dir.mkdir(parents=True)

    customers = pd.DataFrame({
        "customer_id": [501],
        "customer_name": ["Test Customer"],
        "city": ["Pune"],
        "signup_date": ["2025-05-10"],
    })
    customers.to_csv(
        data_dir / "customers_clean.csv",
        index=False,
    )

    with patch.object(load_customers, "load_dotenv"), \
         patch.object(load_customers.os, "getenv", return_value=None), \
         patch.object(load_customers.psycopg2, "connect") as mock_connect:

        with pytest.raises(
            ValueError,
            match="Missing database environment variables",
        ):
            load_customers.main(project_root=tmp_path)

        mock_connect.assert_not_called()
