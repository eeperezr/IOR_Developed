import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")

st.title("Exergy Analysis for Injection Technologies")

# --- Input mode selection ---
input_mode = st.radio("Select input mode:", ("Upload Excel", "Manual Entry"))

# --- Technology selection ---
technology = st.selectbox(
    "Select injection technology:",
    ["Water Injection", "Polymer Injection", "CO2 Injection (coming soon)", "Other Technology (coming soon)"]
)

# --- Input static variables ---
st.sidebar.header("Constant Parameters")

rho_O = st.sidebar.number_input("Oil density (kg/m³)", min_value=800.0, max_value=1100.0, value=900.0)
rho_W = st.sidebar.number_input("Water density (kg/m³)", min_value=1000.0, max_value=1500.0, value=1050.0)
eff_pump = st.sidebar.number_input("Injection pump efficiency (%)", min_value=75.0, max_value=85.0, value=80.0) / 100

# Additional inputs for Polymer
if technology == "Polymer Injection":
    eff_poly = st.sidebar.number_input("Polymer efficiency (%)", min_value=0.0, max_value=100.0, value=90.0) / 100
    eff_pui = st.sidebar.number_input("Preparation unit efficiency (%)", min_value=75.0, max_value=90.0, value=85.0) / 100
    d_shipping = st.sidebar.number_input("Polymer transport distance (km)", min_value=1000.0, max_value=20000.0, value=5000.0)
else:
    # Defaults to 1 if not polymer
    eff_poly = 1.0
    eff_pui = 1.0
    d_shipping = 0.0

eff_valv = st.sidebar.number_input("Control valve efficiency (%)", min_value=75.0, max_value=100.0, value=90.0) / 100
H = st.sidebar.number_input("Lift system height (m)", min_value=100.0, max_value=10000.0, value=1000.0)
ALS = st.sidebar.number_input("ALS efficiency (%)", min_value=75.0, max_value=90.0, value=80.0) / 100
n_valves = st.sidebar.number_input("Number of valves installed", min_value=1, max_value=15, value=5)
CO2_factor = st.sidebar.number_input("CO2 emission factor (kg CO2 / kWh)", value=0.4)
energy_cost = st.sidebar.number_input("Energy cost (USD / kWh)", value=0.1)

# Constants
X_trat = 5  # kW/m³
X_Oil_Chem = 45.63e6  # J/kg
X_man = 123.6e6  # J/kg (Polymer manufacturing exergy)
X_shipping = 188  # J/(kg·km) (Polymer shipping exergy)
g = 9.81  # m/s²
bbl_to_m3 = 0.158987
psi_to_Pa = 6894.76

# --- Load or manual input data ---

if input_mode == "Upload Excel":
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        if "date" not in df.columns:
            st.error("Your Excel file must contain a 'date' column with dates.")
            st.stop()
        required_cols = ["Qinj_B", "qoil_B", "WHP_psi", "WOR"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns in Excel: {missing_cols}")
            st.stop()
        # If polymer selected, ensure 'C' column exists
        if technology == "Polymer Injection" and "C" not in df.columns:
            st.error("For Polymer Injection, the Excel file must include the 'C' column (polymer concentration).")
            st.stop()

        df["date"] = pd.to_datetime(df["date"])
    else:
        st.stop()

else:
    st.subheader("📝 Manual Data Entry")
    num_rows = st.number_input("Number of records to input", min_value=1, max_value=100, value=5)

    default_data = {
        "Qinj_B": [1000.0] * num_rows,
        "qoil_B": [500.0] * num_rows,
        "WHP_psi": [1500.0] * num_rows,
        "WOR": [1.0] * num_rows,
        "date": pd.date_range(start="2025-01-01", periods=num_rows, freq="M"),
    }

    if technology == "Polymer Injection":
        default_data["C"] = [0.05] * num_rows  # polymer concentration fraction

    df = pd.DataFrame(default_data)

    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    df = edited_df.copy()
    df["date"] = pd.to_datetime(df["date"])

# --- Common unit conversions ---
df["Qinj_m3"] = df["Qinj_B"] * bbl_to_m3
df["qoil_m3"] = df["qoil_B"] * bbl_to_m3
df["ΔP_Pa"] = df["WHP_psi"] * psi_to_Pa

# Initialize columns for results
df["X_mix_J"] = 0.0
df["X_W_Prod_J"] = 0.0
df["X_Iny_J"] = 0.0
df["X_RFV_J"] = 0.0
df["X_ALS_J"] = 0.0
df["X_Oil_Total_J"] = 0.0
df["X_RF"] = 0.0

# --- Calculation depending on technology ---
for i, row in df.iterrows():
    V_mix = row["Qinj_m3"]

    # Water Injection calculations
    if technology == "Water Injection":
        X_mix = 0  # no polymer exergy
        X_W_Prod = V_mix * X_trat * 3600 * 1000  # kWh to J
        X_Iny = V_mix * row["ΔP_Pa"] / eff_pump
        X_RFV = 0
        for _ in range(n_valves):
            X_RFV += V_mix * row["ΔP_Pa"] / eff_valv
        X_RFV /= eff_pump

    # Polymer Injection calculations
    elif technology == "Polymer Injection":
        # Polymer concentration fraction C
        C = row.get("C", 0)
        X_mix = (V_mix * C * (X_man + X_shipping * d_shipping)) / eff_pui
        X_W_Prod = V_mix * X_trat * 3600 * 1000
        X_Iny = V_mix * row["ΔP_Pa"] / (eff_pump * eff_poly)
        X_RFV = 0
        for _ in range(n_valves):
            X_RFV += V_mix * row["ΔP_Pa"] / eff_poly
        X_RFV /= eff_pump

    else:
        # Future tech placeholders
        X_mix = 0
        X_W_Prod = 0
        X_Iny = 0
        X_RFV = 0

    # Artificial lift system exergy (same for all)
    rho_mix = row["WOR"] * rho_W + (1 - row["WOR"]) * rho_O
    V_liq = row["qoil_m3"] * (1 + row["WOR"])
    X_ALS = V_liq * rho_mix * g * H / ALS

    # Oil chemical exergy
    m_oil = row["qoil_m3"] * rho_O
    X_Oil_Total = X_Oil_Chem * m_oil

    total_input_exergy = X_mix + X_W_Prod + X_Iny + X_RFV + X_ALS
    X_RF = (X_Oil_Total - total_input_exergy) / X_Oil_Total if X_Oil_Total != 0 else 0

    # Store results
    df.at[i, "X_mix_J"] = X_mix
    df.at[i, "X_W_Prod_J"] = X_W_Prod
    df.at[i, "X_Iny_J"] = X_Iny
    df.at[i, "X_RFV_J"] = X_RFV
    df.at[i, "X_ALS_J"] = X_ALS
    df.at[i, "X_Oil_Total_J"] = X_Oil_Total
    df.at[i, "X_RF"] = X_RF

# Total input exergy
df["Input_Exergies_J"] = df["X_mix_J"] + df["X_W_Prod_J"] + df["X_Iny_J"] + df["X_RFV_J"] + df["X_ALS_J"]
df["Input_Exergies_kWh"] = df["Input_Exergies_J"] * 2.77778e-7
df["CO2_Emissions_tons"] = df["Input_Exergies_kWh"] * CO2_factor / 1000
df["Energy_Cost_kUSD"] = df["Input_Exergies_kWh"] * energy_cost / 1000
df["Useful_Oil_Exergy_GJ"] = (df["X_Oil_Total_J"] * df["X_RF"]) / 1e9

# --- Plotting ---
def style_layout(fig, title, x_title, y_title):
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        plot_bgcolor="rgba(0,0,0,0)",  # transparent background
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="white", showgrid=False, zeroline=False),
        yaxis=dict(color="white", showgrid=False, zeroline=False),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.1)"),
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(color="white"),
    )

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "CO₂ Emissions Over Time",
        "Energy Cost Over Time",
        "Exergetic Efficiency (X_RF) Over Time",
        "Useful Exergy of Produced Oil Over Time"
    )
)

# Plot 1: CO2 Emissions
fig.add_trace(
    go.Scatter(x=df["date"], y=df["CO2_Emissions_tons"], mode="lines+markers", name="CO2 Emissions (tons)", line=dict(color="crimson")),
    row=1, col=1
)

# Plot 2: Energy Cost
fig.add_trace(
    go.Scatter(x=df["date"], y=df["Energy_Cost_kUSD"], mode="lines+markers", name="Energy Cost (thousand USD)", line=dict(color="navy")),
    row=1, col=2
)

# Plot 3: Exergetic Efficiency
fig.add_trace(
    go.Scatter(x=df["date"], y=df["X_RF"], mode="lines+markers", name="Exergetic Efficiency (X_RF)", line=dict(color="darkgreen")),
    row=2, col=1
)

# Plot 4: Useful Oil Exergy
fig.add_trace(
    go.Scatter(x=df["date"], y=df["Useful_Oil_Exergy_GJ"], mode="lines+markers", name="Useful Oil Exergy (GJ)", line=dict(color="darkorange")),
    row=2, col=2
)

# Apply layout styling to each subplot
for i in range(1, 5):
    fig.layout.annotations[i - 1].font.color = "white"
for axis in ['xaxis1', 'xaxis2', 'xaxis3', 'xaxis4', 'yaxis1', 'yaxis2', 'yaxis3', 'yaxis4']:
    fig['layout'][axis]['color'] = 'white'
    fig['layout'][axis]['showgrid'] = False
    fig['layout'][axis]['zeroline'] = False

fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",  # transparent background
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=700,
    width=900,
    margin=dict(t=70)
)

st.plotly_chart(fig, use_container_width=True)
