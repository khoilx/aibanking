import networkx as nx
from collections import defaultdict
import pandas as pd


class VendorHubDetector:
    """Bipartite graph analysis to detect vendor hubs shared by multiple customers."""

    def __init__(self):
        self.graph = None
        self.hub_vendors = {}           # vendor_tax_id -> {cifs, total_amount}
        self.customer_hub_scores = {}   # cif -> {degree, amount_bn, vendors}

    def build_graph(self, db):
        """Build bipartite graph: customers <-> vendors from TaxInvoice table."""
        from models import TaxInvoice, Customer

        G = nx.Graph()
        invoices = db.query(TaxInvoice).filter(TaxInvoice.status != 'cancelled').all()

        # Map tax_id -> cif for all customers that have a tax_id
        customers = db.query(Customer).filter(Customer.tax_id.isnot(None)).all()
        customer_tax_map = {c.tax_id: c.cif for c in customers}

        # Build edge list: customer_cif <-> vendor_tax_id
        vendor_customers = defaultdict(lambda: {'cifs': set(), 'total_amount': 0})

        for inv in invoices:
            buyer_is_customer = inv.buyer_tax_id in customer_tax_map
            seller_is_customer = inv.seller_tax_id in customer_tax_map

            if buyer_is_customer and not seller_is_customer:
                cif = customer_tax_map[inv.buyer_tax_id]
                vendor_tax = inv.seller_tax_id
                if vendor_tax:
                    G.add_edge(
                        f"CIF:{cif}", f"VENDOR:{vendor_tax}",
                        amount=inv.amount or 0,
                        invoice_id=inv.invoice_id
                    )
                    vendor_customers[vendor_tax]['cifs'].add(cif)
                    vendor_customers[vendor_tax]['total_amount'] += (inv.amount or 0)

        self.graph = G

        # Identify hub vendors: connected to >= 3 customers
        self.hub_vendors = {
            vendor: data
            for vendor, data in vendor_customers.items()
            if len(data['cifs']) >= 3
        }

        # Compute per-customer hub scores
        self.customer_hub_scores = {}
        for vendor, data in self.hub_vendors.items():
            for cif in data['cifs']:
                if cif not in self.customer_hub_scores:
                    self.customer_hub_scores[cif] = {
                        'degree': 0, 'amount_bn': 0.0, 'vendors': []
                    }
                self.customer_hub_scores[cif]['degree'] += 1
                self.customer_hub_scores[cif]['amount_bn'] += data['total_amount'] / 1e9
                self.customer_hub_scores[cif]['vendors'].append(vendor)

        return self

    def get_hub_features(self, cif: str) -> dict:
        """Get hub-related features for a customer."""
        if cif in self.customer_hub_scores:
            score = self.customer_hub_scores[cif]
            return {
                'vendor_hub_degree': score['degree'],
                'vendor_hub_amount_bn': score['amount_bn'],
                'is_in_hub': 1
            }
        return {'vendor_hub_degree': 0, 'vendor_hub_amount_bn': 0.0, 'is_in_hub': 0}

    def get_hub_summary(self, db) -> list:
        """Return hub vendor summary for the misuse API."""
        from models import Customer, TaxStatus

        result = []
        for vendor_tax, data in self.hub_vendors.items():
            # Get vendor name from TaxStatus
            tax_status = db.query(TaxStatus).filter(
                TaxStatus.tax_id == vendor_tax
            ).first()
            vendor_name = tax_status.company_name if tax_status else f"MST {vendor_tax}"

            # Get customer names (cap at 10)
            connected_customers = []
            cifs_list = list(data['cifs'])[:10]
            per_cif_amount = data['total_amount'] / max(len(data['cifs']), 1)
            for cif in cifs_list:
                customer = db.query(Customer).filter(Customer.cif == cif).first()
                if customer:
                    connected_customers.append({
                        'cif': cif,
                        'name': customer.customer_name,
                        'amount_bn': round(per_cif_amount / 1e9, 1)
                    })

            result.append({
                'vendor_tax_id': vendor_tax,
                'vendor_name': vendor_name,
                'connected_customer_count': len(data['cifs']),
                'total_amount_bn': round(data['total_amount'] / 1e9, 1),
                'is_suspicious': len(data['cifs']) >= 5,
                'connected_customers': connected_customers
            })

        result.sort(key=lambda x: x['connected_customer_count'], reverse=True)
        return result
