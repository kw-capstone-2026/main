import os
import pyarrow.parquet as pq
import pandas as pd

directory = "e:/capstone/kw-capstone-2026/data/parquet_datas"
files = [f for f in os.listdir(directory) if f.endswith('.parquet')]

with open('e:/capstone/kw-capstone-2026/scratch/parquet_info.txt', 'w', encoding='utf-8') as out_f:
    for f in files:
        file_path = os.path.join(directory, f)
        out_f.write(f"\n{'='*50}\nInspecting File: {f}\n{'='*50}\n")
        
        try:
            parquet_file = pq.ParquetFile(file_path)
            df_sample = parquet_file.read_row_group(0).to_pandas().head(5)
            
            out_f.write("--- Column Data Types ---\n")
            out_f.write(df_sample.dtypes.to_string() + "\n")
            
            out_f.write("\n--- Data Sample (first 5 rows) ---\n")
            out_f.write(df_sample.to_string() + "\n")
            
        except Exception as e:
            out_f.write(f"Error reading {f}: {e}\n")
