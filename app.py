import streamlit as st
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
st.title("🌿 Atlas de Biodiversidad")
st.markdown("""
Análisis de biodiversidad usando la metodología LE.MU + Índice de Shannon
**Versión ultra-compatible - Sin dependencias externas problemáticas**
""")

class BiodiversityAnalyzer:
    """Analizador de biodiversidad sin dependencias externas"""
    
    def __init__(self):
        self.species_pool = [
            'Quercus robur', 'Fagus sylvatica', 'Pinus sylvestris', 
            'Acer pseudoplatanus', 'Betula pendula', 'Alnus glutinosa',
            'Pinus pinaster', 'Quercus ilex', 'Quercus suber',
            'Juniperus communis', 'Castanea sativa', 'Populus nigra'
        ]
    
    def shannon_index(self, abundances):
        """Calcula el índice de Shannon-Wiener"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        
        proportions = [abundance / total for abundance in abundances if abundance > 0]
        return -sum(p * math.log(p) for p in proportions)
    
    def species_richness(self, abundances):
        """Calcula la riqueza de especies"""
        return sum(1 for abundance in abundances if abundance > 0)
    
    def evenness(self, shannon_index, species_richness):
        """Calcula la equitatividad de Pielou"""
        if species_richness <= 1:
            return 1.0
        return shannon_index / math.log(species_richness)
    
    def simpson_index(self, abundances):
        """Calcula el índice de Simpson"""
        total = sum(abundances)
        if total == 0:
            return 0.0
        return sum((abundance / total) ** 2 for abundance in abundances)
    
    def generate_sample_data(self, num_areas, num_species, method="Basado en área"):
        """Genera datos de muestra para el análisis"""
        species_data = []
        locations = []
        
        # Seleccionar especies
        selected_species = random.sample(
            self.species_pool, 
            min(num_species, len(self.species_pool))
        )
        
        # Generar ubicaciones (coordenadas simuladas alrededor de Madrid)
        base_lat, base_lon = 40.4168, -3.7038
        
        for area_id in range(1, num_areas + 1):
            # Variación en coordenadas
            lat = base_lat + random.uniform(-0.1, 0.1)
            lon = base_lon + random.uniform(-0.1, 0.1)
            elevation = random.randint(200, 1000)
            area_hectares = random.uniform(10, 100)
            
            locations.append({
                'area_id': area_id,
                'lat': lat,
                'lon': lon,
                'elevation': elevation,
                'area_hectares': area_hectares
            })
            
            # Generar datos de especies para esta área
            for species in selected_species:
                if method == "Basado en área":
                    abundance = self._area_based_abundance(species, area_hectares, elevation)
                elif method == "Basado en elevación":
                    abundance = self._elevation_based_abundance(species, elevation)
                else:
                    abundance = self._random_abundance(species)
                
                species_data.append({
                    'species': species,
                    'abundance': abundance,
                    'frequency': round(random.uniform(0.1, 1.0), 2),
                    'area_id': area_id,
                    'lat': lat,
                    'lon': lon,
                    'elevation': elevation,
                    'area_hectares': round(area_hectares, 1)
                })
        
        return species_data, locations
    
    def _area_based_abundance(self, species, area_hectares, elevation):
        """Abundancia basada en área y elevación"""
        base_abundance = {
            'Quercus robur': 50, 'Fagus sylvatica': 40, 'Pinus sylvestris': 60,
            'Acer pseudoplatanus': 30, 'Betula pendula': 35, 'Alnus glutinosa': 25,
            'Pinus pinaster': 55, 'Quercus ilex': 45, 'Quercus suber': 40,
            'Juniperus communis': 20, 'Castanea sativa': 35, 'Populus nigra': 30
        }
        
        base = base_abundance.get(species, 25)
        area_factor = area_hectares / 50  # Normalizar a 50 hectáreas
        elevation_factor = 1 + (elevation - 600) / 1000  # Ajuste por elevación
        
        return max(1, int(base * area_factor * elevation_factor * random.uniform(0.7, 1.3)))
    
    def _elevation_based_abundance(self, species, elevation):
        """Abundancia basada en preferencias de elevación"""
        # Especies de baja elevación
        low_elevation = ['Quercus suber', 'Quercus ilex']
        # Especies de media elevación
        mid_elevation = ['Quercus robur', 'Fagus sylvatica', 'Acer pseudoplatanus']
        # Especies de alta elevación
        high_elevation = ['Pinus sylvestris', 'Juniperus communis', 'Betula pendula']
        
        if species in low_elevation and elevation < 400:
            base = 60
        elif species in mid_elevation and 400 <= elevation <= 800:
            base = 50
        elif species in high_elevation and elevation > 800:
            base = 55
        else:
            base = 20
        
        return max(1, int(base * random.uniform(0.5, 1.5)))
    
    def _random_abundance(self, species):
        """Abundancia aleatoria"""
        return random.randint(5, 100)
    
    def analyze_biodiversity(self, species_data):
        """Analiza biodiversidad a partir de datos de especies"""
        if not species_data:
            return {
                'shannon_index': 0,
                'species_richness': 0,
                'total_abundance': 0,
                'evenness': 0,
                'simpson_index': 0
            }
        
        # Agrupar abundancias por especie
        species_abundances = {}
        for record in species_data:
            species = record['species']
            abundance = record['abundance']
            if species in species_abundances:
                species_abundances[species] += abundance
            else:
                species_abundances[species] = abundance
        
        abundances = list(species_abundances.values())
        
        # Calcular métricas
        shannon = self.shannon_index(abundances)
        richness = self.species_richness(abundances)
        total_abundance = sum(abundances)
        evenness_val = self.evenness(shannon, richness)
        simpson = self.simpson_index(abundances)
        
        return {
            'shannon_index': shannon,
            'species_richness': richness,
            'total_abundance': total_abundance,
            'evenness': evenness_val,
            'simpson_index': simpson,
            'species_data': species_data
        }

class DataVisualizer:
    """Visualizador de datos sin dependencias externas"""
    
    def display_metrics(self, results):
        """Muestra métricas en formato atractivo"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Índice de Shannon",
                f"{results['shannon_index']:.3f}",
                help="Diversidad de especies (0=baja, >3=alta)"
            )
        
        with col2:
            st.metric(
                "Riqueza de Especies",
                results['species_richness'],
                help="Número total de especies diferentes"
            )
        
        with col3:
            st.metric(
                "Abundancia Total",
                f"{results['total_abundance']:,}",
                help="Número total de individuos"
            )
        
        with col4:
            st.metric(
                "Equitatividad",
                f"{results['evenness']:.3f}",
                help="Distribución uniforme entre especies (0-1)"
            )
        
        with col5:
            st.metric(
                "Índice Simpson",
                f"{results['simpson_index']:.3f}",
                help="Probabilidad de encuentro misma especie"
            )
    
    def create_species_chart(self, species_data):
        """Crea un gráfico de barras simple para especies"""
        if not species_data:
            return
        
        # Calcular abundancia total por especie
        species_totals = {}
        for record in species_data:
            species = record['species']
            abundance = record['abundance']
            if species in species_totals:
                species_totals[species] += abundance
            else:
                species_totals[species] = abundance
        
        # Ordenar especies por abundancia
        sorted_species = sorted(species_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Mostrar como gráfico de barras simple con st.bar_chart
        if sorted_species:
            species_names = [s[0] for s in sorted_species[:10]]  # Top 10
            species_abundances = [s[1] for s in sorted_species[:10]]
            
            # Crear DataFrame simple para el gráfico
            chart_data = {"Especies": species_names, "Abundancia": species_abundances}
            
            st.subheader("📊 Especies Más Abundantes")
            st.bar_chart(data=chart_data, x="Especies", y="Abundancia")
    
    def create_location_map(self, locations):
        """Crea un mapa simple usando st.map"""
        if not locations:
            return
        
        # Preparar datos para el mapa
        map_data = []
        for loc in locations:
            map_data.append({
                'lat': loc['lat'],
                'lon': loc['lon'],
                'area_id': loc['area_id'],
                'elevation': loc['elevation']
            })
        
        st.subheader("🗺️ Ubicaciones de Muestreo")
        st.map(map_data, zoom=9)
    
    def display_species_table(self, species_data):
        """Muestra tabla de especies"""
        if not species_data:
            return
        
        # Crear resumen por especie
        species_summary = {}
        for record in species_data:
            species = record['species']
            if species not in species_summary:
                species_summary[species] = {
                    'abundance': 0,
                    'areas': set(),
                    'frequency_sum': 0,
                    'count': 0
                }
            
            species_summary[species]['abundance'] += record['abundance']
            species_summary[species]['areas'].add(record['area_id'])
            species_summary[species]['frequency_sum'] += record['frequency']
            species_summary[species]['count'] += 1
        
        # Preparar datos para la tabla
        table_data = []
        for species, data in species_summary.items():
            table_data.append({
                'Especie': species,
                'Abundancia Total': data['abundance'],
                'Áreas Presente': len(data['areas']),
                'Frecuencia Promedio': round(data['frequency_sum'] / data['count'], 2)
            })
        
        # Ordenar por abundancia
        table_data.sort(key=lambda x: x['Abundancia Total'], reverse=True)
        
        st.subheader("📋 Resumen por Especie")
        
        # Mostrar tabla usando st.dataframe
        import pandas as pd
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def display_locations_table(self, locations):
        """Muestra tabla de ubicaciones"""
        if not locations:
            return
        
        st.subheader("📍 Áreas de Estudio")
        
        # Preparar datos para la tabla
        table_data = []
        for loc in locations:
            table_data.append({
                'Área ID': loc['area_id'],
                'Latitud': round(loc['lat'], 4),
                'Longitud': round(loc['lon'], 4),
                'Elevación (m)': loc['elevation'],
                'Área (ha)': round(loc['area_hectares'], 1)
            })
        
        # Mostrar tabla
        import pandas as pd
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración del Análisis")
    
    # Parámetros básicos
    num_areas = st.slider(
        "Número de áreas de estudio",
        min_value=1,
        max_value=20,
        value=8,
        help="Cantidad de áreas geográficas a analizar"
    )
    
    num_species = st.slider(
        "Número máximo de especies",
        min_value=5,
        max_value=20,
        value=10,
        help="Límite de especies diferentes a considerar"
    )
    
    simulation_method = st.selectbox(
        "Método de simulación",
        [
            "Basado en área",
            "Basado en elevación", 
            "Aleatorio"
        ],
        help="Cómo se calcula la abundancia de especies"
    )
    
    st.markdown("---")
    st.header("📊 Visualización")
    
    show_map = st.checkbox("Mostrar mapa de ubicaciones", value=True)
    show_charts = st.checkbox("Mostrar gráficos de especies", value=True)
    show_tables = st.checkbox("Mostrar tablas detalladas", value=True)
    
    st.markdown("---")
    st.header("💡 Información")
    st.info("""
    Esta versión utiliza datos simulados 
    basados en parámetros ecológicos 
    realistas para la península ibérica.
    """)

# Inicializar analizador y visualizador
analyzer = BiodiversityAnalyzer()
visualizer = DataVisualizer()

# Título principal
st.subheader("🎯 Configuración Actual")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Áreas de Estudio", num_areas)
with col2:
    st.metric("Especies Máx.", num_species)
with col3:
    st.metric("Método", simulation_method)

# Botón de ejecución
if st.button("🚀 Ejecutar Análisis de Biodiversidad", type="primary", use_container_width=True):
    
    with st.spinner("Generando datos y calculando métricas de biodiversidad..."):
        # Generar datos de muestra
        species_data, locations = analyzer.generate_sample_data(
            num_areas=num_areas,
            num_species=num_species,
            method=simulation_method
        )
        
        # Analizar biodiversidad
        results = analyzer.analyze_biodiversity(species_data)
    
    # Mostrar resultados
    st.subheader("📈 Resultados del Análisis")
    visualizer.display_metrics(results)
    
    # Interpretación del índice de Shannon
    shannon_value = results['shannon_index']
    if shannon_value < 1.0:
        diversity_level = "Baja diversidad"
        diversity_color = "🔴"
        interpretation = "Pocas especies dominantes en el ecosistema"
    elif shannon_value < 3.0:
        diversity_level = "Diversidad moderada"
        diversity_color = "🟡"
        interpretation = "Equilibrio moderado entre múltiples especies"
    else:
        diversity_level = "Alta diversidad"
        diversity_color = "🟢"
        interpretation = "Múltiples especies bien distribuidas"
    
    st.info(f"""
    **{diversity_color} Interpretación del Índice de Shannon ({shannon_value:.3f}): {diversity_level}**
    
    *{interpretation}*
    """)
    
    # Visualizaciones
    if show_map:
        visualizer.create_location_map(locations)
    
    if show_charts:
        visualizer.create_species_chart(species_data)
    
    if show_tables:
        tab1, tab2 = st.tabs(["🌿 Especies", "📍 Áreas"])
        
        with tab1:
            visualizer.display_species_table(species_data)
        
        with tab2:
            visualizer.display_locations_table(locations)
    
    # Exportar datos
    st.subheader("💾 Exportar Resultados")
    
    if species_data and locations:
        col1, col2 = st.columns(2)
        
        with col1:
            # Exportar datos de especies
            import pandas as pd
            species_df = pd.DataFrame(species_data)
            csv_species = species_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar Datos de Especies (CSV)",
                data=csv_species,
                file_name=f"especies_biodiversidad_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Exportar ubicaciones
            locations_df = pd.DataFrame(locations)
            csv_locations = locations_df.to_csv(index=False)
            
            st.download_button(
                label="📍 Descargar Ubicaciones (CSV)",
                data=csv_locations,
                file_name=f"ubicaciones_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Información adicional
    with st.expander("📚 Métodología y Explicación de Métricas"):
        st.markdown("""
        ### 🌿 Índice de Shannon-Wiener (H')
        **Fórmula**: H' = -Σ(pᵢ × ln(pᵢ))
        
        Donde:
        - pᵢ = proporción de individuos de la especie i
        - ln = logaritmo natural
        
        **Interpretación**:
        - **0-1.0**: Baja diversidad (pocas especies dominantes)
        - **1.0-3.0**: Diversidad moderada
        - **>3.0**: Alta diversidad (múltiples especies bien distribuidas)
        
        ### 🔢 Riqueza de Especies (S)
        - Número total de especies diferentes en el área de estudio
        - No considera la abundancia relativa
        
        ### ⚖️ Equitatividad de Pielou (J')
        **Fórmula**: J' = H' / ln(S)
        - Mide qué tan uniforme es la distribución de individuos entre especies
        - **Rango**: 0-1 (1 = distribución perfectamente uniforme)
        
        ### 📊 Índice de Simpson (λ)
        **Fórmula**: λ = Σ(pᵢ²)
        - Mide la probabilidad de que dos individuos tomados al azar sean de la misma especie
        - Valores más altos indican menor diversidad
        
        ### 📍 Metodología LE.MU
        Basado en la metodología del [LE.MU Atlas](https://www.le.mu/atlas/)
        con adaptaciones para análisis de biodiversidad terrestre.
        """)

else:
    # Mensaje inicial
    st.markdown("""
    ### 🌍 Bienvenido al Atlas de Biodiversidad
    
    **Análisis científico de biodiversidad con:**
    
    📈 **Métricas Avanzadas**
    - Índice de Shannon-Wiener
    - Riqueza de especies
    - Equitatividad de Pielou  
    - Índice de Simpson
    
    🗺️ **Análisis Geoespacial**
    - Mapa interactivo de ubicaciones
    - Distribución por elevación
    - Áreas de muestreo realistas
    
    📊 **Visualización Completa**
    - Gráficos de especies
    - Tablas detalladas
    - Exportación de datos
    
    **🎯 Cómo proceder:**
    1. Configura los parámetros en el panel lateral
    2. Haz clic en **"Ejecutar Análisis de Biodiversidad"**
    3. Explora los resultados y visualizaciones
    4. Exporta los datos para su análisis posterior
    
    **🔍 Características técnicas:**
    - Datos simulados basados en parámetros ecológicos reales
    - Especies representativas de la península ibérica
    - Métodos de simulación configurables
    - Compatible con todos los navegadores
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9em;'>"
    "🌿 <b>Atlas de Biodiversidad</b> | "
    "Metodología LE.MU Atlas | "
    "Versión Ultra-Compatible | "
    "🚀 Desarrollado con Streamlit"
    "</div>",
    unsafe_allow_html=True
)
