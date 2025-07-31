import streamlit as st
import json
from datetime import datetime
import os

# --- Cafe Time Setup ---
day_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
day_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
evening_start = datetime.strptime("17:00:00", "%H:%M:%S").time()
evening_end = datetime.strptime("22:00:00", "%H:%M:%S").time()

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Dill-Khus Cafe",
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("☕ Welcome to Dill-Khus Cafe")

# --- Determine Current Time and Session ---
now = datetime.now()
current_time = now.time()
today_date = now.strftime("%d/%m/%Y")
today_day = now.strftime("%A")
bill_time = now.strftime("%H:%M:%S")

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

# Display cafe details in the sidebar
st.sidebar.header("Cafe Details")
st.sidebar.write(f"**Session:** {session} Menu")
st.sidebar.write(f"**Date:** {today_date} ({today_day})")
st.sidebar.write(f"**Current Time:** {bill_time}")

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


# --- Customer Identity ---
st.header("Your Details")
col1_name, col2_phone = st.columns(2)
with col1_name:
    name = st.text_input("Enter your name:", key="customer_name").strip().capitalize()
with col2_phone:
    phone = st.text_input("Enter your phone number:", key="customer_phone").strip()

if not name or not phone:
    st.info("Please enter your name and phone number to proceed with ordering.")
else:
    if name in customer_data:
        prev_day = customer_data[name].get("day", "previous visit")
        st.info(f'👋 Hello {name}, once again! Hope you enjoyed that {prev_day.lower()}!')
    else:
        st.success(f"👋 Hello {name}, nice to meet you!")

    st.markdown("---")

    # --- Display Menu ---
    st.header(f"Our Menu ({session} Session)")
    for category, items in menu.items():
        with st.expander(f"**{category}**", expanded=True): # Expanders make the menu collapsible
            st.markdown("---")
            for item, price in items.items():
                st.markdown(f"- **{item}**: ₹{price}")
            st.markdown("---")

    st.markdown("---")

    # --- Take Order ---
    st.header("Place Your Order")

    # Initialize session state for order if not present
    if 'current_order_items' not in st.session_state:
        st.session_state.current_order_items = []
    if 'current_order_prices' not in st.session_state:
        st.session_state.current_order_prices = []

    # Collect all available items for the dropdown
    all_menu_items = []
    item_to_price_map = {} # To quickly get the price of a selected item
    for category, items in menu.items():
        for item_name, price in items.items():
            all_menu_items.append(item_name)
            item_to_price_map[item_name] = price
    
    # Sort items alphabetically for better user experience
    all_menu_items.sort()

    # Add a default 'Select an item' option
    all_menu_items.insert(0, "--- Select an item ---")

    # Dropdown menu for selecting items
    selected_item = st.selectbox(
        "Choose a dish to add to your order:",
        options=all_menu_items,
        key="item_selector" # Unique key for the selectbox
    )

    if st.button("Add Selected Item to Order"):
        if selected_item != "--- Select an item ---": # Check if a valid item was selected
            price = item_to_price_map.get(selected_item) # Get price from our map
            if price is not None:
                st.session_state.current_order_items.append(selected_item)
                st.session_state.current_order_prices.append(price)
                st.success(f"✅ '{selected_item}' added to your order.")
                # Force a rerun to reset the selectbox to its default state
                st.rerun()
            else:
                st.error(f"❌ Price for '{selected_item}' not found (internal error).")
        else:
            st.warning("Please select a dish from the dropdown before adding.")

    st.markdown("---")
    st.subheader("📝 Your Current Order")
    if st.session_state.current_order_items:
        # Display current order in a DataFrame for better readability
        order_df_data = [{"Item": item, "Price (₹)": price} for item, price in zip(st.session_state.current_order_items, st.session_state.current_order_prices)]
        st.dataframe(order_df_data, use_container_width=True, hide_index=True)

        # Button to clear the current order
        if st.button("Clear Order", help="Removes all items from your current order."):
            st.session_state.current_order_items = []
            st.session_state.current_order_prices = []
            st.info("Your order has been cleared.")
            st.rerun() # Rerun to refresh the display immediately
            
        st.markdown("---")
        # --- Generate Bill ---
        if st.button("Generate Bill and Finalize Order", type="primary"):
            if st.session_state.current_order_items:
                subtotal = sum(st.session_state.current_order_prices)
                gst = round(subtotal * 0.18, 2)
                total = round(subtotal + gst, 2)

                st.balloons() # Fun visual effect!
                st.subheader("🧾 Your Final Bill")
                st.markdown(f"**Customer Name:** {name}")
                st.markdown(f"**Phone Number:** {phone}")
                st.markdown(f"**Visit Session:** {session}")
                st.markdown(f"**Date:** {today_date}")
                st.markdown(f"**Day:** {today_day}")
                st.markdown(f"**Bill Time:** {bill_time}")
                
                st.write("---")
                st.markdown("### Order Summary:")
                for item, price in zip(st.session_state.current_order_items, st.session_state.current_order_prices):
                    st.markdown(f"- {item}: ₹{price:,.2f}") # Format price
                
                st.write("---")
                st.markdown(f"**Subtotal:** ₹{subtotal:,.2f}")
                st.markdown(f"**GST (18%):** ₹{gst:,.2f}")
                st.markdown(f"## **Total Payable:** ₹{total:,.2f}/-")
                st.write("---")

                # Save customer record
                customer_data[name] = {
                    "phone_number": phone,
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

                # Clear order from session state after generating bill
                st.session_state.current_order_items = []
                st.session_state.current_order_prices = []
                st.info("Your order has been cleared for the next customer.")
            else:
                st.warning("Your order is empty. Please add items before generating the bill.")
    else:
        st.info("Your order is currently empty. Use the dropdown and 'Add Item' button above.")

st.markdown("---")
st.write("Developed with ❤️ for Dill-Khus Cafe")