menu = {
    "Espresso": 80,
    "Cappuccino": 120,
    "Latte": 130,
    "Black Coffee": 70,
    "Cold Coffee": 110,
    "Green Tea": 60,
    "Veg Sandwich": 90,
    "Cheese Sandwich": 110,
    "French Fries": 70,
    "Veg Burger": 100,
    "Cheese Burger": 120,
    "Chocolate Cake": 150,
    "Brownie": 100,
    "Ice Cream Scoop": 80,
    "Muffin": 60,
    "Combo Meal (Coffee + Sandwich)": 180,
    "All Day Breakfast": 220,
    "Pasta (White Sauce)": 160
}

user_items = []
user_price = []
user = input("Enter a dish name: ")

for item, price in menu.items():
    if user == item:
        user_items.append(item)
print(user_items, user_price)