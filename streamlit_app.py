import streamlit as st
import json
from datetime import datetime
import os

# --- Configuration ---
CAFE_NAME = "Bhakti's Cafe.com"
CUSTOMER_DATA_FILE = "customer_data.json"

# Cafe time setup
day_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
day_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
evening_start = datetime.strptime("17:00:00", "%H:%M:%S").time()
evening_end = datetime.strptime("22:00:00", "%H:%M:%S").time()

# --- Helper Functions ---

def load_customer_data():
    """Loads customer data from JSON file."""
    if os.path.exists(CUSTOMER_DATA_FILE):
        try:
            with open(CUSTOMER_DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_customer_data(data):
    """Saves customer data to JSON file."""
    with open(CUSTOMER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_cafe_status():
    """Determines current cafe session and status."""
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
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# --- Streamlit UI ---
st.set_page_config(page_title=CAFE_NAME, layout="centered")

st.title(f"☕ Welcome to {CAFE_NAME}")

# Show current time on dashboard
now = datetime.now()
st.subheader("Current Time & Date")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Date", now.strftime("%d/%m/%Y"))
with col2:
    st.metric("Day", now.strftime("%A"))
with col3:
    st.metric("Time", now.strftime("%H:%M:%S"))

st.markdown("---")

# Determine cafe status and load menu
session, menu_file, current_datetime = get_cafe_status()

if session == "Closed":
    st.error("❌ Sorry! Cafe is closed right now.")
    st.info(f"🕒 Working Hours: {day_start.strftime('%I%p')}–{day_end.strftime('%I%p')} and {evening_start.strftime('%I%p')}–{evening_end.strftime('%I%p')}")
    st.stop() # Stop the app if cafe is closed
else:
    st.success(f"🎉 Cafe is open! Serving our **{session}** menu.")
    menu = load_menu(menu_file)
    if not menu:
        st.error(f"Menu file '{menu_file}' not found. Please contact staff.")
        st.stop()

# Initialize session state for customer details and order
if 'customer_name' not in st.session_state:
    st.session_state.customer_name = ""
if 'customer_phone' not in st.session_state:
    st.session_state.customer_phone = ""
if 'current_order' not in st.session_state:
    st.session_state.current_order = {} # Stores {item_name: quantity}

st.header("Place Your Order")

# Customer Identity
customer_data = load_customer_data()

with st.form("customer_form"):
    name = st.text_input("Enter your Name:", value=st.session_state.customer_name).strip().capitalize()
    phone = st.text_input("Enter your Phone Number:", value=st.session_state.customer_phone).strip()
    
    submitted_identity = st.form_submit_button("Confirm Identity")

    if submitted_identity:
        st.session_state.customer_name = name
        st.session_state.customer_phone = phone
        if name in customer_data:
            prev_day = customer_data[name].get("day", "N/A")
            st.info(f'👋 Hello {name}, once again! Hope you enjoyed that {prev_day.lower()}!')
        else:
            st.success(f"👋 Hello {name}, nice to meet you!")

# Keep customer name and phone number if they exist in session state
# This prevents clearing them and redirecting to the form
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

    selected_items_display = []
    
    with st.form(key="order_selection_form"):
        st.write("Select the items you'd like to order and specify quantities.")
        
        for category, items in menu.items():
            st.markdown(f"**__{category}__**")
            cols = st.columns(3) # Display items in columns
            col_idx = 0
            for item_name, price in items.items():
                with cols[col_idx]:
                    current_qty = st.session_state.current_order.get(item_name, 0)
                    new_qty = st.number_input(f"{item_name} (₹{price})", 
                                              min_value=0, 
                                              value=current_qty, 
                                              step=1, 
                                              key=f"qty_{item_name}")
                    if new_qty > 0:
                        st.session_state.current_order[item_name] = new_qty
                    elif item_name in st.session_state.current_order and new_qty == 0:
                        del st.session_state.current_order[item_name] # Remove if quantity is 0
                col_idx = (col_idx + 1) % 3

        st.form_submit_button("Update Order")

    st.markdown("---")
    st.subheader("Your Current Order")
    if st.session_state.current_order:
        order_details = []
        subtotal = 0
        for item, qty in st.session_state.current_order.items():
            price_per_item = all_menu_items.get(item, 0) # Get price from all_menu_items
            item_total = price_per_item * qty
            order_details.append(f"{item} x {qty} : ₹{item_total:.2f}")
            subtotal += item_total
        
        for item_line in order_details:
            st.write(item_line)
        
        st.write(f"**Subtotal: ₹{subtotal:.2f}**")

        if st.button("Generate Bill"):
            if not st.session_state.current_order:
                st.warning("Your cart is empty. Please add items to generate a bill.")
            else:
                # Calculate bill
                gst = round(subtotal * 0.18, 2)
                total = round(subtotal + gst, 2)
                
                # Get current time for bill generation
                bill_gen_time = datetime.now().strftime("%H:%M:%S")

                st.success("🧾 Bill Generated!")
                st.markdown("### ========== BILL ==========")
                st.write(f"**Customer Name:** {st.session_state.customer_name}")
                st.write(f"**Phone Number:** {st.session_state.customer_phone}")
                st.write(f"**Visit Session:** {session}")
                st.write(f"**Date:** {current_datetime.strftime('%d/%m/%Y')}")
                st.write(f"**Day:** {current_datetime.strftime('%A')}")
                st.write(f"**Bill Generation Time:** {bill_gen_time}") # Specific time for bill
                st.markdown("---")
                st.write("**Items Ordered:**")
                for item, qty in st.session_state.current_order.items():
                    price_per_item = all_menu_items.get(item, 0)
                    st.write(f"- {item} (x{qty}): ₹{price_per_item * qty:.2f}")
                
                st.markdown("---")
                st.write(f"**Subtotal:** ₹{subtotal:.2f}")
                st.write(f"**GST (18%):** ₹{gst:.2f}")
                st.markdown(f"### **Total Payable: ₹{total:.2f}/-**")
                st.markdown("=============================")

                # Save customer record
                customer_data = load_customer_data()
                
                ordered_items_list = []
                ordered_prices_list = []
                for item, qty in st.session_state.current_order.items():
                    price_per_item = all_menu_items.get(item, 0)
                    for _ in range(qty): # Add item and its price as many times as quantity
                        ordered_items_list.append(item)
                        ordered_prices_list.append(price_per_item)

                customer_data[st.session_state.customer_name] = {
                    "phone_number": st.session_state.customer_phone,
                    "Visiting_time": session,
                    "date": current_datetime.strftime("%d/%m/%Y"),
                    "day": current_datetime.strftime("%A"),
                    "bill_time": bill_gen_time, # Store specific bill generation time
                    "user_items": ordered_items_list,
                    "user_price": ordered_prices_list,
                    "total": total
                }
                save_customer_data(customer_data)
                st.success("✅ Order saved. Thank you for visiting!")
                
                # Clear ONLY the order after bill generation for a new order,
                # but keep customer details if they want to order again.
                st.session_state.current_order = {}
                # st.session_state.customer_name = ""  <-- REMOVE OR COMMENT THIS LINE
                # st.session_state.customer_phone = "" <-- REMOVE OR COMMENT THIS LINE
                st.rerun() # Rerun to clear order selection widgets
    else:
        st.info("Your order is empty. Please select items from the menu.")

# Optional: Add a button to start a completely new customer order
if st.session_state.customer_name or st.session_state.current_order: # Show only if there's an active customer/order
    if st.button("Start New Customer Order"):
        st.session_state.customer_name = ""
        st.session_state.customer_phone = ""
        st.session_state.current_order = {}
        st.rerun()

st.markdown("---")
st.markdown("🙏 Thank you for stopping by. See you again!")