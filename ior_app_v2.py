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
st.markdown("Filtra por tipo y/o región de implementación para explorar tecnologías aplicadas a recuperación mejorada de petróleo.")

# Obtener lista única de tipos y regiones
tipos = sorted(set(data["tipo"] for data in ior_techs.values()))
regiones = sorted(set(region for data in ior_techs.values() for region in data["implementacion"]))

# Filtros
tipo_filtro = st.selectbox("📂 Filtrar por tipo de tecnología:", ["Todos"] + tipos)
region_filtro = st.selectbox("🌍 Filtrar por región de implementación:", ["Todas"] + regiones)

# Aplicar filtros
tecnologias_filtradas = {}

for nombre, data in ior_techs.items():
    cumple_tipo = (tipo_filtro == "Todos") or (data["tipo"] == tipo_filtro)
    cumple_region = (region_filtro == "Todas") or (region_filtro in data["implementacion"])
    if cumple_tipo and cumple_region:
        tecnologias_filtradas[nombre] = data

# Mostrar resultados
if tecnologias_filtradas:
    for nombre, data in tecnologias_filtradas.items():
        st.subheader(f"📌 {nombre}")
        st.markdown(f"**Tipo:** {data['tipo']}")
        st.markdown(f"**Descripción:** {data['descripcion']}")
        st.markdown("**Implementación mundial:**")
        st.write("- " + "\n- ".join(data["implementacion"]))
        st.markdown("---")
else:
    st.warning("No se encontraron tecnologías que coincidan con los filtros seleccionados.")
