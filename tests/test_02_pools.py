
import pytest


# A shared global variable to pass the generated pool ID between functions

class TestPoolManagement:
    # This class variable will store the pool ID dynamically between tests
    pool_id = None

    
    def test01_create_pool(self,auth_client):
        response = auth_client.post("/pools/create_pool", json={"name": "Family Stash"})
        
        assert response.status_code == 201
        assert response.json()["success"] is True
        
        # Store the generated ID globally so subsequent test cases can target it
        TestPoolManagement.pool_id = response.json()["data"]["pool_id"]

    
    def test02_add_member(self,auth_client):
        assert TestPoolManagement.pool_id is not None, "Pool was not initialized in the prior test step."        
        payload = {
            "pool_id": TestPoolManagement.pool_id,
            "name": "Father-in-law",
            "phone_number": "+91 9876543211",
            "password": "demo123",
            "role": "member"
        }
        response = auth_client.post("/pools/add_member", json=payload)
        
        assert response.status_code == 201
        assert response.json()["success"] is True

    
    def test03_get_members_list(self,auth_client):
        response = auth_client.post("/pools/members",json={"limit":10,"skip":0,"pool_id": TestPoolManagement.pool_id})
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["total"] >= 2  # Verifies both Priya and FIL persist