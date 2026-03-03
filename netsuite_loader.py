class NetSuiteLoader:
    def __init__(self, config, id_map=None):
        self.config = config
        self.id_map = id_map or {}

    def load_customer(self, customer):
        print(f"[Dry-run] Would load customer to NetSuite: {customer}")

    def load_company(self, company):
        print(f"[Dry-run] Would load company to NetSuite: {company}")

    def load_deal(self, deal):
        print(f"[Dry-run] Would load deal to NetSuite: {deal}")
