import streamlit as st
import json
from datetime import datetime, timedelta # Import timedelta for next day calculation
import os

# --- Configuration & File Paths ---
CAFE_NAME = "Bhakti's Cafe.com"
CUSTOMER_DATA_FILE = "customer_data.json"
CONFIG_FILE = "config.json" # Centralized config file for cafe hours

# --- Helper Functions ---

def load_json_data(file_path):
    """Loads JSON data from a specified file."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Error: File '{file_path}' contains invalid JSON format. Please check its content.")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred while loading '{file_path}': {e}")
            return None
    return None

def save_json_data(data, file_path):
    """Saves data to a JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving data to '{file_path}': {e}")

def load_cafe_config():
    """Loads cafe operating hours from config.json."""
    config = load_json_data(CONFIG_FILE)
    if config:
        try:
            return {
                "day_start": datetime.strptime(config["day_start"], "%H:%M:%S").time(),
                "day_end": datetime.strptime(config["day_end"], "%H:%M:%S").time(),
                "evening_start": datetime.strptime(config["evening_start"], "%H:%M:%S").time(),
                "evening_end": datetime.strptime(config["evening_end"], "%H:%M:%S").time()
            }
        except KeyError:
            st.error(f"Configuration file '{CONFIG_FILE}' is missing required time keys (e.g., 'day_start').")
            return None
        except ValueError:
            st.error(f"Configuration file '{CONFIG_FILE}' contains invalid time formats. Use HH:MM:SS.")
            return None
    else:
        st.error(f"Configuration file '{CONFIG_FILE}' not found or is empty/corrupted.")
        return None

def get_cafe_status(cafe_hours):
    """
    Determines current cafe session and status, providing a specific closed message.
    Returns: (session_name, menu_file, current_datetime_obj, closed_message_if_any)
    """
    if not cafe_hours:
        return "Error", None, None, "Cafe configuration could not be loaded."

    now = datetime.now()
    current_time = now.time()
    
    if cafe_hours["day_start"] <= current_time <= cafe_hours["day_end"]:
        return "Day", "day.json", now, None
    elif cafe_hours["evening_start"] <= current_time <= cafe_hours["evening_end"]:
        return "Evening", "evening.json", now, None
    else:
        # Cafe is closed. Determine the specific message.
        closed_message = ""
        if current_time > cafe_hours["day_end"] and current_time < cafe_hours["evening_start"]:
            closed_message = f"Cafe is currently closed between sessions. Please visit us from {cafe_hours['evening_start'].strftime('%I:%M %p')} for our Evening Menu!"
        elif current_time > cafe_hours["evening_end"]:
            # After evening closing, suggest next day morning
            closed_message = f"Cafe is now closed for the day. We look forward to seeing you tomorrow morning at {cafe_hours['day_start'].strftime('%I:%M %p')}!"
        elif current_time < cafe_hours["day_start"]:
            # Before morning opening
            closed_message = f"Cafe is not yet open. We open at {cafe_hours['day_start'].strftime('%I:%M %p')} today!"
        else:
            closed_message = "Cafe is closed. Please check our working hours." # Fallback

        return "Closed", None, now, closed_message

def load_menu(file_name):
    """Loads menu from JSON file."""
    return load_json_data(file_name)

def generate_and_save_bill(customer_name, customer_phone, items_list, prices_list, all_menu_items, session):
    """Calculates bill, saves customer data, and updates session state for display."""
    subtotal = sum(prices_list)
    gst = round(subtotal * 0.18, 2)
    total = round(subtotal + gst, 2)
    
    bill_moment_datetime = datetime.now() # Capture exact time of bill generation
    bill_gen_time = bill_moment_datetime.strftime("%H:%M:%S")
    bill_date = bill_moment_datetime.strftime("%d/%m/%Y")
    bill_day = bill_moment_datetime.strftime("%A")

    # Prepare data for session state bill display
    items_ordered_for_display = []
    item_counts = {}
    for item in items_list:
        item_counts[item] = item_counts.get(item, 0) + 1

    for item, qty in item_counts.items():
        price_per_item = all_menu_items.get(item, 0)
        item_total = price_per_item * qty
        items_ordered_for_display.append(
            {"item": item, "quantity": qty, "price_per_unit": price_per_item, "total_item_price": item_total}
        )
    
    st.session_state.last_bill_details = {
        "customer_name": customer_name,
        "phone_number": customer_phone,
        "visit_session": session,
        "date": bill_date,
        "day": bill_day,
        "bill_generation_time": bill_gen_time,
        "items_ordered": items_ordered_for_display,
        "subtotal": subtotal,
        "gst": gst,
        "total": total
    }

    # Save customer record
    customer_data = load_json_data(CUSTOMER_DATA_FILE) or {}
    customer_data[customer_name] = {
        "phone_number": customer_phone,
        "Visiting_time": session,
        "date": bill_date,
        "day": bill_day,
        "bill_time": bill_gen_time,
        "user_items": items_list,
        "user_price": prices_list,
        "total": total
    }
    save_json_data(customer_data, CUSTOMER_DATA_FILE)
    st.success("✅ Order saved. Thank you for visiting!")

    st.session_state.show_bill = True
    st.session_state.current_order_items = []
    st.session_state.current_order_prices = []
    st.rerun()


# --- Streamlit UI ---
st.set_page_config(
    page_title=CAFE_NAME,
    layout="wide",
    initial_sidebar_state="auto"
)

st.title(f"☕ Welcome to {CAFE_NAME}")

# Load cafe operating hours from config.json
cafe_hours = load_cafe_config()
if not cafe_hours:
    st.error("Cannot start application: Cafe operating hours could not be loaded from config.json. Please ensure it's set up correctly.")
    st.stop()

# Determine cafe status and load menu based on current real-time and loaded cafe hours
now_for_display_and_status = datetime.now()
session, menu_file_name, cafe_status_datetime, closed_message = get_cafe_status(cafe_hours)

if session == "Closed":
    st.error("❌ Sorry! Cafe is closed. 😔")
    st.info(closed_message) # Display the specific closed message
    st.stop()
elif session == "Error":
    st.stop()
else:
    st.success(f"🎉 Cafe is open! Serving our **{session}** menu.")
    menu = load_menu(menu_file_name)
    if not menu:
        st.stop()

# Display cafe details in the sidebar (dynamically updated on rerun)
st.sidebar.header("Cafe Details")
st.sidebar.write(f"**Session:** {session} Menu")
st.sidebar.write(f"**Date:** {now_for_display_and_status.strftime('%d/%m/%Y')} ({now_for_display_and_status.strftime('%A')})")
st.sidebar.write(f"**Current Time:** {now_for_display_and_status.strftime('%H:%M:%S')}")


# Initialize session state for customer details, order, and bill display
if 'customer_name' not in st.session_state:
    st.session_state.customer_name = ""
if 'customer_phone' not in st.session_state:
    st.session_state.customer_phone = ""
if 'current_order_items' not in st.session_state:
    st.session_state.current_order_items = []
if 'current_order_prices' not in st.session_state:
    st.session_state.current_order_prices = []
if 'show_bill' not in st.session_state:
    st.session_state.show_bill = False
if 'last_bill_details' not in st.session_state:
    st.session_state.last_bill_details = None

st.header("Place Your Order")

# Customer Identity Form
customer_data = load_json_data(CUSTOMER_DATA_FILE) or {}

with st.form("customer_form"):
    name = st.text_input("Enter your Name:", value=st.session_state.customer_name, key="customer_name_input").strip().capitalize()
    phone = st.text_input("Enter your Phone Number:", value=st.session_state.customer_phone, key="customer_phone_input").strip()
    
    submitted_identity = st.form_submit_button("Confirm Identity")

    if submitted_identity:
        st.session_state.show_bill = False 
        st.session_state.last_bill_details = None
        st.session_state.customer_name = name
        st.session_state.customer_phone = phone
        if name in customer_data:
            prev_day = customer_data[name].get("day", "N/A")
            st.info(f'👋 Hello {name}, once again! Hope you enjoyed that {prev_day.lower()}!')
        else:
            st.success(f"👋 Hello {name}, nice to meet you!")
        st.rerun()

# Order Section (shown only if identity is confirmed)
if not st.session_state.customer_name or not st.session_state.customer_phone:
    st.warning("Please enter your name and phone number to proceed with ordering.")
else:
    st.subheader(f"Hello, {st.session_state.customer_name}! Here's our {session} Menu:")

    # Display Menu with Expanders
    st.markdown("---")
    st.header(f"Our Menu ({session} Session)")
    for category, items in menu.items():
        with st.expander(f"**{category}**", expanded=True):
            st.markdown("---")
            for item, price in items.items():
                st.markdown(f"- **{item}**: ₹{price}")
            st.markdown("---")

    st.markdown("---")

    # --- Take Order (Text Input & Add Button) ---
    st.header("Place Your Order")
    item_input = st.text_input("Enter a dish name to add to your order:", key="item_input_field")

    if st.button("Add Item to Order"):
        if item_input:
            # Collect all items and their prices for easy lookup during order taking
            all_menu_items_flat = {}
            for cat_items in menu.values():
                for item_name, price in cat_items.items():
                    all_menu_items_flat[item_name.lower()] = {"name": item_name, "price": price}

            if item_input.lower() in all_menu_items_flat:
                item_details = all_menu_items_flat[item_input.lower()]
                st.session_state.current_order_items.append(item_details["name"])
                st.session_state.current_order_prices.append(item_details["price"])
                st.success(f"✅ '{item_details['name']}' added to your order.")
                st.rerun()
            else:
                st.error(f"❌ Item '{item_input}' not found in the menu. Please check spelling.")
        else:
            st.warning("Please enter an item name to add.")

    st.markdown("---")
    st.subheader("📝 Your Current Order")
    if st.session_state.current_order_items:
        order_df_data = [{"Item": item, "Price (₹)": price} for item, price in zip(st.session_state.current_order_items, st.session_state.current_order_prices)]
        st.dataframe(order_df_data, use_container_width=True, hide_index=True)

        if st.button("Clear Order", help="Removes all items from your current order."):
            st.session_state.current_order_items = []
            st.session_state.current_order_prices = []
            st.info("Your order has been cleared.")
            st.rerun()
            
        st.markdown("---")
        
        if st.button("Generate Bill and Finalize Order", type="primary"):
            if st.session_state.current_order_items:
                all_menu_items_flat_for_bill = {}
                for category, items in menu.items():
                    all_menu_items_flat_for_bill.update(items)

                generate_and_save_bill(
                    st.session_state.customer_name, 
                    st.session_state.customer_phone, 
                    st.session_state.current_order_items,
                    st.session_state.current_order_prices,
                    all_menu_items_flat_for_bill,
                    session
                )
            else:
                st.warning("Your order is empty. Please add items before generating the bill.")
    else:
        st.info("Your order is currently empty. Use the text input and 'Add Item' button above.")

# --- Display the generated bill (using session state) ---
if st.session_state.show_bill and st.session_state.last_bill_details:
    bill = st.session_state.last_bill_details
    st.markdown("### 🧾 ========== BILL ==========")
    st.write(f"**Customer Name:** {bill['customer_name']}")
    st.write(f"**Phone Number:** {bill['phone_number']}")
    st.write(f"**Visit Session:** {bill['visit_session']}")
    st.write(f"**Date:** {bill['date']}")
    st.write(f"**Day:** {bill['day']}")
    st.write(f"**Bill Generation Time:** {bill['bill_generation_time']}")
    st.markdown("---")
    st.write("**Items Ordered:**")
    for item_detail in bill['items_ordered']:
        st.write(f"- {item_detail['item']} (x{item_detail['quantity']}): ₹{item_detail['total_item_price']:.2f}")
    
    st.markdown("---")
    st.write(f"**Subtotal:** ₹{bill['subtotal']:.2f}")
    st.write(f"**GST (18%):** ₹{bill['gst']:.2f}")
    st.markdown(f"## **Total Payable:** ₹{bill['total']:.2f}/-")
    st.markdown("=============================")

    # New buttons after bill generation for workflow clarity
    st.markdown("---")
    col_new_order1, col_new_order2 = st.columns(2)
    with col_new_order1:
        if st.button("New Order for This Customer"):
            st.session_state.current_order_items = []
            st.session_state.current_order_prices = []
            st.session_state.show_bill = False
            st.session_state.last_bill_details = None
            st.rerun()
    with col_new_order2:
        if st.button("Start New Customer Order", key="start_new_customer_after_bill"):
            st.session_state.customer_name = ""
            st.session_state.customer_phone = ""
            st.session_state.current_order_items = []
            st.session_state.current_order_prices = []
            st.session_state.show_bill = False 
            st.session_state.last_bill_details = None
            st.rerun()

# --- Global "Start New Customer Order" Button (for general reset) ---
if not st.session_state.show_bill and (st.session_state.customer_name or st.session_state.current_order_items):
    st.markdown("---") 
    if st.button("Start New Customer Order", key="start_new_customer_global"):
        st.session_state.customer_name = ""
        st.session_state.customer_phone = ""
        st.session_state.current_order_items = []
        st.session_state.current_order_prices = []
        st.session_state.show_bill = False 
        st.session_state.last_bill_details = None
        st.rerun()

st.markdown("---")
st.write("Developed with ❤️ for Dill-Khus Cafe")