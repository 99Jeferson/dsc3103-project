#%%
import pandas as pd 
from src.validate import rules
raw_path = "data/raw/prices.csv"

def infered_schema(df):
    print("\n I Infered Schema")
    print("--" * 20)
    print(df.dtypes)


def run_files(path = raw_path):
    df = pd.read_csv(path)
    infered_schema(df)

    if __name__ == "__main__":
        run_files()

def row_count(df):
    print(f"Row count: {len(df)}")
    
# %%
def negative_values(df):
    neg_prices = rules.rule_positive_price(df)
    print(f"Rows with negative prices: {len(neg_prices)}")
    if len(neg_prices) > 0:
        print(neg_prices[["id", "price", "Reason"]].head(10))
# %%
def run_files(path = raw_path):
    df = pd.read_csv(path)
    infered_schema(df)
    row_count(df)
    negative_values(df)
# %%
