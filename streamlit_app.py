import streamlit as st
import json
from datetime import datetime
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
    """Determines current cafe session and status based on real-time and loaded cafe hours."""
    if not cafe_hours:
        return "Error", None, None # Cannot determine status if config failed to load

    now = datetime.now()
    current_time = now.time()
    
    if cafe_hours["day_start"] <= current_time <= cafe_hours["day_end"]:
        return "Day", "day.json", now
    elif cafe_hours["evening_start"] <= current_time <= cafe_hours["evening_end"]:
        return "Evening", "evening.json", now
    else:
        return "Closed", None, now

def load_menu(file_name):
    """Loads menu from JSON file."""
    return load_json_data(file_name)

def generate_and_save_bill(customer_name, customer_phone, current_order, all_menu_items, session):
    """Calculates bill, saves customer data, and updates session state for display."""
    # current_order is now a dict {item_name: quantity}
    subtotal = sum(all_menu_items.get(item, 0) * qty for item, qty in current_order.items())
    gst = round(subtotal * 0.18, 2)
    total = round(subtotal + gst, 2)
    
    bill_moment_datetime = datetime.now() # Capture exact time of bill generation
    bill_gen_time = bill_moment_datetime.strftime("%H:%M:%S")
    bill_date = bill_moment_datetime.strftime("%d/%m/%Y")
    bill_day = bill_moment_datetime.strftime("%A")

    # Prepare data for session state bill display
    items_ordered_for_display = []
    # No need for item_counts here since current_order already has quantities
    for item, qty in current_order.items():
        price_per_item = all_menu_items.get(item, 0)
        item_total = price_per_item * qty
        items_ordered_for_display.append(
            {"item": item, "quantity": qty, "price_per_unit": price_per_item, "total_item_price": item_total}
        )
    
    # Prepare data for original customer_data.json structure (repeated items for quantity)
    # This recreates the flat list for compatibility with existing customer_data.json structure
    ordered_items_list_for_save = []
    ordered_prices_list_for_save = []
    for item, qty in current_order.items():
        price_per_item = all_menu_items.get(item, 0)
        for _ in range(qty):
            ordered_items_list_for_save.append(item)
            ordered_prices_list_for_save.append(price_per_item)

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
    customer_data = load_json_data(CUSTOMER_DATA_FILE) or {} # Initialize if file doesn't exist/corrupt
    customer_data[customer_name] = {
        "phone_number": customer_phone,
        "Visiting_time": session,
        "date": bill_date,
        "day": bill_day,
        "bill_time": bill_gen_time,
        "user_items": ordered_items_list_for_save,
        "user_price": ordered_prices_list_for_save,
        "total": total
    }
    save_json_data(customer_data, CUSTOMER_DATA_FILE)
    st.success("✅ Order saved. Thank you for visiting!")

    st.session_state.show_bill = True
    st.session_state.current_order = {} # Clear current order inputs after bill
    st.rerun() # Trigger a rerun to display the bill and reset order inputs


# --- Streamlit UI ---
st.set_page_config(page_title=CAFE_NAME, layout="centered")

st.title(f"☕ Welcome to {CAFE_NAME}")

# Show current time on dashboard
st.subheader("Current Time & Date")

# Get current datetime for Date, Day, and Time metrics (updates on each rerun)
current_datetime_for_dashboard = datetime.now() 

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Date", current_datetime_for_dashboard.strftime("%d/%m/%Y"))
with col2:
    st.metric("Day", current_datetime_for_dashboard.strftime("%A"))
with col3:
    st.metric("Time", current_datetime_for_dashboard.strftime("%H:%M:%S")) # Display current time using st.metric


st.markdown("---")

# Load cafe operating hours from config.json
cafe_hours = load_cafe_config()
if not cafe_hours:
    st.error("Cannot start application: Cafe operating hours could not be loaded from config.json. Please ensure it's set up correctly.")
    st.stop() # Stop the app if config is critical

# Determine cafe status and load menu based on current real-time and loaded cafe hours
session, menu_file_name, cafe_status_datetime = get_cafe_status(cafe_hours)

if session == "Closed":
    st.error("❌ Sorry! Cafe is closed right now.")
    st.info(f"🕒 Working Hours: {cafe_hours['day_start'].strftime('%I%p')}–{cafe_hours['day_end'].strftime('%I%p')} and {cafe_hours['evening_start'].strftime('%I%p')}–{cafe_hours['evening_end'].strftime('%I%p')}")
    st.stop() # Stop the app if cafe is closed
elif session == "Error":
    st.stop() # Stop if there was an error loading config (already handled by load_cafe_config)
else:
    st.success(f"🎉 Cafe is open! Serving our **{session}** menu.")
    menu = load_menu(menu_file_name)
    if not menu:
        st.stop() # Stop if menu couldn't be loaded

# Initialize session state for customer details, order, and bill display
if 'customer_name' not in st.session_state:
    st.session_state.customer_name = ""
if 'customer_phone' not in st.session_state:
    st.session_state.customer_phone = ""
if 'current_order' not in st.session_state:
    st.session_state.current_order = {} # Stores {item_name: quantity}
if 'show_bill' not in st.session_state:
    st.session_state.show_bill = False
if 'last_bill_details' not in st.session_state:
    st.session_state.last_bill_details = None

st.header("Place Your Order")

# Customer Identity Form (Conditional Rendering)
# This block only displays the form if customer_name or customer_phone are NOT set in session_state
if not st.session_state.customer_name or not st.session_state.customer_phone:
    with st.form("customer_form"):
        name_input = st.text_input("Enter your Name:", value=st.session_state.customer_name, key="customer_name_input_form").strip().capitalize()
        phone_input = st.text_input("Enter your Phone Number:", value=st.session_state.customer_phone, key="customer_phone_input_form").strip()
        
        submitted_identity = st.form_submit_button("Confirm Identity")

        if submitted_identity:
            if name_input and phone_input: # Ensure both fields are filled
                st.session_state.customer_name = name_input
                st.session_state.customer_phone = phone_input

                customer_data = load_json_data(CUSTOMER_DATA_FILE) or {} # Load data here to check for revisit
                
                # MODIFIED GREETING HERE
                if name_input in customer_data:
                    st.info(f'👋 Hello, {name_input} thank you for revisiting!')
                else:
                    st.success(f"👋 Hello {name_input}, nice to meet you!")
                
                st.rerun() # Rerun to proceed to the order section (this will hide the form)
            else:
                st.warning("Please enter both your name and phone number.")
else:
    # Order Section (shown only if identity is confirmed)
    # The 'Hello, {name}' greeting is displayed here, as the form is now hidden
    st.subheader(f"Hello, {st.session_state.customer_name}! Here's our {session} Menu:")

    # Display Menu and Order Selection
    st.markdown("---")
    st.subheader("Menu Items")

    # Collect all items and their prices for easy lookup
    all_menu_items = {}
    for category, items in menu.items():
        all_menu_items.update(items)

    with st.form(key="order_selection_form"):
        st.write("Select the items you'd like to order and specify quantities.")
        
        order_changed_in_form = False 
        
        for category, items in menu.items():
            st.markdown(f"**__{category}__**")
            cols = st.columns(3) 
            col_idx = 0
            for item_name, price in items.items():
                with cols[col_idx]:
                    # Display name and price prominently, then the number input
                    st.markdown(f"**{item_name}** (₹{price})") 
                    current_qty = st.session_state.current_order.get(item_name, 0)
                    new_qty = st.number_input(f"qty_{item_name}", # Unique key for number_input
                                              min_value=0, 
                                              value=current_qty, 
                                              step=1, 
                                              key=f"qty_input_{item_name}", # Ensure unique key for widget
                                              label_visibility="collapsed") # Hide default label
                    if new_qty > 0:
                        if st.session_state.current_order.get(item_name) != new_qty:
                            st.session_state.current_order[item_name] = new_qty
                            order_changed_in_form = True
                    elif item_name in st.session_state.current_order and new_qty == 0:
                        del st.session_state.current_order[item_name]
                        order_changed_in_form = True
                col_idx = (col_idx + 1) % 3

        submit_order_button = st.form_submit_button("Update Order")
        if submit_order_button and order_changed_in_form:
            st.session_state.show_bill = False
            st.session_state.last_bill_details = None
            st.toast("Order updated!")
            st.rerun()

    st.markdown("---")
    st.subheader("Your Current Order")

    if st.session_state.current_order:
        subtotal = 0
        order_df_data = [] # For st.dataframe
        for item, qty in st.session_state.current_order.items():
            price_per_item = all_menu_items.get(item, 0)
            item_total = price_per_item * qty
            order_df_data.append({"Item": item, "Quantity": qty, "Price (₹)": f"₹{price_per_item:.2f}", "Total (₹)": f"₹{item_total:.2f}"})
            subtotal += item_total
        
        st.dataframe(order_df_data, use_container_width=True, hide_index=True)

        if st.button("Clear Order", help="Removes all items from your current order."):
            st.session_state.current_order = {}
            st.info("Your order has been cleared.")
            st.rerun()
            
        st.markdown("---")
        
        if st.button("Generate Bill", type="primary"):
            if not st.session_state.current_order: 
                st.warning("Your cart is empty. Please add items to generate a bill.")
            else:
                generate_and_save_bill(
                    st.session_state.customer_name, 
                    st.session_state.customer_phone, 
                    st.session_state.current_order, # Passing dictionary now
                    all_menu_items, 
                    session, 
                    cafe_status_datetime
                )
    else:
        st.info("Your order is empty. Please select items from the menu.")

# --- Display the generated bill ---
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
    st.markdown(f"### **Total Payable:** ₹{bill['total']:.2f}/-")
    st.markdown("=============================")

    # New buttons after bill generation for workflow clarity
    st.markdown("---")
    col_new_order1, col_new_order2 = st.columns(2)
    with col_new_order1:
        if st.button("New Order for This Customer"):
            st.session_state.current_order = {}
            st.session_state.show_bill = False
            st.session_state.last_bill_details = None
            st.rerun()
    with col_new_order2:
        if st.button("Start New Customer Order", key="start_new_customer_after_bill"):
            st.session_state.customer_name = ""
            st.session_state.customer_phone = ""
            st.session_state.current_order = {}
            st.session_state.show_bill = False 
            st.session_state.last_bill_details = None
            st.rerun()

# --- Global "Start New Customer Order" Button (always visible if an order is active) ---
# This button provides an escape hatch to start fresh even if no bill was generated.
# It only shows if there's an active customer or order, or a bill displayed.
if not st.session_state.show_bill and (st.session_state.customer_name or st.session_state.current_order):
    st.markdown("---") 
    if st.button("Start New Customer Order", key="start_new_customer_global"):
        st.session_state.customer_name = ""
        st.session_state.customer_phone = ""
        st.session_state.current_order = {}
        st.session_state.show_bill = False 
        st.session_state.last_bill_details = None
        st.rerun()

st.markdown("---")
st.markdown("🙏 Thank you for stopping by. See you again!")