import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.database.db_manager import init_db, get_db_connection

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Automated fixture that builds and seeds tables according to the master schema.
    """
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
 
    cursor.execute("DELETE FROM recipe_ingredients;")
    cursor.execute("DELETE FROM ingredients;")
    cursor.execute("DELETE FROM recipes;")
    

    cursor.execute(
        """
        INSERT INTO recipes (recipe_id, title, instructions, base_servings) 
        VALUES (?, ?, ?, ?)
        """,
        ('rec-0000-0000-0000-000000000001', 'Beef & Sweet Potato Mash', 'Mix and bake.', 4)
    )
    

    cursor.execute(
        """
        INSERT INTO ingredients (ingredient_id, name, display_unit, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ('ing-0000-0000-0000-000000000001', 'Sweet Potato', 'grams', 86.0, 1.6, 20.0, 0.1)
    )
    
    
    cursor.execute(
        """
        INSERT INTO recipe_ingredients (recipe_id, ingredient_id, weight_in_grams, raw_display_amount) 
        VALUES (?, ?, ?, ?)
        """,
        ('rec-0000-0000-0000-000000000001', 'ing-0000-0000-0000-000000000001', 600.0, '600g')
    )
    
    conn.commit()
    conn.close()
    yield

def test_recipe_scaling_calculation():
    """
    Verifies that the core calculation engine scales ingredient metrics accurately.
    """
    # Base servings is 4. Requesting 4 servings means a 1.0x scale (600g).
    response = client.get("/recipe/rec-0000-0000-0000-000000000001?servings=4")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Beef & Sweet Potato Mash"
    assert "ingredients" in data
    
    sweet_potato = data["ingredients"][0]
    
    # 🟢 Update the key inside the brackets to match your API response schema output
    # (e.g., "weight_in_grams", "amount", or "scaled_weight_g")
    assert sweet_potato["weight_in_grams"] == 600.0
    
