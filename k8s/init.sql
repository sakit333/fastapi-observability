-- =========================
-- TABLES
-- =========================

CREATE TABLE restaurants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE food_items (
    id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES restaurants(id),
    name TEXT NOT NULL,
    price FLOAT NOT NULL,
    prep_time INT NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT,
    restaurant_id INT REFERENCES restaurants(id),
    item_id INT REFERENCES food_items(id),
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE,
    balance FLOAT
);

INSERT INTO accounts (user_id, balance) VALUES
(1, 10000),
(2, 5000),
(3, 75000),
(4, 2000),
(5, 15000);


-- =========================
-- RESTAURANTS (30 DATA)
-- =========================

INSERT INTO restaurants (name, location) VALUES
('Biryani House', 'Bangalore'),
('Pizza Corner', 'Bangalore'),
('Andhra Spice', 'Hyderabad'),
('Delhi Tandoor', 'Delhi'),
('Mumbai Street Eats', 'Mumbai'),
('South Kitchen', 'Chennai'),
('Punjabi Dhaba', 'Chandigarh'),
('Royal Mughlai', 'Lucknow'),
('Kolkata Flavours', 'Kolkata'),
('Udupi Veg', 'Bangalore'),
('Arabian Nights', 'Dubai'),
('Burger Hub', 'Bangalore'),
('Chinese Wok', 'Chennai'),
('Italiano Pasta', 'Mumbai'),
('Cafe Coffee Day', 'Pan India'),
('BBQ Nation', 'Delhi'),
('Rolls King', 'Kolkata'),
('Sandwich Express', 'Pune'),
('Healthy Bowl', 'Bangalore'),
('Street Dosa', 'Chennai'),
('Kebab Factory', 'Hyderabad'),
('Grill House', 'Mumbai'),
('Veg Delight', 'Bangalore'),
('NonVeg Express', 'Delhi'),
('Food Court', 'Mall'),
('Tiffin Center', 'Hyderabad'),
('Fast Bites', 'Pune'),
('Snack Shack', 'Mumbai'),
('Fusion Foods', 'Bangalore'),
('Spicy Treat', 'Chennai');

-- =========================
-- FOOD ITEMS (60 DATA)
-- =========================

INSERT INTO food_items (restaurant_id, name, price, prep_time) VALUES
(1, 'Chicken Biryani', 250, 20),
(1, 'Mutton Biryani', 350, 30),
(2, 'Veg Pizza', 200, 15),
(2, 'Chicken Pizza', 300, 20),
(3, 'Andhra Chicken Curry', 280, 25),
(3, 'Gongura Mutton', 320, 30),
(4, 'Butter Chicken', 270, 20),
(4, 'Tandoori Roti', 40, 10),
(5, 'Vada Pav', 50, 5),
(5, 'Pav Bhaji', 120, 15),
(6, 'Idli', 40, 5),
(6, 'Dosa', 80, 10),
(7, 'Chole Bhature', 150, 15),
(7, 'Paneer Butter Masala', 220, 20),
(8, 'Mughlai Chicken', 300, 25),
(8, 'Seekh Kebab', 260, 20),
(9, 'Fish Curry', 280, 25),
(9, 'Rosogolla', 60, 5),
(10, 'Masala Dosa', 90, 10),
(10, 'Upma', 70, 10),
(11, 'Shawarma', 150, 10),
(11, 'Falafel', 120, 10),
(12, 'Cheese Burger', 180, 15),
(12, 'Chicken Burger', 220, 15),
(13, 'Hakka Noodles', 180, 15),
(13, 'Manchurian', 160, 15),
(14, 'Pasta Alfredo', 250, 20),
(14, 'Lasagna', 300, 25),
(15, 'Cold Coffee', 120, 5),
(15, 'Sandwich', 150, 10),
(16, 'BBQ Chicken', 350, 30),
(16, 'Grilled Fish', 320, 25),
(17, 'Egg Roll', 80, 10),
(17, 'Chicken Roll', 120, 10),
(18, 'Veg Sandwich', 100, 10),
(18, 'Grilled Sandwich', 150, 15),
(19, 'Salad Bowl', 200, 10),
(19, 'Fruit Bowl', 180, 5),
(20, 'Plain Dosa', 60, 10),
(20, 'Onion Dosa', 80, 12),
(21, 'Chicken Kebab', 250, 20),
(21, 'Mutton Kebab', 300, 25),
(22, 'Grilled Chicken', 280, 20),
(22, 'BBQ Wings', 240, 20),
(23, 'Veg Thali', 200, 20),
(23, 'Paneer Thali', 250, 20),
(24, 'Chicken Thali', 280, 20),
(24, 'Mutton Thali', 320, 25),
(25, 'Combo Meal', 300, 20),
(25, 'Snack Combo', 150, 10),
(26, 'Idli Combo', 80, 10),
(26, 'Dosa Combo', 120, 15),
(27, 'Burger Combo', 200, 15),
(27, 'Pizza Combo', 300, 20),
(28, 'Fries', 100, 10),
(28, 'Nuggets', 150, 10),
(29, 'Fusion Pizza', 320, 20),
(29, 'Fusion Burger', 280, 20),
(30, 'Spicy Noodles', 180, 15),
(30, 'Spicy Rice', 200, 15);

-- =========================
-- ORDERS (30 SAMPLE DATA)
-- =========================

INSERT INTO orders (user_id, restaurant_id, item_id, status) VALUES
(1, 1, 1, 'delivered'),
(2, 2, 3, 'delivered'),
(3, 3, 5, 'delivered'),
(4, 4, 7, 'delivered'),
(5, 5, 9, 'delivered'),
(6, 6, 11, 'delivered'),
(7, 7, 13, 'delivered'),
(8, 8, 15, 'delivered'),
(9, 9, 17, 'delivered'),
(10, 10, 19, 'delivered'),
(11, 11, 21, 'delivered'),
(12, 12, 23, 'delivered'),
(13, 13, 25, 'delivered'),
(14, 14, 27, 'delivered'),
(15, 15, 29, 'delivered'),
(16, 16, 31, 'delivered'),
(17, 17, 33, 'delivered'),
(18, 18, 35, 'delivered'),
(19, 19, 37, 'delivered'),
(20, 20, 39, 'delivered'),
(21, 21, 41, 'delivered'),
(22, 22, 43, 'delivered'),
(23, 23, 45, 'delivered'),
(24, 24, 47, 'delivered'),
(25, 25, 49, 'delivered'),
(26, 26, 51, 'delivered'),
(27, 27, 53, 'delivered'),
(28, 28, 55, 'delivered'),
(29, 29, 57, 'delivered'),
(30, 30, 59, 'delivered');