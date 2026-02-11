class HubSpotExtractor:
    def __init__(self, config):
        self.config = config
        self.batch_size = config['migration'].get('batch_size', 50)
        self.dry_run = config['migration'].get('dry_run', True)

    def fetch_contacts(self):
        if self.dry_run:
            print(f"[Dry-run] Would fetch up to {self.batch_size} contacts")
            return [
                {'id': '1001', 'first_name': 'Alice', 'last_name': 'Smith', 'email': 'alice@example.com'},
                {'id': '1002', 'first_name': 'Bob', 'last_name': 'Jones', 'email': 'bob@example.com'}
            ]
        # Real API logic goes here
        return []

    def fetch_companies(self):
        if self.dry_run:
            return [
                {'id': '2001', 'name': 'Acme Corp'},
                {'id': '2002', 'name': 'Beta LLC'}
            ]
        return []

    def fetch_deals(self):
        if self.dry_run:
            return [
                {'id': '3001', 'title': 'Deal One', 'amount': 1000},
                {'id': '3002', 'title': 'Deal Two', 'amount': 2000}
            ]
        return []
