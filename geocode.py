import pandas as pd
import requests
import time

def load_addresses(csv_path):
    """
    read address information from csv file, and return a list of dictionary
    """
    df = pd.read_csv(csv_path)
    required_cols = {"RecordID","Address", "City", "State", "Zip"}
    if not required_cols.issubset(df.columns):
        raise ValueError("Missing necessary cols in csv: Address, City, State, Zip")
    
    return [
        {
            "record_id":row["RecordID"],
            "address": row["Address"],
            "city": row["City"],
            "state": row["State"],
            "zip": str(row["Zip"])
        }
        for _, row in df.iterrows()
    ]

def query_melissa(entry, license_key):
    """
    Use Melissa Global Address API for address info
    """
    url = "https://address.melissadata.net/v3/WEB/GlobalAddress/doGlobalAddress"
    params = {
        "t": entry["record_id"],
        "id": license_key,
        "a1": entry["address"],
        "loc": entry["city"], 
        "admarea": entry["state"],
        "postal": entry["zip"],
        "ctry": "US",
        "format": "json"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200 or not response.text.strip():
            return None, f"HTTP_ERROR: {response.status_code}"
        
        data = response.json()
        records = data.get("Records", [])
        
        if not records:
            return None, data.get("TransmissionResults", "NO_MATCH")

        r = records[0]
        return {
            "RecordID":entry["record_id"],
            "InputAddress": entry["address"],
            "City": entry["city"],
            "State": entry["state"],
            "Zip": entry["zip"],
            "Latitude": r.get("Latitude"),
            "Longitude": r.get("Longitude")
        }, None

    except Exception as e:
        return None, f"EXCEPTION: {str(e)}"

def use_api(key, path_csv):

    csv_path = path_csv
    license_key = key

    addresses = load_addresses(csv_path)[0:]
    success_list = []
    failure_list = []

    for i, addr in enumerate(addresses):
        print(f"📍 Processing {i+1}/{len(addresses)}: {addr['address']}")
        result, error = query_melissa(addr, license_key)
        if result:
            success_list.append(result)
        else:
            failure_list.append({
                "RecordID":addr["record_id"],
                "InputAddress": addr["address"],
                "City": addr["city"],
                "State": addr["state"],
                "Zip": addr["zip"],
                "Error": error
            })
        time.sleep(1)  # avoid API lag

 
    pd.DataFrame(success_list).to_csv("geocode.csv", index=False)
    pd.DataFrame(failure_list).to_csv("melissa_failed_addresses.csv", index=False)

    print("\n✅ Success！")
    print(f"✔ Success Address: {len(success_list)}")
    print(f"❌ Failed Address: {len(failure_list)}")

