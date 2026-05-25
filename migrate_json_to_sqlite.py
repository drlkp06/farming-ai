import json

from product_memory import (
    initialize_database,
    save_product
)


# ==========================================
# LOAD JSON PRODUCTS
# ==========================================

PRODUCT_FILE = "memory/products.json"


def load_json_products():

    try:

        with open(
            PRODUCT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(f"\nError loading JSON : {e}")

        return {}


# ==========================================
# MIGRATION
# ==========================================

def migrate_products():

    initialize_database()

    products = load_json_products()

    migrated_count = 0

    for product_name, data in products.items():

        try:

            save_product(
                product_name,
                data
            )

            migrated_count += 1

            print(
                f"✅ Migrated : {product_name}"
            )

        except Exception as e:

            print(
                f"❌ Failed : {product_name}"
            )

            print(e)

    print("\n===================================")

    print(
        f"Migration Completed : {migrated_count} products"
    )

    print("===================================\n")


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    migrate_products()