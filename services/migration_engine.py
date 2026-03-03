# =========================================
# services/migration_engine.py
# =========================================

from datetime import datetime
import sqlite3
import pandas as pd
from database import get_conn, generate_id

# ---------------------------
# Save or update a contact
# ---------------------------
def save_or_update_contact(contact, environment="SANDBOX", dry_run=False):
    """
    Save a contact to the customers table.
    Handles both create and update.
    Supports dry_run mode.
    Logs to audit_log.
    Returns dict with id and action.
    """
    conn = get_conn()
    cursor = conn.cursor()

    # Check if contact exists by email + environment
    cursor.execute("SELECT * FROM customers WHERE email=? AND environment=?", 
                   (contact.get("email"), environment))
    existing = cursor.fetchone()

    if existing:
        # Update existing
        action = "update"
        entity_id = existing["id"]
        if not dry_run:
            cursor.execute("""
            UPDATE customers SET
                hubspot_id=?,
                netsuite_id=?,
                source_system=?,
                first_name=?,
                last_name=?,
                phone=?,
                company=?,
                brand=?,
                lifecycle_stage=?,
                pipeline_stage=?,
                customer_type=?,
                address=?,
                city=?,
                state=?,
                zip=?,
                country=?,
                notes=?,
                last_synced_at=?
            WHERE id=?
            """, (
                contact.get("hubspot_id"),
                contact.get("netsuite_id"),
                contact.get("source_system"),
                contact.get("first_name"),
                contact.get("last_name"),
                contact.get("phone"),
                contact.get("company"),
                contact.get("brand"),
                contact.get("lifecycle_stage"),
                contact.get("pipeline_stage"),
                contact.get("customer_type"),
                contact.get("address"),
                contact.get("city"),
                contact.get("state"),
                contact.get("zip"),
                contact.get("country"),
                contact.get("notes"),
                datetime.now().isoformat(),
                entity_id
            ))

    else:
        # Create new
        entity_id = generate_id("CUST", "customers")
        action = "create"
        if not dry_run:
            cursor.execute("""
            INSERT INTO customers VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """, (
                entity_id,
                contact.get("hubspot_id"),
                contact.get("netsuite_id"),
                contact.get("source_system"),
                contact.get("first_name"),
                contact.get("last_name"),
                contact.get("email"),
                contact.get("phone"),
                contact.get("company"),
                contact.get("brand"),
                contact.get("lifecycle_stage"),
                contact.get("pipeline_stage"),
                contact.get("customer_type"),
                contact.get("address"),
                contact.get("city"),
                contact.get("state"),
                contact.get("zip"),
                contact.get("country"),
                contact.get("notes"),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                environment
            ))

    # Audit log
    if not dry_run:
        cursor.execute("""
        INSERT INTO audit_log VALUES (?,?,?,?,?,?)
        """, (
            generate_id("AUD", "audit_log"),
            "customer",
            entity_id,
            action,
            datetime.now().isoformat(),
            "migration_engine"
        ))

    if not dry_run:
        conn.commit()
    conn.close()

    return {"id": entity_id, "action": action}


# ---------------------------
# ID Mapping
# ---------------------------
def save_id_mapping(source_system, source_id, target_system, target_id, dry_run=False):
    """
    Save mapping between source and target systems.
    """
    if dry_run:
        return

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS id_mappings (
        id TEXT PRIMARY KEY,
        source_system TEXT,
        source_id TEXT,
        target_system TEXT,
        target_id TEXT,
        created_at TEXT
    )
    """)
    cursor.execute("""
    INSERT INTO id_mappings VALUES (?,?,?,?,?,?)
    """, (
        generate_id("MAP", "id_mappings"),
        source_system,
        source_id,
        target_system,
        target_id,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_target_id(source_system, source_id, target_system):
    """
    Return the target system ID if exists.
    """
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT target_id FROM id_mappings
    WHERE source_system=? AND source_id=? AND target_system=?
    """, (source_system, source_id, target_system))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ---------------------------
# Batch migrate HubSpot contacts
# ---------------------------
def migrate_hubspot_contacts(hubspot_contacts, environment="SANDBOX", dry_run=False):
    """
    Migrate a list of HubSpot contacts to the FWD CRM.
    Returns summary with created/updated/failed counts.
    """
    summary = {"created": 0, "updated": 0, "failed": 0, "errors": []}

    for hs_contact in hubspot_contacts:
        try:
            contact = {
                "hubspot_id": hs_contact.get("hubspot_id"),
                "netsuite_id": hs_contact.get("netsuite_id"),
                "source_system": "hubspot",
                "first_name": hs_contact.get("firstname"),
                "last_name": hs_contact.get("lastname"),
                "email": hs_contact.get("email"),
                "phone": hs_contact.get("phone"),
                "company": hs_contact.get("company"),
                "brand": hs_contact.get("brand"),
                "lifecycle_stage": hs_contact.get("lifecycle_stage", "Lead"),
                "pipeline_stage": hs_contact.get("pipeline_stage", "Lead"),
                "customer_type": hs_contact.get("customer_type", "Retail"),
                "address": hs_contact.get("address"),
                "city": hs_contact.get("city"),
                "state": hs_contact.get("state"),
                "zip": hs_contact.get("zip"),
                "country": hs_contact.get("country"),
                "notes": hs_contact.get("notes"),
            }

            result = save_or_update_contact(contact, environment=environment, dry_run=dry_run)

            if result["action"] == "create":
                summary["created"] += 1
            else:
                summary["updated"] += 1

            # Save ID mapping
            save_id_mapping("hubspot", hs_contact.get("hubspot_id"), "fwd_crm", result["id"], dry_run=dry_run)

        except Exception as e:
            summary["failed"] += 1
            summary["errors"].append({"email": hs_contact.get("email"), "error": str(e)})

    return summary


# ---------------------------
# Migrate from CSV
# ---------------------------
def migrate_from_csv(file_path, environment="SANDBOX", dry_run=False):
    """
    Import contacts from CSV and migrate.
    """
    df = pd.read_csv(file_path)
    contacts = df.to_dict(orient="records")
    return migrate_hubspot_contacts(contacts, environment=environment, dry_run=dry_run)


# ---------------------------
# Test / Dry-run
# ---------------------------
if __name__ == "__main__":
    mock_data = [
        {"firstname": "Alice", "lastname": "Smith", "email": "alice@example.com"},
        {"firstname": "Bob", "lastname": "Jones", "email": "bob@example.com"},
    ]
    summary = migrate_hubspot_contacts(mock_data, dry_run=True)
    print(summary)

    # ---------------------------
# HubSpot → NetSuite migration
# ---------------------------
def migrate_hubspot_to_netsuite(hubspot_contacts, netsuite_api, environment="SANDBOX", dry_run=False):
    """
    Push HubSpot contacts to NetSuite.
    netsuite_api: instance with methods like create_customer(), update_customer()
    Returns summary of created/updated/failed.
    """
    summary = {"created": 0, "updated": 0, "failed": 0, "errors": []}

    for hs_contact in hubspot_contacts:
        try:
            # Check if already migrated
            fwd_id = get_target_id("hubspot", hs_contact.get("hubspot_id"), "fwd_crm")
            if not fwd_id:
                # Skip contacts not yet in FWD CRM
                raise ValueError("Contact not yet in FWD CRM. Run FWD migration first.")

            netsuite_id = get_target_id("fwd_crm", fwd_id, "netsuite")

            payload = {
                "first_name": hs_contact.get("firstname"),
                "last_name": hs_contact.get("lastname"),
                "email": hs_contact.get("email"),
                "phone": hs_contact.get("phone"),
                "company": hs_contact.get("company"),
                "brand": hs_contact.get("brand"),
                "address": hs_contact.get("address"),
                "city": hs_contact.get("city"),
                "state": hs_contact.get("state"),
                "zip": hs_contact.get("zip"),
                "country": hs_contact.get("country"),
                "customer_type": hs_contact.get("customer_type", "Retail"),
                "lifecycle_stage": hs_contact.get("lifecycle_stage", "Lead"),
                "pipeline_stage": hs_contact.get("pipeline_stage", "Lead"),
                "notes": hs_contact.get("notes")
            }

            if netsuite_id:
                if not dry_run:
                    netsuite_api.update_customer(netsuite_id, payload)
                action = "update"
                summary["updated"] += 1
            else:
                if not dry_run:
                    new_ns_id = netsuite_api.create_customer(payload)
                    save_id_mapping("fwd_crm", fwd_id, "netsuite", new_ns_id, dry_run=dry_run)
                action = "create"
                summary["created"] += 1

        except Exception as e:
            summary["failed"] += 1
            summary["errors"].append({"email": hs_contact.get("email"), "error": str(e)})

    return summary