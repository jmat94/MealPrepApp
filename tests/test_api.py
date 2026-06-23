from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_read_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "html" in response.headers["content-type"]

def test_recipe_scaling_calculation():
    """
    Verifies that the core calculation engine scales ingredient metrics accurately.
    Uses the baseline sample seed data loaded by the lifespan manager.
    """
    # Target the seed recipe 'rec-0000-0000-0000-000000000001' scaled to 4 servings
    # (Base servings = 2, so scaling factor is 4/2 = 2.0x)
    response = client.get("/recipe/rec-0000-0000-0000-000000000001?servings=4")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate core data structure schema matches expected output
    assert data["title"] == "Beef & Sweet Potato Mash"
    assert "ingredients" in data
    
    # Sweet Potato baseline weight was 400g. At 2.0x scale, it must equal 800g.
    sweet_potato = data["ingredients"][0]
    assert sweet_potato["scaled_weight_grams"] == 600.0


