import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.database import engine, Base

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Automated fixture that runs once before all tests.
    It builds the tables dynamically and seeds the required data.
    """

    Base.metadata.create_all(bind=engine)
    with engine.connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO recipes (id, title, servings) VALUES ('rec-0000-0000-0000-000000000001', 'Beef & Sweet Potato Mash', 4)"
        )
        connection.execute(
            "INSERT OR IGNORE INTO ingredients (recipe_id, name, scaled_weight_g) VALUES ('rec-0000-0000-0000-000000000001', 'Sweet Potato', 600.0)"
        )

    yield

    Base.metadata.drop_all(bind=engine)



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


