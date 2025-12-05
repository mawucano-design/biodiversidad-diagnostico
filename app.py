# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st

# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Dashboard Analítico de Biodiversidad",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ahora sí, el resto de los imports
import pandas as pd
import numpy as np
import tempfile
import os
import zipfile
import math
from math import log
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from io import BytesIO
from datetime import datetime, timedelta
import json
import base64
import warnings
warnings.filterwarnings('ignore')

# Librerías geoespaciales
import folium
from streamlit_folium import st_folium, folium_static
from folium.plugins import Fullscreen, MousePosition, HeatMap, MarkerCluster, Draw
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm

# Manejo alternativo de KML
try:
    from pykml import parser as pykml_parser
    from lxml import etree
    KML_AVAILABLE = True
except ImportError:
    KML_AVAILABLE = False

# ===============================
# 🌿 CONFIGURACIÓN Y ESTILOS GLOBALES - ESTILO ANALÍTICO
# ===============================
def aplicar_estilos_globales():
    st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stApp {
        background: #f0f2f6;
    }
    .analytics-header {
        background: white;
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: #1e3a8a;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-bottom: 4px solid #3b82f6;
    }
    .analytics-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #1e3a8a;
    }
    .kpi-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid;
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 1.5rem;
    }
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e3a8a;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .map-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    .folium-map {
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_header_analitico():
    st.markdown("""
    <div class="analytics-header">
        <h1>📊 Dashboard Analítico de Biodiversidad</h1>
        <p style="color: #6b7280; font-size: 1.1rem;">Sistema de monitoreo y análisis ambiental con indicadores empresariales</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# 🗺️ FUNCIONES DE MAPAS SIMPLIFICADAS Y CORREGIDAS
# ===============================
def crear_mapa_base_simple(gdf, titulo="Área de Estudio"):
    """Crear mapa base SIMPLE y FUNCIONAL con el polígono"""
    try:
        # Crear mapa centrado en América del Sur por defecto
        m = folium.Map(location=[-14.0, -60.0], zoom_start=4, control_scale=True)
        
        # Agregar capas base
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery',
            name='Satélite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            'OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Si hay datos geoespaciales, agregar el polígono
        if gdf is not None and not gdf.empty:
            try:
                # Obtener el primer polígono
                poligono = gdf.geometry.iloc[0]
                
                # Agregar polígono con estilo
                folium.GeoJson(
                    poligono,
                    style_function=lambda x: {
                        'fillColor': '#3b82f6',
                        'color': '#1d4ed8',
                        'weight': 3,
                        'fillOpacity': 0.2,
                        'dashArray': '5, 5'
                    },
                    name='Área de Estudio',
                    tooltip=folium.Tooltip(titulo, sticky=True)
                ).add_to(m)
                
                # Centrar el mapa en el polígono
                bounds = gdf.total_bounds
                if len(bounds) == 4:
                    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
                
            except Exception as e:
                st.warning(f"Error al agregar polígono al mapa: {str(e)}")
        
        # Agregar controles básicos
        folium.LayerControl().add_to(m)
        Fullscreen().add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error crítico creando mapa base: {str(e)}")
        # Mapa de respaldo extremadamente simple
        m = folium.Map(location=[-14.0, -60.0], zoom_start=4)
        folium.TileLayer('OpenStreetMap').add_to(m)
        return m

def crear_mapa_indicador_simple(gdf, datos_indicador, config_indicador):
    """Crear mapa SIMPLE para un indicador específico"""
    try:
        # Crear mapa base
        m = crear_mapa_base_simple(gdf, config_indicador['titulo'])
        
        if datos_indicador is None or len(datos_indicador) == 0:
            return m
        
        # Agregar marcadores para cada área
        for area_data in datos_indicador:
            try:
                valor = area_data.get(config_indicador['columna'], 0)
                geometry = area_data.get('geometry')
                area_id = area_data.get('area', 'Desconocido')
                
                if geometry and hasattr(geometry, 'centroid'):
                    # Obtener centroide
                    centroid = geometry.centroid
                    lat, lon = centroid.y, centroid.x
                    
                    # Determinar color basado en el valor
                    color = '#808080'  # Gris por defecto
                    for rango, color_rango in config_indicador['colores'].items():
                        if rango[0] <= valor <= rango[1]:
                            color = color_rango
                            break
                    
                    # Crear popup simple
                    popup_text = f"""
                    <b>{area_id}</b><br>
                    {config_indicador['titulo']}: {valor:.2f}<br>
                    Lat: {lat:.4f}, Lon: {lon:.4f}
                    """
                    
                    # Agregar marcador
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=8,
                        popup=popup_text,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7,
                        tooltip=f"{area_id}: {valor:.2f}"
                    ).add_to(m)
                    
            except Exception as e:
                continue  # Saltar áreas problemáticas
        
        return m
        
    except Exception as e:
        st.error(f"Error creando mapa de indicador: {str(e)}")
        return crear_mapa_base_simple(gdf)

# ===============================
# FUNCIONES DE PROCESAMIENTO DE ARCHIVOS
# ===============================
def procesar_archivo_cargado(uploaded_file):
    """Procesar archivo KML/ZIP cargado"""
    try:
        if uploaded_file.name.endswith('.kml'):
            try:
                gdf = gpd.read_file(uploaded_file, driver='KML')
                if not gdf.empty:
                    st.success("✅ Archivo KML procesado")
                    return gdf
            except Exception as e1:
                st.warning(f"Intentando método alternativo para KML: {str(e1)}")
                # Método simple para KML
                uploaded_file.seek(0)
                contenido = uploaded_file.read().decode('utf-8')
                import re
                coord_pattern = r'<coordinates>([^<]+)</coordinates>'
                matches = re.findall(coord_pattern, contenido, re.IGNORECASE)
                
                if matches:
                    geometries = []
                    for match in matches:
                        points = []
                        for coord in match.strip().split():
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                try:
                                    lon = float(parts[0].strip())
                                    lat = float(parts[1].strip())
                                    points.append((lon, lat))
                                except:
                                    continue
                        if len(points) >= 3:
                            geometries.append(Polygon(points))
                    
                    if geometries:
                        gdf = gpd.GeoDataFrame({'geometry': geometries}, crs="EPSG:4326")
                        st.success("✅ Archivo KML procesado manualmente")
                        return gdf
                
                st.error("No se pudo procesar el archivo KML")
                return None
                
        elif uploaded_file.name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # Buscar archivos shapefile
                for root, dirs, files in os.walk(tmpdir):
                    for file in files:
                        if file.endswith('.shp'):
                            shp_path = os.path.join(root, file)
                            gdf = gpd.read_file(shp_path)
                            st.success("✅ Archivo SHP procesado")
                            return gdf
                
                st.error("No se encontró archivo .shp en el ZIP")
                return None
        
        elif uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
            try:
                gdf = gpd.read_file(uploaded_file)
                st.success("✅ Archivo GeoJSON procesado")
                return gdf
            except Exception as e:
                st.error(f"Error procesando GeoJSON: {str(e)}")
                return None
        
        return None
        
    except Exception as e:
        st.error(f"Error procesando archivo: {str(e)}")
        return None

# ===============================
# 🧩 CLASE PRINCIPAL DE ANÁLISIS SIMPLIFICADA
# ===============================
class AnalizadorBiodiversidad:
    """Analizador SIMPLIFICADO de biodiversidad"""
    
    def __init__(self):
        self.parametros_ecosistemas = {
            'Bosque Denso Primario': {'ndvi_base': 0.85, 'carbono': 250},
            'Bosque Secundario': {'ndvi_base': 0.75, 'carbono': 120},
            'Bosque Ripario': {'ndvi_base': 0.80, 'carbono': 170},
            'Matorral Denso': {'ndvi_base': 0.65, 'carbono': 55},
            'Matorral Abierto': {'ndvi_base': 0.45, 'carbono': 30},
        }
    
    def _calcular_area_aproximada(self, poligono):
        """Cálculo aproximado del área en hectáreas"""
        try:
            bounds = poligono.bounds
            lat_centro = (bounds[1] + bounds[3]) / 2
            cos_lat = math.cos(math.radians(lat_centro))
            area_grados = poligono.area
            area_km2 = area_grados * 111 * 111 * cos_lat
            return round(area_km2 * 100, 2)
        except:
            return 0
    
    def procesar_poligono(self, gdf, tipo_vegetacion, n_divisiones=5):
        """Método SIMPLIFICADO para procesar el polígono"""
        try:
            if gdf is None or gdf.empty:
                st.error("No hay datos geoespaciales para procesar")
                return None
            
            poligono_principal = gdf.geometry.iloc[0]
            area_total = self._calcular_area_aproximada(poligono_principal)
            
            # Dividir polígono en áreas (simplificado)
            bounds = poligono_principal.bounds
            minx, miny, maxx, maxy = bounds
            
            areas_analisis = []
            id_celda = 1
            
            for i in range(n_divisiones):
                for j in range(n_divisiones):
                    xmin = minx + (i * (maxx-minx)/n_divisiones)
                    xmax = xmin + (maxx-minx)/n_divisiones
                    ymin = miny + (j * (maxy-miny)/n_divisiones)
                    ymax = ymin + (maxy-miny)/n_divisiones
                    
                    celda_rect = Polygon([
                        (xmin, ymin), (xmax, ymin),
                        (xmax, ymax), (xmin, ymax), (xmin, ymin)
                    ])
                    
                    interseccion = poligono_principal.intersection(celda_rect)
                    if not interseccion.is_empty:
                        areas_analisis.append({
                            'id': id_celda,
                            'area': f"Área-{id_celda}",
                            'geometry': interseccion,
                            'centroid': interseccion.centroid,
                            'area_ha': self._calcular_area_aproximada(interseccion)
                        })
                        id_celda += 1
            
            # Obtener parámetros base
            params = self.parametros_ecosistemas.get(tipo_vegetacion, 
                                                    self.parametros_ecosistemas['Bosque Secundario'])
            
            # Calcular indicadores para cada área
            resultados_vegetacion = []
            resultados_carbono = []
            resultados_biodiversidad = []
            
            for area in areas_analisis:
                area_id = area['area']
                area_ha = area['area_ha']
                
                # NDVI con variación aleatoria
                ndvi_base = params['ndvi_base']
                ndvi = ndvi_base + np.random.uniform(-0.2, 0.2)
                ndvi = max(0.1, min(1.0, ndvi))
                
                # Salud vegetación
                if ndvi >= 0.7:
                    salud = "Excelente"
                elif ndvi >= 0.5:
                    salud = "Buena"
                elif ndvi >= 0.3:
                    salud = "Moderada"
                else:
                    salud = "Degradada"
                
                resultados_vegetacion.append({
                    'area': area_id,
                    'ndvi': round(ndvi, 3),
                    'salud_vegetacion': salud,
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Carbono
                carbono_ton_ha = params['carbono'] + np.random.uniform(-50, 50)
                co2_total = carbono_ton_ha * area_ha * 3.67
                
                resultados_carbono.append({
                    'area': area_id,
                    'carbono_ton_ha': round(carbono_ton_ha, 2),
                    'co2_total_ton': round(co2_total, 2),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Biodiversidad (índice de Shannon)
                indice_shannon = 1.5 + np.random.uniform(-0.8, 0.8)
                indice_shannon = max(0.1, min(3.0, indice_shannon))
                
                if indice_shannon >= 2.0:
                    estado_biod = "Alta"
                elif indice_shannon >= 1.0:
                    estado_biod = "Moderada"
                else:
                    estado_biod = "Baja"
                
                resultados_biodiversidad.append({
                    'area': area_id,
                    'indice_shannon': round(indice_shannon, 3),
                    'estado_biodiversidad': estado_biod,
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
            
            # Calcular resumen
            summary_metrics = {
                'estado_general': "Bueno" if np.mean([r['ndvi'] for r in resultados_vegetacion]) > 0.5 else "Moderado",
                'carbono_total_co2_ton': round(sum([r['co2_total_ton'] for r in resultados_carbono]), 2),
                'indice_biodiversidad_promedio': round(np.mean([r['indice_shannon'] for r in resultados_biodiversidad]), 3),
                'areas_analizadas': len(areas_analisis),
                'area_total_ha': area_total
            }
            
            # Compilar resultados
            resultados = {
                'resultados': {
                    'vegetacion': resultados_vegetacion,
                    'carbono': resultados_carbono,
                    'biodiversidad': resultados_biodiversidad,
                    'summary_metrics': summary_metrics
                },
                'areas_analisis': areas_analisis,
                'area_hectareas': area_total,
                'tipo_vegetacion': tipo_vegetacion
            }
            
            return resultados
            
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None

# ===============================
# 📊 FUNCIONES DE GRÁFICOS SIMPLIFICADAS
# ===============================
def crear_kpi_card(titulo, valor, icono, color, unidad=""):
    """Crear tarjeta KPI simple"""
    return f"""
    <div class="kpi-card" style="border-left-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <div class="metric-label">{titulo}</div>
                <div class="metric-value" style="color: {color};">{valor}</div>
                <div style="font-size: 0.9rem; color: #6b7280;">{unidad}</div>
            </div>
            <div style="font-size: 2rem; color: {color};">{icono}</div>
        </div>
    </div>
    """

# ===============================
# 🚀 CONFIGURACIÓN PRINCIPAL
# ===============================
def initialize_session_state():
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = AnalizadorBiodiversidad()

def tiene_poligono_data():
    return (st.session_state.poligono_data is not None and 
            not st.session_state.poligono_data.empty)

# ===============================
# 🎯 APLICACIÓN PRINCIPAL CORREGIDA
# ===============================
def main():
    aplicar_estilos_globales()
    crear_header_analitico()
    initialize_session_state()
    
    # Sidebar simplificado
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        uploaded_file = st.file_uploader(
            "📁 Cargar archivo territorial", 
            type=['kml', 'zip', 'geojson'],
            help="Formatos soportados: KML, GeoJSON, Shapefile (ZIP)"
        )
        
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None and not gdf.empty:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False
                    st.success("✅ Polígono cargado")
                    st.rerun()
        
        if tiene_poligono_data():
            st.markdown("---")
            vegetation_type = st.selectbox(
                "🌿 Tipo de vegetación",
                ['Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
                 'Matorral Denso', 'Matorral Abierto']
            )
            
            divisiones = st.slider("🔲 Nivel de detalle", 3, 7, 4)
            
            if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
                with st.spinner("Analizando..."):
                    resultados = st.session_state.analyzer.procesar_poligono(
                        st.session_state.poligono_data, vegetation_type, divisiones
                    )
                    if resultados:
                        st.session_state.results = resultados
                        st.session_state.analysis_complete = True
                        st.success("✅ Análisis completado")
                        st.rerun()
    
    # Sección principal
    if tiene_poligono_data():
        gdf = st.session_state.poligono_data
        
        # Mapa base - SIEMPRE VISIBLE
        st.markdown("## 🗺️ Visualización del Área de Estudio")
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        
        # Crear y mostrar mapa base
        mapa_base = crear_mapa_base_simple(gdf, "Área de Estudio Cargada")
        
        # Usar folium_static en lugar de st_folium para mayor compatibilidad
        from streamlit_folium import folium_static
        folium_static(mapa_base, width=800, height=500)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Información del área
        col1, col2, col3 = st.columns(3)
        with col1:
            try:
                area_ha = st.session_state.analyzer._calcular_area_aproximada(gdf.geometry.iloc[0])
                st.metric("Área Total", f"{area_ha:,.0f} ha")
            except:
                st.metric("Área Total", "N/A")
        
        with col2:
            st.metric("Tipo de Geometría", gdf.geometry.iloc[0].geom_type)
        
        with col3:
            bounds = gdf.total_bounds
            if len(bounds) == 4:
                st.metric("Centro", f"{bounds[1]:.4f}, {bounds[0]:.4f}")
    
    # Mostrar resultados del análisis
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
        st.markdown("## 📊 Resultados del Análisis")
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(crear_kpi_card(
                "Estado General", 
                summary['estado_general'], 
                "📈", 
                "#10b981" if summary['estado_general'] == "Bueno" else "#f59e0b"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(crear_kpi_card(
                "Carbono Total", 
                f"{summary['carbono_total_co2_ton']:,.0f}", 
                "🌳", 
                "#065f46",
                unidad="ton CO₂"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(crear_kpi_card(
                "Biodiversidad", 
                f"{summary['indice_biodiversidad_promedio']:.2f}", 
                "🦋", 
                "#3b82f6",
                unidad="Índice"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(crear_kpi_card(
                "Áreas Analizadas", 
                f"{summary['areas_analizadas']}", 
                "📍", 
                "#8b5cf6"
            ), unsafe_allow_html=True)
        
        # ==================== MAPAS POR INDICADOR ====================
        st.markdown("## 📍 Mapas por Indicador")
        
        # Configuración SIMPLIFICADA de indicadores
        indicadores_config = [
            {
                'key': 'vegetacion',
                'titulo': '🌿 Salud de la Vegetación (NDVI)',
                'columna': 'ndvi',
                'descripcion': 'Índice de Vegetación de Diferencia Normalizada',
                'colores': {
                    (0, 0.3): '#FF4500',
                    (0.3, 0.5): '#FFD700',
                    (0.5, 0.7): '#32CD32', 
                    (0.7, 1.0): '#006400'
                },
                'leyenda': {
                    (0, 0.3): 'Degradada',
                    (0.3, 0.5): 'Moderada',
                    (0.5, 0.7): 'Buena',
                    (0.7, 1.0): 'Excelente'
                }
            },
            {
                'key': 'carbono',
                'titulo': '🌳 Almacenamiento de Carbono',
                'columna': 'co2_total_ton',
                'descripcion': 'Carbono almacenado en toneladas de CO₂',
                'colores': {
                    (0, 1000): '#ffffcc',
                    (1000, 5000): '#c2e699', 
                    (5000, 10000): '#78c679',
                    (10000, 50000): '#238443'
                },
                'leyenda': {
                    (0, 1000): '< 1K ton',
                    (1000, 5000): '1K-5K ton',
                    (5000, 10000): '5K-10K ton',
                    (10000, 50000): '> 10K ton'
                }
            },
            {
                'key': 'biodiversidad', 
                'titulo': '🦋 Índice de Biodiversidad',
                'columna': 'indice_shannon',
                'descripcion': 'Índice de Shannon-Wiener',
                'colores': {
                    (0, 1.0): '#FF4500',
                    (1.0, 1.5): '#FFD700',
                    (1.5, 2.0): '#32CD32',
                    (2.0, 3.0): '#006400'
                },
                'leyenda': {
                    (0, 1.0): 'Baja',
                    (1.0, 1.5): 'Moderada', 
                    (1.5, 2.0): 'Alta',
                    (2.0, 3.0): 'Muy Alta'
                }
            }
        ]
        
        # Mostrar mapas en tabs - VERSIÓN SIMPLIFICADA Y FUNCIONAL
        tabs = st.tabs([config['titulo'].split()[0] for config in indicadores_config])
        
        for idx, (tab, config) in enumerate(zip(tabs, indicadores_config)):
            with tab:
                st.subheader(config['titulo'])
                st.caption(config['descripcion'])
                
                # Crear y mostrar mapa del indicador
                datos_mapa = resultados['resultados'].get(config['key'], [])
                
                if datos_mapa:
                    # Crear mapa simple
                    mapa_indicador = crear_mapa_indicador_simple(
                        st.session_state.poligono_data,
                        datos_mapa,
                        config
                    )
                    
                    # Mostrar mapa
                    if mapa_indicador:
                        folium_static(mapa_indicador, width=800, height=500)
                    else:
                        st.warning("No se pudo crear el mapa. Mostrando mapa base...")
                        folium_static(crear_mapa_base_simple(st.session_state.poligono_data), 
                                    width=800, height=500)
                
                # Mostrar tabla de datos
                with st.expander("📋 Ver datos detallados"):
                    df = pd.DataFrame(datos_mapa)
                    if not df.empty:
                        st.dataframe(df[['area', config['columna'], 'area_ha']].head(10))
        
        # ==================== GRÁFICOS SIMPLES ====================
        st.markdown("## 📈 Visualizaciones de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de NDVI
            df_vegetacion = pd.DataFrame(resultados['resultados']['vegetacion'])
            if not df_vegetacion.empty:
                fig = px.bar(df_vegetacion.head(10), x='area', y='ndvi',
                           title='NDVI por Área (Top 10)',
                           color='ndvi',
                           color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de carbono
            df_carbono = pd.DataFrame(resultados['resultados']['carbono'])
            if not df_carbono.empty:
                fig = px.bar(df_carbono.head(10), x='area', y='co2_total_ton',
                           title='Carbono por Área (Top 10)',
                           color='co2_total_ton',
                           color_continuous_scale='greens')
                st.plotly_chart(fig, use_container_width=True)
        
        # ==================== DESCARGAS ====================
        st.markdown("## 📥 Exportar Resultados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Descargar Resumen CSV", use_container_width=True):
                # Crear CSV combinado
                datos_combinados = []
                vegetacion = resultados['resultados']['vegetacion']
                carbono = resultados['resultados']['carbono']
                biodiversidad = resultados['resultados']['biodiversidad']
                
                for i in range(len(vegetacion)):
                    fila = {
                        'area': vegetacion[i]['area'],
                        'ndvi': vegetacion[i]['ndvi'],
                        'salud_vegetacion': vegetacion[i]['salud_vegetacion'],
                        'co2_total_ton': carbono[i]['co2_total_ton'] if i < len(carbono) else 0,
                        'indice_shannon': biodiversidad[i]['indice_shannon'] if i < len(biodiversidad) else 0,
                        'area_ha': vegetacion[i]['area_ha']
                    }
                    datos_combinados.append(fila)
                
                df_export = pd.DataFrame(datos_combinados)
                csv = df_export.to_csv(index=False)
                
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv,
                    file_name="resultados_analisis.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Resumen ejecutivo
            resumen_text = f"""
ANÁLISIS DE BIODIVERSIDAD
=========================

Fecha: {datetime.now().strftime('%d/%m/%Y')}

RESUMEN:
• Área total: {summary['area_total_ha']:,.0f} ha
• Tipo de vegetación: {resultados['tipo_vegetacion']}
• Estado general: {summary['estado_general']}
• Carbono total: {summary['carbono_total_co2_ton']:,.0f} ton CO₂
• Biodiversidad promedio: {summary['indice_biodiversidad_promedio']:.2f}
• Áreas analizadas: {summary['areas_analizadas']}
            """
            
            st.download_button(
                label="📋 Descargar Resumen",
                data=resumen_text,
                file_name="resumen_analisis.txt",
                mime="text/plain"
            )
    
    # ==================== PANTALLA DE INICIO ====================
    elif not tiene_poligono_data():
        st.markdown("## 👋 Bienvenido al Dashboard de Biodiversidad")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            ### 🚀 ¿Cómo comenzar?
            
            1. **Carga tu polígono** en el panel lateral (formato KML, GeoJSON o Shapefile en ZIP)
            2. **Configura los parámetros** de análisis
            3. **Ejecuta el análisis** para obtener resultados
            
            ### 📋 Formatos soportados:
            - **KML** (.kml) - Google Earth
            - **GeoJSON** (.geojson, .json)
            - **Shapefile** (.zip con .shp, .shx, .dbf, .prj)
            
            ### 📊 Indicadores que se analizan:
            - 🌿 Salud de la vegetación (NDVI)
            - 🌳 Captura de carbono
            - 🦋 Biodiversidad
            """)
        
        with col2:
            st.success("""
            ### ✅ Prueba rápida:
            
            Si no tienes un archivo, puedes:
            
            1. Buscar ejemplos de KML en internet
            2. Crear un polígono simple en Google Earth y exportarlo como KML
            3. Usar datos de muestra de proyectos ambientales
            """)
            
            # Ejemplo de polígono simple
            if st.button("🧪 Cargar ejemplo de prueba"):
                # Crear un polígono simple para prueba
                polygon = Polygon([
                    (-60.0, -14.0),
                    (-59.5, -14.0),
                    (-59.5, -13.5),
                    (-60.0, -13.5),
                    (-60.0, -14.0)
                ])
                gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
                st.session_state.poligono_data = gdf
                st.session_state.file_processed = True
                st.success("✅ Ejemplo cargado. Ahora configura los parámetros en el sidebar.")
                st.rerun()

if __name__ == "__main__":
    main()
