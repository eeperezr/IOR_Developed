import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Title
st.set_page_config(page_title="IOR Exergy Evaluation", layout="wide")
st.title("🌍 Enhanced Oil Recovery (EOR) Exergy Assessment Tool")

# --- Technology selection ---
tech = st.selectbox("Select EOR Technology", [
    "Waterflooding",
    "Polymer Injection",
    "CO₂ Injection (Coming Soon)",
    "Steam Injection / CSS (Coming Soon)",
    "ASP (Coming Soon)"
])

# --- Upload data or manual entry ---
input_mode = st.radio("Input Mode", ["Upload Excel", "Manual Entry"])

required_columns = ["Qinj_B", "qoil_B", "WHP_psi", "WOR", "C", "date"]
st.markdown(f"📌 Required columns in Excel: `{', '.join(required_columns)}`")

if input_mode == "Upload Excel":
    file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        df["date"] = pd.to_datetime(df["date"])
    else:
        st.stop()
else:
    st.warning("Manual entry mode not implemented yet. Please upload an Excel file.")
    st.stop()

# --- Constant parameters ---
st.sidebar.title("🔧 Global Constants")
rho_O = st.sidebar.number_input("Oil density (kg/m³)", 800.0, 1100.0, 900.0)
rho_W = st.sidebar.number_input("Water density (kg/m³)", 1000.0, 1500.0, 1050.0)
eff_pump = st.sidebar.slider("Injection pump efficiency (%)", 50, 100, 80) / 100
eff_poly = st.sidebar.slider("Polymer efficiency (%)", 0, 100, 90) / 100
eff_pui = st.sidebar.slider("Polymer preparation efficiency (%)", 50, 100, 85) / 100
H = st.sidebar.number_input("Lift height (m)", 100.0, 10000.0, 1500.0)
ALS = st.sidebar.slider("ALS efficiency (%)", 50, 100, 85) / 100
d_shipping = st.sidebar.number_input("Polymer shipping distance (km)", 0, 20000, 5000)
n_valves = st.sidebar.slider("Valves installed per well", 1, 15, 5)
CO2_factor = st.sidebar.number_input("CO₂ emission factor (kg CO₂/kWh)", 0.0, 2.0, 0.4)
energy_cost = st.sidebar.number_input("Energy cost (USD/kWh)", 0.0, 1.0, 0.1)

# --- Constants ---
X_trat = 5  # kWh/m³
X_Oil_Chem = 45.63e6  # J/kg
X_man = 123.6e6  # J/kg
X_shipping = 188  # J/(kg·km)
g = 9.81
bbl_to_m3 = 0.158987
psi_to_Pa = 6894.76

# --- Convert units ---
df["Qinj_m3"] = df["Qinj_B"] * bbl_to_m3
df["qoil_m3"] = df["qoil_B"] * bbl_to_m3
df["ΔP_Pa"] = df["WHP_psi"] * psi_to_Pa

# --- Initialize results ---
df["X_mix_J"] = 0.0
df["X_W_Prod_J"] = 0.0
df["X_Iny_J"] = 0.0
df["X_RFV_J"] = 0.0
df["X_ALS_J"] = 0.0
df["X_Oil_Total_J"] = 0.0
df["X_RF"] = 0.0

# --- Process rows ---
for i, row in df.iterrows():
    V_mix = row["Qinj_m3"]
    WOR = row["WOR"]
    qoil_m3 = row["qoil_m3"]
    pressure = row["ΔP_Pa"]
    C = row["C"]

    # Exergy for polymer mixing
    if tech == "Polymer Injection":
        X_mix = (V_mix * C * (X_man + X_shipping * d_shipping)) / eff_pui
    elif tech == "Waterflooding":
        X_mix = 0
    else:
        X_mix = 0  # Coming soon cases

    X_W_Prod = V_mix * X_trat * 3.6e6  # J
    X_Iny = V_mix * pressure / (eff_pump * (eff_poly if tech == "Polymer Injection" else 1))
    
    X_RFV = 0
    for _ in range(n_valves):
        X_RFV += V_mix * pressure / (eff_poly if tech == "Polymer Injection" else 1)
    X_RFV /= eff_pump

    rho_mix = WOR * rho_W + (1 - WOR) * rho_O
    V_liq = qoil_m3 * (1 + WOR)
    X_ALS = V_liq * rho_mix * g * H / ALS

    m_oil = qoil_m3 * rho_O
    X_Oil_Total = m_oil * X_Oil_Chem

    total_input_exergy = X_mix + X_W_Prod + X_Iny + X_RFV + X_ALS
    X_RF = (X_Oil_Total - total_input_exergy) / X_Oil_Total if X_Oil_Total != 0 else 0

    # Save
    df.loc[i, "X_mix_J"] = X_mix
    df.loc[i, "X_W_Prod_J"] = X_W_Prod
    df.loc[i, "X_Iny_J"] = X_Iny
    df.loc[i, "X_RFV_J"] = X_RFV
    df.loc[i, "X_ALS_J"] = X_ALS
    df.loc[i, "X_Oil_Total_J"] = X_Oil_Total
    df.loc[i, "X_RF"] = X_RF

# --- Final results ---
df["Input_Exergies_J"] = df[["X_mix_J", "X_W_Prod_J", "X_Iny_J", "X_RFV_J", "X_ALS_J"]].sum(axis=1)
df["Input_Exergies_kWh"] = df["Input_Exergies_J"] * 2.77778e-7
df["CO2_Emissions_tons"] = df["Input_Exergies_kWh"] * CO2_factor / 1000
df["Energy_Cost_kUSD"] = df["Input_Exergies_kWh"] * energy_cost / 1000
df["Useful_Oil_Exergy_GJ"] = (df["X_Oil_Total_J"] * df["X_RF"]) / 1e9

# --- Plotting in 2x2 grid ---
fig = make_subplots(rows=2, cols=2, subplot_titles=(
    "CO₂ Emissions Over Time",
    "Energy Cost Over Time",
    "Exergetic Efficiency (X_RF)",
    "Useful Oil Exergy Over Time"
))

fig.update_layout(
    height=800, width=1200,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white'),
    showlegend=False
)

fig.add_trace(go.Scatter(x=df["date"], y=df["CO2_Emissions_tons"], mode="lines+markers", name="CO₂ Emissions", line=dict(color="crimson")),
              row=1, col=1)

fig.add_trace(go.Scatter(x=df["date"], y=df["Energy_Cost_kUSD"], mode="lines+markers", name="Energy Cost", line=dict(color="navy")),
              row=1, col=2)

fig.add_trace(go.Scatter(x=df["date"], y=df["X_RF"], mode="lines+markers", name="Exergetic Efficiency", line=dict(color="darkgreen")),
              row=2, col=1)

fig.add_trace(go.Scatter(x=df["date"], y=df["Useful_Oil_Exergy_GJ"], mode="lines+markers", name="Useful Exergy", line=dict(color="darkorange")),
              row=2, col=2)

# Axis styling
for axis in fig.layout:
    if isinstance(fig.layout[axis], dict) and "color" in fig.layout[axis]:
        fig.layout[axis]["color"] = "white"

st.plotly_chart(fig, use_container_width=True)

# --- Data Summary ---
st.subheader("📋 Summary Table")
st.dataframe(df[["date", "CO2_Emissions_tons", "Energy_Cost_kUSD", "X_RF", "Useful_Oil_Exergy_GJ"]].round(3))
