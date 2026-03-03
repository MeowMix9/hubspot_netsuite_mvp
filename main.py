from utils.helpers import load_config, load_id_map, update_id_map
from hubspot_extractor import HubSpotExtractor
from netsuite_loader import NetSuiteLoader

def main(dry_run=True):
    print("=== HubSpot → NetSuite MVP ===\n")

    config = load_config()
    id_map = load_id_map()
    extractor = HubSpotExtractor(config)
    loader = NetSuiteLoader(config, id_map=id_map)

    # === Safety gate ===
    env = config.get("environment", "sandbox")
    dry_run = config['migration'].get('dry_run', True)
    if env == "production" and not dry_run:
        confirm = input("⚠️ Type 'PROD' to run in production: ")
        if confirm != 'PROD':
            raise RuntimeError("Aborted by user.")

    # === Process Contacts ===
    contacts = extractor.fetch_contacts()
    for c in contacts:
        if c['id'] in id_map:
            print(f"[Dry-run] Skipping {c['id']}, already in ID map")
            continue
        loader.load_customer(c)
        update_id_map(c['id'], f"NS-{c['id']}", id_map)

    # === Process Companies ===
    companies = extractor.fetch_companies()
    for comp in companies:
        if comp['id'] in id_map:
            continue
        loader.load_company(comp)
        update_id_map(comp['id'], f"NS-{comp['id']}", id_map)

    # === Process Deals ===
    deals = extractor.fetch_deals()
    for deal in deals:
        if deal['id'] in id_map:
            continue
        loader.load_deal(deal)
        update_id_map(deal['id'], f"NS-{deal['id']}", id_map)

    print("\nDry-run complete!")
    print("Updated ID map:")
    print(id_map)

if __name__ == "__main__":
    main(dry_run=True)
