





from tests.test_02_pools import TestPoolManagement

import pytest


class TestTransactionManagement:
    pool_id = None
    loan_id = None  # Class tracking variable for the loan
    def test_01_record_income(self, auth_client):
        """Step 1: Record an Income transaction inside the already created pool."""
        # Grab the pool_id generated dynamically in test_pools.py
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "Transaction setup failed: Pool ID was not initialized by test_pools.py"
        
        payload = {
            
            "amount": 75000,
            "transaction_type": "income",
            "belongs_to_member_id": 2,
            "pool_id": pool_id,
        }
        
        response = auth_client.post("/transactions/income", json=payload)
        
        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_02_record_expense(self, auth_client):
        """Step 2: Record an Expense transaction."""
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None
        
        payload = {
            "transaction_type": "expense",
            "belongs_to_member_id": 1,
            "amount":500.00,
            "category":"grocery",
            "pool_id": pool_id}
        
        
        response = auth_client.post("/transactions/expense", json=payload)
        
        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_03_record_loan(self, auth_client):
        """Step 3: Record a Loan transaction."""
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None, "Pool ID not set"
        
        payload = {
            "transaction_type": "loan_given",
            "belongs_to_member_id": 3,
            "amount": 1500.00,
            "lent_to_name": "FIL",
            "note": "Loan to FIL",
            "lent_to_member_id":2,
            "pool_id": pool_id
        }
        
        response = auth_client.post("/transactions/loan", json=payload)
        
        assert response.status_code == 201
        assert response.json()["success"] is True
        
        data = response.json()["data"]
        
        # Save loan_id for repayment test
        TestTransactionManagement.loan_id = data["loan_id"]
        
        print(f"✅ Loan created successfully. Loan ID: {data['loan_id']}")


    def test_04_record_repayment(self, auth_client):
        """Step 4: Record a Loan Repayment transaction."""
        pool_id = TestPoolManagement.pool_id
        assert pool_id is not None
        loan_id = TestTransactionManagement.loan_id

        assert loan_id is not None, "Repayment setup failed: Loan record was not captured."
        payload = {
    "transaction_type": "repayment",
    "loan_id": loan_id,
    "amount":1500.00,
    "payment_method":"UPI",
    "pool_id": pool_id
    }
        response = auth_client.post("/transactions/repayment", json=payload)
        
        assert response.status_code == 201
        assert response.json()["success"] is True