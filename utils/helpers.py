import json
import yaml
import os
import requests

# --------------------
# Paths for config & ID map
# --------------------
CONFIG_PATH = os.path.join("config", "config.yaml")
ID_MAP_PATH = os.path.join("data", "id_map.json")

# --------------------
# Config / ID Map helpers
# --------------------
def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def load_id_map():
    if not os.path.exists(ID_MAP_PATH):
        with open(ID_MAP_PATH, "w") as f:
            json.dump({}, f, indent=2)
    with open(ID_MAP_PATH, "r") as f:
        return json.load(f)

def save_id_map(id_map):
    with open(ID_MAP_PATH, "w") as f:
        json.dump(id_map, f, indent=2)

def update_id_map(shopify_id, netsuite_id, id_map):
    id_map[shopify_id] = netsuite_id
    save_id_map(id_map)

# --------------------
# ZIP Code helper
# --------------------
LOCAL_ZIP_DATA = {
    "10001": {"city": "New York", "state": "NY"},
    "94105": {"city": "San Francisco", "state": "CA"},
    "30301": {"city": "Atlanta", "state": "GA"},
    # Add more common ZIPs here
}

def get_city_state(zip_code):
    """Return city/state for a given ZIP. Try local dictionary first, then fallback to API."""
    if zip_code in LOCAL_ZIP_DATA:
        return LOCAL_ZIP_DATA[zip_code]

    try:
        response = requests.get(f"http://api.zippopotam.us/us/{zip_code}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "city": data["places"][0]["place name"],
                "state": data["places"][0]["state abbreviation"]
            }
    except Exception as e:
        print(f"ZIP API error: {e}")

    return {"city": "", "state": ""}

