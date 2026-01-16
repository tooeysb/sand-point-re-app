"""
Seed tenant leases for the 225 Worth Ave demo property.
Based on the PRD documentation.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Property, Scenario, Lease

def main():
    db = SessionLocal()

    try:
        # Find the 225 Worth Ave property
        property = db.query(Property).filter(Property.name == "225 Worth Ave").first()
        if not property:
            print("Property '225 Worth Ave' not found! Run seed_demo_property.py first.")
            return

        print(f"Found property: {property.name} (ID: {property.id})")

        # Find the Base Case scenario
        scenario = db.query(Scenario).filter(
            Scenario.property_id == property.id,
            Scenario.is_base_case == True
        ).first()
        if not scenario:
            print("Base Case scenario not found!")
            return

        print(f"Found scenario: {scenario.name} (ID: {scenario.id})")

        # Check if leases already exist
        existing_leases = db.query(Lease).filter(Lease.scenario_id == scenario.id).count()
        if existing_leases > 0:
            print(f"Leases already exist ({existing_leases} found). Skipping.")
            return

        # Create leases for the three tenants
        # Total RSF: 9,932 SF
        leases_data = [
            {
                "tenant_name": "Peter Millar / G-Fore",
                "space_id": "Suite 100",
                "rsf": 4200,
                "base_rent_psf": 195.0,
                "market_rent_psf": 220.0,
                "lease_start": date(2022, 1, 1),
                "lease_end": date(2032, 12, 31),
                "escalation_type": "percentage",
                "escalation_value": 0.03,  # 3% annual
                "escalation_frequency": "annual",
                "reimbursement_type": "NNN",
                "recovery_percentage": 1.0,
            },
            {
                "tenant_name": "J. McLaughlin",
                "space_id": "Suite 200",
                "rsf": 2800,
                "base_rent_psf": 200.0,
                "market_rent_psf": 220.0,
                "lease_start": date(2021, 6, 1),
                "lease_end": date(2031, 5, 31),
                "escalation_type": "percentage",
                "escalation_value": 0.025,  # 2.5% annual
                "escalation_frequency": "annual",
                "reimbursement_type": "NNN",
                "recovery_percentage": 1.0,
            },
            {
                "tenant_name": "Gucci",
                "space_id": "Suite 300",
                "rsf": 2932,
                "base_rent_psf": 210.0,
                "market_rent_psf": 225.0,
                "lease_start": date(2023, 3, 1),
                "lease_end": date(2033, 2, 28),
                "escalation_type": "percentage",
                "escalation_value": 0.025,  # 2.5% annual
                "escalation_frequency": "annual",
                "reimbursement_type": "NNN",
                "recovery_percentage": 1.0,
            },
        ]

        for lease_data in leases_data:
            lease = Lease(
                scenario_id=scenario.id,
                **lease_data
            )
            db.add(lease)
            print(f"Created lease: {lease_data['tenant_name']} ({lease_data['rsf']} SF @ ${lease_data['base_rent_psf']}/SF)")

        db.commit()
        print(f"\nSuccessfully created {len(leases_data)} tenant leases!")
        print(f"Total leased SF: {sum(l['rsf'] for l in leases_data):,}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
