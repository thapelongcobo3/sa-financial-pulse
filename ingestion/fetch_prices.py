import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from config.companies import companies


class PriceFetcher:
    def __init__(self, companies, output_dir):
        self.companies = companies
        self.output_dir = output_dir
        self.today = datetime.today().strftime("%Y-%m-%d")

    def get_tickers(self):
        return [company["ticker"] for company in self.companies]

    def download_prices(self):
        try:
            print(f"Downloading price data for {len(self.get_tickers())} tickers...")
            data = yf.download(
                tickers=self.get_tickers(),
                period="5d",
                group_by="ticker",
                auto_adjust=False,
                actions=True
            )
            return data

        except Exception as e:
            print("Download failed:", e)
            return None

    def build_records(self, raw_df):
        try:
            all_dfs = []

            for ticker in self.get_tickers():
                try:
                    df = raw_df[ticker].copy()
                    if df["Close"].isna().all():
                        print(f"{ticker} has no data skipping...")
                        continue
                    df["ticker"] = ticker
                    df = df.drop(columns=["Adj Close"])
                    all_dfs.append(df)

                except KeyError:
                    print(f"Warning: no data for {ticker}, skipping...")
                    continue

            if all_dfs:
                final_df = pd.concat(all_dfs).reset_index()
                final_df["Date"] = pd.to_datetime(final_df["Date"]).dt.date
                return final_df
            else:
                return pd.DataFrame()

        except Exception as e:
            print("build_records failed:", e)
            return None

    def save_to_csv(self, df):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filename = f"prices_{self.today}.csv"
            path = os.path.join(self.output_dir, filename)
            df.to_csv(path, index=False)
            print(f"Saved {len(df)} rows to {path}")

        except Exception as e:
            print("Save failed:", e)


def main():
    fetcher = PriceFetcher(companies, "data/raw")

    raw = fetcher.download_prices()
    if raw is None:
        print("Download failed, exiting.")
        return

    df = fetcher.build_records(raw)
    if df is None:
        print("Build failed, exiting.")
        return
    
    if df.empty:
        print("No data collected, exiting without saving.")
        return

    fetcher.save_to_csv(df)
    print("Pipeline complete.")


if __name__ == "__main__":
    main()