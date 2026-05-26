import requests
import xml.etree.ElementTree as ET

API_KEY = "4f5a75507a646264383269706b4e72"
BASE_URL = "http://openapi.seoul.go.kr:8088"
url = f"{BASE_URL}/{API_KEY}/xml/VwsmTrdarFcltyQq/1/10/20241"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response Text Preview:")
        print(response.text[:1000])
        root = ET.fromstring(response.text)
        rows = root.findall(".//row")
        print(f"Found {len(rows)} rows.")
        if len(rows) > 0:
            print("First row data:")
            for child in rows[0]:
                print(f"  {child.tag}: {child.text}")
except Exception as e:
    print(f"Error: {e}")
