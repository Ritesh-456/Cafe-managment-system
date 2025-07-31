import streamlit as st
import json
from datetime import datetime, time
import os

# Load config.json to determine cafe timings
def load_cafe_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return {
                "day_start": datetime.strptime(config["day_start"], "%H:%M:%S").time(),
                "day_end": datetime.strptime(config["day_end"], "%H:%M:%S").time(),
                "evening_start": datetime.strptime(config["evening_start"], "%H:%M:%S").time(),
                "evening_end": datetime.strptime(config["evening_end"], "%H:%M:%S").time(),
            }
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return None

# Determine current cafe status
def get_cafe_status():
    cafe_hours = load_cafe_config()
    now = datetime.now()
    current_time = now.time()
    
    # Debug info
    st.write(f"⏰ Current Time: {current_time}, Day Time: {cafe_hours['day_start']}–{cafe_hours['day_end']}, Evening Time: {cafe_hours['evening_start']}–{cafe_hours['evening_end']}")
    
    if cafe_hours["day_start"] <= current_time <= cafe_hours["day_end"]:
        return "Day", "day.json", now
    elif cafe_hours["evening_start"] <= current_time <= cafe_hours["evening_end"]:
        return "Evening", "evening.json", now
    else:
        return "Closed", None, now

# Load the current menu
def load_menu(menu_file):
    try:
        with open(menu_file, "r") as f:
            return json.load(f)
    except:
        st.error(f"Menu file {menu_file} not found.")
        return {}

# Load or initialize customer data
def load_customer_data():
    if os.path.exists("customer_data.json"):
        with open("customer_data.json", "r") as f:
            return json.load(f)
    return {}

def save_customer_data(data):
    with open("customer_data.json", "w") as f:
        json.dump(data, f, indent=4)

# Main app
def main():
    st.title("☕ Cafe Ordering System")

    status, menu_file, now = get_cafe_status()
    st.subheader(f"Cafe Status: {status}")
    if status == "Closed":
        st.warning("Cafe is currently closed. Please come during working hours.")
        return

    # Get menu
    menu = load_menu(menu_file)

    # Customer info
    name = st.text_input("Enter your name")
    phone = st.text_input("Enter your phone number")

    if name and phone:
        customer_id = f"{name.strip().lower()}_{phone.strip()}"
        customers = load_customer_data()

        # Greeting
        if customer_id in customers:
            last_visit = customers[customer_id]
            st.success(f"👋 Welcome back, {name.title()}! Hope you enjoyed your last visit on {last_visit['day']} 🌟")
        else:
            st.info(f"👋 Hello {name.title()}, welcome to our cafe!")

        # Select items
        selected_items = []
        total_price = 0

        for category, items in menu.items():
            st.markdown(f"### {category}")
            for item, price in items.items():
                quantity = st.number_input(f"{item} (₹{price})", min_value=0, step=1, key=item)
                if quantity > 0:
                    selected_items.extend([item] * quantity)
                    total_price += price * quantity

        if selected_items:
            gst = round(total_price * 0.18, 2)
            grand_total = round(total_price + gst, 2)

            if st.button("🧾 Generate Bill"):
                user_prices = []
                for item in selected_items:
                    for cat_items in menu.values():
                        if item in cat_items:
                            user_prices.append(cat_items[item])
                            break

                bill_data = {
                    "Visiting_time": status,
                    "date": now.strftime("%d/%m/%Y"),
                    "day": now.strftime("%A"),
                    "bill_time": now.strftime("%H:%M:%S"),
                    "user_items": selected_items,
                    "user_price": user_prices,
                    "total": grand_total
                }

                customers[customer_id] = bill_data
                save_customer_data(customers)

                st.success("✅ Bill generated and saved!")
                st.json(bill_data)

if __name__ == "__main__":
    main()
