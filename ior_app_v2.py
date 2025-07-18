import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- Page Setup ---
st.set_page_config(page_title="IOR Exergy Analysis", layout="wide")
st.title("IOR Technology Selector and Exergy Evaluation")

# --- Sidebar: Technology Selection ---
technology = st.sidebar.selectbox(
    "Select IOR Technology:",
    ("Waterflooding", "Polymer Injection", "CO2 Injection (coming soon)")
)

# --- Sidebar: File Upload or Manual Entry ---
data_input_method = st.sidebar.radio("How would you like to provide data?", ("Upload Excel", "Manual Entry"))

# --- Required Columns Info ---
st.markdown("""
### 📌 Required columns in Excel file:
- `Qinj_B`: Injection rate (bbl/day)
- `qoil_B`: Oil production (bbl/day)
- `WHP_psi`: Wellhead pressure (psi)
- `WOR`: Water-oil ratio (fraction)
- `C`: Polymer concentration (only for Polymer)
- `date`: Date (time series)
""")

# --- Upload Excel File ---
if data_input_method == "Upload Excel":
    uploaded_file = st.file_uploader("Upload your Excel file", type=[".xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
else:
    st.warning("Manual input not yet implemented. Please upload an Excel file.")
    st.stop()

# --- Constants and Conversion Factors ---
bbl_to_m3 = 0.158987
psi_to_Pa = 6894.76
g = 9.81  # m/s²
X_trat = 5  # kW/m³
X_Oil_Chem = 45.63e6  # J/kg
X_man = 123.6e6  # J/kg
X_shipping = 188  # J/(kg·km)

# --- User Parameters ---
st.sidebar.subheader("Global Parameters")
rho_O = st.sidebar.number_input("Oil density (kg/m³)", 800, 1100, 900)
rho_W = st.sidebar.number_input("Water density (kg/m³)", 1000, 1500, 1050)
eff_pump = st.sidebar.slider("Injection pump efficiency (%)", 70, 100, 80) / 100
eff_poly = st.sidebar.slider("Polymer efficiency (%)", 1, 100, 90) / 100 if technology == "Polymer Injection" else 1.0
eff_pui = st.sidebar.slider("Preparation unit efficiency (%)", 70, 100, 85) / 100
d_shipping = st.sidebar.number_input("Polymer transport distance (km)", 1000, 20000, 5000)
H = st.sidebar.number_input("Lift system height (m)", 100, 10000, 1500)
ALS = st.sidebar.slider("ALS efficiency (%)", 70, 100, 85) / 100
n_valves = st.sidebar.slider("Number of valves", 1, 15, 5)
CO2_factor = st.sidebar.number_input("CO₂ emission factor (kg/kWh)", 0.1, 2.0, 0.5)
energy_cost = st.sidebar.number_input("Energy cost (USD/kWh)", 0.01, 1.0, 0.1)

# --- Pre-processing ---
df["Qinj_m3"] = df["Qinj_B"] * bbl_to_m3
df["qoil_m3"] = df["qoil_B"] * bbl_to_m3
df["ΔP_Pa"] = df["WHP_psi"] * psi_to_Pa

# --- Initialize Output Columns ---
df["X_mix_J"] = 0.0
df["X_W_Prod_J"] = 0.0
df["X_Iny_J"] = 0.0
df["X_RFV_J"] = 0.0
df["X_ALS_J"] = 0.0
df["X_Oil_Total_J"] = 0.0
df["X_RF"] = 0.0

# --- Exergy Calculations ---
for i, row in df.iterrows():
    V_mix = row["Qinj_m3"]
    
    # Polymer specific term (X_mix)
    if technology == "Polymer Injection":
        X_mix = (V_mix * row["C"] * (X_man + X_shipping * d_shipping)) / eff_pui
    else:
        X_mix = 0

    X_W_Prod = row["Qinj_m3"] * X_trat * 3600 * 1000  # kWh to J
    X_Iny = row["Qinj_m3"] * row["ΔP_Pa"] / (eff_pump * eff_poly)

    X_RFV = sum([row["Qinj_m3"] * row["ΔP_Pa"] / eff_poly for _ in range(n_valves)]) / eff_pump

    rho_mix = row["WOR"] * rho_W + (1 - row["WOR"]) * rho_O
    V_liq = row["qoil_m3"] * (1 + row["WOR"])
    X_ALS = V_liq * rho_mix * g * H / ALS

    m_oil = row["qoil_m3"] * rho_O
    X_Oil_Total = X_Oil_Chem * m_oil

    total_input_exergy = X_mix + X_W_Prod + X_Iny + X_RFV + X_ALS
    X_RF = (X_Oil_Total - total_input_exergy) / X_Oil_Total if X_Oil_Total != 0 else 0

    # Store results
    df.loc[i, [
        "X_mix_J", "X_W_Prod_J", "X_Iny_J", "X_RFV_J", "X_ALS_J", "X_Oil_Total_J", "X_RF"
    ]] = [X_mix, X_W_Prod, X_Iny, X_RFV, X_ALS, X_Oil_Total, X_RF]

# --- Post-processing ---
df["Input_Exergies_J"] = df[["X_mix_J", "X_W_Prod_J", "X_Iny_J", "X_RFV_J", "X_ALS_J"]].sum(axis=1)
df["Input_Exergies_kWh"] = df["Input_Exergies_J"] * 2.77778e-7
df["CO2_Emissions_tons"] = df["Input_Exergies_kWh"] * CO2_factor / 1000
df["Energy_Cost_kUSD"] = df["Input_Exergies_kWh"] * energy_cost / 1000
df["Useful_Oil_Exergy_GJ"] = (df["X_Oil_Total_J"] * df["X_RF"]) / 1e9

# --- Plot Layout ---
fig = make_subplots(rows=2, cols=2, subplot_titles=(
    "CO₂ Emissions Over Time", "Energy Cost Over Time",
    "Exergetic Efficiency (X_RF)", "Useful Oil Exergy Over Time"
))

fig.add_trace(go.Scatter(x=df["date"], y=df["CO2_Emissions_tons"], mode="lines+markers", name="CO2 Emissions", line=dict(color="crimson")), row=1, col=1)
fig.add_trace(go.Scatter(x=df["date"], y=df["Energy_Cost_kUSD"], mode="lines+markers", name="Energy Cost", line=dict(color="navy")), row=1, col=2)
fig.add_trace(go.Scatter(x=df["date"], y=df["X_RF"], mode="lines+markers", name="X_RF", line=dict(color="darkgreen")), row=2, col=1)
fig.add_trace(go.Scatter(x=df["date"], y=df["Useful_Oil_Exergy_GJ"], mode="lines+markers", name="Useful Exergy", line=dict(color="darkorange")), row=2, col=2)

fig.update_layout(
    height=800,
    showlegend=False,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white'),
    xaxis=dict(linecolor='white', tickfont=dict(color='white')),
    yaxis=dict(linecolor='white', tickfont=dict(color='white')),
)

st.plotly_chart(fig, use_container_width=True)

# --- Final ---
st.success("Calculation complete for: " + technology)
st.dataframe(df[["date", "X_RF", "CO2_Emissions_tons", "Energy_Cost_kUSD", "Useful_Oil_Exergy_GJ"]])
