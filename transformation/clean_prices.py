import pandas as pd
from pathlib import Path
from config.companies import companies


class PriceTransformer:
    def __init__(self, companies, raw_dir, clean_dir):
        self.companies = pd.DataFrame(companies)
        self.raw_dir = Path(raw_dir)
        self.clean_dir = Path(clean_dir)

    def read_raw_csv(self):

        # Find all csv files in data/raw
        csv_files = list(self.raw_dir.glob("*.csv"))

        # Check if they exist
        if not csv_files:
            print("No CSV files found.")
            return None, None
        else:
            # Get the newest file
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)

            # get the datestamp
            filename = latest_file.name
            if filename.startswith("prices_") and filename.endswith(".csv"):
                date_stamp = (
                    filename.removeprefix("prices_").removesuffix(".csv")
                )
            else:
                date_stamp = "processed"
        
        try:
            print(f"Reading {latest_file}...")
            return pd.read_csv(latest_file), date_stamp
        except Exception as e:
            print(f"Failed to read {latest_file}: {e}")
            return None, None
        
    def transform(self, df):
        # Enrich price data with company metadata
        try:
            print(f"Merging company meta-data to prices-data...")
            df = df.merge(self.companies, on="ticker", how="left")

        except Exception as e:
            print(f"Failed to merge company meta-data to prices data: {e}")
            return None
        
        try:
            # Make sure data tickers from company list and price csv still match
            unmapped_rows = df[df["company_name"].isna()]
            if not unmapped_rows.empty:
                unmapped_tickers = unmapped_rows["ticker"].unique()
                print(f"Join failure! The following tickers were not found: {unmapped_tickers}")
                print("Dropping problem rows...")
                df = df.dropna(subset=["company_name", "sector"])

            if df.empty:
                print("Post-join validation resulted in an empty DataFrame.")
                return None

            

            # Convert prices from cents to rands
            price_cols = ["Open", "High", "Low", "Close"]
            df[price_cols] = df[price_cols] / 100.0

            # Handle nulls on Open, High, Low, Close, Volume after standardization
            critical_fields = ["Open", "High", "Low", "Close", "Volume", "ticker"]
            missing_data_rows = df[df[critical_fields].isna().any(axis=1)]
            if not missing_data_rows.empty:
                print(f"Detected {len(missing_data_rows)} partial or corrupted pricing rows in raw dataset.\nDropping records...")
                df = df.dropna(subset=critical_fields)

            if df.empty:
                print("Post-field validation resulted in an empty DataFrame.")
                return None


            # Rename columns to match analytics.company_daily
            renamed_columns = {
                "Date": "trade_date",
                "Open": "open_rands",
                "High": "high_rands",
                "Low": "low_rands",
                "Close": "close_rands",
                "Volume": "volume"
            }
            df = df.rename(columns = renamed_columns)

            # Convert to datetime
            df["trade_date"] = pd.to_datetime(df["trade_date"])

            # Sort by ticker and date
            df = df.sort_values(
                ["ticker", "trade_date"]
            )


            # Calculate daily returns and moving averages
            print("Computing financial indicators...")

            # Daily Percentage Price Returns
            df["daily_return_pct"] = df.groupby("ticker")["close_rands"].pct_change() * 100

            # Moving Window Averages (min_periods=1 ensures calculation safety during initial timeline days)
            df["ma_7_day"] = df.groupby("ticker")["close_rands"].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
            df["ma_30_day"] = df.groupby("ticker")["close_rands"].transform(
                lambda x: x.rolling(window=30, min_periods=1).mean()
            )

            # Restructure and select exact targeted columns
            target_columns = [
                    "ticker", "company_name", "sector", "trade_date", 
                    "open_rands", "high_rands", "low_rands", "close_rands", 
                    "volume", "daily_return_pct", "ma_7_day", "ma_30_day"
                ]
            # Reform timestamps back to standard clean date outputs
            df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")

            return df[target_columns]
        
        except Exception as e:
            print(f"Transformation failed: {e}")
            return None
        
    def save_to_clean(self, df, date_stamp):
        try:
            self.clean_dir.mkdir(
                parents =True,
                exist_ok = True
            )
            filename = f"clean_prices_{date_stamp}.csv"
            path = self.clean_dir /filename

            df.to_csv(path, index=False)
            print(f"\nSaved {len(df)} rows to {path}")
        
        except Exception as e:
            print(f"Save failed: {e}")


def main():
    # Instantiate PriceTransformer
    transformer = PriceTransformer(
        companies = companies,
        raw_dir = "data/raw",
        clean_dir = "data/clean"
    )
    
    # Get raw data
    raw_df, execution_date = transformer.read_raw_csv()

    if raw_df is None:
        print("Transformation process unsuccessful.")
        return
    
    # Clean the data
    cleaned_dataframe = transformer.transform(raw_df)

    if cleaned_dataframe is not None and not cleaned_dataframe.empty:
        transformer.save_to_clean(cleaned_dataframe, execution_date)
        print("Transformation process successful.")
    else:
        print("Transformation process unsuccessful.")


if __name__ == "__main__":
    main()









