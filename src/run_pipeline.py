import logging
from .inspect_data import main as clean_data
from .load_customers import main as load_data

def main():
    logging.info("ShopSphere pipeline started!")
    print("\n====== ShopeSphere Pipeline Started======")

    try:
        clean_data()
        print("\nStep 1 complete: Data cleaning and quarantine")

        load_data()
        print("\nStep 2 complete: Data loaded into PostgreSQL")

    except Exception:
        logging.exception("ShopeSphere pipeline failed")
        print("\nShopSphere pipeline FAILED. Check shopsphere.log for details.")
        raise

    logging.info("ShopSphere pipeline completed successfully")
    print("\n====== ShopSphere Pipeline Completed Successfully ======")

if __name__ == "__main__":
    main()