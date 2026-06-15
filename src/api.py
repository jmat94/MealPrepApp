import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.models import RecipeCreate
from src.database.db_manager import get_db_connection
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown tasks cleanly using the modern lifespan protocol.
    Everything BEFORE 'yield' runs on startup.
    Everything AFTER 'yield' runs on shutdown.
    """
    # ---- STARTUP LOGIC ----
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we already have ingredients
    cursor.execute("SELECT COUNT(*) as count FROM ingredients")
    if cursor.fetchone()["count"] == 0:
        print("🌱 Database empty. Seeding a sample recipe via lifespan startup...")
        
        recipe_id = "rec-0000-0000-0000-000000000001"
        ing1_id = str(uuid.uuid4())
        ing2_id = str(uuid.uuid4())
        
        cursor.execute("INSERT INTO ingredients VALUES (?, ?, ?, ?, ?, ?, ?)", (ing1_id, "Sweet Potato", "grams", 86.0, 1.6, 20.0, 0.1))
        cursor.execute("INSERT INTO ingredients VALUES (?, ?, ?, ?, ?, ?, ?)", (ing2_id, "Lean Ground Beef", "grams", 250.0, 26.0, 0.0, 15.0))
        cursor.execute("INSERT INTO recipes VALUES (?, ?, ?, ?, ?, ?, ?)", (recipe_id, "Beef & Sweet Potato Mash", "Cook beef. Mash potatoes. Combine.", 2, None, None, 0))
        cursor.execute("INSERT INTO recipe_ingredients VALUES (?, ?, ?, ?)", (recipe_id, ing1_id, 400.0, "400g Sweet Potato"))
        cursor.execute("INSERT INTO recipe_ingredients VALUES (?, ?, ?, ?)", (recipe_id, ing2_id, 300.0, "300g Lean Ground Beef"))
        
        conn.commit()
    conn.close()

    yield

    # ---- SHUTDOWN LOGIC (Optional) ----
    print("Cleaning up database connections and shutting down safely...")


# 4. Pass the lifespan function directly into the FastAPI instance
app = FastAPI(
    title="Meal Prep Core API",
    description="Production-ready data service to fetch and scale meal prep metrics.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"], # Allows any local origin file wrapper to query the engine
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_path = os.path.join(current_dir, "frontend")
app.mount("/ui", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def display_homepage():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    home_file_path = os.path.join(current_dir, "frontend", "home.html")
    return  FileResponse(home_file_path)



@app.post("/recipes/create")
def create_recipe(recipe_data: RecipeCreate):
    """
    Receives a validated RecipeCreate object and the store data across Recipes and Ingedients table
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Generate a unique ID
        new_recipe_id = f"rec-{str(uuid.uuid4())[:8]}"
        
        # 1. Insert Main Recipe
        cursor.execute(
            "INSERT INTO recipes (recipe_id, title, instructions, base_servings, is_premium_only) VALUES (?, ?, ?, ?, ?)",
            (new_recipe_id, recipe_data.title, recipe_data.instructions, recipe_data.base_servings, int(recipe_data.is_premium_only))
        )   

        # 2. Process Ingredients
        for ingredient in recipe_data.ingredients:
            # Check if ingredient exists, otherwise insert master definition
            cursor.execute("SELECT ingredient_id FROM ingredients WHERE name = ?", (ingredient.name,))
            existing = cursor.fetchone()
            
            if existing:
                ing_id = existing["ingredient_id"]
            else:
                ing_id = f"ing-{str(uuid.uuid4())[:8]}"
                cursor.execute(
                    "INSERT INTO ingredients (ingredient_id, name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g) VALUES (?, ?, ?, ?, ?, ?)",
                    (ing_id, ingredient.name, ingredient.calories, ingredient.protein, ingredient.carbs, ingredient.fat)
                )
            
            # 3. Link to Recipe_Ingredients
            cursor.execute(
                "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, weight_in_grams) VALUES (?, ?, ?)",
                (new_recipe_id, ing_id, ingredient.weight_in_grams)
            )
            
        conn.commit()
        return {"status": "success", "recipe_id": new_recipe_id}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Data engineering failure: {str(e)}")
    finally:
        conn.close()



# Api endpoint
@app.get("/recipe/{recipe_id}")
def get_scaled_recipe(recipe_id: str, servings: int = Query(default=2, ge=1)):
    """
    Fetches a specific recipe and scales all ingredients and nutritional values 
    dynamically to the user's requested serving size.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Core Recipe Meta Data
    cursor.execute("SELECT title, instructions, base_servings, is_premium_only FROM recipes WHERE recipe_id = ?", (recipe_id,))
    recipe = cursor.fetchone()
    
    if not recipe:
        conn.close()
        raise HTTPException(status_code=404, detail="Recipe not found.")
        
    base_servings = recipe["base_servings"]
    scale_factor = servings / base_servings
    
    # 2. Fetch and calculate scaled structural ingredients
    cursor.execute('''
        SELECT i.name, ri.weight_in_grams, i.display_unit,
               i.calories_per_100g, i.protein_per_100g, i.carbs_per_100g, i.fat_per_100g
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
        WHERE ri.recipe_id = ?
    ''', (recipe_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # 3. Process Data Scaling Loop
    ingredients_list = []
    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    
    for row in rows:
        scaled_weight = row["weight_in_grams"] * scale_factor
        
        # Calculate nutritional weight adjustments relative to 100g master data baseline
        cal = (scaled_weight / 100.0) * row["calories_per_100g"]
        pro = (scaled_weight / 100.0) * row["protein_per_100g"]
        carb = (scaled_weight / 100.0) * row["carbs_per_100g"]
        fat = (scaled_weight / 100.0) * row["fat_per_100g"]
        
        total_calories += cal
        total_protein += pro
        total_carbs += carb
        total_fat += fat
        
        ingredients_list.append({
            "name": row["name"],
            "scaled_weight_g": round(scaled_weight, 1),
            "unit": row["display_unit"]
        })
        
    # 4. Formulate Standard JSON API Response Payload
    return {
        "recipe_id": recipe_id,
        "title": recipe["title"],
        "instructions": recipe["instructions"],
        "requested_servings": servings,
        "base_servings": base_servings,
        "ingredients": ingredients_list,
        "total_nutrition_summary": {
            "calories_kcal": round(total_calories, 1),
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1)
        },
        "per_serving_nutrition": {
            "calories_kcal": round(total_calories / servings, 1),
            "protein_g": round(total_protein / servings, 1),
            "carbs_g": round(total_carbs / servings, 1),
            "fat_g": round(total_fat / servings, 1)
        }
    }



