import pandas as pd
import os

base_dir = "data/parquet_datas"
for f in os.listdir(base_dir):
    if f.endswith('.parquet'):
        path = os.path.join(base_dir, f)
        if f == 'df_final.parquet':
            print(f"File: {f} (Skipping full load, too large: {os.path.getsize(path)/1024/1024/1024:.2f} GB)")
            continue
        try:
            df = pd.read_parquet(path)
            print(f"File: {f}")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)[:15]} ... (total {len(df.columns)} columns)")
        except Exception as e:
            print(f"Error reading {f}: {e}")
