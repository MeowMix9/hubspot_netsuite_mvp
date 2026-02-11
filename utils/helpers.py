import json
import yaml
import os

CONFIG_PATH = os.path.join("config", "config.yaml")
ID_MAP_PATH = os.path.join("data", "id_map.json")

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
