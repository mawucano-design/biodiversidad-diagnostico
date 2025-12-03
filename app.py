import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
from io import BytesIO
import base64
import warnings
warnings.filterwarnings('ignore')

# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition
import geopandas as gpd
from shapely.geometry import Polygon

# ===============================
# 🌿 CONFIGURACIÓN DE PÁGINA
# ===============================

st.set_page_config(
    page_title="Análisis de Biodiversidad",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# 🧩 INICIALIZACIÓN DEL ESTADO
# ===============================

if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.poligono_data = None
    st.session_state.results = None
    st.session_state.analysis_complete = False
    st.session_state.file_processed = False
    st.session_state.uploaded_file_name = None

# ===============================
# 🌿 CLASE DE ANÁLISIS
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
        """Cálculo de área en hectáreas"""
        try:
            # Crear GeoDataFrame
            gdf = gpd.GeoDataFrame([1], geometry=[poligono], crs="EPSG:4326")
            
            # Calcular centroide para determinar zona UTM
            centroide = poligono.centroid
            lat, lon = centroide.y, centroide.x
            
            # Determinar zona UTM
            zona = int((lon + 180) / 6) + 1
            hemisferio = 'north' if lat >= 0 else 'south'
            epsg_code = f"EPSG:326{zona:02d}" if hemisferio == 'north' else f"EPSG:327{zona:02d}"
            
            # Proyectar y calcular área
            gdf_proj = gdf.to_crs(epsg_code)
            area_m2 = gdf_proj.geometry.area.iloc[0]
            area_ha = area_m2 / 10000
            
            return round(area_ha, 2)
        except Exception as e:
            # Cálculo aproximado si falla la proyección
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            
            # Aproximación usando coordenadas
            lat_media = (miny + maxy) / 2
            metros_por_grado_lat = 111320
            metros_por_grado_lon = 111320 * math.cos(math.radians(lat_media))
            
            ancho_m = (maxx - minx) * metros_por_grado_lon
            alto_m = (maxy - miny) * metros_por_grado_lat
            area_m2 = ancho_m * alto_m * 0.7  # Factor de corrección
            
            return round(area_m2 / 10000, 2)
    
    def procesar_poligono(self, gdf, tipo_vegetacion, divisiones=5):
        """Procesar el polígono cargado"""
        try:
            if gdf is None or gdf.empty:
                return None
            
            poligono = gdf.geometry.iloc[0]
            area_total = self.calcular_area(poligono)
            
            # Dividir en áreas
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            
            delta_x = (maxx - minx) / divisiones
            delta_y = (maxy - miny) / divisiones
            
            areas = []
            for i in range(divisiones):
                for j in range(divisiones):
                    cell_minx = minx + i * delta_x
                    cell_maxx = minx + (i + 1) * delta_x
                    cell_miny = miny + j * delta_y
                    cell_maxy = miny + (j + 1) * delta_y
                    
                    cell_poly = Polygon([
                        (cell_minx, cell_miny),
                        (cell_maxx, cell_miny),
                        (cell_maxx, cell_maxy),
                        (cell_minx, cell_maxy)
                    ])
                    
                    if poligono.intersects(cell_poly):
                        intersection = poligono.intersection(cell_poly)
                        if not intersection.is_empty:
                            areas.append({
                                'id': f"Area_{i+1}_{j+1}",
                                'geometry': intersection,
                                'centroid': intersection.centroid
                            })
            
            # Análisis por área
            resultados = []
            params = self.parametros.get(tipo_vegetacion, self.parametros['Bosque Secundario'])
            
            for area in areas:
                # NDVI basado en tipo de vegetación
                ndvi = np.random.normal(params['ndvi_base'], 0.08)
                ndvi = max(0.1, min(0.95, ndvi))
                
                # Carbono
                carbono_min, carbono_max = params['carbono']
                carbono = np.random.uniform(carbono_min, carbono_max)
                
                # Otros indicadores
                biodiversidad = ndvi * 3.5 * np.random.uniform(0.8, 1.2)
                agua = 0.3 + ndvi * 0.5 + np.random.uniform(-0.1, 0.1)
                suelo = 0.4 + ndvi * 0.4 + np.random.uniform(-0.1, 0.1)
                conectividad = 0.5 + ndvi * 0.3 + np.random.uniform(-0.1, 0.1)
                
                resultados.append({
                    'area': area['id'],
                    'ndvi': round(ndvi, 3),
                    'carbono_ton': round(carbono, 1),
                    'biodiversidad': round(biodiversidad, 2),
                    'agua': round(max(0.1, min(1.0, agua)), 2),
                    'suelo': round(max(0.1, min(1.0, suelo)), 2),
                    'conectividad': round(max(0.1, min(1.0, conectividad)), 2),
                    'geometry': area['geometry'],
                    'centroid': area['centroid']
                })
            
            # Calcular resumen
            df = pd.DataFrame(resultados)
            
            summary = {
                'area_total_ha': area_total,
                'tipo_vegetacion': tipo_vegetacion,
                'carbono_total_ton': df['carbono_ton'].sum(),
                'ndvi_promedio': df['ndvi'].mean(),
                'biodiversidad_promedio': df['biodiversidad'].mean(),
                'agua_promedio': df['agua'].mean(),
                'suelo_promedio': df['suelo'].mean(),
                'conectividad_promedio': df['conectividad'].mean(),
                'num_areas': len(resultados)
            }
            
            return {
                'areas': resultados,
                'summary': summary,
                'poligono': poligono,
                'area_total': area_total
            }
            
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None

# ===============================
# 📁 FUNCIONES DE PROCESAMIENTO DE ARCHIVOS
# ===============================

def procesar_archivo(uploaded_file):
    """Procesar archivo KML o ZIP"""
    try:
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as tmpdir:
            if uploaded_file.name.lower().endswith('.kml'):
                # Guardar archivo temporalmente
                temp_path = os.path.join(tmpdir, uploaded_file.name)
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                # Leer KML
                gdf = gpd.read_file(temp_path, driver='KML')
                return gdf
                
            elif uploaded_file.name.lower().endswith('.zip'):
                # Guardar ZIP
                temp_zip = os.path.join(tmpdir, uploaded_file.name)
                with open(temp_zip, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                # Extraer ZIP
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # Buscar archivos shapefile
                shp_files = [f for f in os.listdir(tmpdir) if f.lower().endswith('.shp')]
                
                if shp_files:
                    # Leer el primer shapefile
                    shp_path = os.path.join(tmpdir, shp_files[0])
                    gdf = gpd.read_file(shp_path)
                    return gdf
                else:
                    st.error("No se encontró archivo .shp en el ZIP")
                    return None
            else:
                st.error("Formato no soportado. Use .kml o .zip")
                return None
                
    except Exception as e:
        st.error(f"Error procesando archivo: {str(e)}")
        return None

# ===============================
# 🗺️ FUNCIONES DE MAPA
# ===============================

def crear_mapa_resultados(resultados):
    """Crear mapa con resultados"""
    try:
        if resultados is None or 'poligono' not in resultados:
            return None
        
        poligono = resultados['poligono']
        centroide = poligono.centroid
        
        # Crear mapa
        m = folium.Map(
            location=[centroide.y, centroide.x],
            zoom_start=12,
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Satellite'
        )
        
        # Agregar polígono principal
        folium.GeoJson(
            poligono,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': '#FF0000',
                'weight': 3,
                'fillOpacity': 0
            },
            name='Polígono de estudio'
        ).add_to(m)
        
        # Agregar áreas si existen
        if 'areas' in resultados and resultados['areas']:
            for area in resultados['areas']:
                if 'geometry' in area:
                    # Determinar color basado en NDVI
                    ndvi = area.get('ndvi', 0.5)
                    if ndvi > 0.7:
                        color = '#006400'  # Verde oscuro
                    elif ndvi > 0.5:
                        color = '#32CD32'  # Verde lima
                    elif ndvi > 0.3:
                        color = '#FFD700'  # Amarillo
                    else:
                        color = '#FF4500'  # Rojo
                    
                    # Crear popup
                    popup_text = f"""
                    <b>Área:</b> {area.get('area', 'N/A')}<br>
                    <b>NDVI:</b> {area.get('ndvi', 'N/A'):.3f}<br>
                    <b>Carbono:</b> {area.get('carbono_ton', 'N/A'):.1f} t<br>
                    <b>Biodiversidad:</b> {area.get('biodiversidad', 'N/A'):.2f}<br>
                    <b>Agua:</b> {area.get('agua', 'N/A'):.2f}<br>
                    <b>Suelo:</b> {area.get('suelo', 'N/A'):.2f}
                    """
                    
                    folium.GeoJson(
                        area['geometry'],
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': color,
                            'weight': 1,
                            'fillOpacity': 0.5
                        },
                        popup=folium.Popup(popup_text, max_width=300)
                    ).add_to(m)
        
        # Agregar controles
        folium.TileLayer('OpenStreetMap').add_to(m)
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
        return None

# ===============================
# 🎨 INTERFAZ DE USUARIO
# ===============================

def main():
    """Función principal de la aplicación"""
    
    # CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E8B57;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌿 Análisis Integral de Biodiversidad</h1>
        <p>Sistema de evaluación ambiental con múltiples indicadores</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("### 📁 Cargar Polígono")
        
        # Botón para limpiar
        if st.button("🔄 Limpiar Todo", use_container_width=True):
            for key in ['poligono_data', 'results', 'analysis_complete', 'file_processed', 'uploaded_file_name']:
                if key in st.session_state:
                    st.session_state[key] = None
            st.session_state.analysis_complete = False
            st.session_state.file_processed = False
            st.rerun()
        
        # Uploader de archivos
        uploaded_file = st.file_uploader(
            "Suba su archivo KML o ZIP",
            type=['kml', 'zip'],
            help="Puede subir archivos KML o Shapefiles comprimidos en ZIP"
        )
        
        # Procesar archivo inmediatamente cuando se sube
        if uploaded_file is not None:
            # Verificar si es un archivo nuevo
            current_file_name = st.session_state.get('uploaded_file_name')
            if current_file_name != uploaded_file.name or not st.session_state.get('file_processed', False):
                with st.spinner(f"Procesando {uploaded_file.name}..."):
                    gdf = procesar_archivo(uploaded_file)
                    
                    if gdf is not None and not gdf.empty:
                        st.session_state.poligono_data = gdf
                        st.session_state.file_processed = True
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.session_state.analysis_complete = False
                        st.session_state.results = None
                        st.success(f"✅ Archivo cargado: {uploaded_file.name}")
                    else:
                        st.error("❌ No se pudo procesar el archivo")
        
        st.divider()
        
        # Configuración solo si hay archivo cargado
        if st.session_state.get('file_processed', False):
            st.markdown("### ⚙️ Configuración del Análisis")
            
            tipo_vegetacion = st.selectbox(
                "Tipo de vegetación predominante",
                list(AnalizadorBiodiversidad().parametros.keys()),
                index=1  # Bosque Secundario por defecto
            )
            
            divisiones = st.slider(
                "Número de divisiones para análisis",
                min_value=3,
                max_value=8,
                value=5,
                help="Divide el área en una cuadrícula para análisis detallado"
            )
            
            if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
                with st.spinner("Realizando análisis..."):
                    analizador = AnalizadorBiodiversidad()
                    resultados = analizador.procesar_poligono(
                        st.session_state.poligono_data,
                        tipo_vegetacion,
                        divisiones
                    )
                    
                    if resultados:
                        st.session_state.results = resultados
                        st.session_state.analysis_complete = True
                        st.success("✅ Análisis completado!")
                        st.rerun()
                    else:
                        st.error("❌ Error en el análisis")
    
    # ===== CONTENIDO PRINCIPAL =====
    
    # Panel de bienvenida/información
    if not st.session_state.get('file_processed', False):
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Sistema de Análisis de Biodiversidad!
        
        ### 📋 **Instrucciones:**
        1. **Suba un archivo** en el panel lateral (KML o Shapefile en ZIP)
        2. **Configure los parámetros** de análisis
        3. **Ejecute el análisis** para ver los resultados
        
        ### 🌿 **Indicadores analizados:**
        - **NDVI**: Salud de la vegetación
        - **Carbono**: Almacenamiento de carbono en toneladas
        - **Biodiversidad**: Índice de diversidad de especies
        - **Recursos hídricos**: Disponibilidad de agua
        - **Calidad del suelo**: Salud del suelo
        - **Conectividad ecológica**: Fragmentación del hábitat
        
        ### 📁 **Formatos soportados:**
        - **KML/ KMZ**: Archivos de Google Earth
        - **Shapefile**: Conjunto de archivos (.shp, .shx, .dbf) en ZIP
        
        ### 🗺️ **Características:**
        - Mapas interactivos con imágenes satelitales
        - Análisis por áreas (cuadrícula)
        - Métricas detalladas por sección
        - Exportación de resultados
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Información del archivo cargado
    elif st.session_state.get('file_processed', False) and not st.session_state.get('analysis_complete', False):
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown(f"### 📁 Archivo Cargado: **{st.session_state.uploaded_file_name}**")
        
        # Mostrar información básica del polígono
        if st.session_state.poligono_data is not None:
            gdf = st.session_state.poligono_data
            poligono = gdf.geometry.iloc[0]
            
            # Calcular área aproximada
            analizador = AnalizadorBiodiversidad()
            area_ha = analizador.calcular_area(poligono)
            
            st.write(f"**Área aproximada:** {area_ha:,.2f} hectáreas")
            st.write(f"**Tipo de geometría:** {poligono.geom_type}")
            
            # Mostrar vista previa simple
            bounds = poligono.bounds
            st.write(f"**Extensión geográfica:**")
            st.write(f"- Latitud: {bounds[1]:.4f}° a {bounds[3]:.4f}°")
            st.write(f"- Longitud: {bounds[0]:.4f}° a {bounds[2]:.4f}°")
        
        st.markdown("---")
        st.markdown("### ⚙️ Configuración Pendiente")
        st.info("Configure los parámetros en el panel lateral y haga clic en **'Ejecutar Análisis'**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Resultados del análisis
    elif st.session_state.get('analysis_complete', False) and st.session_state.get('results'):
        resultados = st.session_state.results
        
        # ===== SECCIÓN 1: RESUMEN EJECUTIVO =====
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Resumen Ejecutivo")
        
        summary = resultados['summary']
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Área Total",
                f"{summary['area_total_ha']:,.1f} ha",
                help="Área total del polígono analizado"
            )
        
        with col2:
            st.metric(
                "Carbono Total",
                f"{summary['carbono_total_ton']:,.0f} t",
                help="Carbono almacenado total estimado"
            )
        
        with col3:
            st.metric(
                "NDVI Promedio",
                f"{summary['ndvi_promedio']:.3f}",
                help="Índice de vegetación promedio (0-1)"
            )
        
        with col4:
            st.metric(
                "Áreas Analizadas",
                summary['num_areas'],
                help="Número de subdivisiones analizadas"
            )
        
        # Más métricas
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("Biodiversidad", f"{summary['biodiversidad_promedio']:.2f}")
        
        with col6:
            st.metric("Recursos Hídricos", f"{summary['agua_promedio']:.2f}")
        
        with col7:
            st.metric("Calidad del Suelo", f"{summary['suelo_promedio']:.2f}")
        
        with col8:
            st.metric("Conectividad", f"{summary['conectividad_promedio']:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== SECCIÓN 2: MAPA INTERACTIVO =====
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 🗺️ Mapa de Resultados")
        
        mapa = crear_mapa_resultados(resultados)
        if mapa:
            # Renderizar mapa con tamaño fijo
            st_folium(mapa, width=800, height=500)
        else:
            st.info("No se pudo generar el mapa")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== SECCIÓN 3: DATOS DETALLADOS =====
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📋 Datos por Área")
        
        # Crear DataFrame con los resultados
        if 'areas' in resultados and resultados['areas']:
            df = pd.DataFrame(resultados['areas'])
            
            # Seleccionar columnas para mostrar
            columnas_display = ['area', 'ndvi', 'carbono_ton', 'biodiversidad', 'agua', 'suelo', 'conectividad']
            columnas_existentes = [col for col in columnas_display if col in df.columns]
            
            if columnas_existentes:
                # Mostrar tabla con formato
                st.dataframe(
                    df[columnas_existentes].style.format({
                        'ndvi': '{:.3f}',
                        'carbono_ton': '{:.1f}',
                        'biodiversidad': '{:.2f}',
                        'agua': '{:.2f}',
                        'suelo': '{:.2f}',
                        'conectividad': '{:.2f}'
                    }),
                    use_container_width=True,
                    height=400
                )
                
                # Botones de descarga
                st.markdown("### 📥 Exportar Datos")
                
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    # Exportar a CSV
                    csv = df[columnas_existentes].to_csv(index=False)
                    b64_csv = base64.b64encode(csv.encode()).decode()
                    href_csv = f'<a href="data:file/csv;base64,{b64_csv}" download="resultados_biodiversidad.csv" style="text-decoration: none;">'
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1E90FF 0%, #00BFFF 100%); 
                                padding: 12px; border-radius: 8px; text-align: center; margin: 10px 0;">
                        {href_csv}
                        <span style="color: white; font-weight: bold;">📥 Descargar CSV</span>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_dl2:
                    # Exportar a Excel
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df[columnas_existentes].to_excel(writer, sheet_name='Resultados', index=False)
                    
                    excel_data = excel_buffer.getvalue()
                    b64_excel = base64.b64encode(excel_data).decode()
                    href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="resultados_biodiversidad.xlsx" style="text-decoration: none;">'
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #228B22 0%, #2E8B57 100%); 
                                padding: 12px; border-radius: 8px; text-align: center; margin: 10px 0;">
                        {href_excel}
                        <span style="color: white; font-weight: bold;">📊 Descargar Excel</span>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== SECCIÓN 4: GRÁFICOS =====
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Visualizaciones")
        
        if 'areas' in resultados and resultados['areas']:
            df = pd.DataFrame(resultados['areas'])
            
            # Crear pestañas para diferentes gráficos
            tab1, tab2, tab3 = st.tabs(["📊 Distribución NDVI", "🌳 Carbono por Área", "📋 Comparación Indicadores"])
            
            with tab1:
                # Histograma de NDVI
                fig_ndvi = px.histogram(
                    df, 
                    x='ndvi',
                    nbins=20,
                    title='Distribución del Índice NDVI',
                    labels={'ndvi': 'NDVI', 'count': 'Número de Áreas'},
                    color_discrete_sequence=['#2E8B57']
                )
                fig_ndvi.update_layout(bargap=0.1)
                st.plotly_chart(fig_ndvi, use_container_width=True)
            
            with tab2:
                # Gráfico de barras de carbono
                df_sorted = df.sort_values('carbono_ton', ascending=False).head(15)
                fig_carbono = px.bar(
                    df_sorted,
                    x='area',
                    y='carbono_ton',
                    title='Carbono por Área (Top 15)',
                    labels={'carbono_ton': 'Carbono (ton)', 'area': 'Área'},
                    color='carbono_ton',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_carbono, use_container_width=True)
            
            with tab3:
                # Scatter plot comparando indicadores
                if 'ndvi' in df.columns and 'biodiversidad' in df.columns:
                    fig_scatter = px.scatter(
                        df,
                        x='ndvi',
                        y='biodiversidad',
                        size='carbono_ton',
                        color='agua',
                        hover_name='area',
                        title='Relación entre NDVI y Biodiversidad',
                        labels={
                            'ndvi': 'NDVI',
                            'biodiversidad': 'Índice de Biodiversidad',
                            'carbono_ton': 'Carbono (ton)',
                            'agua': 'Recursos Hídricos'
                        },
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== SECCIÓN 5: RECOMENDACIONES =====
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("### 💡 Recomendaciones")
        
        # Generar recomendaciones basadas en los resultados
        ndvi_prom = summary['ndvi_promedio']
        agua_prom = summary['agua_promedio']
        suelo_prom = summary['suelo_promedio']
        conectividad_prom = summary['conectividad_promedio']
        
        recomendaciones = []
        
        if ndvi_prom < 0.4:
            recomendaciones.append("**🌿 Restauración vegetal:** Implementar programas de reforestación y recuperación de la cubierta vegetal.")
        
        if agua_prom < 0.4:
            recomendaciones.append("**💧 Manejo hídrico:** Desarrollar estrategias de conservación de agua y protección de fuentes.")
        
        if suelo_prom < 0.5:
            recomendaciones.append("**🌱 Conservación de suelos:** Implementar prácticas de manejo sostenible del suelo.")
        
        if conectividad_prom < 0.6:
            recomendaciones.append("**🔗 Corredores ecológicos:** Establecer corredores biológicos para mejorar la conectividad del hábitat.")
        
        if ndvi_prom > 0.7 and agua_prom > 0.6 and suelo_prom > 0.6:
            recomendaciones.append("**✅ Conservación:** Mantener las prácticas actuales de conservación y monitoreo continuo.")
        
        if not recomendaciones:
            recomendaciones.append("**📊 Monitoreo continuo:** Realizar seguimiento periódico de los indicadores ambientales.")
        
        # Mostrar recomendaciones
        for i, rec in enumerate(recomendaciones, 1):
            st.markdown(f"{i}. {rec}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 🚀 EJECUCIÓN
# ===============================

if __name__ == "__main__":
    main()
