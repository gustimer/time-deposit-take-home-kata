"""Unit-level HTTP adapter tests: FastAPI TestClient + in-memory fake repo.

No DB, no testcontainers -- `get_repository` (the DI provider that would
otherwise build a real `SqlAlchemyTimeDepositRepository` bound to a Postgres
session) is overridden via `app.dependency_overrides` with
`FakeTimeDepositRepository`, exercising the full
router -> deps -> use case -> schema wiring without ever touching Postgres.
"""

from fastapi.testclient import TestClient

from adapters.inbound.http.app import create_app
from adapters.inbound.http.deps import get_repository
from domain.withdrawal import Withdrawal
from tests.unit.fake_repository import FakeTimeDepositRepository
from time_deposit import TimeDeposit


def make_client(repo):
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: repo
    return TestClient(app)


class TestUpdateBalancesEndpoint:
    def test_post_update_balances_returns_updated_list(self):
        # Reuses the pinned characterization value: basic/1234567.00/days=45
        # -> 1235595.81 (see tests/unit/test_characterization.py).
        deposit = TimeDeposit(id=1, planType="basic", balance=1234567.00, days=45)
        repo = FakeTimeDepositRepository(deposits=[deposit])
        client = make_client(repo)

        response = client.post("/time-deposits/update-balances")

        assert response.status_code == 200
        assert response.json() == [
            {
                "id": 1,
                "planType": "basic",
                "balance": 1235595.81,
                "days": 45,
                "withdrawals": [],
            }
        ]

    def test_post_update_balances_persists_via_save_all(self):
        deposit = TimeDeposit(id=1, planType="basic", balance=1234567.00, days=45)
        repo = FakeTimeDepositRepository(deposits=[deposit])
        client = make_client(repo)

        client.post("/time-deposits/update-balances")

        assert len(repo.save_all_calls) == 1
        assert repo.save_all_calls[0][0].balance == 1235595.81


class TestListDepositsEndpoint:
    def test_get_time_deposits_returns_nested_withdrawals(self):
        deposit = TimeDeposit(id=1, planType="basic", balance=1000.83, days=31)
        w1 = Withdrawal(id=10, timeDepositId=1, amount=100.0, date="2026-01-01")
        w2 = Withdrawal(id=11, timeDepositId=1, amount=50.0, date="2026-02-01")
        no_withdrawal_deposit = TimeDeposit(
            id=2, planType="student", balance=1002.5, days=365
        )
        repo = FakeTimeDepositRepository(
            deposits=[deposit, no_withdrawal_deposit], withdrawals=[w1, w2]
        )
        client = make_client(repo)

        response = client.get("/time-deposits")

        assert response.status_code == 200
        body = response.json()
        assert body[0] == {
            "id": 1,
            "planType": "basic",
            "balance": 1000.83,
            "days": 31,
            "withdrawals": [
                {"id": 10, "timeDepositId": 1, "amount": 100.0, "date": "2026-01-01"},
                {"id": 11, "timeDepositId": 1, "amount": 50.0, "date": "2026-02-01"},
            ],
        }

    def test_get_time_deposits_empty_withdrawals_is_empty_list(self):
        deposit = TimeDeposit(id=2, planType="student", balance=1002.5, days=365)
        repo = FakeTimeDepositRepository(deposits=[deposit], withdrawals=[])
        client = make_client(repo)

        response = client.get("/time-deposits")

        assert response.status_code == 200
        body = response.json()
        assert body[0]["withdrawals"] == []

    def test_response_keys_are_exactly_the_spec_camel_case_fields(self):
        deposit = TimeDeposit(id=1, planType="basic", balance=1000.0, days=31)
        repo = FakeTimeDepositRepository(deposits=[deposit], withdrawals=[])
        client = make_client(repo)

        response = client.get("/time-deposits")

        assert set(response.json()[0].keys()) == {
            "id",
            "planType",
            "balance",
            "days",
            "withdrawals",
        }


class TestRouteRegistration:
    def test_exactly_two_business_routes_registered(self):
        # The OpenAPI schema is the effective, version-proof route table --
        # it reflects exactly the API endpoints the router registered,
        # independent of how the ASGI framework internally represents
        # included sub-routers. Docs infra (/docs, /redoc, /openapi.json
        # itself) never appears under `paths`.
        app = create_app()
        schema = app.openapi()

        assert set(schema["paths"].keys()) == {
            "/time-deposits",
            "/time-deposits/update-balances",
        }
        assert set(schema["paths"]["/time-deposits"].keys()) == {"get"}
        assert set(schema["paths"]["/time-deposits/update-balances"].keys()) == {
            "post"
        }

    def test_openapi_json_endpoint_lists_both_endpoints(self):
        app = create_app()
        client = TestClient(app)

        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "/time-deposits" in schema["paths"]
        assert "get" in schema["paths"]["/time-deposits"]
        assert "/time-deposits/update-balances" in schema["paths"]
        assert "post" in schema["paths"]["/time-deposits/update-balances"]
