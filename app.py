import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from math import log

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
**Versión simplificada - No requiere instalación de librerías geoespaciales**
""")

class SimpleBiodiversityAnalyzer:
    """Analizador simplificado de biodiversidad sin dependencias complejas"""
    
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
        return -sum(p * log(p) for p in proportions)
    
    def species_richness(self, abundances):
        """Calcula la riqueza de especies"""
        return sum(1 for abundance in abundances if abundance > 0)
    
    def evenness(self, shannon_index, species_richness):
        """Calcula la equitatividad de Pielou"""
        if species_richness <= 1:
            return 1.0
        return shannon_index / log(species_richness)
    
    def simulate_species_data(self, area_count, method="Basado en área", max_species=15):
        """Simula datos de especies"""
        species_data = []
        
        # Seleccionar especies del pool
        selected_species = np.random.choice(
            self.species_pool, 
            size=min(max_species, len(self.species_pool)), 
            replace=False
        )
        
        for area_idx in range(area_count):
            for species in selected_species:
                # Calcular abundancia
                if method == "Basado en área":
                    abundance = self._area_based_abundance(species, area_idx)
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
        """Abundancia basada en área"""
        base_abundance = {
            'Quercus robur': 50, 'Fagus sylvatica': 40, 'Pinus sylvestris': 60,
            'Acer pseudoplatanus': 30, 'Betula pendula': 35, 'Alnus glutinosa': 25
        }
        base = base_abundance.get(species, 20)
        return max(1, int(base * (area_idx + 1) * np.random.lognormal(0, 0.5)))
    
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
                'evenness': 0
            }
        
        # Agrupar por especie y sumar abundancias
        species_abundances = df.groupby('species')['abundance'].sum().values
        
        # Calcular métricas
        shannon = self.shannon_index(species_abundances)
        richness = self.species_richness(species_abundances)
        total_abundance = sum(species_abundances)
        evenness_val = self.evenness(shannon, richness)
        
        return {
            'shannon_index': shannon,
            'species_richness': richness,
            'total_abundance': total_abundance,
            'evenness': evenness_val
        }

class SimpleFileProcessor:
    """Procesador simplificado de archivos"""
    
    def process_uploaded_file(self, uploaded_file):
        """Procesa archivo subido y devuelve número de áreas"""
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
                return 3  # Valor por defecto
        except Exception as e:
            st.warning(f"Error procesando archivo: {e}. Usando datos de ejemplo.")
            return 3  # Valor por defecto
    
    def _process_kml(self, uploaded_file):
        """Procesa KML de forma básica"""
        content = uploaded_file.getvalue().decode('utf-8')
        
        # Contar ocurrencias de <Placemark> como proxy de número de áreas
        placemark_count = content.count('<Placemark>')
        polygon_count = content.count('<Polygon>')
        
        return max(placemark_count, polygon_count, 1)
    
    def _process_zip(self, uploaded_file):
        """Procesa ZIP de forma básica"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                # Estimación simple basada en número de archivos
                return max(len([f for f in file_list if f.endswith('.shp')]) * 5, 3)
        finally:
            os.unlink(tmp_path)

# Sidebar para carga de archivos
with st.sidebar:
    st.header("📁 Cargar Datos")
    
    uploaded_file = st.file_uploader(
        "Sube tu archivo geográfico (opcional)",
        type=['kml', 'zip'],
        help="Formatos soportados: KML, Shapefile (ZIP). Si no subes archivo, usaremos datos de ejemplo."
    )
    
    st.markdown("---")
    st.header("⚙️ Parámetros de Análisis")
    
    # Parámetros configurables
    simulation_method = st.selectbox(
        "Método de simulación",
        ["Basado en área", "Aleatorio"]
    )
    
    num_species = st.slider(
        "Número máximo de especies",
        min_value=5,
        max_value=30,
        value=12
    )
    
    manual_areas = st.slider(
        "Número de áreas (si no subes archivo)",
        min_value=1,
        max_value=10,
        value=3
    )

# Inicializar analizador y procesador
analyzer = SimpleBiodiversityAnalyzer()
processor = SimpleFileProcessor()

# Determinar número de áreas
if uploaded_file:
    with st.spinner("Analizando archivo..."):
        area_count = processor.process_uploaded_file(uploaded_file)
    st.success(f"📊 Archivo procesado: {uploaded_file.name} ({area_count} áreas detectadas)")
else:
    area_count = manual_areas
    st.info(f"🔬 Usando {area_count} áreas de ejemplo")

# Ejecutar análisis
if st.button("🚀 Ejecutar Análisis de Biodiversidad", type="primary"):
    with st.spinner("Calculando métricas de biodiversidad..."):
        # Simular datos de especies
        species_data = analyzer.simulate_species_data(
            area_count, 
            method=simulation_method,
            max_species=num_species
        )
        
        # Calcular métricas
        results = analyzer.analyze_biodiversity(species_data)
    
    # Mostrar métricas
    st.subheader("📈 Métricas de Biodiversidad")
    
    col1, col2, col3, col4 = st.columns(4)
    
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
    
    # Mostrar tabla de especies
    st.subheader("📊 Datos de Especies")
    df_species = pd.DataFrame(species_data)
    st.dataframe(
        df_species,
        use_container_width=True,
        hide_index=True
    )
    
    # Gráfico de abundancia
    st.subheader("📈 Distribución de Abundancia por Especie")
    
    # Preparar datos para el gráfico
    species_summary = df_species.groupby('species')['abundance'].sum().reset_index()
    species_summary = species_summary.sort_values('abundance', ascending=False)
    
    # Mostrar gráfico de barras
    st.bar_chart(species_summary.set_index('species')['abundance'])
    
    # Información detallada
    with st.expander("📋 Información Detallada de los Indicadores"):
        st.markdown("""
        ### Índice de Shannon-Wiener (H')
        - **Fórmula**: H' = -Σ(p_i × ln(p_i))
        - **Interpretación**:
          - 0-1: Baja diversidad
          - 1-3: Diversidad moderada  
          - >3: Alta diversidad
        
        ### Riqueza de Especies (S)
        - Número total de especies diferentes en el área
        
        ### Equitatividad (J')
        - J' = H' / ln(S)
        - Mide qué tan uniforme es la distribución de individuos
        - Rango: 0-1 (1 = distribución perfectamente uniforme)
        
        ### Metodología
        Esta aplicación sigue la metodología de [LE.MU Atlas](https://www.le.mu/atlas/) 
        incorporando el Índice de Shannon para el análisis de biodiversidad.
        """)
    
    # Exportar resultados
    st.subheader("💾 Exportar Resultados")
    
    # Convertir a CSV
    csv_data = df_species.to_csv(index=False)
    st.download_button(
        label="📥 Descargar datos de especies (CSV)",
        data=csv_data,
        file_name="datos_biodiversidad.csv",
        mime="text/csv"
    )

else:
    # Mensaje inicial
    st.markdown("""
    ### 👋 ¡Bienvenido al Atlas de Biodiversidad!
    
    Esta aplicación te permite analizar métricas de biodiversidad usando la metodología 
    LE.MU Atlas + Índice de Shannon.
    
    **¿Cómo funciona?**
    1. **Opcional**: Sube un archivo KML o Shapefile (ZIP)
    2. Configura los parámetros de análisis en la barra lateral
    3. Haz clic en "Ejecutar Análisis de Biodiversidad"
    4. Explora los resultados y métricas
    
    **📁 Formatos soportados:**
    - **KML** (archivos de Google Earth)
    - **Shapefile** (comprimido en ZIP)
    
    **📊 Métricas calculadas:**
    - Índice de Shannon-Wiener
    - Riqueza de especies
    - Abundancia total
    - Equitatividad de Pielou
    
    **🔍 Nota:** Esta versión utiliza datos simulados basados en las características 
    de tu archivo geográfico. Para análisis con datos reales, contacta con los 
    especialistas en biodiversidad.
    """)

# Footer
st.markdown("---")
st.markdown(
    "🌿 **Atlas de Biodiversidad** | "
    "Metodología basada en [LE.MU Atlas](https://www.le.mu/atlas/) | "
    "Desarrollado con Streamlit"
)
