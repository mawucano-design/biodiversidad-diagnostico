import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import tempfile
import os
from utils.biodiversity import BiodiversityAnalyzer
from utils.geo_processing import GeoProcessor

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
""")

# Sidebar para carga de archivos
with st.sidebar:
    st.header("📁 Cargar Datos")
    
    uploaded_file = st.file_uploader(
        "Sube tu archivo geográfico",
        type=['kml', 'zip', 'shp'],
        help="Formatos soportados: KML, Shapefile (ZIP)"
    )
    
    st.markdown("---")
    st.header("⚙️ Parámetros de Análisis")
    
    # Parámetros configurables
    simulation_method = st.selectbox(
        "Método de simulación",
        ["Basado en área", "Basado en tipo de vegetación", "Aleatorio"]
    )
    
    num_species = st.slider(
        "Número máximo de especies a simular",
        min_value=5,
        max_value=50,
        value=15
    )

# Clase principal de la aplicación
class BiodiversityApp:
    def __init__(self):
        self.geo_processor = GeoProcessor()
        self.analyzer = BiodiversityAnalyzer()
        self.geo_data = None
        
    def load_geographic_data(self, uploaded_file):
        """Carga y procesa datos geográficos"""
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Procesar según el tipo de archivo
                if uploaded_file.name.endswith('.kml'):
                    self.geo_data = self.geo_processor.read_kml(tmp_path)
                elif uploaded_file.name.endswith('.zip'):
                    self.geo_data = self.geo_processor.read_shapefile(tmp_path)
                
                os.unlink(tmp_path)
                return True
            except Exception as e:
                st.error(f"Error cargando archivo: {str(e)}")
                return False
        return False
    
    def display_metrics(self, results):
        """Muestra métricas de biodiversidad"""
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
                help="Distribución uniforme de individuos entre especies"
            )
    
    def display_map(self):
        """Muestra el mapa con los datos geográficos"""
        if self.geo_data is not None:
            st.subheader("🗺️ Mapa del Área de Estudio")
            
            # Crear mapa centrado en los datos
            centroid = self.geo_data.geometry.centroid
            m = folium.Map(
                location=[centroid.y.mean(), centroid.x.mean()],
                zoom_start=10
            )
            
            # Añadir datos geoespaciales
            geo_json = folium.GeoJson(
                self.geo_data.__geo_interface__,
                style_function=lambda x: {
                    'fillColor': '#4CAF50',
                    'color': '#2E7D32',
                    'weight': 2,
                    'fillOpacity': 0.5
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['name'] if 'name' in self.geo_data.columns else [],
                    aliases=['Área:'] if 'name' in self.geo_data.columns else []
                )
            ).add_to(m)
            
            # Mostrar mapa en Streamlit
            st_folium(m, width=800, height=400)
    
    def display_species_table(self, species_data):
        """Muestra tabla de especies"""
        st.subheader("📊 Datos de Especies")
        
        df_species = pd.DataFrame(species_data)
        st.dataframe(
            df_species,
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de abundancia
        if not df_species.empty:
            st.subheader("📈 Distribución de Abundancia")
            
            # Ordenar por abundancia
            df_sorted = df_species.sort_values('abundance', ascending=False).head(10)
            
            # Mostrar gráfico de barras
            st.bar_chart(df_sorted.set_index('species')['abundance'])
    
    def run_analysis(self, simulation_method, num_species):
        """Ejecuta el análisis completo"""
        if self.geo_data is None:
            st.warning("Por favor, carga un archivo geográfico primero.")
            return
        
        # Simular datos de especies
        species_data = self.analyzer.simulate_species_data(
            self.geo_data, 
            method=simulation_method,
            max_species=num_species
        )
        
        # Calcular métricas
        results = self.analyzer.analyze_biodiversity(species_data)
        
        # Mostrar resultados
        self.display_metrics(results)
        self.display_map()
        self.display_species_table(species_data)
        
        # Información adicional
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
            """)

# Ejecutar la aplicación
def main():
    app = BiodiversityApp()
    
    # Cargar datos
    if uploaded_file:
        with st.spinner("Procesando archivo..."):
            success = app.load_geographic_data(uploaded_file)
        
        if success:
            st.success("✅ Archivo procesado correctamente")
            
            # Mostrar información básica del dataset
            st.info(f"📁 Archivo cargado: {uploaded_file.name}")
            st.info(f"📊 Número de polígonos/áreas: {len(app.geo_data)}")
            
            # Ejecutar análisis
            if st.button("🚀 Ejecutar Análisis de Biodiversidad", type="primary"):
                app.run_analysis(simulation_method, num_species)
        else:
            st.error("❌ Error al procesar el archivo")
    else:
        # Mensaje inicial
        st.markdown("""
        ### 👈 Comienza subiendo un archivo geográfico
        
        **Formatos soportados:**
        - **KML** (Google Earth)
        - **Shapefile** (comprimido en ZIP, debe incluir .shp, .shx, .dbf, .prj)
        
        **Ejemplo de estructura para Shapefile:**
        ```
        mis_datos.zip
        ├── areas_estudio.shp
        ├── areas_estudio.shx
        ├── areas_estudio.dbf
        └── areas_estudio.prj
        ```
        """)

if __name__ == "__main__":
    main()
