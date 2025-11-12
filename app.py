import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
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
**Versión optimizada para Streamlit Cloud**
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
    
    def simulate_species_data(self, area_count, method="Basado en área", max_species=15):
        """Simula datos de especies basados en datos geográficos"""
        species_data = []
        
        # Seleccionar especies del pool
        selected_species = np.random.choice(
            self.species_pool, 
            size=min(max_species, len(self.species_pool)), 
            replace=False
        )
        
        for area_idx in range(area_count):
            for species in selected_species:
                # Calcular abundancia basada en el método seleccionado
                if method == "Basado en área":
                    abundance = self._area_based_abundance(species, area_idx)
                elif method == "Basado en tipo de vegetación":
                    abundance = self._vegetation_based_abundance(species, area_idx)
                else:  # Aleatorio
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
    
    def _vegetation_based_abundance(self, species, area_idx):
        """Abundancia basada en tipo de vegetación (simulado)"""
        # Simular diferentes tipos de vegetación
        vegetation_types = ['Bosque denso', 'Bosque abierto', 'Matorral', 'Herbazal']
        vegetation = vegetation_types[area_idx % len(vegetation_types)]
        
        vegetation_preferences = {
            'Bosque denso': ['Fagus sylvatica', 'Quercus robur', 'Acer pseudoplatanus'],
            'Bosque abierto': ['Pinus sylvestris', 'Quercus ilex', 'Juniperus communis'],
            'Matorral': ['Crataegus monogyna', 'Rubus fruticosus', 'Corylus avellana'],
            'Herbazal': ['Herbáceas diversas']
        }
        
        # Especies preferentes tienen mayor abundancia
        preferred_species = vegetation_preferences.get(vegetation, [])
        if species in preferred_species:
            base_abundance = np.random.poisson(40) + 20
        else:
            base_abundance = np.random.poisson(15) + 5
            
        return max(1, base_abundance)
    
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
                'simpson_index': 0
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

class FileProcessor:
    """Procesador de archivos KML y ZIP"""
    
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
        
        areas_detected = max(placemark_count, polygon_count, 1)
        st.info(f"🔍 Detectadas {areas_detected} áreas en el archivo KML")
        return areas_detected
    
    def _process_zip(self, uploaded_file):
        """Procesa ZIP de forma básica"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                shp_files = [f for f in file_list if f.endswith('.shp')]
                
                if shp_files:
                    areas_detected = len(shp_files) * 3  # Estimación
                    st.info(f"🔍 Detectado Shapefile con {len(shp_files)} componentes. Estimando {areas_detected} áreas.")
                else:
                    areas_detected = max(len(file_list), 3)
                    st.info(f"🔍 Archivo ZIP con {len(file_list)} archivos. Estimando {areas_detected} áreas.")
                
                return areas_detected
        except Exception as e:
            st.warning(f"Error leyendo ZIP: {e}")
            return 3
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
        ["Basado en área", "Basado en tipo de vegetación", "Aleatorio"]
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
        max_value=20,
        value=5
    )
    
    st.markdown("---")
    st.header("📊 Métricas")
    st.info("""
    - **Índice de Shannon**: Diversidad de especies
    - **Riqueza**: Número de especies
    - **Abundancia**: Total de individuos
    - **Equitatividad**: Distribución uniforme
    """)

# Inicializar analizador y procesador
analyzer = BiodiversityAnalyzer()
processor = FileProcessor()

# Determinar número de áreas
if uploaded_file:
    with st.spinner("Analizando archivo..."):
        area_count = processor.process_uploaded_file(uploaded_file)
    st.success(f"📊 Archivo procesado: {uploaded_file.name}")
else:
    area_count = manual_areas
    st.info(f"🔬 Usando {area_count} áreas de ejemplo")

# Mostrar información del análisis
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Áreas de estudio", area_count)
with col2:
    st.metric("Método de simulación", simulation_method)
with col3:
    st.metric("Especies máx.", num_species)

# Ejecutar análisis
if st.button("🚀 Ejecutar Análisis de Biodiversidad", type="primary", use_container_width=True):
    with st.spinner("Calculando métricas de biodiversidad..."):
        # Simular datos de especies
        species_data = analyzer.simulate_species_data(
            area_count, 
            method=simulation_method,
            max_species=num_species
        )
        
        # Calcular métricas
        results = analyzer.analyze_biodiversity(species_data)
    
    # Mostrar métricas principales
    st.subheader("📈 Métricas Principales de Biodiversidad")
    
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
    
    # Mostrar tabla de especies
    st.subheader("📊 Datos Detallados de Especies")
    df_species = pd.DataFrame(results['species_data'])
    
    # Resumen por especie
    species_summary = df_species.groupby('species').agg({
        'abundance': 'sum',
        'frequency': 'mean',
        'area': 'count'
    }).reset_index()
    species_summary.columns = ['Especie', 'Abundancia Total', 'Frecuencia Promedio', 'Áreas Presente']
    species_summary = species_summary.sort_values('Abundancia Total', ascending=False)
    
    st.dataframe(
        species_summary,
        use_container_width=True,
        hide_index=True
    )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Abundancia por Especie")
        top_species = species_summary.head(10)
        st.bar_chart(top_species.set_index('Especie')['Abundancia Total'])
    
    with col2:
        st.subheader("📊 Distribución por Áreas")
        area_summary = df_species.groupby('area')['abundance'].sum().reset_index()
        st.bar_chart(area_summary.set_index('area')['abundance'])
    
    # Información detallada
    with st.expander("📋 Información Detallada de los Indicadores"):
        st.markdown("""
        ### Índice de Shannon-Wiener (H')
        **Fórmula**: H' = -Σ(p_i × ln(p_i))
        
        **Interpretación**:
        - **0-1**: Baja diversidad - Pocas especies dominantes
        - **1-3**: Diversidad moderada - Equilibrio moderado entre especies  
        - **>3**: Alta diversidad - Múltiples especies bien distribuidas
        
        ### Riqueza de Especies (S)
        - Número total de especies diferentes en el área de estudio
        - No considera la abundancia de cada especie
        
        ### Equitatividad de Pielou (J')
        **Fórmula**: J' = H' / ln(S)
        - Mide qué tan uniforme es la distribución de individuos entre especies
        - **Rango**: 0-1 (1 = distribución perfectamente uniforme)
        
        ### Índice de Simpson (λ)
        **Fórmula**: λ = Σ(p_i²)
        - Mide la probabilidad de que dos individuos tomados al azar sean de la misma especie
        - Valores más altos indican menor diversidad
        
        ### Metodología LE.MU
        Esta aplicación sigue la metodología de [LE.MU Atlas](https://www.le.mu/atlas/) 
        incorporando el Índice de Shannon para el análisis de biodiversidad.
        Los datos se simulan basándose en las características del área de estudio.
        """)
    
    # Exportar resultados
    st.subheader("💾 Exportar Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Convertir a CSV
        csv_data = df_species.to_csv(index=False)
        st.download_button(
            label="📥 Descargar datos completos (CSV)",
            data=csv_data,
            file_name="datos_biodiversidad_completos.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Resumen en CSV
        summary_csv = species_summary.to_csv(index=False)
        st.download_button(
            label="📊 Descargar resumen por especie (CSV)",
            data=summary_csv,
            file_name="resumen_especies.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    # Mensaje inicial
    st.markdown("""
    ### 👋 ¡Bienvenido al Atlas de Biodiversidad!
    
    Esta aplicación te permite analizar métricas de biodiversidad usando la metodología 
    LE.MU Atlas + Índice de Shannon de forma completamente online.
    
    **🎯 ¿Cómo funciona?**
    1. **📁 Opcional**: Sube un archivo KML o Shapefile (ZIP) para personalizar el análisis
    2. **⚙️ Configura** los parámetros en la barra lateral
    3. **🚀 Haz clic** en "Ejecutar Análisis de Biodiversidad"
    4. **📊 Explora** los resultados y métricas calculadas
    
    **📁 Formatos soportados:**
    - **KML** (archivos de Google Earth)
    - **Shapefile** (comprimido en ZIP, debe incluir .shp, .shx, .dbf)
    
    **📊 Métricas calculadas:**
    - 🌿 **Índice de Shannon-Wiener** - Diversidad de especies
    - 🔢 **Riqueza de especies** - Número de especies diferentes
    - 📈 **Abundancia total** - Número total de individuos
    - ⚖️ **Equitatividad** - Distribución uniforme entre especies
    - 📊 **Índice de Simpson** - Probabilidad de encuentro de misma especie
    
    **🔍 Nota importante:** 
    Esta versión utiliza datos ecológicos simulados basados en las características 
    de tu área de estudio. Para análisis con datos reales de campo, contacta con 
    especialistas en biodiversidad.
    
    **🌍 Metodología basada en:** [LE.MU Atlas](https://www.le.mu/atlas/)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'>"
    "🌿 <b>Atlas de Biodiversidad</b> | "
    "Metodología LE.MU Atlas | "
    "Desarrollado con Streamlit 🚀"
    "</div>",
    unsafe_allow_html=True
)
