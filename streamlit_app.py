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
            # Handle empty or corrupted JSON file
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
        st.error(f"Menu file '{file_name}' not found. Please ensure it exists.")
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

# Customer Identity
customer_data = load_customer_data()

with st.form("customer_form"):
    name = st.text_input("Enter your Name:", value=st.session_state.customer_name).strip().capitalize()
    phone = st.text_input("Enter your Phone Number:", value=st.session_state.customer_phone).strip()
    
    submitted_identity = st.form_submit_button("Confirm Identity")

    if submitted_identity:
        st.session_state.customer_name = name
        st.session_state.customer_phone = phone
        # If customer identity is confirmed/changed, hide any previous bill
        st.session_state.show_bill = False 
        st.session_state.last_bill_details = None
        if name in customer_data:
            prev_day = customer_data[name].get("day", "N/A")
            st.info(f'👋 Hello {name}, once again! Hope you enjoyed that {prev_day.lower()}!')
        else:
            st.success(f"👋 Hello {name}, nice to meet you!")
        # To make sure order selection is refreshed with cleared bill display
        st.rerun() 

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
        
        # This flag tracks if any quantity changed in this form submission
        order_changed_in_form = False 
        
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
                        if st.session_state.current_order.get(item_name) != new_qty:
                            st.session_state.current_order[item_name] = new_qty
                            order_changed_in_form = True
                    elif item_name in st.session_state.current_order and new_qty == 0:
                        del st.session_state.current_order[item_name]
                        order_changed_in_form = True
                col_idx = (col_idx + 1) % 3

        submit_order_button = st.form_submit_button("Update Order")
        if submit_order_button and order_changed_in_form:
            # If the order is explicitly updated, hide any previously generated bill
            st.session_state.show_bill = False
            st.session_state.last_bill_details = None # Clear bill details
            st.toast("Order updated!")
            st.rerun() # Rerun to reflect updated order immediately

    st.markdown("---")
    st.subheader("Your Current Order")

    if st.session_state.current_order:
        order_details = []
        subtotal = 0
        for item, qty in st.session_state.current_order.items():
            price_per_item = all_menu_items.get(item, 0)
            item_total = price_per_item * qty
            order_details.append(f"{item} x {qty} : ₹{item_total:.2f}")
            subtotal += item_total
        
        for item_line in order_details:
            st.write(item_line)
        
        st.write(f"**Subtotal: ₹{subtotal:.2f}**")

        if st.button("Generate Bill"):
            # This check is technically redundant here because the button only appears if current_order is not empty
            if not st.session_state.current_order: 
                st.warning("Your cart is empty. Please add items to generate a bill.")
            else:
                # Calculate bill
                gst = round(subtotal * 0.18, 2)
                total = round(subtotal + gst, 2)
                
                # Get current time for bill generation
                bill_gen_time = datetime.now().strftime("%H:%M:%S")

                # Store bill details in session state to display after rerun
                st.session_state.last_bill_details = {
                    "customer_name": st.session_state.customer_name,
                    "phone_number": st.session_state.customer_phone,
                    "visit_session": session,
                    "date": current_datetime.strftime('%d/%m/%Y'),
                    "day": current_datetime.strftime('%A'),
                    "bill_generation_time": bill_gen_time, # Specific time for bill
                    "items_ordered": [], 
                    "subtotal": subtotal,
                    "gst": gst,
                    "total": total
                }
                
                # Populate items_ordered for saving and display
                ordered_items_list = []
                ordered_prices_list = []
                for item, qty in st.session_state.current_order.items():
                    price_per_item = all_menu_items.get(item, 0)
                    item_total = price_per_item * qty
                    st.session_state.last_bill_details["items_ordered"].append(
                        {"item": item, "quantity": qty, "price_per_unit": price_per_item, "total_item_price": item_total}
                    )
                    # For original customer_data.json structure
                    for _ in range(qty): 
                        ordered_items_list.append(item)
                        ordered_prices_list.append(price_per_item)

                # Save customer record
                customer_data = load_customer_data()
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
                
                # Set flag to show bill and clear current order for next interaction
                st.session_state.show_bill = True
                st.session_state.current_order = {} 
                st.rerun() # Trigger a rerun to display the bill and clear the order inputs
    else:
        st.info("Your order is empty. Please select items from the menu.")

# --- Display the generated bill (separate from generation logic) ---
# This block will execute on the rerun triggered by "Generate Bill"
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
    st.markdown(f"### **Total Payable: ₹{bill['total']:.2f}/-**")
    st.markdown("=============================")
    
    # Optionally, provide a button to clear the bill display if user wants
    # or let it persist until a new order is started.

# --- "Start New Customer Order" Button ---
# This button clears everything and allows for a fresh start.
if st.session_state.customer_name or st.session_state.current_order or st.session_state.show_bill:
    st.markdown("---") # Separator for clarity
    if st.button("Start New Customer Order"):
        st.session_state.customer_name = ""
        st.session_state.customer_phone = ""
        st.session_state.current_order = {}
        st.session_state.show_bill = False 
        st.session_state.last_bill_details = None
        st.rerun()

st.markdown("---")
st.markdown("🙏 Thank you for stopping by. See you again!")