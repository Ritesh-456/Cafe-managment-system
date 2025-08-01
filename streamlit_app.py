import streamlit as st
import json
from datetime import datetime
import os
import pytz # Import the pytz library
from fpdf import FPDF # Import FPDF for PDF generation

# --- Configuration & File Paths ---
CAFE_NAME = "Bhakti's Cafe.com"
CUSTOMER_DATA_FILE = "customer_data.json"
CONFIG_FILE = "config.json" # Centralized config file for cafe hours

# Define the timezone for India (Asia/Kolkata)
kolkata_timezone = pytz.timezone('Asia/Kolkata')

# Initialize menu and all_menu_items as empty dictionaries at the global scope.
# They will be populated later if the cafe is open and menu file is loaded successfully.
menu = {}
all_menu_items = {}

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
            st.error(f"Configuration file '{CONFIG_FILE}' is missing required time keys (e.g., 'day_start', 'day_end', 'evening_start', 'evening_end').")
            return None
        except ValueError:
            st.error(f"Configuration file '{CONFIG_FILE}' contains invalid time formats. Use HH:MM:SS (e.g., '10:00:00').")
            return None
    else:
        st.error(f"Configuration file '{CONFIG_FILE}' not found or is empty/corrupted.")
        return None

def get_cafe_status(cafe_hours):
    """
    Determines current cafe session and status, providing a specific closed message.
    Returns: (session_name, menu_file, current_datetime_obj, is_open, closed_message_if_any)
    """
    if not cafe_hours:
        return "Error", None, None, False, "Cafe configuration could not be loaded."

    # Get current time in Asia/Kolkata timezone
    now = datetime.now(kolkata_timezone)
    current_time = now.time()

    if cafe_hours["day_start"] <= current_time <= cafe_hours["day_end"]:
        return "Day", "day.json", now, True, None
    elif cafe_hours["evening_start"] <= current_time <= cafe_hours["evening_end"]:
        return "Evening", "evening.json", now, True, None
    else:
        # Cafe is closed. Determine the specific message.
        closed_message = ""
        if current_time > cafe_hours["day_end"] and current_time < cafe_hours["evening_start"]:
            # Between day and evening sessions
            closed_message = f"Cafe is currently closed between sessions. We will reopen at {cafe_hours['evening_start'].strftime('%I:%M %p')} for our Evening Menu!"
        elif current_time > cafe_hours["evening_end"]:
            # After evening closing
            closed_message = f"Cafe is now closed for the day. We look forward to seeing you tomorrow morning at {cafe_hours['day_start'].strftime('%I:%M %p')}!"
        elif current_time < cafe_hours["day_start"]:
            # Before morning opening
            closed_message = f"Cafe is not yet open. We open at {cafe_hours['day_start'].strftime('%I:%M %p')} today!"
        else:
            closed_message = f"Cafe is closed. Please check our working hours: Day ({cafe_hours['day_start'].strftime('%I:%M %p')} - {cafe_hours['day_end'].strftime('%I:%M %p')}), Evening ({cafe_hours['evening_start'].strftime('%I:%M %p')} - {cafe_hours['evening_end'].strftime('%I:%M %p')})." # Fallback

        return "Closed", None, now, False, closed_message

def load_menu(file_name):
    """Loads menu from JSON file."""
    return load_json_data(file_name)

def generate_pdf_bill(bill_details):
    """Generates a PDF bill from bill details."""
    pdf = FPDF()
    pdf.add_page()

    # --- SIMPLIFIED FONT HANDLING: Using built-in Arial font ---
    # This completely bypasses the need for 'fonts/' folder and custom .ttf files.
    # It might not support all Unicode characters (like ₹), but should prevent font-related errors.
    pdf.set_font("Arial", size=10) # Set a reliable default font

    try:
        # Cafe Header
        pdf.set_font("Arial", "B", 16) # Use Arial
        pdf.cell(0, 10, CAFE_NAME, 0, 1, 'C')
        pdf.set_font("Arial", "", 8) # Use Arial
        pdf.cell(0, 5, "--- Your Coffee & Delights Destination ---", 0, 1, 'C')
        pdf.ln(5)

        # Bill Details
        pdf.set_font("Arial", "B", 10) # Use Arial
        pdf.cell(0, 7, "BILL DETAILS", 0, 1, 'L')
        pdf.set_font("Arial", "", 9) # Use Arial
        # Ensure all keys accessed here exist in bill_details
        pdf.cell(0, 5, f"Customer Name: {bill_details['customer_name']}", 0, 1, 'L')
        pdf.cell(0, 5, f"Phone Number: {bill_details['phone_number']}", 0, 1, 'L')
        pdf.cell(0, 5, f"Visit Session: {bill_details['visit_session']}", 0, 1, 'L')
        pdf.cell(0, 5, f"Date: {bill_details['date']}", 0, 1, 'L')
        pdf.cell(0, 5, f"Day: {bill_details['day']}", 0, 1, 'L')
        pdf.cell(0, 5, f"Bill Time: {bill_details['bill_generation_time']}", 0, 1, 'L')
        pdf.ln(5)

        # Items Ordered Header
        pdf.set_font("Arial", "B", 10) # Use Arial
        pdf.cell(0, 7, "ITEMS ORDERED", 0, 1, 'L')
        pdf.set_font("Arial", "B", 9) # Use Arial
        pdf.cell(100, 6, "Item", 0, 0, 'L')
        pdf.cell(20, 6, "Qty", 0, 0, 'C')
        pdf.cell(30, 6, "Price (Rs)", 0, 0, 'R')
        pdf.cell(30, 6, "Total (Rs)", 0, 1, 'R')
        pdf.set_font("Arial", "", 9) # Use Arial
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y()) # Draw a line

        # Itemized List
        for item_detail in bill_details['items_ordered']:
            pdf.cell(100, 6, item_detail['item'], 0, 0, 'L')
            pdf.cell(20, 6, str(item_detail['quantity']), 0, 0, 'C')
            pdf.cell(30, 6, f"{item_detail['price_per_unit']:.2f}", 0, 0, 'R')
            pdf.cell(30, 6, f"{item_detail['total_item_price']:.2f}", 0, 1, 'R')
        pdf.ln(2)
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y()) # Draw a line
        pdf.ln(2)

        # Summary Totals
        pdf.set_font("Arial", "B", 10) # Use Arial
        pdf.cell(150, 7, "Subtotal (before discount):", 0, 0, 'R')
        pdf.cell(30, 7, f"Rs{bill_details['initial_subtotal']:.2f}", 0, 1, 'R')

        pdf.cell(150, 5, f"Total Items: {bill_details['total_items_count']}", 0, 1, 'R')

        if bill_details['discount_percentage'] > 0:
            pdf.cell(150, 7, f"Discount Applied ({bill_details['discount_percentage']:.0f}%):", 0, 0, 'R')
            pdf.cell(30, 7, f"-Rs{bill_details['discount_amount']:.2f}", 0, 1, 'R')
            pdf.cell(150, 7, "Subtotal (after discount):", 0, 0, 'R')
            pdf.cell(30, 7, f"Rs{bill_details['subtotal_after_discount']:.2f}", 0, 1, 'R')

        pdf.cell(150, 7, "GST (18%):", 0, 0, 'R')
        pdf.cell(30, 7, f"Rs{bill_details['gst']:.2f}", 0, 1, 'R')

        pdf.set_font("Arial", "B", 12) # Use Arial
        pdf.cell(150, 10, "TOTAL PAYABLE:", 0, 0, 'R')
        pdf.cell(30, 10, f"Rs{bill_details['total']:.2f}/-", 0, 1, 'R')
        pdf.ln(5)
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y()) # Draw a line
        pdf.ln(5)

        # Footer
        pdf.set_font("Arial", "I", 9) # Use Arial for italic
        pdf.cell(0, 5, "Thank you for visiting Bhakti's Cafe!", 0, 1, 'C')
        pdf.cell(0, 5, "We hope to see you again soon!", 0, 1, 'C')

        return pdf.output(dest='b')

    except Exception as e:
        # Catch any other error during PDF content generation or output
        st.error(f"An error occurred while generating the PDF bill content: {e}")
        return None # Explicitly return None if an error occurs


def generate_and_save_bill(customer_name, customer_phone, current_order, all_menu_items_context, session):
    """Calculates bill, applies discounts, saves customer data, and updates session state for display."""
    initial_subtotal = sum(all_menu_items_context.get(item, 0) * qty for item, qty in current_order.items())

    total_items_count = sum(current_order.values())
    discount_percentage = 0.0

    if total_items_count > 11:
        discount_percentage = 0.09 # 9% for more than 11 items
    elif total_items_count > 8:
        discount_percentage = 0.06 # 6% for more than 8 items
    elif total_items_count > 5:
        discount_percentage = 0.03 # 3% for more than 5 items

    discount_amount = round(initial_subtotal * discount_percentage, 2)
    subtotal_after_discount = round(initial_subtotal - discount_amount, 2)

    gst = round(subtotal_after_discount * 0.18, 2)
    total = round(subtotal_after_discount + gst, 2)

    # Capture exact time of bill generation in Asia/Kolkata timezone
    bill_moment_datetime = datetime.now(kolkata_timezone)
    bill_gen_time = bill_moment_datetime.strftime("%H:%M:%S")
    bill_date = bill_moment_datetime.strftime("%d/%m/%Y")
    bill_day = bill_moment_datetime.strftime("%A")

    # Prepare data for session state bill display
    items_ordered_for_display = []
    for item, qty in current_order.items():
        price_per_item = all_menu_items_context.get(item, 0)
        item_total = price_per_item * qty
        items_ordered_for_display.append(
            {"item": item, "quantity": qty, "price_per_unit": price_per_item, "total_item_price": item_total}
        )

    # Prepare data for original customer_data.json structure (repeated items for quantity)
    ordered_items_list_for_save = []
    ordered_prices_list_for_save = []
    for item, qty in current_order.items():
        price_per_item = all_menu_items_context.get(item, 0)
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
        "initial_subtotal": initial_subtotal, # Store initial subtotal
        "total_items_count": total_items_count, # Store item count
        "discount_percentage": discount_percentage * 100, # Store as %
        "discount_amount": discount_amount,
        "subtotal_after_discount": subtotal_after_discount, # Store discounted subtotal
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
        "total_items_count": total_items_count, # Save item count
        "discount_applied_percent": discount_percentage * 100, # Save discount
        "total": total
    }
    save_json_data(customer_data, CUSTOMER_DATA_FILE)
    st.success("✅ Order saved. Thank you for visiting!")

    st.session_state.show_bill = True
    st.session_state.current_order = {} # Clear current order inputs after bill
    # Reset wants_to_order after successful bill generation to guide flow
    st.session_state.wants_to_order = False
    st.rerun() # Trigger a rerun to display the bill and reset order inputs


# --- Streamlit UI ---
st.set_page_config(page_title=CAFE_NAME, layout="centered")

st.title(f"☕ Welcome to {CAFE_NAME}")

# Show current time on dashboard
st.subheader("Current Time & Date")

# Get current datetime for Date, Day, and Time metrics (updates on each rerun) in Kolkata timezone
current_datetime_for_dashboard = datetime.now(kolkata_timezone)

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
    # Critical error, stop app as hours are essential
    st.error("Cannot start application: Cafe operating hours could not be loaded from config.json. Please ensure it's set up correctly.")
    st.stop()

# Determine cafe status and load menu based on current real-time and loaded cafe hours
session, menu_file_name, cafe_status_datetime, is_cafe_open, closed_message = get_cafe_status(cafe_hours)

if session == "Error":
    st.error(closed_message)
    st.stop()

# --- Initialize session state for order and bill printing ---
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
if 'wants_to_order' not in st.session_state: # New flag for post-identity decision
    st.session_state.wants_to_order = False


# --- MAIN APP LOGIC FLOW (conditional based on cafe status) ---

if not is_cafe_open:
    # Scenario: Cafe is CLOSED
    st.error("❌ Sorry! Cafe is closed. 😔")
    st.info(closed_message) # Display the specific closed message
    st.markdown("---")
    st.subheader("Browse Our Menu:")
    browsing_menu_content = load_menu("day.json") # Default to day menu for browsing when closed
    if browsing_menu_content:
        for category, items in browsing_menu_content.items():
            with st.expander(f"**{category}**", expanded=False): # Collapsible for long menus
                st.markdown("---")
                for item, price in items.items():
                    st.markdown(f"- **{item}**: ₹{price}")
                st.markdown("---")
    else:
        st.warning("Menu for browsing is not available (e.g., 'day.json' not found).")
    st.stop() # Stop further execution when closed and only displaying static info/menu

else: # Cafe is OPEN
    st.header("Place Your Order")

    # Assign the active session's menu to the global 'menu' variable
    # This block ensures 'menu' and 'all_menu_items' are populated ONLY when cafe is open
    menu = load_menu(menu_file_name)
    if not menu:
        st.error(f"Menu for {session} session ('{menu_file_name}') not found or is empty/corrupted. Please check menu files.")
        st.stop()

    # Populate global all_menu_items after 'menu' is successfully loaded
    for category, items in menu.items():
        all_menu_items.update(items)


    # Display the bill if one was just generated (this block runs on rerun after generate_and_save_bill)
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
        st.write(f"**Subtotal (before discount):** ₹{bill['initial_subtotal']:.2f}")
        st.write(f"**Total Items:** {bill['total_items_count']}")
        if bill['discount_percentage'] > 0:
            st.write(f"**Discount Applied:** {bill['discount_percentage']:.0f}% (₹{bill['discount_amount']:.2f})")
            st.write(f"**Subtotal (after discount):** ₹{bill['subtotal_after_discount']:.2f}")

        st.write(f"**GST (18%):** ₹{bill['gst']:.2f}")
        st.markdown(f"## **Total Payable:** ₹{bill['total']:.2f}/-")
        st.markdown("=============================")

        # PDF Download Button
        pdf_bytes = generate_pdf_bill(bill)
        # Check if pdf_bytes is None (due to an error in generate_pdf_bill)
        if pdf_bytes is not None:
            bill_filename = f"Bhakti_Cafe_Bill_{bill['customer_name'].replace(' ', '_')}_{bill['date'].replace('/', '-')}.pdf"
            st.download_button(
                label="Download Bill as PDF",
                data=pdf_bytes,
                file_name=bill_filename,
                mime="application/pdf",
                type="secondary"
            )
        else:
            st.warning("Could not generate PDF for download. Please check the error messages above for details.")
        st.markdown("---")

        col_new_order1, col_new_order2 = st.columns(2)
        with col_new_order1:
            if st.button("New Order for This Customer"):
                st.session_state.current_order = {}
                st.session_state.show_bill = False
                st.session_state.last_bill_details = None
                st.session_state.wants_to_order = True
                st.rerun()
        with col_new_order2:
            if st.button("Start New Customer Order", key="start_new_customer_after_bill"):
                st.session_state.customer_name = ""
                st.session_state.customer_phone = ""
                st.session_state.current_order = {}
                st.session_state.show_bill = False
                st.session_state.last_bill_details = None
                st.session_state.wants_to_order = False
                st.rerun()
        st.stop() # Stop execution after displaying the bill and options

    # --- Identity Confirmation or Order Flow (if not showing bill) ---
    if not st.session_state.customer_name or not st.session_state.customer_phone:
        # Scenario: Cafe Open, Identity NOT Confirmed - Show Form
        with st.form("customer_form"):
            name_input = st.text_input("Enter your Name:", value=st.session_state.customer_name, key="customer_name_input_form").strip().capitalize()
            phone_input = st.text_input("Enter your Phone Number:", value=st.session_state.customer_phone, key="customer_phone_input_form").strip()

            submitted_identity = st.form_submit_button("Confirm Identity")

            if submitted_identity:
                if name_input and phone_input:
                    st.session_state.customer_name = name_input
                    st.session_state.customer_phone = phone_input

                    customer_data = load_json_data(CUSTOMER_DATA_FILE) or {}

                    if name_input in customer_data:
                        st.info(f'👋 Hello, {name_input} thank you for revisiting!')
                    else:
                        st.success(f"👋 Hello {name_input}, nice to meet you!")

                    st.session_state.wants_to_order = None # Set to None to indicate decision pending
                    st.rerun()
                else:
                    st.warning("Please enter both your name and phone number.")

    else: # Identity IS Confirmed
        st.subheader(f"Hello, {st.session_state.customer_name}! Here's our {session} Menu:")

        # Display Menu with Expanders (shown immediately after login)
        st.markdown("---")
        st.header(f"Our Menu ({session} Session)")
        for category, items in menu.items():
            with st.expander(f"**{category}**", expanded=True):
                st.markdown("---")
                for item, price in items.items():
                    st.markdown(f"- **{item}**: ₹{price}")
                st.markdown("---")

        st.markdown("---")

        if st.session_state.wants_to_order is None:
            # Scenario: Cafe Open, Identity Confirmed, Decision to Order Pending - Show Order Prompt
            st.subheader(f"Would you like to place an order?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, I'd like to order!", key="wants_order_yes"):
                    st.session_state.wants_to_order = True
                    st.rerun()
            with col_no:
                if st.button("No, thank you.", key="wants_order_no"):
                    st.session_state.customer_name = ""
                    st.session_state.customer_phone = ""
                    st.session_state.current_order = {}
                    st.session_state.wants_to_order = False
                    st.info("No problem! Returning to the identity form.")
                    st.rerun()

        elif st.session_state.wants_to_order:
            # Scenario: Cafe Open, Identity Confirmed, WANTS to order - Show Order Form
            st.subheader("Time to select your delicious items!")

            st.markdown("---")
            st.subheader("Menu Items") # This header can be adjusted or removed if redundant

            with st.form(key="order_selection_form"):
                st.write("Select the items you'd like to order and specify quantities.")

                order_changed_in_form = False

                for category, items in menu.items():
                    st.markdown(f"**__{category}__**")
                    cols = st.columns(3)
                    col_idx = 0
                    for item_name, price in items.items():
                        with cols[col_idx]:
                            st.markdown(f"**{item_name}** (₹{price})")
                            current_qty = st.session_state.current_order.get(item_name, 0)
                            new_qty = st.number_input(f"qty_{item_name}",
                                                      min_value=0,
                                                      value=current_qty,
                                                      step=1,
                                                      key=f"qty_input_{item_name}",
                                                      label_visibility="collapsed")
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
            st.subheader("📝 Your Current Order")

            if st.session_state.current_order:
                subtotal = 0
                order_df_data = []
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
                            st.session_state.current_order,
                            all_menu_items,
                            session
                        )
            else:
                st.info("Your order is empty. Please select items from the menu.")

# --- Global "Start New Customer Order" Button (always visible if an order is active) ---
if not st.session_state.show_bill and st.session_state.wants_to_order != False and (st.session_state.customer_name or st.session_state.current_order):
    st.markdown("---")
    if st.button("Start New Customer Order", key="start_new_customer_global"):
        st.session_state.customer_name = ""
        st.session_state.customer_phone = ""
        st.session_state.current_order = {}
        st.session_state.show_bill = False
        st.session_state.last_bill_details = None
        st.session_state.wants_to_order = False
        st.rerun()

st.markdown("---")
st.markdown("🙏 Thank you for stopping by. See you again!")