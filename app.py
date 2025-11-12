import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
from math import log
import geopandas as gpd
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import laspy

# Configuración
st.set_page_config(
    page_title="Atlas de Biodiversidad",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌿 Atlas de Biodiversidad LE.MU")
st.markdown("""
Análisis basado en [LE.MU Atlas](https://www.le.mu/atlas/) + **Índice de Shannon**.  
Mapas ESRI + 3D LiDAR. Todo online.
""")

class BiodiversityAnalyzer:
    def __init__(self):
        self.species_pool = [
            'Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris', 'Acer pseudoplatanus',
            'Betula pendula', 'Alnus glutinosa', 'Pinus pinaster', 'Quercus ilex',
            'Quercus suber', 'Juniperus communis', 'Castanea sativa', 'Populus nigra',
            'Fraxinus excelsior', 'Ulmus minor', 'Salix alba', 'Corylus avellana',
            'Crataegus monogyna', 'Rubus fruticosus'
        ]

    def shannon_index(self, abundances):
        total = sum(abundances)
        if total == 0: return 0.0
        proportions = [a / total for a in abundances if a > 0]
        return -sum(p * log(p) for p in proportions)

    def simpson_index(self, abundances):
        total = sum(abundances)
        if total == 0: return 0.0
        return sum((a / total) ** 2 for a in abundances)

    def species_richness(self, abundances):
        return sum(1 for a in abundances if a > 0)

    def evenness(self, shannon, richness):
        if richness <= 1: return 1.0
        return shannon / log(richness)

    def simulate_species_data(self, gdf, max_species=15):
        selected_species = np.random.choice(self.species_pool, min(max_species, len(self.species_pool)), replace=False)
        species_data = []
        area_metrics = {}

        for idx, row in gdf.iterrows():
            area_m2 = row.geometry.area * 111320 ** 2  # Aprox m² desde grados
            area_ha = area_m2 / 10000
            area_abundances = []
            for species in selected_species:
                abundance = max(1, int(20 * area_ha * np.random.lognormal(0, 0.5)))
                area_abundances.append(abundance)
                species_data.append({
                    'species': species, 'abundance': abundance, 'area_id': idx, 'area_name': row.get('name', f"Área {idx+1}")
                })
            # Métricas por área
            sh = self.shannon_index(area_abundances)
            area_metrics[idx] = {'shannon': sh, 'richness': self.species_richness(area_abundances), 'abundance': sum(area_abundances)}

        return species_data, area_metrics

class FileProcessor:
    @staticmethod
    def process_geo_file(uploaded_file):
        if uploaded_file is None:
            # Ejemplo: 5 polígonos en Madrid
            geometries = [
                Polygon([(-3.7, 40.4), (-3.69, 40.4), (-3.69, 40.41), (-3.7, 40.41)]),
                Polygon([(-3.65, 40.42), (-3.64, 40.42), (-3.64, 40.43), (-3.65, 40.43)]),
                Polygon([(-3.6, 40.45), (-3.59, 40.45), (-3.59, 46), (-3.6, 40.46)]),
                Polygon([(-3.55, 40.47), (-3.54, 40.47), (-3.54, 40.48), (-3.55, 40.48)]),
                Polygon([(-3.5, 40.49), (-3.49, 40.49), (-3.49, 40.5), (-3.5, 40.5)])
            ]
            gdf = gpd.GeoDataFrame({'name': [f'Área {i+1}' for i in range(5)]}, geometry=geometries, crs='EPSG:4326')
            return gdf
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        try:
            if ext == '.kml':
                gdf = gpd.read_file(tmp_path, driver='KML')
            elif ext == '.zip':
                with zipfile.ZipFile(tmp_path) as z:
                    shp = [f for f in z.namelist() if f.endswith('.shp')][0]
                    z.extractall(tempfile.gettempdir())
                    shp_path = os.path.join(tempfile.gettempdir(), shp)
                    gdf = gpd.read_file(shp_path)
                    # Limpia
                    for f in os.listdir(tempfile.gettempdir()):
                        if f.startswith(os.path.basename(shp).split('.')[0]):
                            os.unlink(os.path.join(tempfile.gettempdir(), f))
            gdf = gdf.to_crs('EPSG:4326')
            st.success(f"📁 {len(gdf)} áreas cargadas.")
            return gdf
        except Exception as e:
            st.warning(f"Error: {e}. Usando ejemplo.")
            return FileProcessor.process_geo_file(None)
        finally:
            os.unlink(tmp_path)

    @staticmethod
    def process_lidar(lidar_file):
        if not lidar_file: return None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.las') as tmp:
            if lidar_file.name.endswith('.zip'):
                with zipfile.ZipFile(lidar_file) as z:
                    las = [f for f in z.namelist() if f.endswith('.las')][0]
                    z.extract(las, os.path.dirname(tmp.name))
                    las_path = os.path.join(os.path.dirname(tmp.name), las)
            else:
                tmp.write(lidar_file.getvalue())
                las_path = tmp.name
            las = laspy.read(las_path)
            points = np.vstack((las.x, las.y, las.z)).T
            df = pd.DataFrame({'x': points[:,0], 'y': points[:,1], 'z': points[:,2]})
            st.success(f"🌀 {len(df)} puntos LiDAR.")
            return df

# UI
with st.sidebar:
    st.header("📁 Carga")
    geo_file = st.file_uploader("KML/ZIP", type=['kml', 'zip'])
    lidar_file = st.file_uploader("LiDAR (LAS/ZIP)", type=['las', 'zip'])
    max_species = st.slider("Especies", 5, 30, 12)

analyzer = BiodiversityAnalyzer()
processor = FileProcessor()

gdf = processor.process_geo_file(geo_file)
lidar_df = processor.process_lidar(lidar_file)

col1, col2 = st.columns(2)
col1.metric("Áreas", len(gdf))
col2.metric("Especies", max_species)

if st.button("🚀 Analizar", type="primary"):
    with st.spinner("Calculando..."):
        species_data, area_metrics = analyzer.simulate_species_data(gdf, max_species)
        df_species = pd.DataFrame(species_data)
        
        # Métricas GLOBALES (agrupar por especie)
        global_abund = df_species.groupby('species')['abundance'].sum().values
        shannon = analyzer.shannon_index(global_abund)
        richness = analyzer.species_richness(global_abund)
        total_ab = sum(global_abund)
        even = analyzer.evenness(shannon, richness)
        simpson = analyzer.simpson_index(global_abund)
        
        results = {'shannon': shannon, 'richness': richness, 'abundance': total_ab, 'evenness': even, 'simpson': simpson}

    # Dashboard
    st.subheader("📈 Métricas Globales")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Shannon", f"{shannon:.3f}")
    c2.metric("Riqueza", richness)
    c3.metric("Abundancia", f"{total_ab:,}")
    c4.metric("Equitatividad", f"{even:.3f}")

    level = "Alta 🟢" if shannon > 3 else "Moderada 🟡" if shannon > 1 else "Baja 🔴"
    st.info(f"**Diversidad: {level}** (Shannon: {shannon:.3f})")

    # Tabla Especies
    st.subheader("📊 Especies")
    summary = df_species.groupby('species').agg({'abundance': 'sum'}).sort_values('abundance', ascending=False)
    st.dataframe(summary)

    # Mapa ESRI
    st.subheader("🗺️ Mapa (ESRI Satellite)")
    gdf['shannon'] = [area_metrics.get(idx, {}).get('shannon', 0) for idx in gdf.index]
    m = folium.Map([gdf.centroid.y.mean(), gdf.centroid.x.mean()], zoom_start=10,
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                   attr='ESRI')
    folium.GeoJson(gdf, popup=folium.GeoJsonPopup(['name', 'shannon']),
                   style_function=lambda f: {
                       'fillColor': 'green' if f['properties']['shannon'] > 2 else 'orange' if f['properties']['shannon'] > 1 else 'red',
                       'fillOpacity': 0.6, 'color': 'black', 'weight': 2
                   }).add_to(m)
    st_folium(m, width=700)

    # 3D LiDAR
    if lidar_df is not None:
        st.subheader("🌀 3D LiDAR + Áreas")
        fig = go.Figure()
        fig.add_trace(go.Scatter3d(x=lidar_df['x'], y=lidar_df['y'], z=lidar_df['z'],
                                   mode='markers', marker=dict(size=1, color='blue', opacity=0.6), name='LiDAR'))
        for idx, row in gdf.iterrows():
            sh = area_metrics.get(idx, {}).get('shannon', 0)
            color = 'green' if sh > 2 else 'orange' if sh > 1 else 'red'
            # Extrusión simple del polígono (4 esquinas approx)
            poly = row.geometry
            coords = list(poly.exterior.coords)[:4]
            zs = [0, sh*10, sh*10, 0]
            fig.add_trace(go.Scatter3d(x=[c[0] for c in coords], y=[c[1] for c in coords], z=zs,
                                       mode='lines', line=dict(color=color, width=5), name=f"Área {idx}"))
        fig.update_layout(scene=dict(xaxis_title='Lon', yaxis_title='Lat', zaxis_title='Elev/Shannon'), height=600)
        st.plotly_chart(fig)

    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(summary)
    with col2:
        area_sh = pd.DataFrame(list(area_metrics.items()), columns=['ID', 'Shannon']).set_index('ID')
        st.bar_chart(area_sh['Shannon'])

    # Detalles LE.MU
    with st.expander("📋 Metodología LE.MU"):
        st.markdown("""
        - **Shannon**: -Σ(p ln p) | Baja<1, Alta>3
        - **Riqueza**: Especies únicas (LE.MU Species Richness)
        - **Escala**: Por área real (ha)
        - [Docs](https://www.le.mu/docs/indicators/)
        """)

    # Export
    st.subheader("💾 Exportar")
    st.download_button("CSV Datos", df_species.to_csv(index=False), "biodiversidad.csv")
    gdf_with_metrics = gdf.copy()
    gdf_with_metrics['shannon'] = gdf['shannon']
    gdf_with_metrics.to_file("areas_con_metrics.geojson", driver='GeoJSON')
    with open("areas_con_metrics.geojson", "rb") as f:
        st.download_button("GeoJSON Áreas", f, "areas.geojson")

else:
    st.info("👆 Sube archivos y haz clic en Analizar.")

st.markdown("---")
st.markdown("<div style='text-align:center'>🌿 LE.MU Atlas | Streamlit 2025</div>", unsafe_allow_html=True)
