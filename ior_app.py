# streamlit_waterflooding_exergy.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- Constants ---
X_trat = 5  # kW/m³
X_Oil_Chem = 45.63e6  # J/kg
g = 9.81  # m/s²
bbl_to_m3 = 0.158987
psi_to_Pa = 6894.76

# --- App Config ---
st.set_page_config(page_title="Water Flooding Exergy Analysis", layout="centered")
st.title("💧 Water Flooding – Exergy Evaluation Tool")

# --- Static Parameters Section ---
st.header("🔧 Static Parameters")
with st.form("static_params"):
    rho_O = st.number_input("Oil density (kg/m³)", 800.0, 1100.0, 900.0)
    rho_W = st.number_input("Water density (kg/m³)", 1000.0, 1500.0, 1050.0)
    eff_pump = st.slider("Injection pump efficiency (%)", 75, 85, 80) / 100
    eff_valv = st.slider("Control valve efficiency (%)", 75, 100, 90) / 100
    H = st.number_input("Lift system height (m)", 100.0, 10000.0, 1500.0)
    ALS = st.slider("ALS efficiency (%)", 75, 90, 85) / 100
    n_valves = st.slider("Number of control valves", 1, 15, 5)
    CO2_factor = st.number_input("CO₂ emission factor (kg CO₂/kWh)", value=0.5)
    energy_cost = st.number_input("Energy cost (USD/kWh)", value=0.1)
    submitted = st.form_submit_button("Confirm Parameters")

# --- Data Input Mode ---
st.header("📥 Data Input")
input_mode = st.radio("Select input method:", ["Upload Excel file", "Manual entry"])

# --- Load or Enter Data ---
if input_mode == "Upload Excel file":
    file = st.file_uploader("Upload your Excel file with well data", type=["xlsx"])
    
    st.markdown("""
    **📌 Required columns in Excel file:**
    - `Qinj_B`: Injection rate (bbl/day)
    - `qoil_B`: Oil production (bbl/day)
    - `WHP_psi`: Wellhead pressure (psi)
    - `WOR`: Water-oil ratio (0 to 1)
    - `date`: Date of measurement
    """)

    if file is not None:
        df = pd.read_excel(file)

        # Rename column if legacy name is present
        if "Fecha_poly" in df.columns:
            df.rename(columns={"Fecha_poly": "date"}, inplace=True)

        df["Qinj_m3"] = df["Qinj_B"] * bbl_to_m3
        df["qoil_m3"] = df["qoil_B"] * bbl_to_m3
        df["ΔP_Pa"] = df["WHP_psi"] * psi_to_Pa

elif input_mode == "Manual entry":
    st.info("Enter values for each well below.")
    num_wells = st.number_input("Number of wells to evaluate", min_value=1, max_value=20, value=3)
    well_data = []

    for i in range(int(num_wells)):
        with st.expander(f"Well {i+1}"):
            date = st.date_input(f"Date for well {i+1}")
            Qinj_B = st.number_input(f"Injection rate (bbl/d) - Well {i+1}", value=500.0)
            qoil_B = st.number_input(f"Oil production (bbl/d) - Well {i+1}", value=100.0)
            WHP_psi = st.number_input(f"Wellhead Pressure (psi) - Well {i+1}", value=1000.0)
            WOR = st.number_input(f"Water-Oil Ratio (0–1) - Well {i+1}", min_value=0.0, max_value=1.0, value=0.5)
            well_data.append({"date": date, "Qinj_B": Qinj_B, "qoil_B": qoil_B, "WHP_psi": WHP_psi, "WOR": WOR})

    if well_data:
        df = pd.DataFrame(well_data)
        df["Qinj_m3"] = df["Qinj_B"] * bbl_to_m3
        df["qoil_m3"] = df["qoil_B"] * bbl_to_m3
        df["ΔP_Pa"] = df["WHP_psi"] * psi_to_Pa

# --- Exergy Calculation ---
if 'df' in locals() and not df.empty:
    df["X_W_Prod_J"] = 0.0
    df["X_Iny_J"] = 0.0
    df["X_RFV_J"] = 0.0
    df["X_ALS_J"] = 0.0
    df["X_Oil_Total_J"] = 0.0
    df["X_RF"] = 0.0

    for i, row in df.iterrows():
        X_W_Prod = row["Qinj_m3"] * X_trat * 3600 * 1000
        X_Iny = row["Qinj_m3"] * row["ΔP_Pa"] / eff_pump

        X_RFV = sum(row["Qinj_m3"] * row["ΔP_Pa"] / eff_valv for _ in range(n_valves)) / eff_pump

        rho_mix = row["WOR"] * rho_W + (1 - row["WOR"]) * rho_O
        V_liq = row["qoil_m3"] * (1 + row["WOR"])
        X_ALS = V_liq * rho_mix * g * H / ALS

        m_oil = row["qoil_m3"] * rho_O
        X_Oil_Total = X_Oil_Chem * m_oil

        total_input_exergy = X_W_Prod + X_Iny + X_RFV + X_ALS
        X_RF = (X_Oil_Total - total_input_exergy) / X_Oil_Total if X_Oil_Total != 0 else 0

        df.loc[i, "X_W_Prod_J"] = X_W_Prod
        df.loc[i, "X_Iny_J"] = X_Iny
        df.loc[i, "X_RFV_J"] = X_RFV
        df.loc[i, "X_ALS_J"] = X_ALS
        df.loc[i, "X_Oil_Total_J"] = X_Oil_Total
        df.loc[i, "X_RF"] = X_RF

    # CO₂ and energy metrics
    df["Input_Exergies_J"] = df["X_W_Prod_J"] + df["X_Iny_J"] + df["X_RFV_J"] + df["X_ALS_J"]
    df["Input_Exergies_kWh"] = df["Input_Exergies_J"] * 2.77778e-7
    df["CO2_Emissions_tons"] = df["Input_Exergies_kWh"] * CO2_factor / 1000
    df["Energy_Cost_kUSD"] = df["Input_Exergies_kWh"] * energy_cost / 1000
    df["Useful_Oil_Exergy_GJ"] = (df["X_Oil_Total_J"] * df["X_RF"]) / 1e9

    # --- Plotting Function ---
    def plot_trace(x, y, title, yaxis_title, color):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=color)))
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=yaxis_title,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(
                showgrid=True, zeroline=True, zerolinecolor="white", linecolor='white', tickfont=dict(color='white'),
            ),
            yaxis=dict(
                showgrid=True, zeroline=True, zerolinecolor="white", linecolor='white', tickfont=dict(color='white'),
            ),
            margin=dict(l=30, r=30, t=40, b=30),
            height=400,
        )
        return fig

    # --- Display Plots in 2x2 Layout ---
    st.header("📊 Results Overview")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_trace(df["date"], df["CO2_Emissions_tons"], "CO₂ Emissions Over Time", "CO₂ (tons)", "crimson"), use_container_width=True)
    with col2:
        st.plotly_chart(plot_trace(df["date"], df["Energy_Cost_kUSD"], "Energy Cost Over Time", "Cost (kUSD)", "navy"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(plot_trace(df["date"], df["X_RF"], "Exergetic Efficiency (X_RF)", "X_RF", "darkgreen"), use_container_width=True)
    with col4:
        st.plotly_chart(plot_trace(df["date"], df["Useful_Oil_Exergy_GJ"], "Useful Oil Exergy Over Time", "Exergy (GJ)", "darkorange"), use_container_width=True)
