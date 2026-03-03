# =========================================
# FWD CRM Streamlit App — SaaS Ready Version
# =========================================

import os, sys
from datetime import datetime

import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader

# ---------------------------
# Colab / Drive setup
# ---------------------------
PROJECT_ROOT = "/content/drive/MyDrive/hubspot_netsuite_mvp"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import (
    init_db,
    get_conn,
    fetch_customers,
    fetch_pipeline_stages,
    fetch_tickets,
    fetch_brands,
    create_brand,
    get_brand_by_name,
    fetch_templates_by_brand,
    create_template,
    deactivate_template
)

from utils.helpers import get_city_state
from services.migration_engine import save_or_update_contact

# ---------------------------
# Cloudinary config
# ---------------------------
cloudinary.config(
    cloud_name="duphfrq2e",
    api_key="332995512987615",
    api_secret="Uxn4orWA6QIVUUB5-OOGeDW2eVk"
)

# ---------------------------
# Initialize DB
# ---------------------------
init_db()

# ---------------------------
# Paths
# ---------------------------
LOGO_DIR = os.path.join(PROJECT_ROOT, "logos")
os.makedirs(LOGO_DIR, exist_ok=True)

# ---------------------------
# Streamlit Config
# ---------------------------
st.set_page_config(page_title="FWD CRM", layout="wide")
st.sidebar.title("FWD CRM")

environment_toggle = st.sidebar.toggle("Live Mode", value=False)
env_text = "LIVE" if environment_toggle else "SANDBOX"
st.sidebar.markdown(f"**Environment:** {env_text}")

# ---------------------------
# Load Data
# ---------------------------
customers_raw = fetch_customers(None)

for c in customers_raw:
    if "environment" not in c or not c["environment"]:
        c["environment"] = "SANDBOX"

customers = [c for c in customers_raw if c["environment"] == env_text]
pipeline_stages = fetch_pipeline_stages(env_text)

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.subheader("Sections")
section = st.sidebar.radio(
    "Main Section",
    ["Dashboard", "Customers", "Marketing", "Pipeline & Reports", "Tickets"]
)

child_item = None
if section == "Customers":
    child_item = st.sidebar.selectbox(
        "Customer Pages",
        ["➕ Add Customer", "👥 View Customers"]
    )
elif section == "Marketing":
    child_item = st.sidebar.selectbox(
        "Marketing Pages",
        ["📬 Email Templates", "🚀 Campaigns", "📄 Forms", "🎯 CTAs"]
    )
elif section == "Pipeline & Reports":
    child_item = st.sidebar.selectbox(
        "Pipeline & Reports Pages",
        ["📋 Pipeline Board", "📈 Reporting", "📥 Import Contacts"]
    )

# =====================================================
# MAIN CONTENT
# =====================================================

# -------- Dashboard --------
if section == "Dashboard":
    st.title("FWD CRM Dashboard")
    st.subheader("Customers Overview")

    if customers:
        st.dataframe(pd.DataFrame(customers))
    else:
        st.info("No customers found for this environment.")

# -------- Customers --------
elif section == "Customers":

    if child_item == "➕ Add Customer":

        st.title("Add New Customer")

        with st.form("customer_form"):

            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")

            with col2:
                last_name = st.text_input("Last Name")
                company = st.text_input("Company")
                brand = st.text_input("Brand / Band")

            address = st.text_input("Street Address")
            zip_code = st.text_input("ZIP Code")

            city, state_from_zip = "", ""
            if zip_code:
                loc = get_city_state(zip_code)
                city = loc.get("city", "")
                state_from_zip = loc.get("state", "")

            city = st.text_input("City", value=city)
            state = st.text_input("State", value=state_from_zip)
            country = st.text_input("Country", value="United States")
            notes = st.text_area("Notes")

            logo_file = st.file_uploader(
                "Upload Brand Logo",
                type=["png", "jpg", "jpeg"]
            )

            logo_saved_path = None
            if logo_file:
                logo_saved_path = os.path.join(LOGO_DIR, logo_file.name)
                with open(logo_saved_path, "wb") as f:
                    f.write(logo_file.getbuffer())

            customer_type = st.selectbox(
                "Customer Type",
                ["Retail", "Wholesale", "VIP", "Distributor", "Internal"]
            )

            pipeline_stage = st.selectbox(
                "Pipeline Stage",
                [p["name"] for p in pipeline_stages] if pipeline_stages else ["Default"]
            )

            submitted = st.form_submit_button("Create Customer")

            if submitted:
                if not first_name or not email:
                    st.error("First Name and Email required.")
                else:

                    # 🔥 AUTO-CREATE BRAND IF NEEDED
                    if brand:
                        existing_brand = get_brand_by_name(brand, env_text)
                        if not existing_brand:
                            create_brand(brand, env_text)

                    contact = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "company": company,
                        "brand": brand,
                        "customer_type": customer_type,
                        "address": address,
                        "city": city,
                        "state": state,
                        "zip": zip_code,
                        "country": country,
                        "notes": notes,
                        "logo": logo_saved_path,
                        "pipeline_stage": pipeline_stage,
                        "environment": env_text
                    }

                    save_or_update_contact(contact, environment=env_text)
                    st.success("Customer created successfully.")
                    st.rerun()

    elif child_item == "👥 View Customers":
        st.title("All Customers")
        if customers:
            st.dataframe(pd.DataFrame(customers))
        else:
            st.info("No customers found for this environment.")

# -------- Marketing --------
elif section == "Marketing":

    if child_item == "📬 Email Templates":

        st.title("📧 Email Templates")

        brands = fetch_brands(env_text)

        if not brands:
            st.info("No brands yet. Create a customer with a brand first.")
            st.stop()

        brand_names = [b["name"] for b in brands]
        selected_brand_name = st.selectbox("Select Brand", brand_names)

        selected_brand = get_brand_by_name(selected_brand_name, env_text)
        brand_id = selected_brand["id"]

        # ---- Existing Templates ----
        st.subheader("Existing Templates")

        templates = fetch_templates_by_brand(brand_id, env_text)

        if templates:
            for t in templates:
                with st.expander(t["name"]):
                    st.write("**Subject:**", t["subject"])
                    st.markdown(t["body"], unsafe_allow_html=True)

                    if t["image_url"]:
                        st.image(t["image_url"], width=400)

                    if st.button(f"Deactivate Template {t['id']}"):
                        deactivate_template(t["id"])
                        st.success("Template deactivated.")
                        st.rerun()
        else:
            st.info("No templates for this brand.")

        st.divider()

        # ---- Create Template ----
        st.subheader("Create New Template")

        with st.form("template_form"):

            name = st.text_input("Template Name")
            subject = st.text_input("Subject Line")
            body = st.text_area("Body (HTML Supported)", height=200)

            image_file = st.file_uploader(
                "Upload Image (optional)",
                type=["png","jpg","jpeg"]
            )

            submitted = st.form_submit_button("Save Template")

            if submitted:
                if not name:
                    st.warning("Template name required.")
                else:

                    image_url = None

                    if image_file:
                        try:
                            result = cloudinary.uploader.upload(image_file)
                            image_url = result.get("secure_url")
                        except Exception as e:
                            st.error(f"Image upload failed: {e}")

                    create_template(
                        brand_id,
                        name,
                        subject,
                        body,
                        image_url,
                        env_text
                    )

                    st.success("Template saved successfully.")
                    st.rerun()

    else:
        st.title(child_item + " — Coming Soon")

# -------- Pipeline & Reports --------
elif section == "Pipeline & Reports":

    # ---------- Pipeline Board ----------
    if child_item == "📋 Pipeline Board":
        st.title("📋 Pipeline Board")

        brands = fetch_brands(env_text)
        brand_names = [b["name"] for b in brands] if brands else []

        selected_brand = st.selectbox("Filter by Brand", ["All"] + brand_names)

        if selected_brand != "All":
            filtered_customers = [c for c in customers if c.get("brand") == selected_brand]
        else:
            filtered_customers = customers

        # Group by pipeline stage
        stages = [p["name"] for p in pipeline_stages] if pipeline_stages else ["Lead", "Prospect", "Customer"]
        pipeline_dict = {stage: [] for stage in stages}

        for c in filtered_customers:
            stage = c.get("pipeline_stage") or "Lead"
            if stage not in pipeline_dict:
                pipeline_dict[stage] = []
            pipeline_dict[stage].append(c)

        cols = st.columns(len(stages))
        for i, stage in enumerate(stages):
            with cols[i]:
                st.subheader(stage)
                for cust in pipeline_dict[stage]:
                    st.write(f"{cust.get('first_name','')} {cust.get('last_name','')} — {cust.get('company','')}")

    # ---------- Reporting ----------
    elif child_item == "📈 Reporting":
        import altair as alt
        st.title("📈 CRM Reporting")

        if not customers:
            st.info("No customers to report.")
            st.stop()

        df_pipeline = pd.DataFrame(customers)

        st.subheader("Pipeline Stage Distribution")
        chart_pipeline = alt.Chart(df_pipeline).mark_bar().encode(
            x='pipeline_stage:N',
            y='count()',
            tooltip=['pipeline_stage', 'count()']
        )
        st.altair_chart(chart_pipeline, use_container_width=True)

        st.subheader("Customer Type Distribution")
        chart_type = alt.Chart(df_pipeline).mark_bar().encode(
            x='customer_type:N',
            y='count()',
            tooltip=['customer_type', 'count()']
        )
        st.altair_chart(chart_type, use_container_width=True)

        st.subheader("Customers per Brand")
        chart_brand = alt.Chart(df_pipeline).mark_bar().encode(
            x='brand:N',
            y='count()',
            tooltip=['brand', 'count()']
        )
        st.altair_chart(chart_brand, use_container_width=True)

    # ---------- Import Contacts ----------
elif child_item == "📥 Import Contacts":
    import io

    st.title("📥 Import Contacts (CSV)")

    # CSV template for download
    st.subheader("Download CSV Template")
    csv_template = pd.DataFrame([{
        "first_name": "",
        "last_name": "",
        "email": "",
        "phone": "",
        "company": "",
        "brand": "",
        "customer_type": "",
        "address": "",
        "city": "",
        "state": "",
        "zip": "",
        "country": "",
        "notes": "",
        "pipeline_stage": "",
        "hubspot_id": "",
        "netsuite_id": "",
        "lifecycle_stage": ""
    }])
    csv_buffer = io.StringIO()
    csv_template.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV Template",
        data=csv_buffer.getvalue(),
        file_name="fwd_crm_import_template.csv",
        mime="text/csv"
    )

    # Upload and import CSV
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df_import = pd.read_csv(uploaded_file)
        st.write(f"{len(df_import)} contacts found in CSV")

        # Validate columns
        expected_cols = set(csv_template.columns)
        missing_cols = expected_cols - set(df_import.columns)
        for col in missing_cols:
            df_import[col] = None  # add missing columns with None

        # Conflict handling option
        conflict_option = st.radio(
            "If duplicate contacts are found (same email):",
            ["Skip duplicates", "Overwrite existing", "Ask for each"]
        )

        conflicts_found = []
        imported_count = 0

        for _, row in df_import.iterrows():
            contact = row.to_dict()
            contact["environment"] = env_text

            # Check for existing contact
            existing = [c for c in customers if c.get("email") == contact.get("email")]
            if existing:
                if conflict_option == "Skip duplicates":
                    continue
                elif conflict_option == "Overwrite existing":
                    save_or_update_contact(contact, environment=env_text)
                    imported_count += 1
                elif conflict_option == "Ask for each":
                    key = contact.get("email")
                    overwrite = st.radio(
                        f"Duplicate found for {key}. Overwrite?",
                        ["Yes", "No"],
                        key=f"dup_{key}"
                    )
                    if overwrite == "Yes":
                        save_or_update_contact(contact, environment=env_text)
                        imported_count += 1
                    else:
                        continue
            else:
                save_or_update_contact(contact, environment=env_text)
                imported_count += 1

        st.success(f"✅ Imported {imported_count} contacts successfully.")

# -------- Tickets --------
elif section == "Tickets":
    st.title("Tickets — Coming Soon")