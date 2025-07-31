import streamlit as st
import json
from datetime import datetime
import os
import streamlit.components.v1 as components # Import for custom HTML

# --- Cafe Time Setup ---
day_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
day_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
evening_start = datetime.strptime("17:00:00", "%H:%M:%S").time()
evening_end = datetime.strptime("22:00:00", "%H:%M:%S").time()

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Bhakti's cafe",
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("☕ Welcome to Bhakti's cafe")

# --- Determine Current Time and Session ---
now = datetime.now()
current_time = now.time()
today_date = now.strftime("%d/%m/%Y")
today_day = now.strftime("%A")

session = None
file_name = None

if day_start <= current_time <= day_end:
    session = "Day"
    file_name = "day.json"
elif evening_start <= current_time <= evening_end:
    session = "Evening"
    file_name = "evening.json"
else:
    st.error("❌ Sorry! Cafe is closed. 😔\n🕒 Working Hours: 10AM–3PM and 5PM–10PM")
    st.stop() # Stop the app if the cafe is closed

# --- Display cafe details in the sidebar ---
st.sidebar.header("Cafe Details")
st.sidebar.write(f"**Session:** {session} Menu") # This line is now safe
st.sidebar.write(f"**Date:** {today_date} ({today_day})")

# --- Live Clock in Sidebar (Corrected placement) ---
live_clock_html = """
<div style="font-weight: bold; padding-bottom: 5px;">Current Time: <span id="live-time"></span></div>
<script>
    function updateLiveClock() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const liveTimeElement = document.getElementById('live-time');
        if (liveTimeElement) {
            liveTimeElement.innerText = `${hours}:${minutes}:${seconds}`;
        }
    }
    setInterval(updateLiveClock, 1000);
    updateLiveClock();
</script>
"""
# CORRECTED LINE: Call components.html inside the st.sidebar block
with st.sidebar:
    components.html(live_clock_html, height=50)

# bill_time for saving the order (captured at the start of the script run)
bill_time = now.strftime("%H:%M:%S")


# --- Load Menu ---
menu = {}
try:
    with open(file_name, 'r') as f:
        menu = json.load(f)
except FileNotFoundError:
    st.error(f"Menu file '{file_name}' not found. Please ensure it exists in the same directory as the script.")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Error decoding JSON from '{file_name}'. Please check the file format for errors.")
    st.stop()

# --- Load Customer Data ---
customer_data = {}
customer_data_file = "customer_data.json"
if os.path.exists(customer_data_file):
    try:
        with open(customer_data_file, "r") as f:
            customer_data = json.load(f)
    except json.JSONDecodeError:
        st.warning(f"Could not read '{customer_data_file}'. Starting with empty customer data. "
                   "Please check its JSON format.")
        customer_data = {}
else:
    st.info(f"'{customer_data_file}' not found. A new one will be created upon the first order.")

# --- Initialize Session State for UI Flow ---
# app_stage can be: 'customer_details', 'menu_view', 'ordering', 'bill_generated'
if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'customer_details'
if 'customer_name' not in st.session_state:
    st.session_state.customer_name = ""
if 'customer_phone' not in st.session_state:
    st.session_state.customer_phone = ""
if 'current_order_items' not in st.session_state:
    st.session_state.current_order_items = []
if 'current_order_prices' not in st.session_state:
    st.session_state.current_order_prices = []

# --- Customer Details Stage ---
if st.session_state.app_stage == 'customer_details':
    st.header("Your Details")
    col1_name, col2_phone = st.columns(2)

    with col1_name:
        name_input = st.text_input("Enter your name:", value=st.session_state.customer_name, key="customer_name_input").strip().capitalize()
    with col2_phone:
        phone_input = st.text_input("Enter your phone number:", value=st.session_state.customer_phone, key="customer_phone_input").strip()

    # Update session state with the values from text inputs
    st.session_state.customer_name = name_input
    st.session_state.customer_phone = phone_input

    # Buttons for customer management and proceeding
    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        if st.button("New Customer", help="Clear details to enter a new customer."):
            st.session_state.customer_name = ""
            st.session_state.customer_phone = ""
            st.session_state.current_order_items = []
            st.session_state.current_order_prices = []
            st.session_state.app_stage = 'customer_details'
            st.rerun()

    with col_btn2:
        if st.session_state.customer_name and st.session_state.customer_phone:
            if st.session_state.customer_phone.isdigit():
                if st.button("Process", type="primary", help="Continue with the entered customer details."):
                    st.session_state.app_stage = 'menu_view'
                    st.rerun()
            else:
                st.error("❌ Phone number must contain only digits. Please correct it.")
        else:
            st.info("Please enter your name and phone number to proceed. (Press Enter after typing in fields)")
            
    if st.session_state.customer_name and st.session_state.customer_phone:
        if st.session_state.customer_name in customer_data:
            prev_day = customer_data[st.session_state.customer_name].get("day", "previous visit")
            st.info(f'👋 Hello {st.session_state.customer_name}, once again! Hope you enjoyed that {prev_day.lower()}!')
        else:
            st.success(f"👋 Hello {st.session_state.customer_name}, nice to meet you!")

    st.markdown("---")

# --- Menu View Stage ---
elif st.session_state.app_stage == 'menu_view':
    st.header(f"Our Menu ({session} Session) for {st.session_state.customer_name}")
    for category, items in menu.items():
        with st.expander(f"**{category}**", expanded=True):
            st.markdown("---")
            for item, price in items.items():
                st.markdown(f"- **{item}**: ₹{price}")
            st.markdown("---")

    st.markdown("---")
    
    st.subheader("Ready to order?")
    order_choice = st.radio(
        "Would you like to place an order?",
        options=["Yes, I'd like to order", "No, just browsing"],
        index=0 if st.session_state.current_order_items else 0,
        key="order_prompt_radio"
    )

    if order_choice == "Yes, I'd like to order":
        if st.button("Proceed to Order Form", type="primary"):
            st.session_state.app_stage = 'ordering'
            st.rerun()
    else:
        st.info("🙏 Thank you for stopping by. See you again!")
        if st.button("Go Back to Customer Details"):
            st.session_state.app_stage = 'customer_details'
            st.rerun()


# --- Ordering Stage ---
elif st.session_state.app_stage == 'ordering':
    st.header(f"Place Your Order for {st.session_state.customer_name}")

    all_menu_items_formatted = []
    item_to_price_map = {}
    for category, items in menu.items():
        for item_name, price in items.items():
            item_to_price_map[item_name] = price
            all_menu_items_formatted.append(f"{item_name} (₹{price})")
    
    all_menu_items_formatted.sort()
    all_menu_items_formatted.insert(0, "--- Select an item ---")

    selected_formatted_item = st.selectbox(
        "Choose a dish to add to your order:",
        options=all_menu_items_formatted,
        key="item_selector"
    )

    if st.button("Add Selected Item to Order"):
        if selected_formatted_item != "--- Select an item ---":
            actual_item_name = selected_formatted_item.split(' (₹')[0] 
            
            price = item_to_price_map.get(actual_item_name)
            if price is not None:
                st.session_state.current_order_items.append(actual_item_name)
                st.session_state.current_order_prices.append(price)
                st.success(f"✅ '{actual_item_name}' added to your order.")
                st.rerun()
            else:
                st.error(f"❌ Price for '{actual_item_name}' not found (internal error).")
        else:
            st.warning("Please select a dish from the dropdown before adding.")

    st.markdown("---")
    st.subheader("📝 Your Current Order")
    if st.session_state.current_order_items:
        order_df_data = [{"Item": item, "Price (₹)": price} for item, price in zip(st.session_state.current_order_items, st.session_state.current_order_prices)]
        st.dataframe(order_df_data, use_container_width=True, hide_index=True)

        col_order_btn1, col_order_btn2 = st.columns([1,1])
        with col_order_btn1:
            if st.button("Clear Order", help="Removes all items from your current order."):
                st.session_state.current_order_items = []
                st.session_state.current_order_prices = []
                st.info("Your order has been cleared.")
                st.rerun()
        with col_order_btn2:
            if st.button("Generate Bill and Finalize Order", type="primary"):
                if st.session_state.current_order_items:
                    st.session_state.app_stage = 'bill_generated'
                    st.rerun()
                else:
                    st.warning("Your order is empty. Please add items before generating the bill.")
    else:
        st.info("Your order is currently empty. Use the dropdown and 'Add Item' button above.")
    
    st.markdown("---")
    if st.button("Back to Menu View"):
        st.session_state.app_stage = 'menu_view'
        st.rerun()


# --- Bill Generated Stage ---
elif st.session_state.app_stage == 'bill_generated':
    subtotal = sum(st.session_state.current_order_prices)
    gst = round(subtotal * 0.18, 2)
    total = round(subtotal + gst, 2)

    st.balloons()
    st.subheader("🧾 Your Final Bill")
    st.markdown(f"**Customer Name:** {st.session_state.customer_name}")
    st.markdown(f"**Phone Number:** {st.session_state.customer_phone}")
    st.markdown(f"**Visit Session:** {session}")
    st.markdown(f"**Date:** {today_date}")
    st.markdown(f"**Day:** {today_day}")
    st.markdown(f"**Bill Time:** {bill_time}") 
    
    st.write("---")
    st.markdown("### Order Summary:")
    for item, price in zip(st.session_state.current_order_items, st.session_state.current_order_prices):
        st.markdown(f"- {item}: ₹{price:,.2f}")
    
    st.write("---")
    st.markdown(f"**Subtotal:** ₹{subtotal:,.2f}")
    st.markdown(f"**GST (18%):** ₹{gst:,.2f}")
    st.markdown(f"## **Total Payable:** ₹{total:,.2f}/-")
    st.write("---")

    # Save customer record
    customer_data[st.session_state.customer_name] = {
        "phone_number": st.session_state.customer_phone,
        "Visiting_time": session,
        "date": today_date,
        "day": today_day,
        "bill_time": bill_time,
        "user_items": st.session_state.current_order_items,
        "user_price": st.session_state.current_order_prices,
        "total": total
    }

    try:
        with open(customer_data_file, "w") as f:
            json.dump(customer_data, f, indent=4)
        st.success("✅ Order saved successfully! Thank you for visiting!")
    except IOError as e:
        st.error(f"Failed to save customer data: {e}. Please check file permissions.")

    st.session_state.current_order_items = []
    st.session_state.current_order_prices = []
    st.session_state.customer_name = ""
    st.session_state.customer_phone = ""
    
    st.info("You can now start a new order for the next customer.")
    if st.button("Start New Customer Order", type="primary"):
        st.session_state.app_stage = 'customer_details'
        st.rerun()

st.markdown("---")
st.write("Developed with ❤️ for Bhakti's cafe")