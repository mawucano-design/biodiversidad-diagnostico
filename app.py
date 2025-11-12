import streamlit as st
import pandas as pd
import numpy as np
import math
import random
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
Análisis de biodiversidad con mapas interactivos y visualización 3D
**Versión optimizada para máxima compatibilidad**
""")

class BiodiversityAnalyzer:
    """Analizador completo de biodiversidad con capacidades geoespaciales"""
    
    def __init__(self):
        self.species_pool = [
            'Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris', 
            'Acer pseudoplatanus', 'Betula pendula', 'Alnus glutinosa',
            'Pinus pinaster', 'Quercus ilex', 'Quercus suber',
            'Juniperus communis', 'Castanea sativa', 'Populus nigra',
            'Fraxinus excelsior', 'Ulmus minor', 'Salix alba'
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
            # Variación aleatoria alrededor del punto central
            lat_variation = random.uniform(-0.02, 0.02)
            lon_variation = random.uniform(-0.03, 0.03)
            
            lat = center_lat + lat_variation
            lon = center_lon + lon_variation
            
            # Simular elevación (metros)
            elevation = random.gauss(500, 150)
            
            locations.append({
                'id': i + 1,
                'lat': lat,
                'lon': lon,
                'elevation': max(0, elevation),
                'area_hectares': random.uniform(5, 50)
            })
        
        return locations
    
    def simulate_species_data(self, locations, method="Basado en área", max_species=15):
        """Simula datos de especies basados en ubicaciones geográficas"""
        species_data = []
        
        # Seleccionar especies del pool
        selected_species = random.sample(
            self.species_pool, 
            min(max_species, len(self.species_pool))
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
                    'frequency': round(random.uniform(0.1, 1.0), 3),
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
        area_factor = location['area_hectares'] / 25
        elevation_factor = 1 + (location['elevation'] - 500) / 1000
        
        return max(1, int(base * area_factor * elevation_factor * random.lognormvariate(0, 0.3)))
    
    def _elevation_based_abundance(self, species, location):
        """Abundancia basada en preferencias de elevación"""
        low_elevation_species = ['Quercus suber', 'Olea europaea']
        mid_elevation_species = ['Quercus robur', 'Fagus sylvatica', 'Acer pseudoplatanus']
        high_elevation_species = ['Pinus sylvestris', 'Juniperus communis', 'Betula pendula']
        
        elevation = location['elevation']
        
        if species in low_elevation_species and elevation < 300:
            base = 60
        elif species in mid_elevation_species and 300 <= elevation <= 800:
            base = 50
        elif species in high_elevation_species and elevation > 800:
            base = 55
        else:
            base = 20
        
        return max(1, int(base * random.lognormvariate(0, 0.4)))
    
    def _random_abundance(self, species):
        """Abundancia aleatoria"""
        return random.randint(1, 50)
    
    def analyze_biodiversity(self, species_data):
        """Analiza biodiversidad a partir de datos de especies"""
        if not species_data:
            return {
                'shannon_index': 0,
                'species_richness': 0,
                'total_abundance': 0,
                'evenness': 0,
                'simpson_index': 0,
                'species_data': []
            }
        
        df = pd.DataFrame(species_data)
        
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
    """Clase para visualizaciones geoespaciales simplificadas"""
    
    def create_interactive_map(self, species_data, center_lat, center_lon):
        """Crea un mapa interactivo simple usando Plotly"""
        if not species_data:
            return None
            
        df = pd.DataFrame(species_data)
        
        # Calcular riqueza por área
        richness_by_area = df.groupby('area_id').agg({
            'species': 'nunique',
            'abundance': 'sum',
            'lat': 'first',
            'lon': 'first',
            'elevation': 'first'
        }).reset_index()
        
        # Crear mapa con Plotly
        fig = px.scatter_mapbox(
            richness_by_area,
            lat="lat",
            lon="lon",
            color="species",
            size="abundance",
            hover_name="area_id",
            hover_data={
                "species": True,
                "abundance": True,
                "elevation": True,
                "lat": False,
                "lon": False
            },
            color_continuous_scale=px.colors.sequential.Viridis,
            zoom=10,
            height=600,
            title="Mapa de Biodiversidad - Riqueza por Área"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        return fig
    
    def create_species_distribution_chart(self, species_data):
        """Crea gráfico de distribución de especies"""
        if not species_data:
            return None
            
        df = pd.DataFrame(species_data)
        
        # Top 10 especies más abundantes
        top_species = df.groupby('species')['abundance'].sum().nlargest(10)
        
        fig = px.bar(
            x=top_species.index,
            y=top_species.values,
            title="Top 10 Especies por Abundancia",
            labels={'x': 'Especie', 'y': 'Abundancia Total'},
            color=top_species.values,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        return fig
    
    def create_elevation_chart(self, species_data):
        """Crea gráfico de biodiversidad vs elevación"""
        if not species_data:
            return None
            
        df = pd.DataFrame(species_data)
        
        # Agrupar por área y calcular métricas
        area_metrics = df.groupby('area_id').agg({
            'species': 'nunique',
            'abundance': 'sum',
            'elevation': 'first'
        }).reset_index()
        
        fig = px.scatter(
            area_metrics,
            x="elevation",
            y="species",
            size="abundance",
            color="species",
            hover_name="area_id",
            title="Riqueza de Especies vs Elevación",
            labels={'elevation': 'Elevación (m)', 'species': 'Riqueza de Especies'},
            size_max=20
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
        coords = {
            "Madrid, España (40.4168, -3.7038)": (40.4168, -3.7038),
            "Barcelona, España (41.3851, 2.1734)": (41.3851, 2.1734),
            "Sevilla, España (37.3891, -5.9845)": (37.3891, -5.9845),
            "Valencia, España (39.4699, -0.3763)": (39.4699, -0.3763),
        }
        center_lat, center_lon = coords[location_preset]
    
    st.markdown("---")
    st.header("⚙️ Parámetros de Análisis")
    
    simulation_method = st.selectbox(
        "Método de simulación",
        ["Basado en área", "Basado en elevación", "Aleatorio"]
    )
    
    num_areas = st.slider("Número de áreas", 1, 15, 8)
    num_species = st.slider("Especies máx.", 5, 20, 10)
    
    st.markdown("---")
    st.header("📊 Visualización")
    
    show_species_chart = st.checkbox("Mostrar gráfico de especies", value=True)
    show_elevation_chart = st.checkbox("Mostrar análisis de elevación", value=True)

# Inicializar clases
analyzer = BiodiversityAnalyzer()
visualizer = MapVisualizer()

# Mostrar información de ubicación
st.subheader("🎯 Configuración del Análisis")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📍 Ubicación", f"{center_lat:.4f}, {center_lon:.4f}")
with col2:
    st.metric("📐 Áreas", num_areas)
with col3:
    st.metric("🌿 Especies", num_species)
with col4:
    st.metric("⚙️ Método", simulation_method)

# Ejecutar análisis
if st.button("🚀 Ejecutar Análisis de Biodiversidad", type="primary", use_container_width=True):
    
    with st.spinner("Generando datos y calculando métricas..."):
        # Generar ubicaciones de muestreo
        locations = analyzer.generate_sample_locations(center_lat, center_lon, num_areas)
        
        # Simular datos de especies
        species_data = analyzer.simulate_species_data(
            locations, 
            method=simulation_method,
            max_species=num_species
        )
        
        # Calcular métricas de biodiversidad
        results = analyzer.analyze_biodiversity(species_data)
    
    # Mostrar métricas principales
    st.subheader("📈 Métricas de Biodiversidad")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Índice de Shannon", f"{results['shannon_index']:.3f}")
    with col2:
        st.metric("Riqueza", results['species_richness'])
    with col3:
        st.metric("Abundancia", f"{results['total_abundance']:,}")
    with col4:
        st.metric("Equitatividad", f"{results['evenness']:.3f}")
    with col5:
        st.metric("Índice Simpson", f"{results['simpson_index']:.3f}")
    
    # Interpretación del índice de Shannon
    shannon_value = results['shannon_index']
    if shannon_value < 1.0:
        diversity_level = "Baja diversidad"
        diversity_color = "🔴"
    elif shannon_value < 3.0:
        diversity_level = "Diversidad moderada"
        diversity_color = "🟡"
    else:
        diversity_level = "Alta diversidad"
        diversity_color = "🟢"
    
    st.info(f"**{diversity_color} Interpretación del Índice de Shannon ({shannon_value:.3f}): {diversity_level}**")
    
    # SECCIÓN DE MAPAS Y GRÁFICOS
    st.subheader("🗺️ Visualizaciones")
    
    # Mapa interactivo
    st.markdown("#### 📍 Mapa de Distribución")
    map_fig = visualizer.create_interactive_map(species_data, center_lat, center_lon)
    if map_fig:
        st.plotly_chart(map_fig, use_container_width=True)
    else:
        st.warning("No hay datos para mostrar el mapa")
    
    # Gráficos adicionales
    if show_species_chart or show_elevation_chart:
        col1, col2 = st.columns(2)
        
        with col1:
            if show_species_chart:
                st.markdown("#### 🌿 Distribución de Especies")
                species_chart = visualizer.create_species_distribution_chart(species_data)
                if species_chart:
                    st.plotly_chart(species_chart, use_container_width=True)
        
        with col2:
            if show_elevation_chart:
                st.markdown("#### 🏔️ Biodiversidad vs Elevación")
                elevation_chart = visualizer.create_elevation_chart(species_data)
                if elevation_chart:
                    st.plotly_chart(elevation_chart, use_container_width=True)
    
    # TABLAS DE DATOS
    st.subheader("📋 Datos Detallados")
    
    tab1, tab2 = st.tabs(["📊 Resumen por Especie", "📍 Áreas de Estudio"])
    
    with tab1:
        if species_data:
            df_species = pd.DataFrame(species_data)
            species_summary = df_species.groupby('species').agg({
                'abundance': 'sum',
                'frequency': 'mean',
                'area_id': 'nunique'
            }).reset_index()
            species_summary.columns = ['Especie', 'Abundancia Total', 'Frecuencia Promedio', 'Áreas Presente']
            species_summary = species_summary.sort_values('Abundancia Total', ascending=False)
            
            st.dataframe(species_summary, use_container_width=True)
        else:
            st.info("No hay datos de especies para mostrar")
    
    with tab2:
        if locations:
            areas_df = pd.DataFrame(locations)
            st.dataframe(areas_df, use_container_width=True)
        else:
            st.info("No hay datos de áreas para mostrar")
    
    # EXPORTAR RESULTADOS
    st.subheader("💾 Exportar Resultados")
    
    if species_data and locations:
        col1, col2 = st.columns(2)
        
        with col1:
            csv_species = pd.DataFrame(species_data).to_csv(index=False)
            st.download_button(
                "📥 Descargar Datos de Especies (CSV)",
                csv_species,
                f"biodiversidad_especies_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            csv_areas = pd.DataFrame(locations).to_csv(index=False)
            st.download_button(
                "📍 Descargar Ubicaciones (CSV)",
                csv_areas,
                f"biodiversidad_ubicaciones_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
    
    # INFORMACIÓN ADICIONAL
    with st.expander("📚 Información sobre los Indicadores"):
        st.markdown("""
        ### 🌿 Índice de Shannon-Wiener (H')
        Mide la diversidad de especies considerando tanto la riqueza como la equitatividad.
        
        **Interpretación:**
        - **0-1.0**: Baja diversidad (pocas especies dominantes)
        - **1.0-3.0**: Diversidad moderada
        - **>3.0**: Alta diversidad (múltiples especies bien distribuidas)
        
        ### 🔢 Riqueza de Especies (S)
        Número total de especies diferentes en el área de estudio.
        
        ### ⚖️ Equitatividad de Pielou (J')
        Mide qué tan uniforme es la distribución de individuos entre especies.
        - **Rango**: 0-1 (1 = distribución perfectamente uniforme)
        
        ### 📊 Índice de Simpson (λ)
        Mide la probabilidad de que dos individuos tomados al azar sean de la misma especie.
        - Valores más altos indican menor diversidad
        """)

else:
    # Mensaje inicial
    st.markdown("""
    ### 🌍 Bienvenido al Atlas de Biodiversidad
    
    **Características principales:**
    
    📈 **Análisis Completo de Biodiversidad**
    - Índice de Shannon-Wiener
    - Riqueza de especies
    - Equitatividad de Pielou
    - Índice de Simpson
    
    🗺️ **Visualizaciones Geoespaciales**
    - Mapas interactivos de distribución
    - Análisis por elevación
    - Gráficos de especies principales
    
    📊 **Datos y Exportación**
    - Tablas detalladas interactivas
    - Exportación a CSV
    - Métricas en tiempo real
    
    **🎯 Cómo usar:**
    1. Selecciona la ubicación de estudio
    2. Configura los parámetros en el panel lateral
    3. Haz clic en "Ejecutar Análisis de Biodiversidad"
    4. Explora los resultados y visualizaciones
    
    **📍 Ubicaciones disponibles:**
    - Madrid, Barcelona, Sevilla, Valencia
    - O configura coordenadas personalizadas
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🌿 <b>Atlas de Biodiversidad</b> | "
    "Metodología LE.MU Atlas | "
    "Desarrollado con Streamlit 🚀"
    "</div>",
    unsafe_allow_html=True
)
