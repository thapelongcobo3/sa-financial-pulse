import pandas as pd
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

class SectorAggregator:
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
    
    def connect_to_database(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("Successfully connected to the database.")
            return True
        except Exception as e:
            print(f"Database Error: {e}")
            return False
    
    def read_company_data(self):
        # Read daily company metrics from the analytics layer.
        base_query = "SELECT * FROM analytics.company_daily;"
        try:
            print("Extracting data from analytics.company_daily...")
            return pd.read_sql(base_query, self.conn)
        except Exception as e:
            print(f"Failed to extract company data: {e}")
            return None
        
    def aggregate_sector_data(self, df):
        if df is None or df.empty:
            print("No data available to aggregate.")
            return None
        
        print("Calculating sector-level aggregations...")

        # Group by sector and date
        grouped = df.groupby(["sector", "trade_date"])

        # Run aggregations
        df = grouped.agg(
            avg_daily_return_pct = ("daily_return_pct", "mean"),
            total_volume = ("volume", "sum"),
            company_count = ("ticker", "count")
        ).reset_index()
        return df
    

    def load_sector_data(self, df, table_name: str, conflict_columns: list = None):
        if df is None or df.empty:
            print(f"No data to load for {table_name}.")
            return
        
        columns = ", ".join(df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        if conflict_columns:
            conflict_targets = ", ".join(conflict_columns)
            insert_query += f" ON CONFLICT ({conflict_targets}) DO NOTHING"
        
        data_tuples = [
            tuple(None if pd.isna(v) else v for v in row)
            for row in df.to_numpy()
        ]

        try:
            print(f"Loading {len(df)} rows into '{table_name}'...")
            psycopg2.extras.execute_batch(
                self.cursor, insert_query, data_tuples, page_size = 1000
            )
            self.conn.commit()
            print(f"Database transaction successfully commmitted!")
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
    aggregator = SectorAggregator(
        host = os.getenv("DB_HOST"),
        database = os.getenv("DB_NAME"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        port = os.getenv("DB_PORT", "5432"),
    )

    try:
        # Establish db connection
        if not aggregator.connect_to_database():
            print("Database failed to be established.")
            return
        
        # Extract existing data
        company_df = aggregator.read_company_data()

        # aggregate
        sector_df = aggregator.aggregate_sector_data(company_df)

        # Load result
        aggregator.load_sector_data(
            df = sector_df,
            table_name = "analytics.sector_daily",
            conflict_columns = ["sector", "trade_date"]
        )

    except Exception as e:
        print(f"Failed to aggregate data: {e}")

    finally:
        aggregator.close_connection()


if __name__ == "__main__":
    main()






