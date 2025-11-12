import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
from math import log

# Librerías adicionales para mapas
import folium
from streamlit_folium import st_folium
import pydeck as pdk

# ===============================
# 🌿 CONFIGURACIÓN DE LA PÁGINA
# ===============================

st.set_page_config(
    page_title="Atlas de Biodiversidad",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# 🧭 TÍTULO Y DESCRIPCIÓN
# ===============================

st.title("🌿 Atlas de Biodiversidad")
st.markdown("""
Análisis de biodiversidad usando la metodología **LE.MU Atlas** + **Índice de Shannon-Wiener**  
Versión optimizada para **Streamlit Cloud** (100% en línea)
""")

# ===============================
# 🧩 CLASES DE ANÁLISIS
# ===============================

class BiodiversityAnalyzer:
    """Analizador completo de biodiversidad"""
   
    def __init__(self):
        self.species_pool = [
            'Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris',
            'Acer pseudoplatanus', 'Betula pendula', 'Alnus glutinosa',
            'Pinus pinaster', 'Quercus ilex', 'Quercus suber',
            'Juniperus communis', 'Castanea sativa', 'Populus nigra',
            'Fraxinus excelsior', 'Ulmus minor', 'Salix alba',
            'Corylus avellana', 'Crataegus monogyna', 'Rubus fruticosus'
        ]
   
    def shannon_index(self, abundances):
        total = sum(abundances)
        if total == 0:
            return 0.0
        proportions = [a / total for a in abundances if a > 0]
        return -sum(p * math.log(p) for p in proportions)
   
    def simpson_index(self, abundances):
        total = sum(abundances)
        if total == 0:
            return 0.0
        return sum((a / total) ** 2 for a in abundances)
   
    def species_richness(self, abundances):
        return sum(1 for a in abundances if a > 0)
   
    def evenness(self, shannon_index, richness):
        if richness <= 1:
            return 1.0
        return shannon_index / math.log(richness)
   
    def simulate_species_data(self, area_count, method="Basado en área", max_species=15):
        species_data = []
        selected_species = np.random.choice(
            self.species_pool,
            size=min(max_species, len(self.species_pool)),
            replace=False
        )
        for area_idx in range(area_count):
            for species in selected_species:
                if method == "Basado en área":
                    abundance = self._area_based_abundance(species, area_idx)
                elif method == "Basado en tipo de vegetación":
                    abundance = self._vegetation_based_abundance(species, area_idx)
                else:
                    abundance = self._random_abundance(species)
                species_data.append({
                    'species': species,
                    'abundance': int(abundance),
                    'frequency': round(np.random.uniform(0.1, 1.0), 3),
                    'area': f"Área {area_idx + 1}"
                })
        return species_data
   
    def _area_based_abundance(self, species, area_idx):
        base_abundance = {
            'Quercus robur': 50, 'Fagus sylvatica': 40, 'Pinus sylvestris': 60,
            'Acer pseudoplatanus': 30, 'Betula pendula': 35, 'Alnus glutinosa': 25
        }
        base = base_abundance.get(species, 20)
        return max(1, int(base * (area_idx + 1) * np.random.lognormal(0, 0.5)))
   
    def _vegetation_based_abundance(self, species, area_idx):
        vegetation_types = ['Bosque denso', 'Bosque abierto', 'Matorral', 'Herbazal']
        vegetation = vegetation_types[area_idx % len(vegetation_types)]
        vegetation_preferences = {
            'Bosque denso': ['Fagus sylvatica', 'Quercus robur', 'Acer pseudoplatanus'],
            'Bosque abierto': ['Pinus sylvestris', 'Quercus ilex', 'Juniperus communis'],
            'Matorral': ['Crataegus monogyna', 'Rubus fruticosus', 'Corylus avellana'],
            'Herbazal': ['Herbáceas diversas']
        }
        preferred = vegetation_preferences.get(vegetation, [])
        if species in preferred:
            base_abundance = np.random.poisson(40) + 20
        else:
            base_abundance = np.random.poisson(15) + 5
        return max(1, base_abundance)
   
    def _random_abundance(self, species):
        return np.random.poisson(25) + 1
   
    def analyze_biodiversity(self, species_data):
        df = pd.DataFrame(species_data)
        if df.empty:
            return {'shannon_index': 0, 'species_richness': 0,
                    'total_abundance': 0, 'evenness': 0, 'simpson_index': 0}
        species_abundances = df.groupby('species')['abundance'].sum().values
        shannon = self.shannon_index(species_abundances)
        richness = self.species_richness(species_abundances)
        total = sum(species_abundances)
        evenness = self.evenness(shannon, richness)
        simpson = self.simpson_index(species_abundances)
        return {
            'shannon_index': shannon,
            'species_richness': richness,
            'total_abundance': total,
            'evenness': evenness,
            'simpson_index': simpson,
            'species_data': species_data
        }

class FileProcessor:
    """Procesador de archivos KML y ZIP"""
   
    def process_uploaded_file(self, uploaded_file):
        if uploaded_file is None:
            return 0
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        try:
            if file_extension == '.kml':
                return self._process_kml(uploaded_file)
            elif file_extension == '.zip':
                return self._process_zip(uploaded_file)
            else:
                st.warning(f"Formato {file_extension} no soportado. Usando datos de ejemplo.")
                return 3
        except Exception as e:
            st.warning(f"Error procesando archivo: {e}. Usando datos de ejemplo.")
            return 3
   
    def _process_kml(self, uploaded_file):
        content = uploaded_file.getvalue().decode('utf-8')
        placemark_count = content.count('<Placemark>')
        polygon_count = content.count('<Polygon>')
        areas_detected = max(placemark_count, polygon_count, 1)
        st.info(f"🔍 Detectadas {areas_detected} áreas en el archivo KML")
        return areas_detected
   
    def _process_zip(self, uploaded_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                shp_files = [f for f in files if f.endswith('.shp')]
                if shp_files:
                    areas_detected = len(shp_files) * 3
                    st.info(f"🔍 Shapefile detectado. Estimadas {areas_detected} áreas.")
                else:
                    areas_detected = max(len(files), 3)
                    st.info(f"🔍 Archivo ZIP con {len(files)} archivos. Estimando {areas_detected} áreas.")
                return areas_detected
        finally:
            os.unlink(tmp_path)

# ===============================
# 📁 SIDEBAR DE CONFIGURACIÓN
# ===============================

with st.sidebar:
    st.header("📁 Cargar Datos")
    uploaded_file = st.file_uploader(
        "Sube tu archivo geográfico (opcional)",
        type=['kml', 'zip'],
        help="Formatos soportados: KML, Shapefile (ZIP)"
    )
    st.markdown("---")
    st.header("⚙️ Parámetros de Análisis")
    simulation_method = st.selectbox(
        "Método de simulación",
        ["Basado en área", "Basado en tipo de vegetación", "Aleatorio"]
    )
    num_species = st.slider(
        "Número máximo de especies",
        min_value=5, max_value=30, value=12
    )
    manual_areas = st.slider(
        "Número de áreas (si no subes archivo)",
        min_value=1, max_value=20, value=5
    )
    st.markdown("---")
    st.info("""
    - **Shannon**: Diversidad  
    - **Riqueza**: # de especies  
    - **Equitatividad**: Uniformidad  
    - **Simpson**: Dominancia
    """)

# ===============================
# 🚀 EJECUCIÓN DEL ANÁLISIS
# ===============================

analyzer = BiodiversityAnalyzer()
processor = FileProcessor()

if uploaded_file:
    with st.spinner("Analizando archivo..."):
        area_count = processor.process_uploaded_file(uploaded_file)
    st.success(f"📊 Archivo procesado: {uploaded_file.name}")
else:
    area_count = manual_areas
    st.info(f"🔬 Usando {area_count} áreas de ejemplo")

col1, col2, col3 = st.columns(3)
col1.metric("Áreas de estudio", area_count)
col2.metric("Método de simulación", simulation_method)
col3.metric("Especies máx.", num_species)

if st.button("🚀 Ejecutar Análisis de Biodiversidad", type="primary", use_container_width=True):
    with st.spinner("Calculando métricas..."):
        species_data = analyzer.simulate_species_data(area_count, simulation_method, num_species)
        results = analyzer.analyze_biodiversity(species_data)

    st.subheader("📈 Métricas Principales")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Índice de Shannon", f"{results['shannon_index']:.3f}")
    col2.metric("Riqueza de Especies", results['species_richness'])
    col3.metric("Abundancia Total", f"{results['total_abundance']:,}")
    col4.metric("Equitatividad", f"{results['evenness']:.3f}")

    # Interpretación visual
    sh = results['shannon_index']
    if sh < 1.0:
        st.error("🌱 Baja diversidad")
    elif sh < 3.0:
        st.warning("🌿 Diversidad moderada")
    else:
        st.success("🌳 Alta diversidad")

    # Datos y gráficos
    df_species = pd.DataFrame(results['species_data'])
    summary = df_species.groupby('species').agg({
        'abundance': 'sum', 'frequency': 'mean', 'area': 'count'
    }).reset_index()
    summary.columns = ['Especie', 'Abundancia', 'Frecuencia', 'Áreas']
    st.dataframe(summary, use_container_width=True)

    st.bar_chart(summary.set_index('Especie')['Abundancia'])

    # ===========================
    # 🌍 MAPA BASE ESRI
    # ===========================

    st.subheader("🗺️ Mapa Interactivo de Resultados")
    m = folium.Map(location=[-30.0, -62.5], zoom_start=7, tiles=None)
    folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='ESRI Satellite').add_to(m)

    for idx in range(area_count):
        folium.Marker(
            location=[-30.0 + np.random.uniform(-0.3, 0.3),
                      -62.5 + np.random.uniform(-0.3, 0.3)],
            popup=f"Área {idx+1}",
            icon=folium.Icon(color='green', icon='leaf')
        ).add_to(m)
    st_folium(m, width=800, height=500)

    # ===========================
    # 🌄 VISUALIZACIÓN 3D LIDAR
    # ===========================

    st.subheader("🌄 Visualización 3D LiDAR (experimental)")
    uploaded_lidar = st.file_uploader("Sube archivo LiDAR (.las o .laz)", type=["las", "laz"])

    if uploaded_lidar:
        import laspy
        with tempfile.NamedTemporaryFile(delete=False, suffix='.las') as tmp_las:
            tmp_las.write(uploaded_lidar.read())
            tmp_path = tmp_las.name
        las = laspy.read(tmp_path)
        x, y, z = las.x, las.y, las.z
        df_lidar = pd.DataFrame({"x": x, "y": y, "z": z})
        midpoint = (np.mean(df_lidar["y"]), np.mean(df_lidar["x"]))
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/satellite-v9",
            initial_view_state=pdk.ViewState(
                latitude=midpoint[0],
                longitude=midpoint[1],
                zoom=13,
                pitch=60,
            ),
            layers=[
                pdk.Layer(
                    "PointCloudLayer",
                    data=df_lidar,
                    get_position=["x", "y", "z"],
                    get_color=[0, 255, 0, 80],
                    point_size=1,
                ),
            ],
        ))
    else:
        st.info("Sube un archivo LiDAR (.las o .laz) para visualizar el terreno en 3D.")

else:
    st.info("""
### 👋 ¡Bienvenido al Atlas de Biodiversidad!

1️⃣ Sube un **KML o Shapefile (ZIP)**  
2️⃣ Configura tus parámetros  
3️⃣ Presiona **Ejecutar Análisis de Biodiversidad**  
4️⃣ Explora métricas, mapas y visualizaciones 3D  

📊 Metodología: [LE.MU Atlas](https://www.le.mu/atlas/)
""")

st.markdown("---")
st.markdown(
    "<div style='text-align: center'>🌿 <b>Atlas de Biodiversidad</b> | "
    "Metodología LE.MU Atlas | Desarrollado con Streamlit 🚀</div>",
    unsafe_allow_html=True
)
