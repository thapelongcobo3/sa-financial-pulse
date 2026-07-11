import pandas as pd
from pathlib import Path
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()


class PriceLoader:
    def __init__(self, host, database, user, password, port="5432"):
        self.db_config = {
            "host": host,
            "database": database,
            "user": user,
            "password": password,
            "port": port
        }
        self.conn = None
        self.cursor = None

    def read_latest_csv(self, dir):

        # Find all csv files in data/raw
        csv_files = list(Path(dir).glob("*.csv"))

        # Check if they exist
        if not csv_files:
            print("No CSV files found.")
            return None
        else:
            # Get the newest file
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        
        # Read and correct the raw csv file
        try:
            print(f"Reading {latest_file}...")
            df = pd.read_csv(latest_file)
            filename = latest_file.name

            if filename.startswith("prices_"):
                # Map CSV headers directly to raw.daily_prices table
                column_mapping = {
                "Date": "trade_date",
                "Open": "open_cents",
                "High": "high_cents",
                "Low": "low_cents",
                "Close": "close_cents",
                "Volume": "volume",
                "Dividends": "dividends",
                "Stock Splits": "stock_splits",
                "ticker": "ticker",
                }

                # Rename the columns in memory
                df = df.rename(columns = column_mapping)

                # Correct the column order to match raw.daily_prices
                corrected_columns = [
                "ticker",
                "trade_date",
                "open_cents",
                "high_cents",
                "low_cents",
                "close_cents",
                "volume",
                "dividends",
                "stock_splits",
                ]

                return df[corrected_columns]
            else:
                return df

        except Exception as e:
            print(f"Failed to read {latest_file}: {e}")
            return None

    def connect_to_database(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("Successfully connected to the database.")
            return True
        except Exception as e:
            if self.conn is not None:
                self.conn.rollback()
            print(f"Database Error: {e}")
            return False
    
    def load_data(self, df, table_name: str, conflict_columns: list = None):
        if df is None or df.empty:
            print(f"No data to load for {table_name}.")
            return

        columns = ", ".join(df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))

        # Base query
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # prevents error during duplication
        if conflict_columns:
            conflict_targets = ", ".join(conflict_columns)
            # does nothing if duplication occures
            insert_query += f" ON CONFLICT ({conflict_targets}) DO NOTHING"

        # Convert df rows to pyhton tuples
        data_tuples = [tuple(x) for x in df.to_numpy()]

        try:
            # insert data
            print(f"Loading {len(df)} rows into '{table_name}'...")
            psycopg2.extras.execute_batch(
            self.cursor, insert_query, data_tuples, page_size = 1000
            )

            # Commit changes to db
            self.conn.commit()
            print("Database transaction successfully committed!")
        except Exception as e:
            self.conn.rollback()
            print(f"Failed to insert data into {table_name}: {e}")


    def close_connection(self):
        if self.cursor is not None:
            self.cursor.close()
        if self.conn is not None:
            self.conn.close()
        print("Database connection closed.")


def main():
    loader = PriceLoader(
            host = os.getenv("DB_HOST"),
            database = os.getenv("DB_NAME"),
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            port = os.getenv("DB_PORT", "5432"),
        )

    try:
        # Run processing methods on CSV files
        raw_df = loader.read_latest_csv("data/raw")
        clean_df =  loader.read_latest_csv("data/clean")

        # Connect to database
        if not loader.connect_to_database():
            print("Failed to connect to the database.")
            return

        # Load csv files into database
        loader.load_data(raw_df, "raw.daily_prices", conflict_columns = ["ticker", "trade_date"])
        loader.load_data(clean_df, "analytics.company_daily", conflict_columns = ["ticker", "trade_date"])

    except Exception as e:
        print(f"Data loading failed: {e}")
    finally:
        # Guaranteed to attempt closure
        loader.close_connection()



if __name__ == "__main__":
        main()
        




