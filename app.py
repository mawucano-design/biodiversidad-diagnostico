import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Atlas de Biodiversidad",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título y descripción
st.title("🌿 Atlas de Biodiversidad - Análisis Avanzado")
st.markdown("""
Análisis de biodiversidad con mapas interactivos, base ESRI Satellite y visualización 3D con LiDAR simulado
""")

class BiodiversityAnalyzer:
    """Analizador completo de biodiversidad con capacidades geoespaciales"""
    
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
    
    def generate_sample_locations(self, center_lat, center_lon, num_areas, area_size_km=0.5):
        """Genera ubicaciones geográficas para las áreas de muestreo"""
        locations = []
        
        for i in range(num_areas):
            # Variación aleatoria alrededor del punto central (aproximadamente 0.5-2km)
            lat_variation = np.random.uniform(-0.02, 0.02)  # ~2km
            lon_variation = np.random.uniform(-0.03, 0.03)  # ~3km
            
            lat = center_lat + lat_variation
            lon = center_lon + lon_variation
            
            # Simular elevación (metros)
            elevation = np.random.normal(500, 150)  # Media 500m, desviación 150m
            
            locations.append({
                'id': i + 1,
                'lat': lat,
                'lon': lon,
                'elevation': max(0, elevation),
                'area_hectares': np.random.uniform(5, 50)  # 5-50 hectáreas
            })
        
        return locations
    
    def simulate_lidar_data(self, locations):
        """Simula datos LiDAR para visualización 3D"""
        lidar_data = []
        
        for loc in locations:
            # Crear una cuadrícula de puntos alrededor de cada ubicación
            points_per_side = 10
            spacing = 0.001  # ~100 metros entre puntos
            
            for i in range(points_per_side):
                for j in range(points_per_side):
                    lat = loc['lat'] + (i - points_per_side/2) * spacing
                    lon = loc['lon'] + (j - points_per_side/2) * spacing
                    
                    # Simular altura de vegetación basada en elevación y ruido
                    base_height = loc['elevation']
                    vegetation_height = np.random.exponential(20)  # Altura de árboles
                    
                    lidar_data.append({
                        'lat': lat,
                        'lon': lon,
                        'elevation': base_height,
                        'vegetation_height': vegetation_height,
                        'total_height': base_height + vegetation_height,
                        'area_id': loc['id'],
                        'intensity': np.random.uniform(0.5, 1.0)  # Intensidad LiDAR
                    })
        
        return pd.DataFrame(lidar_data)
    
    def simulate_species_data(self, locations, method="Basado en área", max_species=15):
        """Simula datos de especies basados en ubicaciones geográficas"""
        species_data = []
        
        # Seleccionar especies del pool
        selected_species = np.random.choice(
            self.species_pool, 
            size=min(max_species, len(self.species_pool)), 
            replace=False
        )
        
        for loc in locations:
            for species in selected_species:
                # Calcular abundancia basada en el método seleccionado
                if method == "Basado en área":
                    abundance = self._area_based_abundance(species, loc)
                elif method == "Basado en elevación":
                    abundance = self._elevation_based_abundance(species, loc)
                else:  # Aleatorio
                    abundance = self._random_abundance(species)
                
                species_data.append({
                    'species': species,
                    'abundance': int(abundance),
                    'frequency': round(np.random.uniform(0.1, 1.0), 3),
                    'area_id': loc['id'],
                    'lat': loc['lat'],
                    'lon': loc['lon'],
                    'elevation': loc['elevation'],
                    'area_hectares': loc['area_hectares']
                })
        
        return species_data
    
    def _area_based_abundance(self, species, location):
        """Abundancia basada en área y características geográficas"""
        base_abundance = {
            'Quercus robur': 50, 'Fagus sylvatica': 40, 'Pinus sylvestris': 60,
            'Acer pseudoplatanus': 30, 'Betula pendula': 35, 'Alnus glutinosa': 25
        }
        base = base_abundance.get(species, 20)
        
        # Modificar basado en área y elevación
        area_factor = location['area_hectares'] / 25  # Normalizar a 25 hectáreas
        elevation_factor = 1 + (location['elevation'] - 500) / 1000  # Ajuste por elevación
        
        return max(1, int(base * area_factor * elevation_factor * np.random.lognormal(0, 0.3)))
    
    def _elevation_based_abundance(self, species, location):
        """Abundancia basada en preferencias de elevación"""
        # Especies de baja elevación
        low_elevation_species = ['Quercus suber', 'Olea europaea', 'Pistacia lentiscus']
        # Especies de media elevación
        mid_elevation_species = ['Quercus robur', 'Fagus sylvatica', 'Acer pseudoplatanus']
        # Especies de alta elevación
        high_elevation_species = ['Pinus sylvestris', 'Juniperus communis', 'Betula pendula']
        
        elevation = location['elevation']
        
        if species in low_elevation_species and elevation < 300:
            base = 60
        elif species in mid_elevation_species and 300 <= elevation <= 800:
            base = 50
        elif species in high_elevation_species and elevation > 800:
            base = 55
        else:
            base = 20  # Abundancia baja para hábitat no preferido
        
        return max(1, int(base * np.random.lognormal(0, 0.4)))
    
    def _random_abundance(self, species):
        """Abundancia aleatoria"""
        return np.random.poisson(25) + 1
    
    def analyze_biodiversity(self, species_data):
        """Analiza biodiversidad a partir de datos de especies"""
        df = pd.DataFrame(species_data)
        
        if df.empty:
            return {
                'shannon_index': 0,
                'species_richness': 0,
                'total_abundance': 0,
                'evenness': 0,
                'simpson_index': 0,
                'species_data': []
            }
        
        # Agrupar por especie y sumar abundancias
        species_abundances = df.groupby('species')['abundance'].sum().values
        
        # Calcular métricas
        shannon = self.shannon_index(species_abundances)
        richness = self.species_richness(species_abundances)
        total_abundance = sum(species_abundances)
        evenness_val = self.evenness(shannon, richness)
        simpson = self.simpson_index(species_abundances)
        
        return {
            'shannon_index': shannon,
            'species_richness': richness,
            'total_abundance': total_abundance,
            'evenness': evenness_val,
            'simpson_index': simpson,
            'species_data': species_data
        }

class MapVisualizer:
    """Clase para visualizaciones geoespaciales"""
    
    def create_biodiversity_map(self, species_data, center_lat, center_lon):
        """Crea mapa de biodiversidad con Folium"""
        
        # Calcular riqueza por área
        df = pd.DataFrame(species_data)
        richness_by_area = df.groupby('area_id').agg({
            'species': 'nunique',
            'abundance': 'sum',
            'lat': 'first',
            'lon': 'first'
        }).reset_index()
        
        # Crear mapa base con ESRI Satellite
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=None
        )
        
        # Añadir ESRI Satellite
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='ESRI Satellite',
            name='ESRI Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Añadir OpenStreetMap como alternativa
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Añadir marcadores para cada área de muestreo
        for _, area in richness_by_area.iterrows():
            # Color basado en riqueza de especies
            richness = area['species']
            if richness <= 3:
                color = 'red'
            elif richness <= 6:
                color = 'orange'
            else:
                color = 'green'
            
            # Popup con información
            popup_text = f"""
            <b>Área {int(area['area_id'])}</b><br>
            <b>Riqueza:</b> {int(richness)} especies<br>
            <b>Abundancia:</b> {int(area['abundance'])} ind.<br>
            <b>Coordenadas:</b> {area['lat']:.4f}, {area['lon']:.4f}
            """
            
            folium.CircleMarker(
                location=[area['lat'], area['lon']],
                radius=10 + richness * 2,  # Tamaño proporcional a riqueza
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        
        # Añadir control de capas
        folium.LayerControl().add_to(m)
        
        return m
    
    def create_3d_visualization(self, lidar_data, species_data):
        """Crea visualización 3D con PyDeck"""
        
        # Combinar datos LiDAR con información de especies
        df_lidar = lidar_data.copy()
        df_species = pd.DataFrame(species_data)
        
        # Calcular métricas por área para el color
        richness_by_area = df_species.groupby('area_id').agg({
            'species': 'nunique'
        }).reset_index()
        
        # Unir con datos LiDAR
        df_3d = df_lidar.merge(richness_by_area, on='area_id', how='left')
        
        # Capa de puntos LiDAR 3D
        point_cloud_layer = pdk.Layer(
            "PointCloudLayer",
            df_3d,
            get_position=['lon', 'lat', 'total_height'],
            get_normal=[0, 0, 1],
            get_color='[255, (species * 25) % 255, 0, 255]',
            auto_highlight=True,
            pickable=True,
            point_size=3,
        )
        
        # Configurar vista inicial
        view_state = pdk.ViewState(
            longitude=df_3d['lon'].mean(),
            latitude=df_3d['lat'].mean(),
            zoom=11,
            pitch=45,
            bearing=0,
            min_zoom=5,
            max_zoom=20
        )
        
        # Crear deck
        deck = pdk.Deck(
            layers=[point_cloud_layer],
            initial_view_state=view_state,
            tooltip={
                'html': '''
                <b>Altura Total:</b> {total_height:.1f} m<br/>
                <b>Elevación:</b> {elevation:.1f} m<br/>
                <b>Vegetación:</b> {vegetation_height:.1f} m<br/>
                <b>Riqueza:</b> {species} especies
                ''',
                'style': {
                    'color': 'white',
                    'backgroundColor': 'rgba(0,0,0,0.7)',
                    'padding': '10px'
                }
            }
        )
        
        return deck
    
    def create_species_distribution_map(self, species_data):
        """Crea mapa de distribución de especies específicas"""
        df = pd.DataFrame(species_data)
        
        # Encontrar las especies más abundantes
        top_species = df.groupby('species')['abundance'].sum().nlargest(5).index.tolist()
        
        fig = px.scatter_mapbox(
            df[df['species'].isin(top_species)],
            lat="lat",
            lon="lon",
            color="species",
            size="abundance",
            hover_name="species",
            hover_data={"abundance": True, "elevation": True, "area_hectares": True},
            zoom=10,
            height=600,
            title="Distribución de Especies Principales"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        return fig

# Sidebar para configuración
with st.sidebar:
    st.header("📍 Configuración Geográfica")
    
    # Selector de ubicación predefinida
    location_preset = st.selectbox(
        "Ubicación de estudio",
        [
            "Madrid, España (40.4168, -3.7038)",
            "Barcelona, España (41.3851, 2.1734)", 
            "Sevilla, España (37.3891, -5.9845)",
            "Valencia, España (39.4699, -0.3763)",
            "Personalizada..."
        ]
    )
    
    if "Personalizada" in location_preset:
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("Latitud", value=40.4168, format="%.6f")
        with col2:
            center_lon = st.number_input("Longitud", value=-3.7038, format="%.6f")
    else:
        # Extraer coordenadas del texto seleccionado
        coords = {
            "Madrid, España (40.4168, -3.7038)": (40.4168, -3.7038),
            "Barcelona, España (41.3851, 2.1734)": (41.3851, 2.1734),
            "Sevilla, España (37.3891, -5.9845)": (37.3891, -5.9845),
            "Valencia, España (39.4699, -0.3763)": (39.4699, -0.3763),
        }
        center_lat, center_lon = coords[location_preset]
    
    st.markdown("---")
    st.header("📁 Carga de Datos")
    
    uploaded_file = st.file_uploader(
        "Sube archivo geográfico (opcional)",
        type=['kml', 'zip'],
        help="KML o Shapefile para personalizar el análisis"
    )
    
    st.markdown("---")
    st.header("⚙️ Parámetros de Análisis")
    
    simulation_method = st.selectbox(
        "Método de simulación",
        ["Basado en área", "Basado en elevación", "Aleatorio"]
    )
    
    num_areas = st.slider("Número de áreas", 1, 15, 8)
    num_species = st.slider("Especies máx.", 5, 30, 12)
    
    st.markdown("---")
    st.header("🎨 Visualización")
    
    show_3d = st.checkbox("Mostrar visualización 3D LiDAR", value=True)
    show_species_map = st.checkbox("Mostrar mapa de especies", value=True)

# Inicializar clases
analyzer = BiodiversityAnalyzer()
visualizer = MapVisualizer()

# Mostrar información de ubicación
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ubicación", f"{center_lat:.4f}, {center_lon:.4f}")
with col2:
    st.metric("Áreas de estudio", num_areas)
with col3:
    st.metric("Método", simulation_method)

# Ejecutar análisis
if st.button("🚀 Ejecutar Análisis Completo", type="primary", use_container_width=True):
    
    with st.spinner("Generando datos geoespaciales y calculando métricas..."):
        # Generar ubicaciones de muestreo
        locations = analyzer.generate_sample_locations(center_lat, center_lon, num_areas)
        
        # Simular datos LiDAR
        lidar_data = analyzer.simulate_lidar_data(locations)
        
        # Simular datos de especies
        species_data = analyzer.simulate_species_data(
            locations, 
            method=simulation_method,
            max_species=num_species
        )
        
        # Calcular métricas de biodiversidad
        results = analyzer.analyze_biodiversity(species_data)
    
    # Mostrar métricas principales
    st.subheader("📊 Métricas de Biodiversidad")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics_config = {
        'shannon_index': ("Índice de Shannon", "%.3f"),
        'species_richness': ("Riqueza", "%d"),
        'total_abundance': ("Abundancia", "%,d"),
        'evenness': ("Equitatividad", "%.3f"),
        'simpson_index': ("Índice Simpson", "%.3f")
    }
    
    for i, (key, (name, fmt)) in enumerate(metrics_config.items()):
        with [col1, col2, col3, col4, col5][i]:
            st.metric(name, fmt % results[key])
    
    # Interpretación del índice de Shannon
    shannon_value = results['shannon_index']
    if shannon_value < 1.0:
        diversity_level = "Baja diversidad"
        diversity_color = "red"
    elif shannon_value < 3.0:
        diversity_level = "Diversidad moderada"
        diversity_color = "orange"
    else:
        diversity_level = "Alta diversidad"
        diversity_color = "green"
    
    st.info(f"**Interpretación del Índice de Shannon ({shannon_value:.3f}):** "
            f":{diversity_color}[**{diversity_level}**]")
    
    # SECCIÓN DE MAPAS
    st.subheader("🗺️ Visualizaciones Geoespaciales")
    
    # Mapa principal de biodiversidad
    st.markdown("#### 📍 Mapa de Biodiversidad - ESRI Satellite")
    biodiversity_map = visualizer.create_biodiversity_map(species_data, center_lat, center_lon)
    st_folium(biodiversity_map, width=1200, height=500)
    
    # Visualización 3D LiDAR
    if show_3d:
        st.markdown("#### 🌳 Visualización 3D - Datos LiDAR Simulados")
        deck = visualizer.create_3d_visualization(lidar_data, species_data)
        st.pydeck_chart(deck, use_container_width=True)
        
        with st.expander("ℹ️ Información LiDAR"):
            st.markdown("""
            **Datos LiDAR simulados incluyen:**
            - **Elevación del terreno**: Modelo digital del terreno
            - **Altura de vegetación**: Estructura vertical del bosque
            - **Intensidad**: Reflectancia de la superficie
            - **Puntos 3D**: Nube de puntos para análisis estructural
            """)
    
    # Mapa de distribución de especies
    if show_species_map:
        st.markdown("#### 🌿 Mapa de Distribución de Especies")
        species_map = visualizer.create_species_distribution_map(species_data)
        st.plotly_chart(species_map, use_container_width=True)
    
    # Tablas de datos
    st.subheader("📋 Datos Detallados")
    
    tab1, tab2, tab3 = st.tabs(["Especies", "Áreas de Estudio", "Datos LiDAR"])
    
    with tab1:
        df_species = pd.DataFrame(species_data)
        species_summary = df_species.groupby('species').agg({
            'abundance': 'sum',
            'frequency': 'mean',
            'area_id': 'nunique'
        }).reset_index()
        species_summary.columns = ['Especie', 'Abundancia Total', 'Frecuencia Promedio', 'Áreas Presente']
        species_summary = species_summary.sort_values('Abundancia Total', ascending=False)
        
        st.dataframe(species_summary, use_container_width=True)
    
    with tab2:
        areas_df = pd.DataFrame(locations)
        st.dataframe(areas_df, use_container_width=True)
    
    with tab3:
        st.dataframe(lidar_data.head(100), use_container_width=True)  # Mostrar solo primeros 100 puntos
    
    # Exportar resultados
    st.subheader("💾 Exportar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_species = pd.DataFrame(species_data).to_csv(index=False)
        st.download_button(
            "📥 Datos de Especies (CSV)",
            csv_species,
            "datos_especies.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        csv_areas = pd.DataFrame(locations).to_csv(index=False)
        st.download_button(
            "📊 Ubicaciones (CSV)",
            csv_areas,
            "ubicaciones_areas.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col3:
        csv_lidar = lidar_data.to_csv(index=False)
        st.download_button(
            "🌳 Datos LiDAR (CSV)",
            csv_lidar,
            "datos_lidar.csv",
            "text/csv",
            use_container_width=True
        )

else:
    # Mensaje inicial
    st.markdown("""
    ### 🌍 Atlas de Biodiversidad Avanzado
    
    **Nuevas funcionalidades implementadas:**
    
    🗺️ **Mapas Interactivos**
    - Base ESRI Satellite de alta resolución
    - Mapas de distribución de especies
    - Visualización de riqueza por área
    
    🌳 **Visualización 3D con LiDAR**
    - Modelado de elevación del terreno
    - Estructura de vegetación en 3D
    - Nube de puntos interactiva
    
    📊 **Análisis Geoespacial**
    - Ubicaciones realistas de muestreo
    - Influencia de elevación en biodiversidad
    - Mapas de calor de distribución
    
    **🎯 Cómo usar:**
    1. Selecciona ubicación en el panel lateral
    2. Configura parámetros de análisis
    3. Haz clic en "Ejecutar Análisis Completo"
    4. Explora los mapas y visualizaciones 3D
    
    **🔍 Datos incluidos:**
    - Simulación LiDAR realista
    - Modelos de elevación digital
    - Distribución espacial de especies
    - Métricas de biodiversidad geo-referenciadas
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'>"
    "🌿 <b>Atlas de Biodiversidad Avanzado</b> | "
    "ESRI Satellite 🗺️ | LiDAR 3D 🌳 | "
    "Streamlit 🚀"
    "</div>",
    unsafe_allow_html=True
)
