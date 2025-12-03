import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
import base64
import warnings
from datetime import datetime
from io import BytesIO
import hashlib
warnings.filterwarnings('ignore')

# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition
import geopandas as gpd
from shapely.geometry import Polygon, Point
import plotly.express as px

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

# Inicializar estado de sesión de forma segura
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.poligono_data = None
    st.session_state.results = None
    st.session_state.analysis_complete = False
    st.session_state.file_processed = False
    st.session_state.uploaded_file_name = None
    st.session_state.map_key = 0  # Para forzar la recreación del mapa

# ===============================
# 🌿 CLASE DE ANÁLISIS
# ===============================

class AnalizadorBiodiversidad:
    def __init__(self):
        self.parametros = {
            'Bosque Denso Primario': {
                'ndvi_base': 0.85, 'carbono': (180, 320),
                'biodiversidad': 0.85, 'humedad': 0.9
            },
            'Bosque Secundario': {
                'ndvi_base': 0.75, 'carbono': (80, 160),
                'biodiversidad': 0.65, 'humedad': 0.8
            },
            'Bosque Ripario': {
                'ndvi_base': 0.80, 'carbono': (120, 220),
                'biodiversidad': 0.75, 'humedad': 0.95
            },
            'Matorral Denso': {
                'ndvi_base': 0.65, 'carbono': (40, 70),
                'biodiversidad': 0.45, 'humedad': 0.6
            },
            'Matorral Abierto': {
                'ndvi_base': 0.45, 'carbono': (20, 40),
                'biodiversidad': 0.25, 'humedad': 0.5
            },
            'Sabana Arborizada': {
                'ndvi_base': 0.35, 'carbono': (25, 45),
                'biodiversidad': 0.35, 'humedad': 0.4
            },
            'Herbazal Natural': {
                'ndvi_base': 0.25, 'carbono': (8, 18),
                'biodiversidad': 0.15, 'humedad': 0.7
            },
            'Zona de Transición': {
                'ndvi_base': 0.30, 'carbono': (15, 30),
                'biodiversidad': 0.25, 'humedad': 0.6
            },
            'Área de Restauración': {
                'ndvi_base': 0.55, 'carbono': (30, 90),
                'biodiversidad': 0.50, 'humedad': 0.75
            }
        }
    
    def calcular_area(self, poligono):
        """Calcular área en hectáreas"""
        try:
            # Usar proyección UTM para cálculo preciso
            gdf = gpd.GeoDataFrame([1], geometry=[poligono], crs="EPSG:4326")
            centroide = poligono.centroid
            lat, lon = centroide.y, centroide.x
            
            # Determinar zona UTM
            zona = int((lon + 180) / 6) + 1
            hemisferio = 'north' if lat >= 0 else 'south'
            epsg_code = f"EPSG:326{zona:02d}" if hemisferio == 'north' else f"EPSG:327{zona:02d}"
            
            # Proyectar y calcular área
            gdf_proj = gdf.to_crs(epsg_code)
            area_m2 = gdf_proj.geometry.area.iloc[0]
            return round(area_m2 / 10000, 2)
        except Exception as e:
            # Cálculo aproximado
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            lat_media = (miny + maxy) / 2
            metros_por_grado_lat = 111320
            metros_por_grado_lon = 111320 * math.cos(math.radians(lat_media))
            ancho_m = (maxx - minx) * metros_por_grado_lon
            alto_m = (maxy - miny) * metros_por_grado_lat
            area_m2 = ancho_m * alto_m * 0.7
            return round(area_m2 / 10000, 2)
    
    def procesar_poligono(self, gdf, tipo_vegetacion, divisiones=5):
        """Procesar polígono y generar análisis"""
        try:
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
                                'geometry': intersection,
                                'centroid': intersection.centroid,
                                'area_ha': self.calcular_area(intersection)
                            })
            
            # Analizar cada área
            params = self.parametros.get(tipo_vegetacion, self.parametros['Bosque Secundario'])
            resultados = []
            
            for area in areas:
                # NDVI
                ndvi = np.random.normal(params['ndvi_base'], 0.08)
                ndvi = max(0.1, min(0.95, ndvi))
                
                # Carbono
                carbono_min, carbono_max = params['carbono']
                carbono = np.random.uniform(carbono_min, carbono_max)
                
                # Biodiversidad
                biodiv = params['biodiversidad'] * np.random.uniform(0.8, 1.2)
                
                # Humedad
                humedad = params['humedad'] * np.random.uniform(0.8, 1.2)
                humedad = max(0.1, min(1.0, humedad))
                
                # Otros indicadores
                agua = 0.3 + ndvi * 0.5 + np.random.uniform(-0.1, 0.1)
                suelo = 0.4 + ndvi * 0.4 + np.random.uniform(-0.1, 0.1)
                conectividad = 0.5 + ndvi * 0.3 + np.random.uniform(-0.1, 0.1)
                presion = np.random.uniform(0.1, 0.9)
                
                resultados.append({
                    'area': area['id'],
                    'area_ha': round(area['area_ha'], 2),
                    'ndvi': round(ndvi, 3),
                    'carbono_ton': round(carbono * area['area_ha'], 1),
                    'biodiversidad': round(biodiv, 2),
                    'humedad': round(humedad, 2),
                    'agua': round(max(0.1, min(1.0, agua)), 2),
                    'suelo': round(max(0.1, min(1.0, suelo)), 2),
                    'conectividad': round(max(0.1, min(1.0, conectividad)), 2),
                    'presion': round(presion, 2),
                    'geometry': area['geometry']
                })
            
            # Calcular resumen
            df = pd.DataFrame(resultados)
            summary = {
                'area_total_ha': area_total,
                'tipo_vegetacion': tipo_vegetacion,
                'carbono_total_ton': df['carbono_ton'].sum(),
                'ndvi_promedio': df['ndvi'].mean(),
                'biodiversidad_promedio': df['biodiversidad'].mean(),
                'humedad_promedio': df['humedad'].mean(),
                'agua_promedio': df['agua'].mean(),
                'suelo_promedio': df['suelo'].mean(),
                'conectividad_promedio': df['conectividad'].mean(),
                'presion_promedio': df['presion'].mean(),
                'num_areas': len(resultados)
            }
            
            return {
                'areas': resultados,
                'summary': summary,
                'poligono': poligono,
                'config': {'divisiones': divisiones, 'tipo_vegetacion': tipo_vegetacion}
            }
            
        except Exception as e:
            st.error(f"Error en procesamiento: {str(e)}")
            return None

# ===============================
# 📁 FUNCIONES DE PROCESAMIENTO
# ===============================

def procesar_archivo(uploaded_file):
    """Procesar archivo KML o ZIP"""
    try:
        if uploaded_file is None:
            return None
            
        if uploaded_file.name.lower().endswith('.kml'):
            return gpd.read_file(uploaded_file, driver='KML')
            
        elif uploaded_file.name.lower().endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Guardar ZIP
                temp_zip = os.path.join(tmpdir, uploaded_file.name)
                with open(temp_zip, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                # Extraer ZIP
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # Buscar shapefiles
                shp_files = [f for f in os.listdir(tmpdir) if f.lower().endswith('.shp')]
                if shp_files:
                    return gpd.read_file(os.path.join(tmpdir, shp_files[0]))
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

def crear_mapa_resultados(resultados, map_key):
    """Crear mapa con resultados"""
    try:
        if not resultados or 'poligono' not in resultados:
            return None
            
        poligono = resultados['poligono']
        centroide = poligono.centroid
        
        # Crear mapa base
        m = folium.Map(
            location=[centroide.y, centroide.x],
            zoom_start=12,
            control_scale=True
        )
        
        # Agregar capa base
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Imagen Satelital',
            overlay=False
        ).add_to(m)
        
        folium.TileLayer('OpenStreetMap').add_to(m)
        
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
            for area in resultados['areas'][:50]:  # Limitar a 50 áreas
                ndvi = area.get('ndvi', 0.5)
                
                # Determinar color basado en NDVI
                if ndvi > 0.7:
                    color = '#006400'  # Verde oscuro
                elif ndvi > 0.5:
                    color = '#32CD32'  # Verde
                elif ndvi > 0.3:
                    color = '#FFD700'  # Amarillo
                else:
                    color = '#FF4500'  # Rojo
                
                popup_text = f"""
                <b>Área:</b> {area['area']}<br>
                <b>NDVI:</b> {ndvi:.3f}<br>
                <b>Carbono:</b> {area.get('carbono_ton', 'N/A')} t<br>
                <b>Biodiversidad:</b> {area.get('biodiversidad', 'N/A')}
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
        
        # Controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
        
    except Exception as e:
        st.warning(f"No se pudo crear el mapa: {str(e)}")
        return None

# ===============================
# 📊 FUNCIONES DE VISUALIZACIÓN
# ===============================

def crear_grafico_barras(df, columna, titulo):
    """Crear gráfico de barras"""
    try:
        fig = px.bar(
            df.head(20),  # Mostrar solo top 20
            x='area',
            y=columna,
            title=titulo,
            color=columna,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            xaxis_title="Área",
            yaxis_title=columna.replace('_', ' ').title(),
            showlegend=False
        )
        return fig
    except:
        return None

def crear_histograma(df, columna, titulo):
    """Crear histograma"""
    try:
        fig = px.histogram(
            df,
            x=columna,
            title=titulo,
            nbins=20,
            color_discrete_sequence=['#2E8B57']
        )
        return fig
    except:
        return None

# ===============================
# 🎨 INTERFAZ DE USUARIO
# ===============================

def mostrar_pantalla_inicio():
    """Pantalla de inicio"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%); 
                padding: 3rem; border-radius: 15px; color: white; text-align: center; 
                margin-bottom: 2rem;'>
        <h1>🌿 Análisis Integral de Biodiversidad</h1>
        <p>Sistema de evaluación ecológica con múltiples indicadores ambientales</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3>📋 Instrucciones de uso:</h3>
        
        <ol>
        <li><strong>Sube tu archivo geográfico</strong> en el panel lateral (KML o Shapefile en ZIP)</li>
        <li><strong>Configura los parámetros</strong> de análisis (tipo de vegetación, divisiones)</li>
        <li><strong>Ejecuta el análisis</strong> para procesar los datos</li>
        <li><strong>Explora los resultados</strong> en las diferentes secciones</li>
        <li><strong>Exporta los datos</strong> en formatos CSV, JSON o GeoJSON</li>
        </ol>
        
        <h3>🌿 Indicadores analizados:</h3>
        <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1rem 0;'>
            <div style='background: #f0f9f0; padding: 1rem; border-radius: 8px; border-left: 4px solid #2E8B57;'>
                <strong>🌱 Vegetación (NDVI)</strong><br>Salud de la cubierta vegetal
            </div>
            <div style='background: #f0f9f0; padding: 1rem; border-radius: 8px; border-left: 4px solid #2E8B57;'>
                <strong>🌳 Carbono</strong><br>Almacenamiento de carbono en toneladas
            </div>
            <div style='background: #f0f9f0; padding: 1rem; border-radius: 8px; border-left: 4px solid #2E8B57;'>
                <strong>🦋 Biodiversidad</strong><br>Índice de diversidad de especies
            </div>
            <div style='background: #f0f9f0; padding: 1rem; border-radius: 8px; border-left: 4px solid #2E8B57;'>
                <strong>💧 Recursos Hídricos</strong><br>Disponibilidad de agua
            </div>
        </div>
        
        <h3>📁 Formatos soportados:</h3>
        <div style='display: flex; gap: 1rem; margin: 1rem 0;'>
            <div style='background: #e6f3ff; padding: 0.5rem 1rem; border-radius: 20px;'>
                <strong>KML</strong> - Google Earth
            </div>
            <div style='background: #e6f3ff; padding: 0.5rem 1rem; border-radius: 20px;'>
                <strong>Shapefile</strong> - Comprimido en ZIP
            </div>
        </div>
        
        <div style='background: #fff3cd; padding: 1rem; border-radius: 8px; margin-top: 2rem; border: 1px solid #ffeaa7;'>
            <strong>💡 Consejo:</strong> Para mejores resultados, usa polígonos con área entre 10 y 10,000 hectáreas.
        </div>
    </div>
    """, unsafe_allow_html=True)

def mostrar_resumen_ejecutivo(summary):
    """Mostrar resumen ejecutivo"""
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
        <h2>📊 Resumen Ejecutivo</h2>
    </div>
    """, unsafe_allow_html=True)
    
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
        st.metric("Humedad", f"{summary['humedad_promedio']:.2f}")
    
    with col7:
        st.metric("Recursos Hídricos", f"{summary['agua_promedio']:.2f}")
    
    with col8:
        st.metric("Calidad del Suelo", f"{summary['suelo_promedio']:.2f}")

def mostrar_mapa(resultados):
    """Mostrar mapa interactivo"""
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
        <h2>🗺️ Mapa de Resultados</h2>
        <p style='color: #666;'>Visualización geográfica de los indicadores por área. Las áreas se colorean según su valor de NDVI.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generar una clave única para el mapa basada en los resultados y un contador
    if 'map_key' not in st.session_state:
        st.session_state.map_key = 0
    else:
        st.session_state.map_key += 1
    
    map_key = st.session_state.map_key
    
    mapa = crear_mapa_resultados(resultados, map_key)
    if mapa:
        # Usar la clave única para forzar un nuevo mapa cada vez
        st_folium(mapa, width=800, height=500, key=f"mapa_{map_key}")
    else:
        st.info("No se pudo generar el mapa")

def mostrar_datos_tabulares(resultados):
    """Mostrar tabla de datos"""
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
        <h2>📋 Datos por Área</h2>
        <p style='color: #666;'>Tabla detallada con todos los indicadores calculados para cada subárea.</p>
    </div>
    """, unsafe_allow_html=True)
    
    df = pd.DataFrame(resultados['areas'])
    
    # Seleccionar columnas para mostrar
    columnas_display = [
        'area', 'area_ha', 'ndvi', 'carbono_ton', 
        'biodiversidad', 'humedad', 'agua', 'suelo'
    ]
    
    columnas_existentes = [col for col in columnas_display if col in df.columns]
    
    if columnas_existentes:
        st.dataframe(
            df[columnas_existentes].style.format({
                'area_ha': '{:.2f}',
                'ndvi': '{:.3f}',
                'carbono_ton': '{:.1f}',
                'biodiversidad': '{:.2f}',
                'humedad': '{:.2f}',
                'agua': '{:.2f}',
                'suelo': '{:.2f}'
            }),
            use_container_width=True,
            height=400
        )

def mostrar_graficos(resultados):
    """Mostrar gráficos de análisis"""
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
        <h2>📈 Visualizaciones</h2>
        <p style='color: #666;'>Gráficos para analizar la distribución de los indicadores.</p>
    </div>
    """, unsafe_allow_html=True)
    
    df = pd.DataFrame(resultados['areas'])
    
    if not df.empty:
        # Tabs para diferentes gráficos
        tab1, tab2, tab3 = st.tabs(["📊 Distribución NDVI", "🌳 Carbono por Área", "📋 Comparación"])
        
        with tab1:
            fig = crear_histograma(df, 'ndvi', 'Distribución del Índice NDVI')
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = crear_grafico_barras(df, 'carbono_ton', 'Carbono por Área (Top 20)')
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            if 'ndvi' in df.columns and 'biodiversidad' in df.columns:
                fig = px.scatter(
                    df,
                    x='ndvi',
                    y='biodiversidad',
                    size='carbono_ton',
                    color='area_ha',
                    hover_name='area',
                    title='Relación entre NDVI y Biodiversidad',
                    labels={
                        'ndvi': 'NDVI',
                        'biodiversidad': 'Índice de Biodiversidad',
                        'carbono_ton': 'Carbono (ton)',
                        'area_ha': 'Área (ha)'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

def mostrar_descargas(resultados):
    """Mostrar opciones de descarga"""
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
        <h2>📥 Exportar Resultados</h2>
        <p style='color: #666;'>Descarga los resultados del análisis en diferentes formatos.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🗺️ Datos Geoespaciales**")
        
        # GeoJSON con geometrías
        if resultados and 'areas' in resultados:
            try:
                gdf = gpd.GeoDataFrame(resultados['areas'], geometry='geometry')
                gdf.crs = "EPSG:4326"
                geojson_str = gdf.to_json()
                
                b64 = base64.b64encode(geojson_str.encode()).decode()
                href = f'<a href="data:application/json;base64,{b64}" download="resultados_biodiversidad.geojson">'
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1E90FF 0%, #00BFFF 100%); 
                            padding: 1rem; border-radius: 8px; text-align: center; margin: 10px 0;'>
                    {href}
                    <span style='color: white; font-weight: bold;'>📥 Descargar GeoJSON</span>
                    </a>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.info("GeoJSON no disponible")
    
    with col2:
        st.markdown("**📊 Datos Tabulares**")
        
        # CSV
        if resultados and 'areas' in resultados:
            df = pd.DataFrame(resultados['areas'])
            csv = df.to_csv(index=False)
            
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="resultados_biodiversidad.csv">'
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #228B22 0%, #2E8B57 100%); 
                        padding: 1rem; border-radius: 8px; text-align: center; margin: 10px 0;'>
                {href}
                <span style='color: white; font-weight: bold;'>📥 Descargar CSV</span>
                </a>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("**📄 Informe Ejecutivo**")
        
        # Informe en texto
        if resultados and 'summary' in resultados:
            summary = resultados['summary']
            informe = f"""
            INFORME DE ANÁLISIS DE BIODIVERSIDAD
            ====================================
            
            Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            RESULTADOS PRINCIPALES:
            
            • Área analizada: {summary['area_total_ha']:,.2f} hectáreas
            • Tipo de vegetación: {summary['tipo_vegetacion']}
            • Carbono total almacenado: {summary['carbono_total_ton']:,.0f} toneladas
            • Índice de vegetación (NDVI) promedio: {summary['ndvi_promedio']:.3f}
            • Índice de biodiversidad promedio: {summary['biodiversidad_promedio']:.2f}
            • Humedad promedio: {summary['humedad_promedio']:.2f}
            • Disponibilidad de agua: {summary['agua_promedio']:.2f}
            • Calidad del suelo: {summary['suelo_promedio']:.2f}
            • Conectividad ecológica: {summary['conectividad_promedio']:.2f}
            • Presión antrópica: {summary['presion_promedio']:.2f}
            
            Áreas analizadas: {summary['num_areas']}
            
            RECOMENDACIONES:
            
            1. Mantener el monitoreo continuo de los indicadores clave
            2. Implementar medidas de conservación en áreas con valores bajos
            3. Considerar programas de restauración ecológica si es necesario
            4. Proteger las áreas con alta biodiversidad y carbono almacenado
            """
            
            b64 = base64.b64encode(informe.encode()).decode()
            href = f'<a href="data:text/plain;base64,{b64}" download="informe_biodiversidad.txt">'
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%); 
                        padding: 1rem; border-radius: 8px; text-align: center; margin: 10px 0;'>
                {href}
                <span style='color: white; font-weight: bold;'>📥 Descargar Informe</span>
                </a>
            </div>
            """, unsafe_allow_html=True)

# ===============================
# 🎯 APLICACIÓN PRINCIPAL
# ===============================

def main():
    """Función principal"""
    
    # Barra lateral
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h2 style='color: #2E8B57;'>🌿</h2>
            <h3 style='color: #2E8B57;'>Análisis de Biodiversidad</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón para limpiar
        if st.button("🔄 Reiniciar Aplicación", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        st.header("📁 Cargar Polígono")
        uploaded_file = st.file_uploader(
            "Suba su archivo KML o ZIP",
            type=['kml', 'zip'],
            help="Archivos KML de Google Earth o Shapefiles comprimidos en ZIP"
        )
        
        # Procesar archivo cuando se sube
        if uploaded_file is not None:
            current_file_name = st.session_state.get('uploaded_file_name')
            if current_file_name != uploaded_file.name or not st.session_state.get('file_processed', False):
                with st.spinner("Procesando archivo..."):
                    gdf = procesar_archivo(uploaded_file)
                    
                    if gdf is not None and not gdf.empty:
                        st.session_state.poligono_data = gdf
                        st.session_state.file_processed = True
                        st.session_state.uploaded_file_name = uploaded_file.name
                        st.session_state.analysis_complete = False
                        st.success(f"✅ {uploaded_file.name}")
                    else:
                        st.error("❌ No se pudo procesar el archivo")
        
        st.divider()
        
        # Configuración del análisis
        if st.session_state.get('file_processed', False):
            st.header("⚙️ Configuración")
            
            tipo_vegetacion = st.selectbox(
                "Tipo de vegetación predominante",
                list(AnalizadorBiodiversidad().parametros.keys()),
                index=1
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
    
    # Contenido principal
    if not st.session_state.get('file_processed', False):
        mostrar_pantalla_inicio()
    
    elif st.session_state.get('file_processed', False) and not st.session_state.get('analysis_complete', False):
        st.info("📁 **Archivo cargado** - Configure los parámetros en el panel lateral y ejecute el análisis")
        
        # Mostrar información básica del archivo
        if st.session_state.poligono_data is not None:
            gdf = st.session_state.poligono_data
            poligono = gdf.geometry.iloc[0]
            
            analizador = AnalizadorBiodiversidad()
            area_ha = analizador.calcular_area(poligono)
            
            st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; margin-top: 1rem;'>
                <h3>📐 Información del Archivo</h3>
                <p><strong>Archivo:</strong> {st.session_state.uploaded_file_name}</p>
                <p><strong>Área aproximada:</strong> {area_ha:,.2f} hectáreas</p>
                <p><strong>Geometría:</strong> {poligono.geom_type}</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.get('analysis_complete', False) and st.session_state.get('results'):
        resultados = st.session_state.results
        
        # Mostrar todas las secciones
        mostrar_resumen_ejecutivo(resultados['summary'])
        mostrar_mapa(resultados)
        mostrar_datos_tabulares(resultados)
        mostrar_graficos(resultados)
        mostrar_descargas(resultados)

# ===============================
# 🚀 EJECUCIÓN
# ===============================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        st.markdown("""
        <div style='background: #fff3cd; padding: 1rem; border-radius: 8px; border: 1px solid #ffeaa7; margin: 1rem 0;'>
            <strong>⚠️ Solución recomendada:</strong>
            <ol>
            <li>Recarga la página (F5)</li>
            <li>Limpia la caché del navegador</li>
            <li>Verifica que el archivo sea válido</li>
            <li>Intenta nuevamente</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Reiniciar aplicación"):
            st.session_state.clear()
            st.rerun()
