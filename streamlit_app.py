import streamlit as st
import json
from datetime import datetime
import os

# Function to load menu
def load_menu(file_name):
    try:
        with open(file_name, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ '{file_name}' not found.")
        st.stop()
    except json.JSONDecodeError:
        st.error(f"❌ Failed to read '{file_name}'. Invalid format.")
        st.stop()

# Time-based menu setup
day_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
day_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
evening_start = datetime.strptime("17:00:00", "%H:%M:%S").time()
evening_end = datetime.strptime("22:00:00", "%H:%M:%S").time()

now = datetime.now()
current_time = now.time()

if day_start <= current_time <= day_end:
    session = "Day"
    file_name = "day.json"
elif evening_start <= current_time <= evening_end:
    session = "Evening"
    file_name = "evening.json"
else:
    st.error("❌ Sorry! Cafe is closed.\n🕒 Working Hours: 10AM–3PM and 5PM–10PM")
    st.stop()

menu = load_menu(file_name)

# Load customer data
if os.path.exists("customer_data.json"):
    try:
        with open("customer_data.json", "r") as f:
            customer_data = json.load(f)
    except json.JSONDecodeError:
        customer_data = {}
else:
    customer_data = {}

# Live time display
st.markdown(
    f"""
    <h2 style='text-align:center;'>Welcome to Dill-Khus Cafe ☕</h2>
    <p style='text-align:center;'>🕒 Current Time: <span id="time">{now.strftime("%H:%M:%S")}</span></p>
    <p style='text-align:center;'>🍴 Session: <b>{session}</b></p>
    <script>
    const timeTag = document.getElementById("time");
    setInterval(() => {{
        const d = new Date();
        timeTag.innerText = d.toLocaleTimeString();
    }}, 1000);
    </script>
    """,
    unsafe_allow_html=True
)

# Collect customer details
with st.form("customer_form"):
    name = st.text_input("👤 Enter your name:").strip().capitalize()
    phone = st.text_input("📞 Enter your phone number:").strip()
    submit = st.form_submit_button("Continue")

if submit:
    if not name or not phone:
        st.warning("Please enter both name and phone number.")
        st.stop()

    st.session_state.customer_name = name
    st.session_state.customer_phone = phone
    customer_key = f"{name}_{phone}"

    if customer_key in customer_data:
        last_day = customer_data[customer_key]["day"]
        st.success(f"👋 Welcome back, {name}! Hope you enjoyed your {last_day.lower()} visit!")
    else:
        st.success(f"👋 Hello {name}, nice to meet you!")

    # Store customer_key for future use
    st.session_state.customer_key = customer_key
    st.session_state.user_items = []
    st.session_state.user_price = []

# Display menu
if "customer_key" in st.session_state:
    st.header("📋 Menu")
    for category, items in menu.items():
        st.subheader(f"🍽️ {category}")
        for item, price in items.items():
            if st.button(f"Add {item} (₹{price})"):
                st.session_state.user_items.append(item)
                st.session_state.user_price.append(price)
                st.success(f"✅ {item} added!")

# Show order summary
if st.session_state.get("user_items"):
    st.subheader("🛒 Your Order")
    for i, item in enumerate(st.session_state.user_items):
        st.markdown(f"{i+1}. {item} - ₹{st.session_state.user_price[i]}")

    subtotal = sum(st.session_state.user_price)
    gst = round(subtotal * 0.18, 2)
    total = round(subtotal + gst, 2)

    st.markdown("---")
    st.markdown(f"**Subtotal:** ₹{subtotal}")
    st.markdown(f"**GST (18%):** ₹{gst}")
    st.markdown(f"💵 **Total Payable:** ₹{total}/-")
    st.markdown("---")

    if st.button("💾 Confirm and Save Order"):
        bill_time = datetime.now().strftime("%H:%M:%S")
        today_date = datetime.now().strftime("%d/%m/%Y")
        today_day = datetime.now().strftime("%A")

        customer_data[st.session_state.customer_key] = {
            "phone_number": st.session_state.customer_phone,
            "Visiting_time": session,
            "date": today_date,
            "day": today_day,
            "bill_time": bill_time,
            "user_items": st.session_state.user_items,
            "user_price": st.session_state.user_price,
            "total": total
        }

        with open("customer_data.json", "w") as f:
            json.dump(customer_data, f, indent=4)

        st.success("✅ Order saved. Thank you for visiting Dill-Khus Cafe!")

# Optional: Exit message
st.markdown("---")
st.markdown("<h4 style='text-align:center;'>🙏 Thank you! Come again! 🙏</h4>", unsafe_allow_html=True)
