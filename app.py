import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import zipfile
import tempfile
import os

st.set_page_config(
    page_title="Atlas de Biodiversidad",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌿 Atlas de Biodiversidad")

class BiodiversityAnalyzer:
    def __init__(self):
        self.species_pool = ['Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris',
                              'Acer pseudoplatanus', 'Betula pendula', 'Alnus glutinosa',
                              'Pinus pinaster', 'Quercus ilex', 'Quercus suber',
                              'Juniperus communis', 'Castanea sativa', 'Populus nigra']
    
    def shannon_index(self, abundances):
        total = sum(abundances)
        if total == 0:
            return 0.0
        proportions = [a / total for a in abundances if a > 0]
        return -sum(p * np.log(p) for p in proportions)
    
    def species_richness(self, abundances):
        return sum(1 for a in abundances if a > 0)
    
    def simulate_species_data(self, area_count, max_species=10):
        species = np.random.choice(self.species_pool, size=max_species, replace=False)
        data = []
        for area in range(area_count):
            for sp in species:
                abundance = np.random.poisson(20) + 1
                data.append({'species': sp, 'abundance': abundance, 'area': f"Área {area+1}"})
        return data
    
    def analyze(self, data):
        df = pd.DataFrame(data)
        abundances = df.groupby('species')['abundance'].sum()
        shannon = self.shannon_index(abundances)
        richness = self.species_richness(abundances)
        return shannon, richness, df

def process_zip(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    try:
        with zipfile.ZipFile(tmp_path) as z:
            shp_files = [f for f in z.namelist() if f.endswith('.shp')]
            # Read first shapefile with geopandas if exists
            if shp_files:
                gdf = gpd.read_file(f"zip://{tmp_path}!{shp_files[0]}")
                st.map(gdf)
                return len(gdf)
    except Exception as e:
        st.warning(f"Error leyendo shapefile: {e}")
    finally:
        os.unlink(tmp_path)
    return 1

# Sidebar
st.sidebar.header("Cargar archivo")
uploaded_file = st.sidebar.file_uploader("Sube KML o ZIP con shapefile", type=["kml", "zip"])
area_count = 5
if uploaded_file is not None:
    ext = os.path.splitext(uploaded_file.name)[1]
    if ext == ".zip":
        area_count = process_zip(uploaded_file)
    else:
        area_count = 5
else:
    area_count = st.sidebar.slider("Número de áreas para simulación", 1, 20, 5)

# Run analysis
if st.button("Ejecutar análisis"):
    analyzer = BiodiversityAnalyzer()
    species_data = analyzer.simulate_species_data(area_count)
    shannon, richness, df = analyzer.analyze(species_data)
    st.write(f"Índice de Shannon: {shannon:.3f}")
    st.write(f"Riqueza de especies: {richness}")
    st.dataframe(df)
    
    # Map visualization example
    m = folium.Map(location=[40, -3], zoom_start=5,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri Satellite')
    st_folium(m, width=700, height=500)
else:
    st.write("Carga un archivo o ajusta número de áreas y haz click en ejecutar análisis para comenzar.")

