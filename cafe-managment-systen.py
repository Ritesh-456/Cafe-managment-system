import json
from datetime import datetime
import os

# Cafe time setup
day_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
day_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
evening_start = datetime.strptime("17:00:00", "%H:%M:%S").time()
evening_end = datetime.strptime("22:00:00", "%H:%M:%S").time()

# Determine current time and session
now = datetime.now()
current_time = now.time()
today_date = now.strftime("%d/%m/%Y")
today_day = now.strftime("%A")
bill_time = now.strftime("%H:%M:%S")

if day_start <= current_time <= day_end:
    session = "Day"
    file_name = "day.json"
elif evening_start <= current_time <= evening_end:
    session = "Evening"
    file_name = "evening.json"
else:
    print("❌ Sorry! Cafe is closed.\n🕒 Working Hours: 10AM–3PM and 5PM–10PM")
    exit()

# Load menu
try:
    with open(file_name, 'r') as f:
        menu = json.load(f)
except FileNotFoundError:
    print(f"Menu file '{file_name}' not found.")
    exit()

# Load customer data if exists
if os.path.exists("customer_data.json"):
    try:
        with open("customer_data.json", "r") as f:
            customer_data = json.load(f)
    except json.JSONDecodeError:
        customer_data = {}
else:
    customer_data = {}

# Greet customer
print(f"\nWelcome to Dill-Khus Cafe ({session} Menu)\n")

# Take customer identity
name = input("Enter your name: ").strip().capitalize()
phone = input("Enter your phone number: ").strip()

if name in customer_data:
    prev_day = customer_data[name]["day"]
    print(f'👋 Hello {name}, once again! Hope you enjoyed that {prev_day.lower()}!')
else:
    print(f"👋 Hello {name}, nice to meet you!")

# Show menu
def display_menu():
    print("\n========== CAFE MENU ==========")
    for category, items in menu.items():
        print(f"\n-- {category} --")
        for item, price in items.items():
            print(f"{item}: ₹{price}")
    print("================================")

display_menu()

# Take order
agree = input("\nWould you like to order? (yes/no): ").strip().lower()
user_items = []
user_price = []

if agree == "yes":
    while True:
        item_input = input("Enter a dish name (or 'done' to finish): ").strip().lower()
        if item_input == "done":
            break

        found = False
        for cat_items in menu.values():
            for item_name, price in cat_items.items():
                if item_name.lower() == item_input:
                    user_items.append(item_name)
                    user_price.append(price)
                    print(f"✅ {item_name} added to your order.")
                    found = True
                    break
            if found:
                break

        if not found:
            print("❌ Item not found. Please try again.")

    # Calculate bill
    subtotal = sum(user_price)
    gst = round(subtotal * 0.18, 2)
    total = round(subtotal + gst, 2)

    print("\n🧾 ========== BILL ==========")
    print("Customer Name:", name)
    print("Phone Number:", phone)
    print("Visit Time:", session)
    print("Date:", today_date)
    print("Day:", today_day)
    print("Bill Time:", bill_time)
    print("Items Ordered:", ", ".join(user_items))
    print("Prices:", user_price)
    print(f"Subtotal: ₹{subtotal}")
    print(f"GST (18%): ₹{gst}")
    print(f"Total Payable: ₹{total}/-")
    print("=============================")

    # Save customer record
    customer_data[name] = {
        "phone_number": phone,
        "Visiting_time": session,
        "date": today_date,
        "day": today_day,
        "bill_time": bill_time,
        "user_items": user_items,
        "user_price": user_price,
        "total": total
    }

    with open("customer_data.json", "w") as f:
        json.dump(customer_data, f, indent=4)

    print("✅ Order saved. Thank you for visiting!")
else:
    print("🙏 Thank you for stopping by. See you again!")
