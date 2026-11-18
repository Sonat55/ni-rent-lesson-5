import pytest

from src.manager import Manager
from src.models import Parameters
from src.models import Bill
from src.models import ApartmentSettlement
from src.models import Tenant
from src.models import TenantSettlement

def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=1250.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-03-15',
        settlement_year=2024,
        settlement_month=2,
        amount_pln=1150.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-02-02',
        settlement_year=2024,
        settlement_month=1,
        amount_pln=222.0,
        type='electricity'
    ))

    costs = manager.get_apartment_costs('apartment-1', 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs('apart-polanka', 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs('apart-polanka', 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs('apart-polanka', 2025, 1)
    assert costs == 910.0

    costs = manager.get_apartment_costs('apart-polanka', 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs('apart-polanka')
    assert costs == 3532.0

    costs = manager.get_apartment_costs('apart-nie-istnieje', 2024, 2)
    assert costs is None

    costs = manager.get_apartment_costs('apart-polanka', 2024, 5)
    assert costs == 0.0

    costs = manager.get_apartment_costs('apart-polanka', 2024, 2)
    assert costs == 1150.0

def test_apartment_settlement():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
            apartment='apart-polanka',
            date_due='2025-03-15',
            settlement_year=2025,
            settlement_month=2,
            amount_pln=1250.0,
            type='rent'
        ))

    manager.bills.append(Bill(
            apartment='apart-polanka',
            date_due='2024-03-15',
            settlement_year=2024,
            settlement_month=2,
            amount_pln=1150.0,
            type='rent'
        ))
    
    manager.bills.append(Bill(
            apartment='apart-polanka',
            date_due='2024-02-02',
            settlement_year=2024,
            settlement_month=1,
            amount_pln=222.0,
            type='electricity'
        ))


    settlement = manager.create_apartment_settlement('apart-polanka', 2025, 1)
    assert settlement is not None
    assert isinstance(settlement, ApartmentSettlement)
    assert settlement.apartment == 'apart-polanka'
    assert settlement.year == 2025
    assert settlement.month == 1
    assert settlement.total_bills_pln == 910.0


    settlement = manager.create_apartment_settlement('apart-polanka', 2025, 2)
    assert settlement.total_bills_pln == 1250.0
    assert settlement.total_due_pln == -1250.0

    settlement = manager.create_apartment_settlement('apart-polanka', 2025, 3)
    assert settlement.apartment == 'apart-polanka'
    assert settlement.month == 3


    assert manager.create_apartment_settlement('nie-apart', 2025, 1) is None


def test_tenant_setlement():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
                apartment='apart-polanka',
                date_due='2025-03-15',
                settlement_year=2025,
                settlement_month=2,
                amount_pln=1250.0,
                type='rent'
            ))
    
    manager.bills.append(Bill(
                apartment='apart-polanka',
                date_due='2024-03-15',
                settlement_year=2024,
                settlement_month=2,
                amount_pln=1150.0,
                type='rent'
            ))
        
    manager.bills.append(Bill(
                apartment='apart-polanka',
                date_due='2024-02-02',
                settlement_year=2024,
                settlement_month=1,
                amount_pln=222.0,
                type='electricity'
            ))

    manager.tenants = {
        'tenant-1': Tenant(
            name="Jan Nowak",
            apartment="apart-polanka",
            room="room-bigger",
            rent_pln=1500.0,
            deposit_pln=3000.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31'
        ),
        'tenant-2': Tenant(
            name="Adam Kowalski",
            apartment="apart-polanka",
            room="room-medium",
            rent_pln=1400.0,
            deposit_pln=2900.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31'
        ),
        'tenant-3': Tenant(
            name="Ewa Adamska",
            apartment="apart-polanka",
            room="room-smaller",
            rent_pln=1300.0,
            deposit_pln=2800.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31'
        ),
    }

    # 3 najemców: rachunki dzielone po równo
    apartment_settlement = manager.create_apartment_settlement('apart-polanka', 2025, 1)
    tenant_settlements = manager.create_tenant_settlements(apartment_settlement)

    assert len(tenant_settlements) == 3
    assert all(isinstance(s, TenantSettlement) for s in tenant_settlements)
    assert {s.tenant for s in tenant_settlements} == {'tenant-1', 'tenant-2', 'tenant-3'}
    for s in tenant_settlements:
        assert s.apartment_settlement == 'apart-polanka'
        assert s.year == 2025
        assert s.month == 1
        assert s.bills_pln == pytest.approx(910.0 / 3)
        assert s.total_due_pln == pytest.approx(-910.0 / 3)
    assert sum(s.bills_pln for s in tenant_settlements) == pytest.approx(910.0)

    # 1 najemca: ponosi całość rachunków
    manager.tenants = {'tenant-1': manager.tenants['tenant-1']}
    tenant_settlements = manager.create_tenant_settlements(apartment_settlement)

    assert len(tenant_settlements) == 1
    assert tenant_settlements[0].tenant == 'tenant-1'
    assert tenant_settlements[0].bills_pln == pytest.approx(910.0)
    assert tenant_settlements[0].total_due_pln == pytest.approx(-910.0)

    # brak najemców: rozliczenia nie powinny być tworzone
    manager.tenants = {}
    assert manager.create_tenant_settlements(apartment_settlement) == []
