import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
import warnings
warnings.filterwarnings('ignore')

# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition
import geopandas as gpd
from shapely.geometry import Polygon, Point

# ===============================
# 🌿 CONFIGURACIÓN DE PÁGINA - SOLUCIÓN CRÍTICA
# ===============================

# CONFIGURACIÓN SIMPLIFICADA - EVITA CONFLICTOS DE RENDERIZADO
st.set_page_config(
    page_title="Análisis de Biodiversidad",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="auto"  # Cambiado de 'expanded'
)

# ===============================
# 🧩 INICIALIZACIÓN DEL ESTADO - MÉTODO SEGURO
# ===============================

# Limpiar estado de sesión al inicio de forma segura
if 'init' not in st.session_state:
    st.session_state.clear()
    st.session_state.init = True
    st.session_state.poligono_data = None
    st.session_state.results = None
    st.session_state.analysis_complete = False
    st.session_state.file_processed = False
    st.session_state.current_view = "upload"  # Control de vistas
    st.session_state.component_counter = 0  # Contador para keys únicas

# Función para generar keys únicas
def get_unique_key(base_name):
    st.session_state.component_counter += 1
    return f"{base_name}_{st.session_state.component_counter}"

# ===============================
# 🌿 CLASE DE ANÁLISIS (SIMPLIFICADA)
# ===============================

class AnalizadorBiodiversidad:
    def __init__(self):
        self.parametros = {
            'Bosque Denso Primario': {'ndvi_base': 0.85, 'carbono': (180, 320)},
            'Bosque Secundario': {'ndvi_base': 0.75, 'carbono': (80, 160)},
            'Bosque Ripario': {'ndvi_base': 0.80, 'carbono': (120, 220)},
            'Matorral Denso': {'ndvi_base': 0.65, 'carbono': (40, 70)},
            'Matorral Abierto': {'ndvi_base': 0.45, 'carbono': (20, 40)},
            'Sabana Arborizada': {'ndvi_base': 0.35, 'carbono': (25, 45)},
            'Herbazal Natural': {'ndvi_base': 0.25, 'carbono': (8, 18)},
            'Zona de Transición': {'ndvi_base': 0.30, 'carbono': (15, 30)},
            'Área de Restauración': {'ndvi_base': 0.55, 'carbono': (30, 90)}
        }
    
    def calcular_area(self, poligono):
        """Cálculo simplificado pero robusto"""
        try:
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            lat_media = (miny + maxy) / 2
            metros_por_grado_lat = 111320
            metros_por_grado_lon = 111320 * math.cos(math.radians(lat_media))
            ancho_m = (maxx - minx) * metros_por_grado_lon
            alto_m = (maxy - miny) * metros_por_grado_lat
            area_m2 = ancho_m * alto_m * 0.75  # Factor de ajuste
            return round(area_m2 / 10000, 2)
        except:
            return 1000.0
    
    def procesar_poligono(self, gdf, tipo_vegetacion, divisiones=5):
        """Procesamiento simplificado"""
        try:
            poligono = gdf.geometry.iloc[0]
            area_ha = self.calcular_area(poligono)
            
            # Dividir en áreas
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            delta_x = (maxx - minx) / divisiones
            delta_y = (maxy - miny) / divisiones
            
            areas = []
            for i in range(divisiones):
                for j in range(divisiones):
                    cell_poly = Polygon([
                        (minx + i * delta_x, miny + j * delta_y),
                        (minx + (i + 1) * delta_x, miny + j * delta_y),
                        (minx + (i + 1) * delta_x, miny + (j + 1) * delta_y),
                        (minx + i * delta_x, miny + (j + 1) * delta_y)
                    ])
                    
                    if poligono.intersects(cell_poly):
                        intersection = poligono.intersection(cell_poly)
                        if not intersection.is_empty:
                            areas.append({
                                'id': f"Area_{i+1}_{j+1}",
                                'geometry': intersection
                            })
            
            # Análisis por área
            resultados = []
            params = self.parametros.get(tipo_vegetacion, self.parametros['Bosque Secundario'])
            
            for area in areas:
                ndvi = np.random.normal(params['ndvi_base'], 0.1)
                ndvi = max(0.1, min(0.9, ndvi))
                
                carbono_min, carbono_max = params['carbono']
                carbono = np.random.uniform(carbono_min, carbono_max) * area_ha / len(areas)
                
                resultados.append({
                    'area': area['id'],
                    'ndvi': round(ndvi, 3),
                    'carbono_ton': round(carbono, 1),
                    'biodiversidad': round(ndvi * 3.5, 2),
                    'agua': round(np.random.uniform(0.3, 0.9), 2),
                    'suelo': round(np.random.uniform(0.4, 0.95), 2),
                    'conectividad': round(np.random.uniform(0.5, 0.95), 2),
                    'geometry': area['geometry']
                })
            
            # Resumen
            df = pd.DataFrame(resultados)
            summary = {
                'area_total': area_ha,
                'tipo_vegetacion': tipo_vegetacion,
                'carbono_total': df['carbono_ton'].sum(),
                'ndvi_promedio': df['ndvi'].mean(),
                'biodiversidad_promedio': df['biodiversidad'].mean(),
                'num_areas': len(resultados)
            }
            
            return {
                'areas': resultados,
                'summary': summary,
                'poligono': poligono
            }
            
        except Exception as e:
            st.error(f"Error en procesamiento: {str(e)}")
            return None

# ===============================
# 🗺️ FUNCIONES DE MAPA (SIMPLIFICADAS)
# ===============================

def crear_mapa_simple(resultados):
    """Crear mapa simple sin complicaciones"""
    try:
        if not resultados or 'areas' not in resultados:
            return None
            
        # Centro aproximado
        centroide = resultados['poligono'].centroid
        m = folium.Map(location=[centroide.y, centroide.x], zoom_start=12)
        
        # Agregar polígono principal
        folium.GeoJson(
            resultados['poligono'],
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#FF0000',
                'weight': 3,
                'fillOpacity': 0
            }
        ).add_to(m)
        
        # Agregar áreas
        for area in resultados['areas'][:20]:  # Limitar a 20 áreas máximo
            color = '#00FF00' if area['ndvi'] > 0.5 else '#FFFF00' if area['ndvi'] > 0.3 else '#FF0000'
            
            folium.GeoJson(
                area['geometry'],
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': '#000000',
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                tooltip=f"Área: {area['area']}<br>NDVI: {area['ndvi']}<br>Carbono: {area['carbono_ton']} t"
            ).add_to(m)
        
        return m
        
    except Exception as e:
        st.warning(f"Mapa no disponible: {str(e)}")
        return None

# ===============================
# 📊 VISUALIZACIONES (SIMPLIFICADAS)
# ===============================

def mostrar_metricas(summary):
    """Mostrar métricas principales"""
    cols = st.columns(4)
    with cols[0]:
        st.metric("Área Total", f"{summary['area_total']:,.1f} ha", key=get_unique_key("area"))
    with cols[1]:
        st.metric("Carbono Total", f"{summary['carbono_total']:,.0f} t", key=get_unique_key("carbono"))
    with cols[2]:
        st.metric("NDVI Promedio", f"{summary['ndvi_promedio']:.2f}", key=get_unique_key("ndvi"))
    with cols[3]:
        st.metric("Áreas Analizadas", summary['num_areas'], key=get_unique_key("areas"))

def mostrar_tabla_datos(resultados):
    """Mostrar tabla de datos simplificada"""
    df = pd.DataFrame(resultados['areas'])
    # Seleccionar solo columnas esenciales
    columnas = ['area', 'ndvi', 'carbono_ton', 'biodiversidad', 'agua', 'suelo']
    columnas = [c for c in columnas if c in df.columns]
    
    if len(columnas) > 0:
        st.dataframe(
            df[columnas].style.format({
                'ndvi': '{:.3f}',
                'carbono_ton': '{:.1f}',
                'biodiversidad': '{:.2f}',
                'agua': '{:.2f}',
                'suelo': '{:.2f}'
            }),
            use_container_width=True,
            height=300
        )

# ===============================
# 📁 MANEJO DE ARCHIVOS
# ===============================

def procesar_archivo(uploaded_file):
    """Procesar archivo KML/ZIP"""
    try:
        if uploaded_file.name.endswith('.kml'):
            return gpd.read_file(uploaded_file, driver='KML')
        elif uploaded_file.name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if shp_files:
                    return gpd.read_file(os.path.join(tmpdir, shp_files[0]))
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# ===============================
# 🎨 INTERFAZ PRINCIPAL - DISEÑO ROBUSTO
# ===============================

def main():
    """Función principal - Diseñada para evitar errores de DOM"""
    
    # CSS minimalista
    st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .data-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header simple
    st.markdown("""
    <div class="main-header">
        <h1>🌿 Análisis de Biodiversidad</h1>
        <p>Sistema simplificado de evaluación ambiental</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== SIDEBAR SIMPLIFICADO =====
    with st.sidebar:
        st.header("📁 Cargar Datos")
        
        # Control para limpiar estado
        if st.button("🔄 Reiniciar Aplicación", key=get_unique_key("reset")):
            st.session_state.clear()
            st.rerun()
        
        uploaded_file = st.file_uploader(
            "Subir archivo KML o ZIP",
            type=['kml', 'zip'],
            key=get_unique_key("uploader")
        )
        
        if uploaded_file and not st.session_state.get('file_processed', False):
            with st.spinner("Procesando..."):
                gdf = procesar_archivo(uploaded_file)
                if gdf is not None and not gdf.empty:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.success(f"✅ Archivo cargado: {uploaded_file.name}")
        
        st.divider()
        
        if st.session_state.get('file_processed', False):
            st.header("⚙️ Configuración")
            
            tipo_vegetacion = st.selectbox(
                "Tipo de vegetación",
                list(AnalizadorBiodiversidad().parametros.keys()),
                key=get_unique_key("vegetation")
            )
            
            divisiones = st.slider(
                "Número de divisiones",
                2, 8, 4,
                key=get_unique_key("divisions")
            )
            
            if st.button("📊 Ejecutar Análisis", type="primary", key=get_unique_key("analyze")):
                with st.spinner("Analizando..."):
                    analizador = AnalizadorBiodiversidad()
                    resultados = analizador.procesar_poligono(
                        st.session_state.poligono_data,
                        tipo_vegetacion,
                        divisiones
                    )
                    
                    if resultados:
                        st.session_state.results = resultados
                        st.session_state.analysis_complete = True
                        st.session_state.current_view = "results"
                        st.rerun()
    
    # ===== CONTENIDO PRINCIPAL =====
    
    # Vista: Sin datos cargados
    if not st.session_state.get('file_processed', False):
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 Bienvenido
        
        ### Para comenzar:
        1. Sube un archivo KML o ZIP con tu polígono en el panel lateral
        2. Configura los parámetros de análisis
        3. Haz clic en "Ejecutar Análisis"
        
        **Formatos soportados:** KML, Shapefile (comprimido en ZIP)
        
        ### Características:
        - 🌿 Análisis de vegetación (NDVI)
        - 🌳 Estimación de carbono
        - 🦋 Índices de biodiversidad
        - 💧 Recursos hídricos
        - 🗺️ Visualización geoespacial
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Vista: Datos cargados pero sin análisis
    elif st.session_state.get('file_processed', False) and not st.session_state.get('analysis_complete', False):
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.info("📁 **Archivo cargado** - Configura los parámetros en el panel lateral y haz clic en 'Ejecutar Análisis'")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Vista: Resultados del análisis
    elif st.session_state.get('analysis_complete', False) and st.session_state.get('results'):
        resultados = st.session_state.results
        
        # Sección 1: Métricas principales
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader("📊 Resumen del Análisis")
        mostrar_metricas(resultados['summary'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección 2: Mapa
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader("🗺️ Mapa de Distribución")
        mapa = crear_mapa_simple(resultados)
        if mapa:
            # Usar try-except para manejar posibles errores en el renderizado del mapa
            try:
                st_folium(mapa, width=700, height=500, key=get_unique_key("map"))
            except:
                st.warning("El mapa no se pudo cargar correctamente")
        else:
            st.info("No hay datos geoespaciales para mostrar")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección 3: Datos detallados
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader("📋 Datos por Área")
        mostrar_tabla_datos(resultados)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección 4: Descargas
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader("📥 Exportar Resultados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Descargar CSV", key=get_unique_key("download_csv")):
                df = pd.DataFrame(resultados['areas'])
                # Convertir a CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Guardar CSV",
                    data=csv,
                    file_name="resultados_analisis.csv",
                    mime="text/csv",
                    key=get_unique_key("csv_download")
                )
        
        with col2:
            if st.button("📄 Generar Informe", key=get_unique_key("generate_report")):
                # Crear informe simple en texto
                informe = f"""
                INFORME DE ANÁLISIS DE BIODIVERSIDAD
                ====================================
                
                Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
                
                RESULTADOS PRINCIPALES:
                - Área total: {resultados['summary']['area_total']:,.1f} ha
                - Tipo de vegetación: {resultados['summary']['tipo_vegetacion']}
                - Carbono total estimado: {resultados['summary']['carbono_total']:,.0f} toneladas
                - NDVI promedio: {resultados['summary']['ndvi_promedio']:.2f}
                - Índice de biodiversidad promedio: {resultados['summary']['biodiversidad_promedio']:.2f}
                - Número de áreas analizadas: {resultados['summary']['num_areas']}
                
                RECOMENDACIONES:
                - Mantener el monitoreo continuo del área
                - Implementar medidas de conservación según los resultados
                - Considerar programas de restauración si se detectan áreas degradadas
                """
                
                st.download_button(
                    label="⬇️ Descargar Informe",
                    data=informe,
                    file_name="informe_biodiversidad.txt",
                    mime="text/plain",
                    key=get_unique_key("report_download")
                )
        st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================

if __name__ == "__main__":
    # Configuración adicional para Streamlit
    import streamlit as st
    
    # Forzar modo simple
    st.config.set_option('client.caching', 'clear')
    
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        st.info("""
        **Solución recomendada:**
        1. Recarga la página (F5)
        2. Limpia la caché del navegador
        3. Intenta nuevamente
        """)
        
        if st.button("🔄 Reiniciar aplicación", key="error_restart"):
            st.session_state.clear()
            st.rerun()
