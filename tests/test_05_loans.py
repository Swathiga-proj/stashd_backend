import pytest

from tests.test_02_pools import TestPoolManagement

class TestLoans:
    pool_id = None

    def test_01_loans_list(self,auth_client):
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "LoanList setup failed: Pool ID was not initialized by test_loans.py"
 
        payload = {
            
            "limit":10,
            "skip":0,
            "pool_id": pool_id
        }
        
        response = auth_client.post("/transactions/loans_list", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True