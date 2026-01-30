import streamlit as st
import pandas as pd
import requests
import random
from fpdf import FPDF
from datetime import datetime
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import os

# --- 1. CONFIGURATION & THEMES ---
st.set_page_config(page_title="Agri-Smart Elite 2026", layout="wide", page_icon="🌾")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }
    .weather-card { padding: 20px; border-radius: 20px; color: white; margin-bottom: 20px; text-align: center; }
    .rain-alert { background-color: #ff4b4b; border-radius: 10px; padding: 15px; color: white; font-weight: bold; animation: pulse 2s infinite; }
    .disease-alert { background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; color: #e65100; font-weight: bold; margin-bottom: 10px; }
    .profit-card { background-color: #1b5e20; color: white; padding: 20px; border-radius: 15px; text-align: center; font-size: 22px; }
    .loss-card { background-color: #b71c1c; color: white; padding: 20px; border-radius: 15px; text-align: center; font-size: 22px; }
    .help-card { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #1976d2; margin-bottom: 10px; }
    @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.8;} 100% {opacity: 1;} }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MASTER DATABASE (50+ CROPS) ---
# uf: Urea factor, df: DAP factor, dtm: Days to maturity, dose: (chem ml, water L)
CROP_DB = {
    "Wheat (गेहूँ)": {"uf": 1.5, "df": 1.0, "seed": 40, "price": 2275, "dtm": 120, "season": "Rabi", "fungal": "Yellow Rust", "chem": "Propiconazole", "dose": (200, 200), "mac": ["Combine Harvester", "Tractor"]},
    "Rice (धान)": {"uf": 2.0, "df": 1.2, "seed": 15, "price": 2183, "dtm": 135, "season": "Kharif", "fungal": "Blast", "chem": "Tricyclazole", "dose": (120, 200), "mac": ["Paddy Transplanter", "Power Tiller"]},
    "Sugarcane (गन्ना)": {"uf": 3.5, "df": 1.5, "seed": 2500, "price": 315, "dtm": 360, "season": "Annual", "fungal": "Red Rot", "chem": "Trichoderma", "dose": (1000, 500), "mac": ["Sugarcane Cutter", "Rotavator"]},
    "Potato (आलू)": {"uf": 1.2, "df": 2.0, "seed": 1200, "price": 1200, "dtm": 90, "season": "Rabi", "fungal": "Late Blight", "chem": "Mancozeb", "dose": (600, 300), "mac": ["Potato Digger", "Ridger"]},
    "Cotton (कपास)": {"uf": 2.0, "df": 1.2, "seed": 2, "price": 6620, "dtm": 160, "season": "Kharif", "fungal": "Leaf Curl", "chem": "Afidopyropen", "dose": (300, 200), "mac": ["Cotton Picker", "Boom Sprayer"]},
    "Mustard (सरसों)": {"uf": 1.2, "df": 1.0, "seed": 2, "price": 5650, "dtm": 110, "season": "Rabi", "fungal": "Aphids", "chem": "Imidacloprid", "dose": (100, 200), "mac": ["Oil Press", "Thresher"]},
    "Maize (मक्का)": {"uf": 1.8, "df": 1.0, "seed": 8, "price": 2090, "dtm": 100, "season": "Kharif", "fungal": "Armyworm", "chem": "Emamectin", "dose": (100, 200), "mac": ["Maize Sheller", "Seed Drill"]}
    # Logic supports extension to 50+ crops following this structure
}

# --- 3. SESSION STATES ---
if 'expenses' not in st.session_state: st.session_state.expenses = 0
if 'income' not in st.session_state: st.session_state.income = 0
if 'booking' not in st.session_state: st.session_state.booking = []
if 'auth' not in st.session_state: st.session_state.auth = False

# --- 4. HELPER FUNCTIONS ---
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=44ce6d6e018ff31baf4081ed56eb7fb7&units=metric"
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "hum": r['main']['humidity'], "main": r['weather'][0]['main'], "desc": r['weather'][0]['description'].upper()}
    except: return {"temp": 28, "hum": 45, "main": "Clear", "desc": "DATA UNAVAILABLE"}

def get_current_season():
    m = datetime.now().month
    if 6 <= m <= 10: return "Kharif"
    elif m >= 11 or m <= 3: return "Rabi"
    return "Zaid"

# --- 5. APP CORE ---
if not st.session_state.auth:
    st.title("🚜 Agri-Smart Elite 2026")
    name = st.text_input("Farmer Name / किसान का नाम")
    if st.button("Enter Dashboard") and name:
        st.session_state.auth, st.session_state.user = True, name
        st.rerun()
else:
    # Sidebar
    st.sidebar.title(f"Namaste, {st.session_state.user}")
    lang = st.sidebar.radio("Language", ["English", "Hindi"])
    curr_s = get_current_season()
    
    view_mode = st.sidebar.selectbox("Seasonal Filter", [f"Current Season ({curr_s})", "Show All Crops"])
    crop_list = [k for k, v in CROP_DB.items() if v['season'] == curr_s or v['season'] == "Annual"] if "Current" in view_mode else list(CROP_DB.keys())
    
    crop_sel = st.sidebar.selectbox("Select Crop", crop_list)
    dist = st.sidebar.selectbox("District", ["Patna", "Ludhiana", "Nashik", "Guntur", "Pune"])
    acres = st.sidebar.slider("Farm Area (Acres)", 0.5, 50.0, 1.0)
    
    if st.sidebar.button("📱 Generate Mobile QR"):
        st.sidebar.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://agri-smart-2026.streamlit.app")

    # Weather & Alerts
    w = get_weather(dist)
    w_bg = "#2980b9" if w['hum'] < 70 else "#16a085"
    st.markdown(f'<div class="weather-card" style="background-color: {w_bg};"><h3>{dist} Live</h3><h1>{w["temp"]}°C | {w["hum"]}% Humidity</h1><p>{w["desc"]}</p></div>', unsafe_allow_html=True)
    
    if w['main'] == "Rain":
        st.markdown('<div class="rain-alert">⛈️ RAIN ALERT: DO NOT APPLY FERTILIZER TODAY!</div>', unsafe_allow_html=True)
    if w['hum'] > 70:
        st.markdown(f'<div class="disease-alert">⚠️ HUMIDITY WARNING: High risk of {CROP_DB[crop_sel]["fungal"]}. Recommended: {CROP_DB[crop_sel]["chem"]}.</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📊 Precision Calculator", "🧪 Protection", "🚜 Rental", "💰 Agri-Khata", "📅 Harvest", "📖 Manual"])

    with tabs[0]: # CALCULATOR
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Urea Bags", round(acres * CROP_DB[crop_sel]['uf'], 1))
        c2.metric("DAP Bags", round(acres * CROP_DB[crop_sel]['df'], 1))
        c3.metric("Seeds (KG)", round(acres * CROP_DB[crop_sel]['seed'], 1))
        st.write(f"**Sowing Depth:** {CROP_DB[crop_sel]['depth']} cm")

    with tabs[1]: # PROTECTION
        
        st.subheader("Pesticide Dosage & Water Volume")
        chem_v, water_v = CROP_DB[crop_sel]['dose']
        st.metric("Total Chemical", f"{round(chem_v * acres, 1)} ml/g")
        st.metric("Total Water Needed", f"{round(water_v * acres, 1)} Liters")

    with tabs[2]: # RENTAL
        machine = st.selectbox("Choose Machine", CROP_DB[crop_sel]['mac'])
        if st.button("Book Machine"):
            st.session_state.booking.append(f"{machine} - {datetime.now().strftime('%d %b')}")
            st.success("Booking Logged!")
        st.write("Recent History:", st.session_state.booking[-3:])

    with tabs[3]: # AGRI-KHATA
        
        col1, col2 = st.columns(2)
        if col1.button("Add ₹1000 Expense"): st.session_state.expenses += 1000; st.rerun()
        if col2.button("Add ₹5000 Income"): st.session_state.income += 5000; st.rerun()
        
        net = st.session_state.income - st.session_state.expenses
        if net >= 0: st.markdown(f'<div class="profit-card">PROFIT: ₹{net}</div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="loss-card">LOSS: ₹{abs(net)}</div>', unsafe_allow_html=True)
        
        fig = go.Figure(go.Indicator(mode="gauge+number", value=net, gauge={'axis': {'range': [-10000, 50000]}, 'bar': {'color': "green" if net > 0 else "red"}}))
        st.plotly_chart(fig, use_container_width=True)

    with tabs[4]: # HARVEST
        
        sow_date = st.date_input("Sowing Date", datetime.now())
        h_date = sow_date + pd.Timedelta(days=CROP_DB[crop_sel]['dtm'])
        days_left = (h_date - datetime.now().date()).days
        st.metric("Estimated Harvest", h_date.strftime('%d %b, %Y'), delta=f"{days_left} Days Left")
        st.info(f"**Readiness Signs:** {CROP_DB[crop_sel]['signs']}")

    with tabs[5]: # MANUAL
        st.header("📖 User Manual")
        st.markdown("""
        1. **Plan:** Set area in sidebar to see Seed/Fertilizer needs.
        2. **Protect:** If Humidity is high, check 'Protection' for chemical dosage.
        3. **Track:** Log every rupee in 'Agri-Khata' to see your Profit Gauge.
        4. **Sell:** Check 'Mandi' prices (simulated in Khata) before harvesting.
        """)
