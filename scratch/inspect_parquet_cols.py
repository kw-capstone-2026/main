import pandas as pd
import json

df = pd.read_parquet("data/parquet_datas/final_merged_commercial_data.parquet")
columns = list(df.columns)
print(f"Shape: {df.shape}")
print(f"Total columns: {len(columns)}")

with open("scratch/columns_list.json", "w", encoding="utf-8") as f:
    json.dump(columns, f, ensure_ascii=False, indent=2)

print("Columns list saved to scratch/columns_list.json")
