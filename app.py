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
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import laspy  # Para LiDAR

# Configuración de la página
st.set_page_config(
    page_title="Atlas de Biodiversidad",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título y descripción
st.title("🌿 Atlas de Biodiversidad")
st.markdown("""
Análisis de biodiversidad usando la metodología LE.MU + Índice de Shannon
**Versión optimizada para Streamlit Cloud con mapas ESRI y 3D LiDAR**
""")

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
        """Calcula el índice de Shannon-Wiener"""
        total = sum(abundances)
        if total == 0:
            return 0.0
       
        proportions = [abundance / total for abundance in abundances if abundance > 0]
        return -sum(p * math.log(p) for p in proportions)
   
    def simpson_index(self, abundances):
        """Calcula el índice de Simpson"""
        total = sum(abundances)
        if total == 0:
            return 0.0
       
        return sum((abundance / total) ** 2 for abundance in abundances)
   
    def species_richness(self, abundances):
        """Calcula la riqueza de especies"""
        return sum(1 for abundance in abundances if abundance > 0)
   
    def evenness(self, shannon_index, species_richness):
        """Calcula la equitatividad de Pielou"""
        if species_richness <= 1:
            return 1.0
        return shannon_index / math.log(species_richness)
   
    def simulate_species_data(self, gdf, max_species=15):
        """Simula datos por geometría (usa área real para escalar abundancia)"""
        species_data = []
        selected_species = np.random.choice(self.species_pool, size=min(max_species, len(self.species_pool)), replace=False)
       
        for idx, row in gdf.iterrows():
            area_m2 = row.geometry.area  # Área en m² (asumiendo CRS métrico)
            area_ha = area_m2 / 10000  # Convertir a hectáreas
            for species in selected_species:
                abundance = max(1, int(20 * area_ha * np.random.lognormal(0, 0.5)))  # Escala por área
                species_data.append({
                    'species': species,
                    'abundance': abundance,
                    'frequency': round(np.random.uniform(0.1, 1.0), 3),
                    'area_id': idx,
                    'area_name': f"Área {idx + 1}"
                })
       
        # Calcular métricas por área
        area_metrics = {}
        for idx in gdf.index:
            area_abundances = [d['abundance'] for d in species_data if d['area_id'] == idx]
            area_metrics[idx] = {
                'shannon': self.shannon_index(area_abundances),
                'richness': self.species_richness(area_abundances),
                'total_abundance': sum(area_abundances)
            }
       
        return species_data, area_metrics
   
    # ... (mantén el resto de métodos: _area_based_abundance, etc., pero no se usan ahora ya que simulamos por geo)

class FileProcessor:
    """Procesador de archivos KML, ZIP y LiDAR"""
   
    def process_uploaded_file(self, uploaded_file):
        """Procesa y devuelve GeoDataFrame de áreas"""
        if uploaded_file is None:
            # GeoDataFrame de ejemplo (polígonos simples en España para demo)
            from shapely.geometry import Point
            gdf = gpd.GeoDataFrame(
                {'name': [f'Área {i}' for i in range(5)]},
                geometry=[Polygon([( -4 + i*0.5, 40 + i*0.1, -4 + i*0.5 + 0.1, 40 + i*0.1 + 0.05, -4 + i*0.5, 40 + i*0.1)]) for i in range(5)],
                crs='EPSG:4326'
            )
            return gdf, 5
       
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
       
        try:
            if file_extension == '.kml':
                with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                gdf = gpd.read_file(tmp_path, driver='KML')
                os.unlink(tmp_path)
            elif file_extension == '.zip':
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                with zipfile.ZipFile(tmp_path, 'r') as z:
                    shp_name = [f for f in z.namelist() if f.endswith('.shp')][0]
                    z.extractall(tempfile.gettempdir())
                shp_path = os.path.join(tempfile.gettempdir(), shp_name)
                gdf = gpd.read_file(shp_path)
                # Limpiar temps
                for f in os.listdir(tempfile.gettempdir()):
                    if f.startswith(os.path.basename(shp_path).split('.')[0]):
                        os.unlink(os.path.join(tempfile.gettempdir(), f))
                os.unlink(tmp_path)
            else:
                st.warning("Formato no soportado. Usando ejemplo.")
                return self._example_gdf()
           
            if gdf.empty:
                st.warning("No se detectaron geometrías. Usando ejemplo.")
                return self._example_gdf()
           
            gdf = gdf.to_crs('EPSG:4326')  # Normalizar a WGS84
            st.success(f"Procesado: {len(gdf)} áreas detectadas.")
            return gdf, len(gdf)
        except Exception as e:
            st.error(f"Error: {e}. Usando ejemplo.")
            return self._example_gdf()
   
    def _example_gdf(self):
        # Ejemplo simple
        from shapely.geometry import Polygon
        gdf = gpd.GeoDataFrame(
            {'name': ['Ejemplo 1', 'Ejemplo 2']},
            geometry=[Polygon([(-4,40), (-3.9,40), (-3.9,40.1), (-4,40.1)]), Polygon([(-3,40), (-2.9,40), (-2.9,40.1), (-3,40.1)])],
            crs='EPSG:4326'
        )
        return gdf, 2
   
    def process_lidar(self, lidar_file):
        """Procesa LiDAR LAS y devuelve puntos para 3D"""
        if lidar_file is None:
            return None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.las') as tmp:
                if lidar_file.name.endswith('.zip'):
                    with zipfile.ZipFile(lidar_file, 'r') as z:
                        las_name = [f for f in z.namelist() if f.endswith('.las')][0]
                        z.extract(las_name, tmp.name.replace('.las', ''))
                    las_path = os.path.join(tmp.name.replace('.las', ''), las_name)
                else:
                    tmp.write(lidar_file.getvalue())
                    las_path = tmp.name
            las = laspy.read(las_path)
            points = np.vstack((las.x, las.y, las.z)).T
            colors = las.red / 65535 if 'red' in las.point_format.dimension_names else np.ones(len(las.x))
            df_points = pd.DataFrame({'x': points[:,0], 'y': points[:,1], 'z': points[:,2], 'color': colors})
            st.success(f"LiDAR cargado: {len(df_points)} puntos.")
            return df_points
        except Exception as e:
            st.error(f"Error LiDAR: {e}")
            return None
        finally:
            # Limpiar temps (simplificado)

# Sidebar
with st.sidebar:
    st.header("📁 Cargar Datos")
    uploaded_file = st.file_uploader("Archivo geográfico (KML/ZIP)", type=['kml', 'zip'])
    lidar_file = st.file_uploader("Archivo LiDAR (LAS/ZIP, opcional para 3D)", type=['las', 'zip'])
   
    st.markdown("---")
    st.header("⚙️ Parámetros")
    num_species = st.slider("Especies máx.", 5, 30, 12)
   
    st.markdown("---")
    st.header("📊 Métricas LE.MU")
    st.info("Basado en Species Richness + Shannon para diversidad.")

# Inicializar
analyzer = BiodiversityAnalyzer()
processor = FileProcessor()

# Procesar archivos
gdf, area_count = processor.process_uploaded_file(uploaded_file)
lidar_points = processor.process_lidar(lidar_file)

# Mostrar info
col1, col2 = st.columns(2)
with col1:
    st.metric("Áreas", area_count)
with col2:
    st.metric("Especies máx.", num_species)

# Ejecutar
if st.button("🚀 Ejecutar Análisis", type="primary"):
    with st.spinner("Analizando..."):
        species_data, area_metrics = analyzer.simulate_species_data(gdf, num_species)
        # Métricas globales (agrega por área)
        all_abundances = [d['abundance'] for d in species_data]
        results = {
            'shannon_index': analyzer.shannon_index(all_abundances),
            'species_richness': analyzer.species_richness(all_abundances),
            'total_abundance': sum(all_abundances),
            'evenness': analyzer.evenness(results['shannon_index'], results['species_richness']),
            'simpson_index': analyzer.simpson_index(all_abundances),
            'species_data': species_data,
            'area_metrics': area_metrics,
            'gdf': gdf
        }
   
    # Métricas principales (igual que antes)
    st.subheader("📈 Métricas Globales")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Shannon", f"{results['shannon_index']:.3f}")
    with col2: st.metric("Riqueza", results['species_richness'])
    with col3: st.metric("Abundancia", f"{results['total_abundance']:,}")
    with col4: st.metric("Equitatividad", f"{results['evenness']:.3f}")
   
    # Interpretación (igual)
    shannon_value = results['shannon_index']
    if shannon_value < 1.0: diversity_level, color = "Baja", "🔴"
    elif shannon_value < 3.0: diversity_level, color = "Moderada", "🟡"
    else: diversity_level, color = "Alta", "🟢"
    st.info(f"**Shannon ({shannon_value:.3f}):** {color} {diversity_level}")
   
    # Tabla especies (igual, adapta)
    df_species = pd.DataFrame(results['species_data'])
    species_summary = df_species.groupby('species').agg({'abundance': 'sum', 'frequency': 'mean'}).reset_index()
    species_summary.columns = ['Especie', 'Abundancia', 'Frecuencia']
    st.dataframe(species_summary.sort_values('Abundancia', ascending=False))
   
    # NUEVO: Mapa con ESRI
    st.subheader("🗺️ Mapa de Biodiversidad (Base ESRI Satellite)")
    # Asigna Shannon por área a gdf
    gdf['shannon'] = [results['area_metrics'].get(idx, {}).get('shannon', 0) for idx in gdf.index]
    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=10, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='ESRI Satellite')
    folium.GeoJson(
        gdf,
        data=gdf,
        style_function=lambda x: {
            'fillColor': 'green' if x['properties']['shannon'] > 2 else 'orange' if x['properties']['shannon'] > 1 else 'red',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5
        },
        popup=folium.GeoJsonPopup(fields=['name', 'shannon'])
    ).add_to(m)
    st_folium(m, width=700, height=500)
   
    # NUEVO: 3D LiDAR
    if lidar_points is not None:
        st.subheader("🌀 Visualización 3D LiDAR + Áreas")
        fig = go.Figure()
        # Puntos LiDAR (coloreados por Z/elevación)
        fig.add_trace(go.Scatter3d(
            x=lidar_points['x'], y=lidar_points['y'], z=lidar_points['z'],
            mode='markers', marker=dict(size=1, color=lidar_points['z'], colorscale='Viridis', opacity=0.6),
            name='Puntos LiDAR'
        ))
        # Superponer áreas (simplificado: usa centroides o extruye por Shannon)
        for idx, row in gdf.iterrows():
            cent = row.geometry.centroid
            sh = results['area_metrics'].get(idx, {}).get('shannon', 0)
            fig.add_trace(go.Scatter3d(
                x=[cent.x]*4, y=[cent.y]*4, z=[0, sh*10, sh*10, 0],  # Extrusión simple por Shannon
                mode='lines', line=dict(width=5, color='red' if sh<1 else 'orange' if sh<3 else 'green'),
                name=f'Área {idx+1} (Shannon: {sh:.2f})'
            ))
        fig.update_layout(scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'), title="3D: LiDAR + Biodiversidad")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sube un archivo LiDAR para ver 3D.")
   
    # Gráficos viejos (mantén uno)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Abundancia por Especie")
        st.bar_chart(species_summary.set_index('Especie')['Abundancia'])
    with col2:
        st.subheader("Shannon por Área")
        area_df = pd.DataFrame([(k, v['shannon']) for k,v in results['area_metrics'].items()], columns=['Área', 'Shannon'])
        st.bar_chart(area_df.set_index('Área')['Shannon'])
   
    # Expander y Export (igual que antes)
    with st.expander("📋 Detalles LE.MU"):
        st.markdown("""
        **Metodología**: Basado en LE.MU (Species Richness, Biorarity). Shannon integra diversidad. Datos espaciales zonifican análisis.
        **Fuentes**: [Atlas](https://www.le.mu/atlas/), [Indicators](https://www.le.mu/docs/indicators/).
        """)
   
    # Export
    st.subheader("💾 Exportar")
    csv = df_species.to_csv(index=False)
    st.download_button("CSV Datos", csv, "biodiversidad.csv")
    gdf.to_file("areas.geojson", driver='GeoJSON')  # Para map
    with open("areas.geojson", 'r') as f:
        st.download_button("GeoJSON Áreas", f.read(), "areas.geojson")

else:
    st.markdown("""
    **¡Bienvenido!** Sube archivos y ejecuta para ver mapas ESRI + 3D LiDAR.
    """)

# Footer (igual)
st.markdown("---")
st.markdown("<div style='text-align: center'>🌿 <b>Atlas LE.MU</b> | Streamlit 🚀</div>", unsafe_allow_html=True)
