# ior_app.py

import streamlit as st

# ----- Diccionario de tecnologías IOR -----

ior_techs = {
    "Inyección de CO₂": {
        "tipo": "Gas",
        "descripcion": "Se inyecta CO₂ en el yacimiento para reducir la viscosidad del crudo y mejorar su movilidad.",
        "implementacion": ["EE. UU. (Permian Basin)", "Canadá", "Emiratos Árabes"]
    },
    "Inyección de Vapor (Steamflooding)": {
        "tipo": "Térmica",
        "descripcion": "Se inyecta vapor para calentar el crudo y hacerlo más fluido, facilitando su extracción.",
        "implementacion": ["California", "Venezuela", "Canadá"]
    },
    "Combustión In Situ (ISC)": {
        "tipo": "Térmica",
        "descripcion": "Se quema una parte del crudo dentro del yacimiento para generar calor y reducir viscosidad.",
        "implementacion": ["India", "Rusia", "Venezuela"]
    },
    "Inyección de Polímeros": {
        "tipo": "Química",
        "descripcion": "Se agregan polímeros al agua inyectada para aumentar su viscosidad y mejorar el barrido del petróleo.",
        "implementacion": ["China", "Canadá", "Argentina"]
    },
    "ASP (Alcalino-Surfactante-Polímero)": {
        "tipo": "Química",
        "descripcion": "Combinación de agentes químicos para reducir la tensión interfacial y mejorar la movilidad del crudo.",
        "implementacion": ["China", "India", "EE. UU."]
    },
    "Microbiana (MEOR)": {
        "tipo": "Biológica",
        "descripcion": "Uso de microorganismos que generan gases o biosurfactantes para mejorar la recuperación.",
        "implementacion": ["India", "Rusia", "Proyectos piloto"]
    },
    "Nanotecnología (emergente)": {
        "tipo": "Avanzada",
        "descripcion": "Aplicación de nanopartículas para alterar propiedades del crudo o del medio poroso.",
        "implementacion": ["EE. UU.", "Emiratos Árabes", "Fase piloto"]
    },
}

# ----- Streamlit App -----

st.set_page_config(page_title="Selector de Tecnología IOR", layout="centered")

st.title("🔍 Selector de Tecnología IOR")
st.markdown("Selecciona una tecnología de recuperación mejorada de petróleo para obtener más información.")

# Menú desplegable
tecnologia_seleccionada = st.selectbox("Tecnología IOR:", list(ior_techs.keys()))

# Mostrar información
if tecnologia_seleccionada:
    data = ior_techs[tecnologia_seleccionada]
    st.subheader(f"📌 {tecnologia_seleccionada}")
    st.markdown(f"**Tipo:** {data['tipo']}")
    st.markdown(f"**Descripción:** {data['descripcion']}")
    st.markdown(f"**Implementación mundial:**")
    st.write("- " + "\n- ".join(data["implementacion"]))
