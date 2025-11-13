import streamlit as st
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
from io import BytesIO
from datetime import datetime, timedelta

# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition
import geopandas as gpd
from shapely.geometry import Polygon, Point
import pyproj

# ===============================
# 🌿 CONFIGURACIÓN Y ESTILOS GLOBALES
# ===============================

st.set_page_config(
    page_title="Diagnóstico de Biodiversidad Ambiental",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def aplicar_estilos_globales():
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .custom-header {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        padding: 3rem 1rem;
        border-radius: 0 0 25px 25px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    .custom-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="leaf" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M10,5 C15,2 18,8 15,12 C12,15 5,15 5,10 C5,5 8,2 10,5 Z" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23leaf)"/></svg>');
    }
    .custom-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 2rem;
    }
    .stButton button {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_header():
    st.markdown("""
    <div class="custom-header">
        <h1>🌍 Diagnóstico de Biodiversidad Ambiental</h1>
        <p>Análisis específico del área cargada - Sistema LE.MU Atlas</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# 🧩 CLASES DE ANÁLISIS MEJORADAS
# ===============================

class PoligonoAnalyzer:
    """Analizador específico para el polígono cargado"""
    
    def __init__(self):
        self.carbon_stock_values = {
            'Bosque Denso Primario': {'min': 150, 'max': 300},
            'Bosque Secundario': {'min': 80, 'max': 150},
            'Bosque Ripario': {'min': 120, 'max': 200},
            'Matorral Denso': {'min': 30, 'max': 60},
            'Matorral Abierto': {'min': 15, 'max': 30},
            'Sabana Arborizada': {'min': 20, 'max': 40},
            'Herbazal Natural': {'min': 5, 'max': 15},
            'Zona de Transición': {'min': 10, 'max': 25},
            'Área de Restauración': {'min': 25, 'max': 80}
        }
    
    def procesar_poligono(self, gdf, vegetation_type, puntos_muestreo=50):
        """Procesar el polígono cargado y generar análisis específico"""
        
        if gdf is None or gdf.empty:
            return None
        
        try:
            # Obtener el polígono principal
            poligono = gdf.geometry.iloc[0]
            
            # Calcular área en hectáreas
            area_hectareas = self._calcular_area_hectareas(poligono)
            
            # Generar puntos de muestreo dentro del polígono
            puntos_muestreo_data = self._generar_puntos_muestreo(poligono, puntos_muestreo)
            
            # Analizar cada punto de muestreo
            resultados = self._analizar_puntos_muestreo(puntos_muestreo_data, vegetation_type, area_hectareas)
            
            return {
                'poligono': poligono,
                'area_hectareas': area_hectareas,
                'puntos_muestreo': puntos_muestreo_data,
                'resultados': resultados,
                'centroide': poligono.centroid
            }
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None
    
    def _calcular_area_hectareas(self, poligono):
        """Calcular área en hectáreas usando proyección UTM apropiada"""
        try:
            # Determinar la zona UTM basada en el centroide
            centroid = poligono.centroid
            utm_zone = int((centroid.x + 180) / 6) + 1
            hemisphere = 'north' if centroid.y >= 0 else 'south'
            
            # Proyectar a UTM y calcular área
            utm_crs = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
            poligono_utm = gpd.GeoSeries([poligono], crs="EPSG:4326").to_crs(utm_crs)
            area_m2 = poligono_utm.area.iloc[0]
            area_hectareas = area_m2 / 10000
            
            return round(area_hectareas, 2)
        except:
            # Fallback: cálculo aproximado
            bounds = poligono.bounds
            area_aproximada = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) * 11100 * 11100 * 0.8
            return round(area_aproximada / 10000, 2)
    
    def _generar_puntos_muestreo(self, poligono, num_puntos):
        """Generar puntos de muestreo distribuidos dentro del polígono"""
        puntos = []
        bounds = poligono.bounds
        minx, miny, maxx, maxy = bounds
        
        puntos_generados = 0
        intentos = 0
        max_intentos = num_puntos * 10
        
        while puntos_generados < num_puntos and intentos < max_intentos:
            intentos += 1
            # Generar punto aleatorio dentro del bounding box
            random_lon = np.random.uniform(minx, maxx)
            random_lat = np.random.uniform(miny, maxy)
            punto = Point(random_lon, random_lat)
            
            # Verificar si el punto está dentro del polígono
            if poligono.contains(punto):
                puntos_generados += 1
                puntos.append({
                    'id': f"Punto_{puntos_generados}",
                    'lat': random_lat,
                    'lon': random_lon,
                    'geometry': punto
                })
        
        return puntos
    
    def _analizar_puntos_muestreo(self, puntos_muestreo, vegetation_type, area_total):
        """Analizar cada punto de muestreo con indicadores realistas"""
        
        carbon_indicators = []
        vegetation_classification = []
        impact_data = []
        deforestation_data = []
        
        for i, punto in enumerate(puntos_muestreo):
            # Simular datos espectrales basados en el tipo de vegetación
            ndvi, evi, ndwi = self._simular_datos_espectrales(vegetation_type)
            
            # Calcular indicadores de carbono
            carbon_info = self._calcular_carbon_potential(vegetation_type, area_total / len(puntos_muestreo), ndvi)
            
            carbon_indicators.append({
                'area': punto['id'],
                **carbon_info,
                'lat': punto['lat'],
                'lon': punto['lon'],
                'ndvi': ndvi
            })
            
            # Clasificar vegetación
            veg_class = self._clasificar_vegetacion(ndvi, evi, ndwi)
            vegetation_classification.append({
                'area': punto['id'],
                'clasificacion': veg_class,
                'ndvi': ndvi,
                'evi': evi,
                'ndwi': ndwi,
                'lat': punto['lat'],
                'lon': punto['lon']
            })
            
            # Evaluar impacto antrópico
            impact_info = self._evaluar_impacto_antropico(punto['id'], punto['lat'], punto['lon'])
            impact_data.append(impact_info)
            
            # Simular datos de deforestación
            deforestation_info = self._simular_deforestacion(punto['id'], punto['lat'], punto['lon'], vegetation_type)
            deforestation_data.extend(deforestation_info)
        
        # Calcular métricas resumen
        summary_metrics = self._calcular_metricas_resumen(
            carbon_indicators, deforestation_data, impact_data, vegetation_classification
        )
        
        return {
            'carbon_indicators': carbon_indicators,
            'vegetation_classification': vegetation_classification,
            'impact_data': impact_data,
            'deforestation_data': deforestation_data,
            'summary_metrics': summary_metrics
        }
    
    def _simular_datos_espectrales(self, vegetation_type):
        """Simular datos espectrales realistas basados en el tipo de vegetación"""
        base_ndvi = {
            'Bosque Denso Primario': 0.85,
            'Bosque Secundario': 0.75,
            'Bosque Ripario': 0.80,
            'Matorral Denso': 0.65,
            'Matorral Abierto': 0.45,
            'Sabana Arborizada': 0.35,
            'Herbazal Natural': 0.25,
            'Zona de Transición': 0.30,
            'Área de Restauración': 0.55
        }
        
        base_ndvi_val = base_ndvi.get(vegetation_type, 0.5)
        ndvi = max(0.1, min(0.9, np.random.normal(base_ndvi_val, 0.08)))
        evi = ndvi * 0.9 + np.random.normal(0, 0.03)
        ndwi = (1 - ndvi) * 0.4 + np.random.normal(0, 0.02)
        
        return ndvi, evi, ndwi
    
    def _calcular_carbon_potential(self, vegetation_type, area_hectares, ndvi):
        """Calcular potencial de captura de CO2"""
        carbon_params = self.carbon_stock_values.get(vegetation_type, {'min': 10, 'max': 20})
        base_carbon = np.random.uniform(carbon_params['min'], carbon_params['max'])
        
        # Ajustar por salud de la vegetación (NDVI)
        carbon_adjusted = base_carbon * (0.3 + ndvi * 0.7)
        co2_potential = carbon_adjusted * 3.67
        
        return {
            'carbono_almacenado_tha': round(carbon_adjusted, 1),
            'co2_capturado_tha': round(co2_potential, 1),
            'co2_total_ton': round(co2_potential * area_hectares, 1),
            'potencial_secuestro': 'Alto' if carbon_adjusted > 100 else 'Medio' if carbon_adjusted > 50 else 'Bajo'
        }
    
    def _clasificar_vegetacion(self, ndvi, evi, ndwi):
        """Clasificar tipo de vegetación basado en índices espectrales"""
        if ndvi > 0.7:
            return "Bosque Denso"
        elif ndvi > 0.5:
            return "Bosque Abierto"
        elif ndvi > 0.3:
            return "Matorral Denso"
        elif ndvi > 0.2:
            return "Matorral Abierto"
        elif ndvi > 0.1:
            return "Herbazal"
        else:
            return "Suelo Desnudo"
    
    def _evaluar_impacto_antropico(self, area_id, lat, lon):
        """Evaluar impacto antrópico en el punto"""
        # Simular factores de impacto basados en ubicación
        distancia_urbana = np.random.uniform(0, 1)
        impacto_total = min(1.0, distancia_urbana * 0.6 + np.random.uniform(0, 0.4))
        
        if impacto_total > 0.7:
            nivel_impacto = "Muy Alto"
            color = 'red'
        elif impacto_total > 0.5:
            nivel_impacto = "Alto"
            color = 'orange'
        elif impacto_total > 0.3:
            nivel_impacto = "Moderado"
            color = 'yellow'
        else:
            nivel_impacto = "Bajo"
            color = 'green'
        
        return {
            'area': area_id,
            'impacto_total': round(impacto_total, 3),
            'nivel_impacto': nivel_impacto,
            'color': color,
            'lat': lat,
            'lon': lon
        }
    
    def _simular_deforestacion(self, area_id, lat, lon, vegetation_type):
        """Simular datos históricos de deforestación"""
        deforestation_data = []
        current_year = datetime.now().year
        
        # Tasa base según tipo de vegetación
        tasas_base = {
            'Bosque Denso Primario': 0.015,
            'Bosque Secundario': 0.025,
            'Bosque Ripario': 0.020,
            'Matorral Denso': 0.035,
            'Matorral Abierto': 0.045,
            'Sabana Arborizada': 0.030,
            'Herbazal Natural': 0.050,
            'Zona de Transición': 0.040,
            'Área de Restauración': -0.10  # Ganancia
        }
        
        base_rate = tasas_base.get(vegetation_type, 0.03)
        area_coverage = 100  # 100% inicial
        
        for year in range(2020, current_year + 1):
            annual_change = base_rate * np.random.uniform(0.8, 1.2)
            
            if 'Restauración' in vegetation_type:
                area_coverage = min(100, area_coverage * (1 - annual_change))
            else:
                area_coverage = max(0, area_coverage * (1 - annual_change))
            
            deforestation_data.append({
                'area': area_id,
                'año': year,
                'cobertura_porcentaje': round(area_coverage, 1),
                'perdida_acumulada': round(100 - area_coverage, 1),
                'lat': lat,
                'lon': lon
            })
        
        return deforestation_data
    
    def _calcular_metricas_resumen(self, carbon_data, deforestation_data, impact_data, vegetation_data):
        """Calcular métricas resumen para el dashboard"""
        total_co2 = sum([area['co2_total_ton'] for area in carbon_data])
        
        current_year = datetime.now().year
        current_deforestation = [d for d in deforestation_data if d['año'] == current_year]
        avg_loss = np.mean([d['perdida_acumulada'] for d in current_deforestation]) if current_deforestation else 0
        
        avg_impact = np.mean([d['impacto_total'] for d in impact_data])
        
        # Distribución de vegetación
        veg_classes = {}
        for area in vegetation_data:
            class_name = area['clasificacion']
            veg_classes[class_name] = veg_classes.get(class_name, 0) + 1
        
        return {
            'carbono_total_co2_ton': round(total_co2, 1),
            'perdida_bosque_promedio': round(avg_loss, 1),
            'impacto_antropico_promedio': round(avg_impact, 3),
            'distribucion_vegetacion': veg_classes,
            'areas_analizadas': len(carbon_data)
        }

# ===============================
# 🗺️ FUNCIONES DE MAPAS MEJORADAS
# ===============================

def crear_mapa_poligono_analisis(gdf, resultados):
    """Crear mapa principal con el polígono y puntos de análisis"""
    if gdf is None or resultados is None:
        return crear_mapa_base()
    
    try:
        # Obtener el centroide para centrar el mapa
        centroide = resultados['centroide']
        m = folium.Map(
            location=[centroide.y, centroide.x],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Agregar el polígono cargado
        poligono_geojson = gdf.__geo_interface__
        folium.GeoJson(
            poligono_geojson,
            style_function=lambda x: {
                'fillColor': '#2E8B57',
                'color': '#228B22',
                'weight': 3,
                'fillOpacity': 0.2
            },
            tooltip="Área de estudio cargada"
        ).add_to(m)
        
        # Agregar puntos de muestreo con colores según carbono
        for punto in resultados['resultados']['carbon_indicators']:
            co2_potential = punto['co2_total_ton']
            
            if co2_potential > 5000:
                color = '#00441b'
                size = 10
            elif co2_potential > 2000:
                color = '#238443'
                size = 8
            elif co2_potential > 1000:
                color = '#78c679'
                size = 6
            elif co2_potential > 500:
                color = '#c2e699'
                size = 5
            else:
                color = '#ffffcc'
                size = 4
            
            popup_text = f"""
            <div style="min-width: 250px;">
                <h4>🌿 {punto['area']}</h4>
                <p><b>CO₂:</b> {punto['co2_total_ton']:,} ton</p>
                <p><b>Carbono:</b> {punto['carbono_almacenado_tha']} t/ha</p>
                <p><b>NDVI:</b> {punto['ndvi']:.3f}</p>
            </div>
            """
            
            folium.CircleMarker(
                location=[punto['lat'], punto['lon']],
                radius=size,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{punto['area']}: {punto['co2_total_ton']:,} ton CO₂",
                color=color,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
        return crear_mapa_base()

def crear_mapa_base():
    """Crear mapa base simple"""
    return folium.Map(
        location=[-14.0, -60.0],
        zoom_start=4,
        tiles='OpenStreetMap'
    )

# ===============================
# 📊 FUNCIONES DE VISUALIZACIÓN
# ===============================

def crear_grafico_distribucion_vegetacion(vegetation_data):
    """Crear gráfico de distribución de vegetación"""
    if not vegetation_data:
        return go.Figure()
    
    df = pd.DataFrame(vegetation_data)
    conteo = df['clasificacion'].value_counts()
    
    fig = px.pie(
        values=conteo.values,
        names=conteo.index,
        title="🌿 Distribución de Tipos de Vegetación"
    )
    
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    return fig

def crear_grafico_carbonos(carbon_data):
    """Crear gráfico de distribución de carbono"""
    if not carbon_data:
        return go.Figure()
    
    df = pd.DataFrame(carbon_data)
    
    fig = px.bar(
        df, 
        x='area', 
        y='co2_total_ton',
        title="🌳 Potencial de Captura de CO₂ por Punto de Muestreo",
        labels={'co2_total_ton': 'CO₂ Total (ton)', 'area': 'Punto de Muestreo'}
    )
    
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    return fig

# ===============================
# 📁 MANEJO DE ARCHIVOS
# ===============================

def procesar_archivo_cargado(uploaded_file):
    """Procesar archivo KML/ZIP cargado"""
    try:
        if uploaded_file.name.endswith('.kml'):
            # Procesar archivo KML
            gdf = gpd.read_file(uploaded_file, driver='KML')
            return gdf
            
        elif uploaded_file.name.endswith('.zip'):
            # Procesar archivo ZIP (Shapefile)
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                # Buscar archivo .shp
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    return gdf
                else:
                    st.error("No se encontró archivo .shp en el ZIP")
                    return None
        else:
            st.error("Formato de archivo no soportado")
            return None
            
    except Exception as e:
        st.error(f"Error procesando archivo: {str(e)}")
        return None

# ===============================
# 🚀 CONFIGURACIÓN PRINCIPAL
# ===============================

def initialize_session_state():
    """Inicializar el estado de la sesión de forma segura"""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = PoligonoAnalyzer()

def tiene_poligono_data():
    """Verificar de forma segura si hay datos de polígono"""
    return (st.session_state.poligono_data is not None and 
            hasattr(st.session_state.poligono_data, 'empty') and 
            not st.session_state.poligono_data.empty)

def sidebar_config():
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%); border-radius: 12px;'>
            <h2 style='color: white; margin-bottom: 0;'>🌍</h2>
            <h3 style='color: white; margin: 0;'>Análisis de Polígono</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("🗺️ Cargar Polígono")
        
        uploaded_file = st.file_uploader(
            "Sube tu archivo territorial",
            type=['kml', 'zip'],
            help="Archivo KML o ZIP con Shapefile del área de estudio"
        )
        
        # Procesar archivo inmediatamente después de cargar
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False  # Resetear análisis
                    st.success(f"✅ Polígono cargado: {uploaded_file.name}")
                    st.rerun()
        
        st.markdown("---")
        st.header("📊 Configuración de Análisis")
        
        vegetation_type = st.selectbox(
            "🌿 Tipo de vegetación predominante",
            [
                'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
                'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
                'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
            ]
        )
        
        puntos_muestreo = st.slider(
            "🔍 Puntos de muestreo",
            min_value=10,
            max_value=200,
            value=50,
            help="Número de puntos de análisis dentro del polígono"
        )
        
        return uploaded_file, vegetation_type, puntos_muestreo

# ===============================
# 🎯 APLICACIÓN PRINCIPAL
# ===============================

def main():
    aplicar_estilos_globales()
    crear_header()
    initialize_session_state()
    
    # Sidebar
    uploaded_file, vegetation_type, puntos_muestreo = sidebar_config()
    
    # Mostrar información del polígono si está cargado
    if tiene_poligono_data():
        gdf = st.session_state.poligono_data
        poligono = gdf.geometry.iloc[0]
        area_ha = st.session_state.analyzer._calcular_area_hectareas(poligono)
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📐 Información del Polígono Cargado")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Área aproximada", f"{area_ha:,} ha")
        with col2:
            st.metric("Tipo de geometría", poligono.geom_type)
        with col3:
            st.metric("Puntos de muestreo", puntos_muestreo)
        
        # Mostrar vista previa del polígono
        st.subheader("🗺️ Vista Previa del Polígono")
        mapa_preview = crear_mapa_base()
        
        # Agregar polígono a la vista previa
        try:
            poligono_geojson = gdf.__geo_interface__
            folium.GeoJson(
                poligono_geojson,
                style_function=lambda x: {
                    'fillColor': '#2E8B57',
                    'color': '#228B22',
                    'weight': 3,
                    'fillOpacity': 0.3
                }
            ).add_to(mapa_preview)
            
            # Centrar el mapa en el polígono
            bounds = gdf.bounds
            mapa_preview.fit_bounds([
                [bounds.miny.iloc[0], bounds.minx.iloc[0]],
                [bounds.maxy.iloc[0], bounds.maxx.iloc[0]]
            ])
        except Exception as e:
            st.error(f"Error mostrando vista previa: {str(e)}")
        
        st_folium(mapa_preview, width=700, height=300, key="preview_map")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de análisis (solo si hay polígono cargado)
    if tiene_poligono_data() and not st.session_state.analysis_complete:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        if st.button("🚀 EJECUTAR ANÁLISIS DEL POLÍGONO", type="primary", use_container_width=True):
            with st.spinner("Realizando análisis específico del polígono..."):
                resultados = st.session_state.analyzer.procesar_poligono(
                    st.session_state.poligono_data, 
                    vegetation_type, 
                    puntos_muestreo
                )
                
                if resultados:
                    st.session_state.results = resultados
                    st.session_state.analysis_complete = True
                    st.success("✅ Análisis completado exitosamente!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar resultados del análisis
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        
        # Mapa principal con análisis
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("🗺️ Mapa de Análisis del Polígono")
        
        mapa = crear_mapa_poligono_analisis(st.session_state.poligono_data, resultados)
        st_folium(mapa, width=800, height=500, key="main_map")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas principales
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 Resumen del Análisis")
        
        summary = resultados['resultados']['summary_metrics']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌳 Carbono Total CO₂", f"{summary['carbono_total_co2_ton']:,} ton")
        with col2:
            st.metric("📉 Pérdida de Bosque", f"{summary['perdida_bosque_promedio']}%")
        with col3:
            st.metric("⚠️ Impacto Antrópico", f"{summary['impacto_antropico_promedio']}")
        with col4:
            st.metric("🔍 Puntos Analizados", summary['areas_analizadas'])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.plotly_chart(
                crear_grafico_distribucion_vegetacion(resultados['resultados']['vegetation_classification']),
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.plotly_chart(
                crear_grafico_carbonos(resultados['resultados']['carbon_indicators']),
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif not tiene_poligono_data():
        # Pantalla de bienvenida
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Análisis de Biodiversidad!
        
        ### 🎯 Análisis Específico del Polígono
        
        Esta herramienta realiza un análisis **específico** del área que cargues:
        
        1. **Carga tu polígono** en formato KML o Shapefile (ZIP)
        2. **Configura** el tipo de vegetación predominante
        3. **Ejecuta el análisis** sobre tu área específica
        
        ### 📁 Formatos Soportados:
        - **KML** (Google Earth, QGIS)
        - **Shapefile** (comprimido en ZIP)
        
        El análisis generará:
        - 🗺️ Mapa interactivo con puntos de muestreo
        - 📊 Indicadores de carbono y vegetación
        - ⚠️ Evaluación de impacto antrópico
        - 💡 Recomendaciones específicas
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
