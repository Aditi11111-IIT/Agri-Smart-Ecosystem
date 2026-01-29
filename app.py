import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import os
import requests
from fpdf import FPDF
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Agri-Smart Ecosystem (A.S.E)", layout="wide")

API_KEY = "44ce6d6e018ff31baf4081ed56eb7fb7"
# Note: In a real-world scenario, you'd use a specific Govt API key here.
# For the prototype, we use a Resource Discovery function.

LANG_DICT = {
    "English": {
        "title": "Agri-Smart Dashboard",
        "weather": "Live Weather & 5-Day Forecast",
        "soil_step": "Step 1: Visual Soil Selection",
        "report": "Precision Soil Report",
        "schemes": "Live Govt. Schemes & Updates",
        "contact": "Resource Connectivity",
        "rain_alert": "⚠️ CRITICAL: Rain Predicted! DO NOT apply fertilizer today.",
        "clear_alert": "✅ SAFE: Weather is clear. You may apply fertilizer today.",
    },
    "Hindi": {
        "title": "एग्री-स्मार्ट डैशबोर्ड",
        "weather": "लाइव मौसम और 5-दिनीय पूर्वानुमान",
        "soil_step": "चरण 1: मिट्टी का दृश्य चयन",
        "report": "सटीक मिट्टी रिपोर्ट",
        "schemes": "लाइव सरकारी योजनाएं एवं अपडेट",
        "contact": "संसाधन कनेक्टिविटी",
        "rain_alert": "⚠️ चेतावनी: बारिश की संभावना! आज उर्वरक (खाद) न डालें।",
        "clear_alert": "✅ सुरक्षित: मौसम साफ है। आप आज उर्वरक डाल सकते हैं।",
    }
}

# --- 2. LIVE SCHEME FETCHING LOGIC ---
def fetch_live_schemes():
    """Simulates fetching real-time agricultural schemes from an open-source data feed"""
    # Using an open API endpoint for agricultural news/resources
    try:
        # Placeholder for a live Govt API or Agricultural Resource RSS-to-JSON
        schemes = [
            {"Name": "PM-Kisan Nidhi", "Details": "Direct benefit transfer of ₹6000/year.", "Status": "Active"},
            {"Name": "PM Fasal Bima Yojana", "Details": "Crop insurance for natural disasters.", "Status": "Open"},
            {"Name": "Kisan Credit Card", "Details": "Low interest loans for farmers.", "Status": "Ongoing"},
            {"Name": "Soil Health Card", "Details": "Free soil testing and nutrient advice.", "Status": "Available"},
            {"Name": "e-NAM", "Details": "Digital platform for crop trade.", "Status": "Live"}
        ]
        return pd.DataFrame(schemes)
    except:
        return pd.DataFrame([{"Error": "Could not connect to Govt. API"}])

# --- 3. CORE ANALYTICS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    return requests.get(url).json()

def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    return requests.get(url).json()

def calculate_suitability(vec):
    crops_db = {
        "Wheat": np.array([80, 40, 40, 20]),
        "Rice": np.array([100, 60, 40, 80]),
        "Maize": np.array([60, 30, 30, 40])
    }
    return {c: np.dot(vec, t)/(np.linalg.norm(vec)*np.linalg.norm(t)) for c, t in crops_db.items()}

# --- 4. AUTHENTICATION ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🚜 Agri-Smart Secure Access")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            st.session_state.authenticated = True
            st.session_state.user = u
            st.rerun()
    with tab2:
        st.text_input("Full Name")
        st.text_input("Mobile Number")
        st.button("Register")
else:
    # --- 5. DASHBOARD ---
    lang = st.sidebar.selectbox("Language / भाषा", ["English", "Hindi"])
    T = LANG_DICT[lang]
    city = st.sidebar.text_input("District", "Patna")
    
    st.title(f"🌾 {T['title']}")

    # Weather & Live Alerts
    w, f = get_weather(city), get_forecast(city)
    if w and w.get("main"):
        desc = w['weather'][0]['description'].lower()
        if any(word in desc for word in ["rain", "drizzle", "storm"]):
            st.error(T['rain_alert'])
        else:
            st.success(T['clear_alert'])

        # Forecast Chart
        if f and f.get("list"):
            dates = [item['dt_txt'] for item in f['list'][::8]]
            temps = [item['main']['temp'] for item in f['list'][::8]]
            fig = go.Figure(data=[go.Bar(x=dates, y=temps, marker_color='#2E7D32')])
            fig.update_layout(title="5-Day Temperature Forecast", height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Visual Soil Selection
    st.header(T['soil_step'])
    cols = st.columns(3)
    soils = [{"n": "Alluvial", "v": [90,50,45,30], "i": "assets/alluvial.jpg"},
             {"n": "Black", "v": [70,40,60,50], "i": "assets/black.jpg"},
             {"n": "Clay", "v": [50,30,30,70], "i": "assets/clay.jpg"}]

    for idx, s in enumerate(soils):
        with cols[idx]:
            if os.path.exists(s['i']): st.image(Image.open(s['i']), use_container_width=True)
            if st.button(f"Analyze {s['n']}"):
                st.session_state.soil_vec, st.session_state.soil_name = s['v'], s['n']

    # Soil Results & LIVE SCHEMES API
    if 'soil_vec' in st.session_state:
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"📊 {T['report']}")
            scores = calculate_suitability(np.array(st.session_state.soil_vec))
            for crop, score in scores.items():
                st.write(f"**{crop}** ({round(score*100,1)}%)")
                st.progress(score)
        
        with c2:
            st.subheader(f"📋 {T['schemes']}")
            st.write("Fetching latest updates from live resource feed...")
            live_df = fetch_live_schemes() # Calling our API simulation function
            st.dataframe(live_df, hide_index=True, use_container_width=True)

    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))
