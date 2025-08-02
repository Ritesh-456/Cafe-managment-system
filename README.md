# ☕ Bhakti's Cafe Management System

This is a complete **Streamlit-based Café Management App** that allows users to:
- Place orders from a time-sensitive menu (Day / Evening)
- View itemized billing with dynamic discounts
- Generate downloadable **PDF bills**
- Save customer order history (locally in `customer_data.json`)

> **Live Demo:** [Bhakti's Cafe on Streamlit](https://bhaktis-cafe.streamlit.app/)

---

## 📂 Project Structurec
```bash
📁 Bhakti_Cafe/ │ ├── customer_data.json        # Stores customer order history ├── config.json               # Defines day & evening café hours ├── day.json                  # Menu items for the Day session ├── evening.json              # Menu items for the Evening session ├── app.py                    # Main Streamlit application └── requirements.txt          # Dependencies
```
---

## ⚙️ Features

### ✅ Session-based Menu
- Uses `Asia/Kolkata` timezone to determine the current session.
- Loads `day.json` or `evening.json` menu dynamically.

### 🧾 Bill Generation
- Discounts based on quantity:
  - 3% for >5 items
  - 6% for >8 items
  - 9% for >11 items
- 18% GST applied to final subtotal
- PDF bill generated using **ReportLab** (downloadable via Streamlit)

### 🧑‍💼 Customer Data Handling
- Order details saved in `customer_data.json`
- Remembers returning customers
- View or clear current order

### 📉 Visual Dashboard
- Current **Date**, **Time**, and **Day**
- Streamlit metrics display real-time values
- Automatically refreshes using `st.rerun()` to show updated data

---

## 📤 Sample Output

### 🧾 PDF Bill (Auto-generated)
- Header with logo and slogan
- Itemized table with quantity, rate, total
- Summary: subtotal, discount, GST, grand total
- Contact information and store link

---

## 📅 Configuration Guide

Edit `config.json` to set café opening/closing times:

```json
{
  "day_start": "09:00:00",
  "day_end": "13:00:00",
  "evening_start": "16:00:00",
  "evening_end": "21:30:00"
}
```
---

##📝 Local Storage Notice

NOTE:
Your data are temporary. If the system sleeps (Streamlit Cloud timeout), it will clear all your details.

> 🔁 To persist your data permanently, fork the project and run it locally.

---


## 🚀 Getting Started

### 🔧 Requirements

Install Python libraries:
```bash

pip install streamlit reportlab pytz
```

▶️ Run the App
```bash

streamlit run app.py
```
---