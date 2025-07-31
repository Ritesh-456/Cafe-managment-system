import streamlit as st
import json
from datetime import datetime
import os
# No need to import streamlit.components.v1 as components if not using live clock

# --- Configuration ---
CAFE_NAME = "Bhakti's Cafe.com"
CUSTOMER_DATA_FILE = "customer_data.json"

# Cafe time setup (static times for opening/closing)
day_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
day_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
evening_start = datetime.strptime("17:00:00", "%H:%M:%S").time()
evening_end = datetime.strptime("22:00:00", "%H:%M:%S").time()

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

def get_cafe_status():
    """Determines current cafe session and status based on real-time."""
    now = datetime.now()
    current_time = now.time()
    
    if day_start <= current_time <= day_end:
        return "Day", "day.json", now
    elif evening_start <= current_time <= evening_end:
        return "Evening", "evening.json", now
    else:
        return "Closed", None, now

def load_menu(file_name):
    """Loads menu from JSON file."""
    return load_json_data(file_name)

def generate_and_save_bill(customer_name, customer_phone, current_order, all_menu_items, session, cafe_status_datetime):
    """Calculates bill, saves customer data, and updates session state for display."""
    subtotal = sum(all_menu_items.get(item, 0) * qty for item, qty in current_order.items())
    gst = round(subtotal * 0.18, 2)
    total = round(subtotal + gst, 2)
    
    bill_moment_datetime = datetime.now() # Capture exact time of bill generation
    bill_gen_time = bill_moment_datetime.strftime("%H:%M:%S")
    bill_date = bill_moment_datetime.strftime("%d/%m/%Y")
    bill_day = bill_moment_datetime.strftime("%A")

    # Prepare data for session state bill display
    items_ordered_for_display = []
    for item, qty in current_order.items():
        price_per_item = all_menu_items.get(item, 0)
        item_total = price_per_item * qty
        items_ordered_for_display.append(
            {"item": item, "quantity": qty, "price_per_unit": price_per_item, "total_item_price": item_total}
        )
    
    # Prepare data for original customer_data.json structure (repeated items for quantity)
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

# Determine cafe status and load menu based on current real-time
session, menu_file_name, cafe_status_datetime = get_cafe_status()

if session == "Closed":
    st.error("❌ Sorry! Cafe is closed right now.")
    st.info(f"🕒 Working Hours: {day_start.strftime('%I%p')}–{day_end.strftime('%I%p')} and {evening_start.strftime('%I%p')}–{evening_end.strftime('%I%p')}")
    st.stop() # Stop the app if cafe is closed
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

# Customer Identity Form
customer_data = load_json_data(CUSTOMER_DATA_FILE) or {} # Ensure customer_data is a dict even if file is new/corrupt

with st.form("customer_form"):
    name = st.text_input("Enter your Name:", value=st.session_state.customer_name).strip().capitalize()
    phone = st.text_input("Enter your Phone Number:", value=st.session_state.customer_phone).strip()
    
    submitted_identity = st.form_submit_button("Confirm Identity")

    if submitted_identity:
        # Reset bill display when identity is confirmed/changed
        st.session_state.show_bill = False 
        st.session_state.last_bill_details = None
        st.session_state.customer_name = name
        st.session_state.customer_phone = phone
        if name in customer_data:
            prev_day = customer_data[name].get("day", "N/A")
            st.info(f'👋 Hello {name}, once again! Hope you enjoyed that {prev_day.lower()}!')
        else:
            st.success(f"👋 Hello {name}, nice to meet you!")
        st.rerun() # Rerun to refresh the display based on new identity status

# Order Section (shown only if identity is confirmed)
if not st.session_state.customer_name or not st.session_state.customer_phone:
    st.warning("Please enter your name and phone number to proceed with ordering.")
else:
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
        for item, qty in st.session_state.current_order.items():
            price_per_item = all_menu_items.get(item, 0)
            item_total = price_per_item * qty
            st.write(f"- {item} x {qty} : ₹{item_total:.2f}")
            subtotal += item_total
        
        st.write(f"**Subtotal: ₹{subtotal:.2f}**")

        if st.button("Generate Bill"):
            if not st.session_state.current_order: 
                st.warning("Your cart is empty. Please add items to generate a bill.")
            else:
                generate_and_save_bill(
                    st.session_state.customer_name, 
                    st.session_state.customer_phone, 
                    st.session_state.current_order, 
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
    st.write(f"**Phone Number:** {bill['phone_phone_number']}")
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
    st.markdown(f"### **Total Payable: ₹{bill['total']:.2f}/-**")
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