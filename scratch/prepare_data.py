import os
import sys
import pandas as pd
import pickle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
from src.data_acquisition import PublicDataAPI

load_dotenv()

def prepare_data():
    print("📡 Downloading raw data for iterative experiments...")
    api = PublicDataAPI()
    
    stores_json = api.get_store_info_hybrid()
    sales_raw = api.get_seoul_commercial_sales("20241")
    pop_raw = api.get_seoul_commercial_pop("20241")
    living_pop_raw = api.get_seoul_living_pop_grid("20240101")
    
    data = {
        'stores': stores_json['body']['items'] if stores_json and 'body' in stores_json else [],
        'sales': sales_raw if sales_raw else [],
        'pop': pop_raw if pop_raw else [],
        'living_pop': living_pop_raw if living_pop_raw else []
    }
    
    with open('scratch/data_dump.pkl', 'wb') as f:
        pickle.dump(data, f)
        
    print(f"✅ Data dumped to scratch/data_dump.pkl")
    print(f"   Stores: {len(data['stores'])}")
    print(f"   Sales: {len(data['sales'])}")
    print(f"   Population: {len(data['pop'])}")

if __name__ == "__main__":
    prepare_data()
