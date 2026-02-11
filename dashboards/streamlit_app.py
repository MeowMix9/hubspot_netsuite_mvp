import streamlit as st
import json
from utils.helpers import load_id_map, load_config

st.title("HubSpot → NetSuite MVP Dashboard")

config = load_config()
st.write("**Environment:**", config.get("environment"))
st.write("**Dry-run:**", config['migration'].get('dry_run', True))

id_map = load_id_map()
st.subheader("ID Map")
st.json(id_map)
