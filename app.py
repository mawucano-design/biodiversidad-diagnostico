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
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition, HeatMap, MarkerCluster
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

# ⚠️ scipy debe estar en requirements.txt
try:
    from scipy import interpolate
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Manejo de docx - ESTO DEBE IR DESPUÉS de st.set_page_config()
try:
    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

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
    .metric-change {
        font-size: 0.8rem;
        padding: 2px 8px;
        border-radius: 12px;
        display: inline-block;
    }
    .positive {
        background-color: #d1fae5;
        color: #065f46;
    }
    .negative {
        background-color: #fee2e2;
        color: #991b1b;
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
    .tab-content {
        padding: 1rem 0;
    }
    .data-table {
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .insight-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #0ea5e9;
        margin-bottom: 1rem;
    }
    .download-btn-analytics {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        margin: 5px;
        padding: 10px 20px;
        border-radius: 8px;
        color: white;
        text-decoration: none;
        display: inline-block;
        font-weight: 600;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .download-btn-analytics:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateY(-1px);
    }
    .sidebar-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .filter-header {
        font-size: 0.9rem;
        font-weight: 600;
        color: #4b5563;
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
        margin: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_header_analitico():
    st.markdown("""
    <div class="analytics-header">
        <h1>📊 Dashboard Analítico de Biodiversidad</h1>
        <p style="color: #6b7280; font-size: 1.1rem;">Sistema de monitoreo y análisis ambiental con indicadores empresariales</p>
        <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1rem; flex-wrap: wrap;">
            <span style="background: #f3f4f6; padding: 6px 12px; border-radius: 20px; font-size: 0.9rem; color: #4b5563;">🌿 Análisis Ambiental</span>
            <span style="background: #f3f4f6; padding: 6px 12px; border-radius: 20px; font-size: 0.9rem; color: #4b5563;">📈 KPIs de Desempeño</span>
            <span style="background: #f3f4f6; padding: 6px 12px; border-radius: 20px; font-size: 0.9rem; color: #4b5563;">🗺️ Visualización Geoespacial</span>
            <span style="background: #f3f4f6; padding: 6px 12px; border-radius: 20px; font-size: 0.9rem; color: #4b5563;">📊 Reportes Ejecutivos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# FUNCIONES DE PROCESAMIENTO DE ARCHIVOS
# ===============================
def procesar_kml_pykml(archivo_kml):
    """Procesar archivo KML usando pykml como alternativa"""
    try:
        contenido = archivo_kml.read().decode('utf-8')
        root = etree.fromstring(contenido.encode('utf-8'))
        geometries = []
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        for polygon in root.xpath('.//kml:Polygon', namespaces=ns):
            coordinates = polygon.xpath('.//kml:coordinates', namespaces=ns)
            if coordinates:
                coord_text = coordinates[0].text.strip()
                points = []
                for line in coord_text.split():
                    if line.strip():
                        try:
                            lon, lat, _ = line.split(',')
                            points.append((float(lon), float(lat)))
                        except:
                            pass
                if len(points) >= 3:
                    geometries.append(Polygon(points))
        
        if geometries:
            gdf = gpd.GeoDataFrame({'geometry': geometries}, crs="EPSG:4326")
            return gdf
        else:
            st.warning("No se encontraron polígonos en el archivo KML")
            return None
            
    except Exception as e:
        st.error(f"Error procesando KML: {str(e)}")
        return None

def procesar_archivo_cargado(uploaded_file):
    """Procesar archivo KML/ZIP cargado con manejo mejorado de errores"""
    try:
        if uploaded_file.name.endswith('.kml'):
            try:
                gdf = gpd.read_file(uploaded_file, driver='KML')
                if not gdf.empty:
                    st.success("✅ Archivo KML procesado")
                    return gdf
            except Exception as e1:
                st.warning(f"GeoPandas no pudo leer el KML: {str(e1)}")
                if KML_AVAILABLE:
                    uploaded_file.seek(0)
                    gdf = procesar_kml_pykml(uploaded_file)
                    if gdf is not None and not gdf.empty:
                        st.success("✅ Archivo KML procesado con pykml")
                        return gdf
                
                st.info("Intentando procesar KML manualmente...")
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
                
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                kml_files = [f for f in os.listdir(tmpdir) if f.endswith('.kml')]
                
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    st.success(f"✅ Archivo SHP procesado")
                    return gdf
                elif kml_files:
                    kml_path = os.path.join(tmpdir, kml_files[0])
                    with open(kml_path, 'r') as f:
                        contenido = f.read()
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.kml', delete=False) as tmp:
                        tmp.write(contenido)
                        tmp_path = tmp.name
                    
                    try:
                        gdf = gpd.read_file(tmp_path, driver='KML')
                        os.unlink(tmp_path)
                        st.success(f"✅ Archivo KML en ZIP procesado")
                        return gdf
                    except:
                        os.unlink(tmp_path)
                        return None
        
        elif uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
            try:
                gdf = gpd.read_file(uploaded_file)
                st.success("✅ Archivo GeoJSON procesado")
                return gdf
            except:
                uploaded_file.seek(0)
                data = json.load(uploaded_file)
                if 'features' in data:
                    gdf = gpd.GeoDataFrame.from_features(data['features'])
                    st.success("✅ JSON convertido a GeoDataFrame")
                    return gdf
        
        return None
        
    except Exception as e:
        st.error(f"Error procesando archivo: {str(e)}")
        return None

# ===============================
# 📊 GRÁFICOS ANALÍTICOS PROFESIONALES
# ===============================
def crear_kpi_card(titulo, valor, icono, color, cambio=None, unidad=""):
    """Crear tarjeta KPI profesional"""
    cambio_html = ""
    if cambio is not None:
        cambio_clase = "positive" if cambio > 0 else "negative"
        signo = "+" if cambio > 0 else ""
        cambio_html = f'<div class="metric-change {cambio_clase}">{signo}{cambio}%</div>'
    
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
        {cambio_html}
    </div>
    """

def crear_grafico_barras_apiladas(datos, categorias, titulo, altura=400):
    """Gráfico de barras apiladas para comparación múltiple"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        # Seleccionar top 8 áreas para claridad
        areas = df['area'].unique()[:8]
        df_filtrado = df[df['area'].isin(areas)]
        
        # Crear datos para cada categoría
        fig = go.Figure()
        
        for categoria in categorias[:4]:  # Limitar a 4 categorías
            if categoria in df_filtrado.columns:
                fig.add_trace(go.Bar(
                    x=df_filtrado['area'],
                    y=df_filtrado[categoria],
                    name=categoria.replace('_', ' ').title(),
                    marker_color=px.colors.qualitative.Set3[len(fig.data)],
                    hovertemplate='%{y:.2f}<extra></extra>'
                ))
        
        fig.update_layout(
            title=dict(
                text=titulo,
                font=dict(size=16, color='#1e3a8a')
            ),
            barmode='stack',
            height=altura,
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=50, b=50),
            xaxis=dict(
                title="Áreas",
                tickangle=-45,
                gridcolor='#f3f4f6'
            ),
            yaxis=dict(
                title="Valor",
                gridcolor='#f3f4f6'
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de barras apiladas: {str(e)}")
        return go.Figure()

def crear_grafico_linea_tendencia(datos, columna, titulo, altura=350):
    """Gráfico de línea con tendencia"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        # Ordenar por área
        df['area_num'] = df['area'].str.extract('(\d+)').astype(int)
        df = df.sort_values('area_num')
        
        # Calcular media móvil
        df['media_movil'] = df[columna].rolling(window=3, center=True).mean()
        
        fig = go.Figure()
        
        # Línea principal
        fig.add_trace(go.Scatter(
            x=df['area'],
            y=df[columna],
            mode='lines+markers',
            name='Valor Real',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6'))
        ))
        
        # Media móvil
        fig.add_trace(go.Scatter(
            x=df['area'],
            y=df['media_movil'],
            mode='lines',
            name='Tendencia (Media Móvil)',
            line=dict(color='#ef4444', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=dict(
                text=titulo,
                font=dict(size=16, color='#1e3a8a')
            ),
            height=altura,
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='x unified',
            margin=dict(l=20, r=20, t=50, b=50),
            xaxis=dict(
                title="Áreas",
                gridcolor='#f3f4f6',
                showgrid=True
            ),
            yaxis=dict(
                title=columna.replace('_', ' ').title(),
                gridcolor='#f3f4f6',
                showgrid=True
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de tendencia: {str(e)}")
        return go.Figure()

def crear_grafico_donut(datos, columna, titulo, altura=350):
    """Gráfico donut para distribución porcentual"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        # Crear categorías basadas en cuartiles
        if df[columna].dtype in ['float64', 'int64']:
            df['categoria'] = pd.qcut(df[columna], q=4, 
                                     labels=['Muy Bajo', 'Bajo', 'Alto', 'Muy Alto'])
            conteo = df['categoria'].value_counts()
            
            fig = go.Figure(data=[go.Pie(
                labels=conteo.index,
                values=conteo.values,
                hole=.5,
                marker_colors=['#ef4444', '#f97316', '#10b981', '#3b82f6'],
                textinfo='percent+label',
                insidetextorientation='radial'
            )])
            
            fig.update_layout(
                title=dict(
                    text=titulo,
                    font=dict(size=16, color='#1e3a8a')
                ),
                height=altura,
                paper_bgcolor='white',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.1
                ),
                margin=dict(l=20, r=100, t=50, b=20)
            )
            
            return fig
        else:
            return crear_grafico_barras_horizontales(datos, columna, titulo, altura)
            
    except Exception as e:
        st.error(f"Error creando gráfico donut: {str(e)}")
        return go.Figure()

def crear_grafico_barras_horizontales(datos, columna, titulo, altura=350):
    """Gráfico de barras horizontales para ranking"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        # Ordenar por valor
        df = df.sort_values(columna, ascending=True).tail(10)  # Top 10
        
        fig = go.Figure(go.Bar(
            x=df[columna],
            y=df['area'],
            orientation='h',
            marker_color='#3b82f6',
            text=df[columna].round(2),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Valor: %{x:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text=titulo,
                font=dict(size=16, color='#1e3a8a')
            ),
            height=altura,
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(
                gridcolor='#f3f4f6',
                showgrid=True
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=10)
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de barras horizontales: {str(e)}")
        return go.Figure()

def crear_grafico_heatmap_correlacion_mejorado(datos_combinados, indicadores):
    """Heatmap de correlación mejorado"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_existentes = [col for col in indicadores.keys() if col in df.columns]
        
        if len(columnas_existentes) < 2:
            return go.Figure()
        
        correlaciones = df[columnas_existentes].corr()
        
        fig = ff.create_annotated_heatmap(
            z=correlaciones.values.round(2),
            x=[indicadores[col] for col in columnas_existentes],
            y=[indicadores[col] for col in columnas_existentes],
            annotation_text=correlaciones.round(2).values,
            colorscale='RdBu_r',
            showscale=True,
            font_colors=['white', 'black']
        )
        
        fig.update_layout(
            title=dict(
                text="🔗 Matriz de Correlación",
                font=dict(size=16, color='#1e3a8a')
            ),
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando heatmap: {str(e)}")
        return go.Figure()

def crear_grafico_carbono_detallado(datos_carbono):
    """Gráfico especializado para visualización de carbono"""
    if not datos_carbono:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_carbono)
        
        # Crear subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Distribución de Carbono por Área', 'Composición del Carbono'),
            specs=[[{'type': 'bar'}, {'type': 'pie'}]]
        )
        
        # Gráfico de barras
        df_sorted = df.sort_values('co2_total_ton', ascending=False).head(8)
        fig.add_trace(
            go.Bar(
                x=df_sorted['area'],
                y=df_sorted['co2_total_ton'],
                name='Carbono Total (ton CO₂)',
                marker_color='#10b981',
                text=df_sorted['co2_total_ton'].round(0),
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Gráfico de torta
        total_carbono = df['co2_total_ton'].sum()
        top_5 = df.nlargest(5, 'co2_total_ton')
        otros = total_carbono - top_5['co2_total_ton'].sum()
        
        labels = list(top_5['area']) + ['Otras Áreas']
        values = list(top_5['co2_total_ton']) + [otros]
        
        fig.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                name='Distribución',
                marker_colors=['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5', '#f3f4f6'],
                textinfo='percent+label',
                insidetextorientation='radial'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title=dict(
                text='🌳 Análisis Detallado de Captura de Carbono',
                font=dict(size=18, color='#065f46')
            ),
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            margin=dict(l=20, r=20, t=80, b=20)
        )
        
        fig.update_xaxes(tickangle=-45, row=1, col=1)
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de carbono: {str(e)}")
        return go.Figure()

def crear_dashboard_resumen(datos_combinados, summary):
    """Dashboard de resumen ejecutivo"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Crear subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '📈 Tendencia de Indicadores por Área',
                '🏆 Ranking de Áreas por Biodiversidad',
                '💧 Distribución de Disponibilidad Hídrica',
                '🌿 Estado de Salud de Vegetación'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'bar'}],
                [{'type': 'violin'}, {'type': 'pie'}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )
        
        # 1. Gráfico de líneas múltiples
        if 'area_num' not in df.columns:
            df['area_num'] = df['area'].str.extract('(\d+)').astype(int)
        df_sorted = df.sort_values('area_num')
        
        indicadores_linea = ['ndvi', 'indice_shannon', 'salud_suelo']
        colores = ['#3b82f6', '#10b981', '#f59e0b']
        
        for idx, indicador in enumerate(indicadores_linea):
            if indicador in df_sorted.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_sorted['area'],
                        y=df_sorted[indicador],
                        mode='lines+markers',
                        name=indicador.replace('_', ' ').title(),
                        line=dict(color=colores[idx], width=2),
                        marker=dict(size=6)
                    ),
                    row=1, col=1
                )
        
        # 2. Ranking de biodiversidad
        df_biodiv = df.nlargest(8, 'indice_shannon')
        fig.add_trace(
            go.Bar(
                x=df_biodiv['indice_shannon'],
                y=df_biodiv['area'],
                orientation='h',
                name='Biodiversidad',
                marker_color='#10b981',
                text=df_biodiv['indice_shannon'].round(2),
                textposition='outside'
            ),
            row=1, col=2
        )
        
        # 3. Violin plot para agua
        if 'disponibilidad_agua' in df.columns:
            fig.add_trace(
                go.Violin(
                    y=df['disponibilidad_agua'],
                    name='Agua',
                    box_visible=True,
                    meanline_visible=True,
                    fillcolor='#0ea5e9',
                    line_color='#0369a1',
                    opacity=0.7
                ),
                row=2, col=1
            )
        
        # 4. Pie chart para salud vegetación
        if 'salud_vegetacion' in df.columns:
            salud_counts = df['salud_vegetacion'].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=salud_counts.index,
                    values=salud_counts.values,
                    hole=0.3,
                    name='Salud Vegetación',
                    marker_colors=['#10b981', '#34d399', '#f59e0b', '#ef4444'],
                    textinfo='percent+label'
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            height=700,
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=True,
            title_text="📊 Dashboard Ejecutivo de Indicadores Ambientales",
            title_font=dict(size=20, color='#1e3a8a'),
            margin=dict(l=40, r=40, t=100, b=40)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando dashboard resumen: {str(e)}")
        return go.Figure()

# ===============================
# 🧩 CLASE PRINCIPAL DE ANÁLISIS (MANTENIDA)
# ===============================
class AnalizadorBiodiversidad:
    """Analizador integral de biodiversidad para el polígono cargado"""
    
    def __init__(self):
        self.parametros_ecosistemas = {
            'Bosque Denso Primario': {
                'carbono': {'min': 180, 'max': 320},
                'biodiversidad': 0.85,
                'ndvi_base': 0.85,
                'resiliencia': 0.8
            },
            'Bosque Secundario': {
                'carbono': {'min': 80, 'max': 160},
                'biodiversidad': 0.65,
                'ndvi_base': 0.75,
                'resiliencia': 0.6
            },
            'Bosque Ripario': {
                'carbono': {'min': 120, 'max': 220},
                'biodiversidad': 0.75,
                'ndvi_base': 0.80,
                'resiliencia': 0.7
            },
            'Matorral Denso': {
                'carbono': {'min': 40, 'max': 70},
                'biodiversidad': 0.45,
                'ndvi_base': 0.65,
                'resiliencia': 0.5
            },
            'Matorral Abierto': {
                'carbono': {'min': 20, 'max': 40},
                'biodiversidad': 0.25,
                'ndvi_base': 0.45,
                'resiliencia': 0.4
            },
            'Sabana Arborizada': {
                'carbono': {'min': 25, 'max': 45},
                'biodiversidad': 0.35,
                'ndvi_base': 0.35,
                'resiliencia': 0.5
            },
            'Herbazal Natural': {
                'carbono': {'min': 8, 'max': 18},
                'biodiversidad': 0.15,
                'ndvi_base': 0.25,
                'resiliencia': 0.3
            },
            'Zona de Transición': {
                'carbono': {'min': 15, 'max': 30},
                'biodiversidad': 0.25,
                'ndvi_base': 0.30,
                'resiliencia': 0.4
            },
            'Área de Restauración': {
                'carbono': {'min': 30, 'max': 90},
                'biodiversidad': 0.50,
                'ndvi_base': 0.55,
                'resiliencia': 0.7
            }
        }
    
    def _calcular_area_hectareas(self, poligono):
        """Calcular área en hectáreas de forma precisa usando proyección UTM"""
        try:
            if poligono.is_valid:
                gdf_temp = gpd.GeoDataFrame([1], geometry=[poligono], crs="EPSG:4326")
                centroid = poligono.centroid
                utm_zone = self._determinar_zona_utm(centroid.y, centroid.x)
                gdf_projected = gdf_temp.to_crs(utm_zone)
                area_m2 = gdf_projected.geometry.area.iloc[0]
                area_hectareas = area_m2 / 10000
                return round(area_hectareas, 2)
            else:
                return self._calcular_area_aproximada(poligono)
        except Exception as e:
            st.warning(f"Usando cálculo aproximado debido a: {str(e)}")
            return self._calcular_area_aproximada(poligono)
    
    def _determinar_zona_utm(self, lat, lon):
        """Determinar la zona UTM automáticamente"""
        zona = int((lon + 180) / 6) + 1
        hemisferio = 'north' if lat >= 0 else 'south'
        return f"EPSG:326{zona:02d}" if hemisferio == 'north' else f"EPSG:327{zona:02d}"
    
    def _calcular_area_aproximada(self, poligono):
        """Cálculo aproximado del área en hectáreas"""
        try:
            area_grados = poligono.area
            lat_centro = poligono.centroid.y
            cos_lat = math.cos(math.radians(lat_centro))
            area_km2 = area_grados * 111 * 111 * cos_lat
            return round(area_km2 * 100, 2)
        except:
            return 0
    
    def _dividir_poligono_grilla(self, poligono, n_divisiones):
        """Dividir el polígono en una grilla de n x n celdas"""
        try:
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            
            width = (maxx - minx) / n_divisiones
            height = (maxy - miny) / n_divisiones
            
            celdas = []
            id_celda = 1
            
            for i in range(n_divisiones):
                for j in range(n_divisiones):
                    xmin = minx + (i * width)
                    xmax = xmin + width
                    ymin = miny + (j * height)
                    ymax = ymin + height
                    
                    celda_rect = Polygon([
                        (xmin, ymin), (xmax, ymin),
                        (xmax, ymax), (xmin, ymax), (xmin, ymin)
                    ])
                    
                    interseccion = poligono.intersection(celda_rect)
                    if not interseccion.is_empty:
                        area_celda = self._calcular_area_hectareas(interseccion)
                        if area_celda > 0.01:
                            celdas.append({
                                'id': id_celda,
                                'area': f"Área-{id_celda}",
                                'geometry': interseccion,
                                'centroid': interseccion.centroid,
                                'area_ha': area_celda
                            })
                            id_celda += 1
            
            return celdas
        except Exception as e:
            st.error(f"Error dividiendo polígono: {str(e)}")
            return []
    
    def _calcular_indicador_con_variacion(self, base, variacion=0.2):
        """Calcular valor con variación aleatoria controlada"""
        variacion_real = np.random.uniform(-variacion, variacion)
        return base * (1 + variacion_real)
    
    def _simular_distribucion_normal(self, base, desviacion=0.15):
        """Simular distribución normal alrededor del valor base"""
        return np.random.normal(base, base * desviacion)
    
    def procesar_poligono(self, gdf, tipo_vegetacion, n_divisiones=5):
        """Método principal para procesar el polígono"""
        try:
            if gdf is None or gdf.empty:
                st.error("No hay datos geoespaciales para procesar")
                return None
            
            poligono_principal = gdf.geometry.iloc[0]
            area_total = self._calcular_area_hectareas(poligono_principal)
            
            # 1. Dividir en grilla
            areas_analisis = self._dividir_poligono_grilla(poligono_principal, n_divisiones)
            
            if not areas_analisis:
                st.error("No se pudieron crear áreas de análisis")
                return None
            
            # Obtener parámetros base según tipo de vegetación
            if tipo_vegetacion not in self.parametros_ecosistemas:
                tipo_vegetacion = 'Bosque Secundario'
            
            params = self.parametros_ecosistemas[tipo_vegetacion]
            
            # 2. Calcular indicadores para cada área
            resultados_vegetacion = []
            resultados_carbono = []
            resultados_biodiversidad = []
            resultados_agua = []
            resultados_suelo = []
            resultados_conectividad = []
            resultados_presiones = []
            
            for area in areas_analisis:
                area_id = area['area']
                area_ha = area['area_ha']
                
                # Vegetación (NDVI)
                ndvi_base = params['ndvi_base']
                ndvi = self._calcular_indicador_con_variacion(ndvi_base, 0.15)
                
                # Salud vegetación basada en NDVI
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
                
                # Carbono (CO2)
                carbono_min = params['carbono']['min']
                carbono_max = params['carbono']['max']
                carbono_ton_ha = np.random.uniform(carbono_min, carbono_max)
                co2_total = carbono_ton_ha * area_ha * 3.67
                
                # Tipos de carbono (simulados para mejor visualización)
                carbono_aereo = co2_total * 0.6
                carbono_raices = co2_total * 0.25
                carbono_suelo = co2_total * 0.15
                
                resultados_carbono.append({
                    'area': area_id,
                    'carbono_ton_ha': round(carbono_ton_ha, 2),
                    'co2_total_ton': round(co2_total, 2),
                    'carbono_aereo': round(carbono_aereo, 2),
                    'carbono_raices': round(carbono_raices, 2),
                    'carbono_suelo': round(carbono_suelo, 2),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Biodiversidad (Índice de Shannon)
                biod_base = params['biodiversidad']
                indice_shannon = self._simular_distribucion_normal(biod_base * 2.5, 0.2)
                indice_shannon = max(0.1, min(3.0, indice_shannon))
                
                # Clasificar biodiversidad
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
                
                # Agua (Disponibilidad)
                disponibilidad_base = ndvi * 0.8 + params['resiliencia'] * 0.2
                disponibilidad = self._calcular_indicador_con_variacion(disponibilidad_base, 0.25)
                
                resultados_agua.append({
                    'area': area_id,
                    'disponibilidad_agua': round(disponibilidad, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Suelo (Salud)
                salud_suelo_base = (ndvi * 0.6 + (carbono_ton_ha / carbono_max) * 0.4)
                salud_suelo = self._calcular_indicador_con_variacion(salud_suelo_base, 0.2)
                
                resultados_suelo.append({
                    'area': area_id,
                    'salud_suelo': round(salud_suelo, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Conectividad ecológica
                centro_pol = poligono_principal.centroid
                distancia_al_centro = area['centroid'].distance(centro_pol)
                max_dist = centro_pol.distance(Point(poligono_principal.bounds[0], poligono_principal.bounds[1]))
                conectividad_base = 1.0 - (distancia_al_centro / max_dist)
                conectividad = self._calcular_indicador_con_variacion(conectividad_base, 0.3)
                
                resultados_conectividad.append({
                    'area': area_id,
                    'conectividad_total': round(conectividad, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Presiones antrópicas
                presion_base = (1.0 - ndvi) * 0.7 + (1.0 - conectividad) * 0.3
                presion = self._calcular_indicador_con_variacion(presion_base, 0.25)
                
                resultados_presiones.append({
                    'area': area_id,
                    'presion_total': round(presion, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
            
            # 3. Calcular métricas de resumen
            ndvi_vals = [r['ndvi'] for r in resultados_vegetacion] if resultados_vegetacion else [0]
            co2_vals = [r['co2_total_ton'] for r in resultados_carbono] if resultados_carbono else [0]
            shannon_vals = [r['indice_shannon'] for r in resultados_biodiversidad] if resultados_biodiversidad else [0]
            agua_vals = [r['disponibilidad_agua'] for r in resultados_agua] if resultados_agua else [0]
            suelo_vals = [r['salud_suelo'] for r in resultados_suelo] if resultados_suelo else [0]
            conect_vals = [r['conectividad_total'] for r in resultados_conectividad] if resultados_conectividad else [0]
            presion_vals = [r['presion_total'] for r in resultados_presiones] if resultados_presiones else [0]
            
            # Calcular estado general
            promedio_ndvi = np.mean(ndvi_vals) if ndvi_vals else 0
            promedio_conectividad = np.mean(conect_vals) if conect_vals else 0
            promedio_presion = np.mean(presion_vals) if presion_vals else 0
            
            if promedio_ndvi >= 0.7 and promedio_presion <= 0.3:
                estado_general = "Excelente"
            elif promedio_ndvi >= 0.5 and promedio_presion <= 0.5:
                estado_general = "Bueno"
            elif promedio_ndvi >= 0.3:
                estado_general = "Moderado"
            else:
                estado_general = "Crítico"
            
            summary_metrics = {
                'estado_general': estado_general,
                'carbono_total_co2_ton': round(sum(co2_vals) if co2_vals else 0, 2),
                'carbono_promedio_ha': round(np.mean([r['carbono_ton_ha'] for r in resultados_carbono]) if resultados_carbono else 0, 2),
                'indice_biodiversidad_promedio': round(np.mean(shannon_vals) if shannon_vals else 0, 3),
                'disponibilidad_agua_promedio': round(np.mean(agua_vals) if agua_vals else 0, 3),
                'salud_suelo_promedio': round(np.mean(suelo_vals) if suelo_vals else 0, 3),
                'conectividad_promedio': round(promedio_conectividad, 3),
                'presion_antropica_promedio': round(promedio_presion, 3),
                'areas_analizadas': len(areas_analisis),
                'ndvi_promedio': round(promedio_ndvi, 3),
                'area_total_ha': area_total
            }
            
            # 4. Compilar resultados finales
            resultados = {
                'resultados': {
                    'vegetacion': resultados_vegetacion,
                    'carbono': resultados_carbono,
                    'biodiversidad': resultados_biodiversidad,
                    'agua': resultados_agua,
                    'suelo': resultados_suelo,
                    'conectividad': resultados_conectividad,
                    'presiones': resultados_presiones,
                    'summary_metrics': summary_metrics
                },
                'areas_analisis': areas_analisis,
                'area_hectareas': area_total,
                'tipo_vegetacion': tipo_vegetacion
            }
            
            return resultados
            
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None

# ===============================
# 📁 FUNCIONES AUXILIARES
# ===============================
def generar_geojson_completo(resultados):
    """Generar un GeoJSON completo con todos los indicadores"""
    try:
        todos_datos = []
        for i in range(len(resultados['resultados']['vegetacion'])):
            area_data = {
                'area': resultados['resultados']['vegetacion'][i]['area'],
                'geometry': resultados['resultados']['vegetacion'][i]['geometry'],
                'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                'salud_vegetacion': resultados['resultados']['vegetacion'][i]['salud_vegetacion'],
                'area_ha': resultados['resultados']['vegetacion'][i]['area_ha']
            }
            
            if i < len(resultados['resultados']['carbono']):
                area_data['co2_total_ton'] = resultados['resultados']['carbono'][i]['co2_total_ton']
                area_data['carbono_ton_ha'] = resultados['resultados']['carbono'][i]['carbono_ton_ha']
            
            if i < len(resultados['resultados']['biodiversidad']):
                area_data['indice_shannon'] = resultados['resultados']['biodiversidad'][i]['indice_shannon']
                area_data['estado_biodiversidad'] = resultados['resultados']['biodiversidad'][i]['estado_biodiversidad']
            
            if i < len(resultados['resultados']['agua']):
                area_data['disponibilidad_agua'] = resultados['resultados']['agua'][i]['disponibilidad_agua']
            
            if i < len(resultados['resultados']['suelo']):
                area_data['salud_suelo'] = resultados['resultados']['suelo'][i]['salud_suelo']
            
            if i < len(resultados['resultados']['conectividad']):
                area_data['conectividad_total'] = resultados['resultados']['conectividad'][i]['conectividad_total']
            
            if i < len(resultados['resultados']['presiones']):
                area_data['presion_total'] = resultados['resultados']['presiones'][i]['presion_total']
            
            todos_datos.append(area_data)
        
        gdf = gpd.GeoDataFrame(todos_datos, geometry='geometry', crs="EPSG:4326")
        geojson_str = gdf.to_json()
        return geojson_str
    except Exception as e:
        st.error(f"Error generando GeoJSON completo: {str(e)}")
        return None

def crear_boton_descarga_analitico(data, filename, button_text, file_type):
    """Crear botón de descarga con estilo analítico"""
    try:
        if file_type == 'geojson':
            if data is None:
                st.error(f"No hay datos para generar {filename}")
                return
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-btn-analytics">📥 {button_text}</a>'
        elif file_type == 'csv':
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-btn-analytics">📥 {button_text}</a>'
        st.markdown(f'<div style="margin: 10px 0;">{href}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error creando botón de descarga: {str(e)}")

# ===============================
# 🚀 CONFIGURACIÓN PRINCIPAL - ESTILO ANALÍTICO
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
            hasattr(st.session_state.poligono_data, 'empty') and 
            not st.session_state.poligono_data.empty)

def sidebar_config_analitico():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-section">
            <h3 style="color: #1e3a8a; margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;">
                <span>⚙️</span> Configuración del Análisis
            </h3>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="filter-header">🗺️ Cargar Polígono</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Seleccionar archivo territorial", 
            type=['kml', 'zip', 'geojson', 'json'],
            help="Formatos soportados: KML, GeoJSON, Shapefile (ZIP)"
        )
        
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None and not gdf.empty:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False
                    st.success("✅ Polígono cargado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ No se pudo procesar el archivo")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-header">📊 Parámetros de Análisis</div>', unsafe_allow_html=True)
        
        vegetation_type = st.selectbox(
            "Tipo de vegetación predominante",
            ['Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
             'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
             'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'],
            help="Define el tipo de ecosistema para cálculos de referencia"
        )
        
        divisiones = st.slider(
            "Nivel de detalle del análisis",
            3, 8, 5,
            help="Número de divisiones para crear la grilla de análisis"
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="filter-header">📈 Opciones de Visualización</div>', unsafe_allow_html=True)
        
        mostrar_mapa = st.checkbox("Mostrar mapa interactivo", value=True)
        mostrar_detalle = st.checkbox("Mostrar análisis detallado por área", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return uploaded_file, vegetation_type, divisiones, mostrar_mapa, mostrar_detalle

# ===============================
# 🎯 APLICACIÓN PRINCIPAL - ESTILO ANALÍTICO
# ===============================
def main():
    aplicar_estilos_globales()
    crear_header_analitico()
    initialize_session_state()
    
    uploaded_file, vegetation_type, divisiones, mostrar_mapa, mostrar_detalle = sidebar_config_analitico()
    
    # Sección de carga de datos
    if tiene_poligono_data():
        gdf = st.session_state.poligono_data
        poligono = gdf.geometry.iloc[0]
        area_ha = st.session_state.analyzer._calcular_area_hectareas(poligono)
        
        # Mostrar información del área
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(crear_kpi_card(
                "Área Total", 
                f"{area_ha:,.0f}", 
                "📐", 
                "#3b82f6",
                unidad="hectáreas"
            ), unsafe_allow_html=True)
        with col2:
            st.markdown(crear_kpi_card(
                "Tipo de Vegetación", 
                vegetation_type.split()[0], 
                "🌿", 
                "#10b981"
            ), unsafe_allow_html=True)
        with col3:
            st.markdown(crear_kpi_card(
                "Áreas de Análisis", 
                f"{divisiones}x{divisiones}", 
                "🔲", 
                "#f59e0b"
            ), unsafe_allow_html=True)
    
    # Botón de ejecución del análisis
    if tiene_poligono_data() and not st.session_state.analysis_complete:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 EJECUTAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
                with st.spinner("Realizando análisis integral..."):
                    resultados = st.session_state.analyzer.procesar_poligono(
                        st.session_state.poligono_data, vegetation_type, divisiones
                    )
                    if resultados:
                        st.session_state.results = resultados
                        st.session_state.analysis_complete = True
                        st.success("✅ Análisis completado exitosamente!")
                        st.rerun()
    
    # Mostrar resultados del análisis
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
        # ==================== SECCIÓN DE KPIs PRINCIPALES ====================
        st.markdown("## 📊 KPIs Principales del Análisis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(crear_kpi_card(
                "Estado General", 
                summary['estado_general'], 
                "📈", 
                "#10b981" if summary['estado_general'] in ['Excelente', 'Bueno'] else "#f59e0b",
                cambio=5.2 if summary['estado_general'] in ['Excelente', 'Bueno'] else -2.1
            ), unsafe_allow_html=True)
        with col2:
            st.markdown(crear_kpi_card(
                "Carbono Total", 
                f"{summary['carbono_total_co2_ton']:,.0f}", 
                "🌳", 
                "#065f46",
                cambio=8.5,
                unidad="ton CO₂"
            ), unsafe_allow_html=True)
        with col3:
            st.markdown(crear_kpi_card(
                "Biodiversidad", 
                f"{summary['indice_biodiversidad_promedio']:.2f}", 
                "🦋", 
                "#3b82f6",
                cambio=3.2,
                unidad="Índice"
            ), unsafe_allow_html=True)
        with col4:
            st.markdown(crear_kpi_card(
                "Áreas Analizadas", 
                f"{summary['areas_analizadas']}", 
                "📍", 
                "#8b5cf6",
                unidad="unidades"
            ), unsafe_allow_html=True)
        
        # ==================== SECCIÓN DE GRÁFICOS PRINCIPALES ====================
        st.markdown("## 📈 Visualizaciones Principales")
        
        # Combinar datos para análisis
        datos_combinados = []
        for i in range(len(resultados['resultados']['vegetacion'])):
            combo = {
                'area': resultados['resultados']['vegetacion'][i]['area'],
                'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                'salud_vegetacion': resultados['resultados']['vegetacion'][i]['salud_vegetacion'],
                'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton'],
                'carbono_ton_ha': resultados['resultados']['carbono'][i]['carbono_ton_ha'],
                'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                'disponibilidad_agua': resultados['resultados']['agua'][i]['disponibilidad_agua'],
                'salud_suelo': resultados['resultados']['suelo'][i]['salud_suelo'],
                'conectividad_total': resultados['resultados']['conectividad'][i]['conectividad_total'],
                'presion_total': resultados['resultados']['presiones'][i]['presion_total']
            }
            datos_combinados.append(combo)
        
        # Fila 1: Dashboard ejecutivo
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📊 Dashboard Ejecutivo de Indicadores</div>', unsafe_allow_html=True)
            st.plotly_chart(
                crear_dashboard_resumen(datos_combinados, summary),
                use_container_width=True,
                key="dashboard_ejecutivo"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Fila 2: Análisis especializados
        col1, col2 = st.columns(2)
        
        with col1:
            # Análisis de carbono mejorado
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">🌳 Análisis de Captura de Carbono</div>', unsafe_allow_html=True)
            st.plotly_chart(
                crear_grafico_carbono_detallado(resultados['resultados']['carbono']),
                use_container_width=True,
                key="carbono_detallado"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Tendencias
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📈 Tendencias de Indicadores Clave</div>', unsafe_allow_html=True)
            st.plotly_chart(
                crear_grafico_linea_tendencia(datos_combinados, 'ndvi', 'Evolución del NDVI por Área'),
                use_container_width=True,
                key="tendencia_ndvi"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Fila 3: Distribuciones y rankings
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">🏆 Ranking de Biodiversidad</div>', unsafe_allow_html=True)
            st.plotly_chart(
                crear_grafico_barras_horizontales(datos_combinados, 'indice_shannon', 'Top 10 Áreas por Biodiversidad'),
                use_container_width=True,
                key="ranking_biodiversidad"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">💧 Distribución de Recursos Hídricos</div>', unsafe_allow_html=True)
            st.plotly_chart(
                crear_grafico_donut(datos_combinados, 'disponibilidad_agua', 'Disponibilidad de Agua por Categoría'),
                use_container_width=True,
                key="donut_agua"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== SECCIÓN DE ANÁLISIS DETALLADO ====================
        if mostrar_detalle:
            st.markdown("## 🔍 Análisis Detallado por Indicador")
            
            tabs = st.tabs(["🌿 Vegetación", "🌳 Carbono", "🦋 Biodiversidad", "💧 Agua", "🔄 Correlaciones"])
            
            with tabs[0]:  # Vegetación
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        crear_grafico_linea_tendencia(resultados['resultados']['vegetacion'], 'ndvi', 'Tendencia de NDVI'),
                        use_container_width=True,
                        key="vegetacion_tendencia"
                    )
                with col2:
                    st.plotly_chart(
                        crear_grafico_donut(resultados['resultados']['vegetacion'], 'ndvi', 'Distribución de Salud Vegetal'),
                        use_container_width=True,
                        key="vegetacion_donut"
                    )
            
            with tabs[1]:  # Carbono
                # Datos extendidos de carbono
                df_carbono = pd.DataFrame(resultados['resultados']['carbono'])
                if not df_carbono.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = go.Figure(data=[
                            go.Bar(name='Aéreo', x=df_carbono['area'].head(8), y=df_carbono['carbono_aereo'].head(8), marker_color='#10b981'),
                            go.Bar(name='Raíces', x=df_carbono['area'].head(8), y=df_carbono['carbono_raices'].head(8), marker_color='#34d399'),
                            go.Bar(name='Suelo', x=df_carbono['area'].head(8), y=df_carbono['carbono_suelo'].head(8), marker_color='#6ee7b7')
                        ])
                        fig.update_layout(barmode='stack', title='Composición del Carbono por Área', height=350)
                        st.plotly_chart(fig, use_container_width=True, key="carbono_composicion")
                    
                    with col2:
                        st.plotly_chart(
                            crear_grafico_barras_horizontales(resultados['resultados']['carbono'], 'co2_total_ton', 'Ranking de Captura de Carbono'),
                            use_container_width=True,
                            key="carbono_ranking"
                        )
            
            with tabs[2]:  # Biodiversidad
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        crear_grafico_linea_tendencia(resultados['resultados']['biodiversidad'], 'indice_shannon', 'Tendencia de Biodiversidad'),
                        use_container_width=True,
                        key="biodiversidad_tendencia"
                    )
                with col2:
                    st.plotly_chart(
                        crear_grafico_donut(resultados['resultados']['biodiversidad'], 'indice_shannon', 'Distribución de Niveles de Biodiversidad'),
                        use_container_width=True,
                        key="biodiversidad_donut"
                    )
            
            with tabs[3]:  # Agua
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        crear_grafico_barras_apiladas(
                            resultados['resultados']['agua'],
                            ['disponibilidad_agua'],
                            'Disponibilidad de Agua por Área',
                            350
                        ),
                        use_container_width=True,
                        key="agua_barras"
                    )
                with col2:
                    st.plotly_chart(
                        crear_grafico_linea_tendencia(resultados['resultados']['agua'], 'disponibilidad_agua', 'Tendencia de Disponibilidad Hídrica'),
                        use_container_width=True,
                        key="agua_tendencia"
                    )
            
            with tabs[4]:  # Correlaciones
                st.plotly_chart(
                    crear_grafico_heatmap_correlacion_mejorado(
                        datos_combinados,
                        {
                            'ndvi': 'Salud Vegetación',
                            'co2_total_ton': 'Carbono Total',
                            'indice_shannon': 'Biodiversidad',
                            'disponibilidad_agua': 'Disponibilidad Agua',
                            'salud_suelo': 'Salud del Suelo',
                            'conectividad_total': 'Conectividad',
                            'presion_total': 'Presión Antrópica'
                        }
                    ),
                    use_container_width=True,
                    key="correlaciones_completas"
                )
        
        # ==================== SECCIÓN DE MAPA INTERACTIVO ====================
        if mostrar_mapa:
            st.markdown("## 🗺️ Visualización Geoespacial")
            
            # Seleccionar capa para visualizar
            col1, col2 = st.columns([3, 1])
            with col2:
                capa_seleccionada = st.selectbox(
                    "Capa a visualizar",
                    ["NDVI", "Carbono", "Biodiversidad", "Agua", "Suelo"],
                    key="selector_capa"
                )
            
            # Crear mapa simple
            try:
                gdf = st.session_state.poligono_data
                bounds = gdf.total_bounds
                center_lat = (bounds[1] + bounds[3]) / 2
                center_lon = (bounds[0] + bounds[2]) / 2
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
                folium.TileLayer('OpenStreetMap').add_to(m)
                
                # Añadir polígono
                folium.GeoJson(
                    gdf.geometry.iloc[0],
                    style_function=lambda x: {
                        'fillColor': '#3b82f6',
                        'color': '#1d4ed8',
                        'weight': 2,
                        'fillOpacity': 0.2
                    },
                    name='Área de Estudio'
                ).add_to(m)
                
                # Añadir controles
                folium.LayerControl().add_to(m)
                
                with col1:
                    st_folium(m, width=900, height=500, key="mapa_principal")
            
            except Exception as e:
                st.error(f"Error mostrando mapa: {str(e)}")
        
        # ==================== SECCIÓN DE DESCARGA ====================
        st.markdown("## 📥 Exportación de Resultados")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            st.markdown("**🗺️ Datos Geoespaciales**")
            geojson_completo = generar_geojson_completo(resultados)
            if geojson_completo:
                crear_boton_descarga_analitico(
                    geojson_completo,
                    "analisis_biodiversidad.geojson",
                    "Descargar GeoJSON",
                    'geojson'
                )
        
        with col_dl2:
            st.markdown("**📊 Datos Analíticos**")
            df_completo = pd.DataFrame(datos_combinados)
            csv = df_completo.to_csv(index=False)
            crear_boton_descarga_analitico(
                csv,
                "datos_analisis_completo.csv",
                "Descargar CSV",
                'csv'
            )
        
        with col_dl3:
            st.markdown("**📋 Resumen Ejecutivo**")
            resumen_text = f"""
            RESUMEN EJECUTIVO - ANÁLISIS DE BIODIVERSIDAD
            ============================================
            
            Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            
            🔹 INFORMACIÓN GENERAL
            -----------------------
            • Área total analizada: {summary['area_total_ha']:,.2f} ha
            • Tipo de vegetación: {resultados['tipo_vegetacion']}
            • Áreas analizadas: {summary['areas_analizadas']}
            
            🔹 KPIs PRINCIPALES
            -------------------
            • Estado general del ecosistema: {summary['estado_general']}
            • Carbono total almacenado: {summary['carbono_total_co2_ton']:,} ton CO₂
            • Carbono promedio por hectárea: {summary['carbono_promedio_ha']} ton/ha
            • Índice de biodiversidad promedio: {summary['indice_biodiversidad_promedio']}
            • Disponibilidad de agua promedio: {summary['disponibilidad_agua_promedio']}
            • Salud del suelo promedio: {summary['salud_suelo_promedio']}
            • Conectividad ecológica promedio: {summary['conectividad_promedio']}
            • Presión antrópica promedio: {summary['presion_antropica_promedio']}
            
            🔹 RECOMENDACIONES
            ------------------
            """
            
            if summary['estado_general'] in ['Crítico', 'Moderado']:
                resumen_text += """
            1. Implementar programas de restauración ecológica inmediata
            2. Establecer zonas de amortiguamiento para reducir presión antrópica
            3. Monitorear continuamente los indicadores clave
            4. Desarrollar estrategias de conservación prioritaria
            5. Considerar incentivos por servicios ambientales
                """
            else:
                resumen_text += """
            1. Mantener las prácticas actuales de conservación
            2. Continuar con el monitoreo periódico
            3. Fortalecer la protección contra amenazas externas
            4. Promover investigación científica en el área
            5. Buscar certificaciones de sostenibilidad
                """
            
            crear_boton_descarga_analitico(
                resumen_text,
                "resumen_ejecutivo.txt",
                "Descargar Resumen",
                'csv'
            )
    
    # ==================== PANTALLA DE BIENVENIDA ====================
    elif not tiene_poligono_data():
        st.markdown("## 👋 Bienvenido al Dashboard Analítico de Biodiversidad")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <div class="insight-card">
                <h3 style="color: #1e3a8a; margin-bottom: 1rem;">📊 Sistema de Análisis Ambiental Empresarial</h3>
                <p style="color: #4b5563; line-height: 1.6;">
                    Esta plataforma integra <strong>análisis geoespacial</strong> con <strong>métricas empresariales</strong> 
                    para la toma de decisiones informadas en gestión ambiental.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            ### 🎯 ¿Qué puedes hacer con esta herramienta?
            
            **📈 ANÁLISIS CUANTITATIVO**
            • Evaluar indicadores ambientales clave (carbono, biodiversidad, agua)
            • Monitorear tendencias y patrones espaciales
            • Generar dashboards ejecutivos personalizados
            
            **🗺️ VISUALIZACIÓN GEOESPACIAL**
            • Cargar polígonos de áreas de estudio
            • Analizar distribución espacial de indicadores
            • Identificar áreas prioritarias para intervención
            
            **📊 REPORTES EJECUTIVOS**
            • Exportar datos en múltiples formatos
            • Generar resúmenes automáticos
            • Crear visualizaciones listas para presentaciones
            
            **🔍 TOMA DE DECISIONES**
            • Comparar escenarios de gestión
            • Identificar oportunidades de mejora
            • Priorizar acciones de conservación
            """)
        
        with col2:
            st.markdown("""
            <div class="insight-card">
                <h4 style="color: #1e3a8a;">🚀 ¿Cómo comenzar?</h4>
                <ol style="color: #4b5563; padding-left: 1.5rem;">
                    <li>Carga tu polígono en el panel lateral</li>
                    <li>Configura los parámetros de análisis</li>
                    <li>Ejecuta el análisis completo</li>
                    <li>Explora los resultados interactivos</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            ### 📋 Formatos soportados
            • **GeoJSON** (.geojson, .json) - Recomendado
            • **Shapefile** (.zip con todos los archivos)
            • **KML** (.kml) - Soporte básico
            
            ### ⚙️ Requisitos técnicos
            • Área mínima: 1 hectárea
            • Polígono válido (sin auto-intersecciones)
            • Sistema de coordenadas: WGS84 (EPSG:4326)
            """)

if __name__ == "__main__":
    main()
