import pytest
from tests.test_02_pools import TestPoolManagement
import uuid



class TestSplitExpense:
    member_ids = []  # member ids in the pool, populated in test_01

    def test_01_get_pool_members(self, auth_client):
        """Ensure at least 2 members exist in the pool, then fetch their ids."""
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "Pool ID not set"
        payload = {
            "skip":0,
            "limit":10,
            "pool_id":pool_id
        }
        response = auth_client.post("/pools/members",json=payload)
        assert response.status_code == 200

        members = response.json()["data"]
        names_to_add = ["Grandma", "FIL"]
        idx = 0

        while len(members) < 2 and idx < len(names_to_add):
            unique_id = str(uuid.uuid4())[:6]
            add_response = auth_client.post("/pools/add_member", json={
                "pool_id": pool_id,
                "name": names_to_add[idx],
                "phone_number": f"+91 99432{unique_id}",
                "password": "demo123",
                "role": "member"
            })
            assert add_response.status_code == 201, add_response.text
            idx += 1

            response = auth_client.get("/pools/members")
            members = response.json()["data"]

        assert len(members) >= 2, "Need at least 2 members in the pool to test a split"
        TestSplitExpense.member_ids = [m["id"] for m in members]


    def test_02_create_split_expense_valid(self, auth_client):
        """Split expense across valid pool members should succeed."""
        member_ids = TestSplitExpense.member_ids
        assert len(member_ids) >= 2
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "Pool ID not set"
        print("MEMBER IDS BEING USED:", member_ids)
        payload = {
            "pool_id": pool_id,
            "total_amount": 1000.00,
            "category": "groceries",
            "note": "Weekly shopping",
            "split_details": [
                {"member_id": member_ids[0], "amount": 500.00},
                {"member_id": member_ids[1], "amount": 500.00},
            ]
        }

        response = auth_client.post("/transactions/split_expense", json=payload)
        assert response.status_code == 201

        body = response.json()
        assert body["success"] is True
        assert "message" in body["data"] or "message" in body

    def test_03_create_split_expense_invalid_member(self, auth_client):
        """Splitting with a member_id outside the pool should be rejected."""
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "Pool ID not set"

        payload = {
            "pool_id": pool_id,
            "total_amount": 500.00,
            "category": "transport",
            "note": "Cab fare",
            "split_details": [
                {"member_id": 99999, "amount": 500.00},  # nonexistent / wrong-pool member
            ]
        }

        response = auth_client.post("/transactions/split_expense", json=payload)
        assert response.status_code == 400
        assert "don't belong to this pool" in response.json()["detail"]

    def test_04_split_amounts_must_sum_to_total(self, auth_client):
        """Split amounts that don't add up to total_amount should fail validation."""
        member_ids = TestSplitExpense.member_ids
        assert len(member_ids) >= 2
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "Pool ID not set"

        payload = {
            "pool_id": pool_id,
            "total_amount": 1000.00,
            "category": "groceries",
            "note": "Mismatched split",
            "split_details": [
                {"member_id": member_ids[0], "amount": 300.00},
                {"member_id": member_ids[1], "amount": 300.00},  # only sums to 600, not 1000
            ]
        }

        response = auth_client.post("/transactions/split_expense", json=payload)
        # Adjust expected status depending on whether this validation exists yet
        assert response.status_code in (400, 422)