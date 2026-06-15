CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    account_tier TEXT NOT NULL DEFAULT 'free',
    daily_calorie_target REAL,
    protein_target_g REAL,
    carbs_target_g REAL,
    fat_target_g REAL
);

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    display_unit TEXT DEFAULT 'grams', 
    calories_per_100g REAL NOT NULL,
    protein_per_100g  REAL NOT NULL,
    carbs_per_100g    REAL NOT NULL,
    fat_per_100g      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    instructions TEXT NOT NULL,
    base_servings INTEGER NOT NULL DEFAULT 4,
    image_url TEXT,
    created_by_user_id TEXT,
    is_premium_only INTEGER NOT NULL DEFAULT 0, 
    FOREIGN KEY(created_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id TEXT,
    ingredient_id TEXT,
    weight_in_grams REAL NOT NULL, 
    raw_display_amount TEXT, 
    PRIMARY KEY (recipe_id, ingredient_id),
    FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    FOREIGN KEY(ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT
);


