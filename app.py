# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st

# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Análisis Integral de Biodiversidad",
    page_icon="🌍",
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
# 🌿 CONFIGURACIÓN Y ESTILOS GLOBALES
# ===============================
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
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #2E8B57;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .download-btn {
        background: linear-gradient(135deg, #1E90FF 0%, #00BFFF 100%) !important;
        margin: 5px;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        text-decoration: none;
        display: inline-block;
        font-weight: 600;
        border: none;
        cursor: pointer;
        font-size: 14px;
    }
    .download-btn:hover {
        background: linear-gradient(135deg, #0066CC 0%, #0099FF 100%) !important;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_header():
    st.markdown("""
    <div class="custom-header">
        <h1>🌿 Análisis Integral de Biodiversidad</h1>
        <p>Sistema de evaluación ecológica con múltiples indicadores ambientales</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# FUNCIONES DE PROCESAMIENTO DE ARCHIVOS CORREGIDAS
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
        st.error(f"Error procesando KML con pykml: {str(e)}")
        return None

def procesar_archivo_cargado(uploaded_file):
    """Procesar archivo KML/ZIP cargado con manejo mejorado de errores"""
    try:
        if uploaded_file.name.endswith('.kml'):
            try:
                gdf = gpd.read_file(uploaded_file, driver='KML')
                if not gdf.empty:
                    st.success("✅ Archivo KML procesado con GeoPandas")
                    return gdf
            except Exception as e1:
                st.warning(f"GeoPandas no pudo leer el KML: {str(e1)}")
                if KML_AVAILABLE:
                    st.info("Intentando procesar KML con pykml...")
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
                
                st.error("No se pudo procesar el archivo KML con ningún método")
                return None
                
        elif uploaded_file.name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                kml_files = [f for f in os.listdir(tmpdir) if f.endswith('.kml')]
                
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    st.success(f"✅ Archivo SHP procesado: {shp_files[0]}")
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
# 🗺️ FUNCIONES DE MAPAS MEJORADAS CON ZOOM AUTOMÁTICO
# ===============================
def calcular_zoom_automatico(gdf):
    """Calcular nivel de zoom automático basado en el área del polígono"""
    if gdf is None or gdf.empty:
        return 10
    
    try:
        # Calcular el área en km²
        poligono = gdf.geometry.iloc[0]
        area_km2 = gdf.area.sum() * 111.32 * 111.32 * math.cos(math.radians(poligono.centroid.y))
        
        # Determinar zoom basado en el área
        if area_km2 < 1:  # Muy pequeño
            return 16
        elif area_km2 < 10:  # Pequeño
            return 14
        elif area_km2 < 100:  # Mediano
            return 12
        elif area_km2 < 1000:  # Grande
            return 10
        elif area_km2 < 10000:  # Muy grande
            return 8
        else:  # Enorme
            return 6
    except:
        return 10

def crear_mapa_indicador(gdf, datos, indicador_config):
    """Crear mapa con zoom automático y mejores visualizaciones"""
    if gdf is None or datos is None or len(datos) == 0:
        return crear_mapa_base()
    
    try:
        # Calcular centroide y zoom automático
        bounds = gdf.total_bounds
        if len(bounds) == 4:
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            zoom = calcular_zoom_automatico(gdf)
        else:
            center_lat = -14.0
            center_lon = -60.0
            zoom = 4
        
        # Crear mapa con zoom calculado
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=zoom,
            tiles=None,
            control_scale=True
        )
        
        # Agregar capas base
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite ESRI',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Agregar polígono principal
        poligono_principal = gdf.geometry.iloc[0]
        folium.GeoJson(
            poligono_principal,
            style_function=lambda x: {
                'fillColor': '#ffffff',
                'color': '#0066cc',
                'weight': 3,
                'fillOpacity': 0.1,
                'dashArray': '5, 5'
            },
            name='Área de estudio',
            tooltip='Área de estudio principal'
        ).add_to(m)
        
        # Crear cluster para muchas áreas
        marker_cluster = MarkerCluster(name="Áreas de análisis").add_to(m)
        
        # Agregar áreas del indicador
        for area_data in datos:
            valor = area_data.get(indicador_config['columna'], 0)
            geometry = area_data.get('geometry')
            area_id = area_data.get('area', 'Desconocido')
            
            if geometry:
                # Determinar color basado en el valor
                color = '#808080'  # Gris por defecto
                for rango, color_rango in indicador_config['colores'].items():
                    if valor >= rango[0] and valor <= rango[1]:
                        color = color_rango
                        break
                
                # Calcular centroide para el marcador
                centroid = geometry.centroid
                
                # Agregar marcador al cluster
                popup_content = f"""
                <div style="min-width: 250px;">
                    <h4 style="color: #2E8B57;">📍 {area_id}</h4>
                    <hr style="margin: 8px 0;">
                    <p><b>{indicador_config['titulo']}:</b> {valor:.2f}</p>
                    <p><b>Estado:</b> {area_data.get('estado', 'N/A')}</p>
                    <p><b>Área:</b> {area_data.get('area_ha', 'N/A'):.2f} ha</p>
                    <p><b>Coordenadas:</b><br>
                    Lat: {centroid.y:.6f}<br>
                    Lon: {centroid.x:.6f}</p>
                </div>
                """
                
                folium.Marker(
                    location=[centroid.y, centroid.x],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{area_id}: {valor:.2f}",
                    icon=folium.Icon(color='green', icon='leaf', prefix='fa')
                ).add_to(marker_cluster)
                
                # Agregar área coloreada
                area_geojson = gpd.GeoSeries([geometry]).__geo_interface__
                folium.GeoJson(
                    area_geojson,
                    style_function=lambda x, color=color: {
                        'fillColor': color,
                        'color': color,
                        'weight': 1,
                        'fillOpacity': 0.5
                    },
                    name=f'Área {area_id}'
                ).add_to(m)
        
        # Agregar leyenda
        try:
            colormap = LinearColormap(
                colors=[c for c in indicador_config['colores'].values()],
                vmin=min([r[0] for r in indicador_config['colores'].keys()]),
                vmax=max([r[1] for r in indicador_config['colores'].keys()]),
                caption=indicador_config['titulo']
            )
            colormap.add_to(m)
        except Exception as e:
            st.warning(f"Leyenda no generada: {str(e)}")
        
        # Agregar controles
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        folium.LayerControl().add_to(m)
        
        # Agregar botón de reset view
        folium.plugins.LocateControl(auto_start=False).add_to(m)
        
        return m
        
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
        return crear_mapa_base()

def crear_mapa_base():
    """Crear mapa base con ESRI Satellite"""
    m = folium.Map(location=[-14.0, -60.0], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite ESRI'
    ).add_to(m)
    folium.TileLayer('OpenStreetMap').add_to(m)
    folium.LayerControl().add_to(m)
    return m

# ===============================
# 📊 GRÁFICOS AVANZADOS MEJORADOS
# ===============================
def crear_grafico_radial_bar(datos_combinados, categorias):
    """Crear gráfico de barras radiales (más moderno que radar)"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Seleccionar las primeras 6 áreas para claridad
        areas_seleccionadas = df['area'].unique()[:6]
        df = df[df['area'].isin(areas_seleccionadas)]
        
        fig = go.Figure()
        
        for area in areas_seleccionadas:
            area_data = df[df['area'] == area]
            valores = [area_data[cat].values[0] if cat in area_data.columns else 0 for cat in categorias.keys()]
            
            fig.add_trace(go.Barpolar(
                r=valores,
                theta=list(categorias.values()),
                name=area,
                marker_color=px.colors.qualitative.Set2[len(fig.data) % len(px.colors.qualitative.Set2)],
                marker_line_color='black',
                marker_line_width=1,
                opacity=0.8
            ))
        
        fig.update_layout(
            title='Comparación Radial de Indicadores',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    tickfont=dict(size=10)
                ),
                angularaxis=dict(
                    tickfont=dict(size=11),
                    rotation=90
                ),
                bgcolor='#f8f9fa'
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            paper_bgcolor='white',
            plot_bgcolor='white',
            height=500
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico radial: {str(e)}")
        return go.Figure()

def crear_grafico_ridge(datos, columna_valor, columna_grupo, titulo):
    """Crear gráfico Ridge (joyplot) para distribución de valores"""
    if not datos or len(datos) == 0:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        # Preparar datos para ridge plot
        fig = go.Figure()
        
        grupos = df[columna_grupo].unique()[:8]  # Limitar a 8 grupos
        
        for i, grupo in enumerate(grupos):
            valores = df[df[columna_grupo] == grupo][columna_valor]
            
            if len(valores) > 0:
                # Usar índice entero para seleccionar color
                color_idx = int(i % len(px.colors.sequential.Viridis))
                fig.add_trace(go.Violin(
                    x=valores,
                    y0=str(grupo),  # Asegurar que sea string
                    name=str(grupo),
                    orientation='h',
                    side='positive',
                    line_color=px.colors.sequential.Viridis[color_idx],
                    fillcolor=px.colors.sequential.Viridis[color_idx],
                    opacity=0.7,
                    meanline_visible=True,
                    meanline_color='white',
                    meanline_width=2
                ))
        
        fig.update_layout(
            title=titulo,
            xaxis_title=columna_valor,
            yaxis_title=columna_grupo,
            showlegend=False,
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico ridge: {str(e)}")
        return go.Figure()

def crear_grafico_parallel_categories(datos_combinados, dimensiones, titulo):
    """Crear gráfico de categorías paralelas para relaciones multidimensionales"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Crear categorías para las dimensiones continuas
        for dim in dimensiones:
            if dim in df.columns:
                if df[dim].dtype in ['float64', 'int64']:
                    df[f'{dim}_cat'] = pd.qcut(df[dim], q=4, labels=['Muy Bajo', 'Bajo', 'Alto', 'Muy Alto'])
        
        # Seleccionar columnas categóricas
        cat_columns = [f'{dim}_cat' for dim in dimensiones if f'{dim}_cat' in df.columns]
        
        if len(cat_columns) >= 2:
            fig = px.parallel_categories(
                df,
                dimensions=cat_columns,
                color_continuous_scale=px.colors.sequential.Viridis,
                title=titulo,
                height=400
            )
            
            fig.update_layout(
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig
        else:
            return crear_grafico_heatmap_correlacion(datos_combinados, dimensiones)
            
    except Exception as e:
        st.error(f"Error creando gráfico de categorías paralelas: {str(e)}")
        return go.Figure()

def crear_grafico_heatmap_correlacion(datos_combinados, indicadores):
    """Crear heatmap de correlación mejorado"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_existentes = [col for col in indicadores.keys() if col in df.columns]
        
        if len(columnas_existentes) < 2:
            st.warning("No hay suficientes indicadores para calcular correlaciones")
            return go.Figure()
        
        correlaciones = df[columnas_existentes].corr()
        
        # Crear heatmap con anotaciones
        fig = ff.create_annotated_heatmap(
            z=correlaciones.values.round(2),
            x=[indicadores[col] for col in columnas_existentes],
            y=[indicadores[col] for col in columnas_existentes],
            annotation_text=correlaciones.round(2).values,
            colorscale='RdYlBu',
            showscale=True,
            font_colors=['black', 'white']
        )
        
        fig.update_layout(
            title="🔗 Matriz de Correlación entre Indicadores",
            title_font=dict(size=16, color='#2E8B57'),
            paper_bgcolor='white',
            plot_bgcolor='white',
            height=500,
            margin=dict(l=50, r=50, t=60, b=50)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando heatmap: {str(e)}")
        return go.Figure()

def crear_grafico_bubble_chart(datos_combinados, ejes_config):
    """Crear gráfico de burbujas interactivo"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Verificar columnas requeridas
        required_cols = ['x', 'y', 'size', 'color']
        available_cols = {}
        
        for col in required_cols:
            if col in ejes_config and ejes_config[col] in df.columns:
                available_cols[col] = ejes_config[col]
        
        if len(available_cols) >= 3:
            fig = px.scatter(
                df,
                x=available_cols.get('x'),
                y=available_cols.get('y'),
                size=available_cols.get('size', available_cols.get('x')),
                color=available_cols.get('color', available_cols.get('x')),
                hover_name='area',
                size_max=40,
                title=ejes_config.get('titulo', 'Gráfico de Burbujas'),
                color_continuous_scale='Viridis',
                template='plotly_white'
            )
            
            fig.update_layout(
                paper_bgcolor='white',
                plot_bgcolor='white',
                height=500,
                xaxis_title=available_cols.get('x'),
                yaxis_title=available_cols.get('y'),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            return fig
        else:
            return crear_grafico_3d_scatter(datos_combinados, ejes_config)
            
    except Exception as e:
        st.error(f"Error creando gráfico de burbujas: {str(e)}")
        return go.Figure()

def crear_grafico_3d_scatter(datos_combinados, ejes_config):
    """Crear gráfico 3D scatter básico"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Verificar columnas requeridas
        required_cols = ['x', 'y', 'z']
        available_cols = {}
        
        for col in required_cols:
            if col in ejes_config and ejes_config[col] in df.columns:
                available_cols[col] = ejes_config[col]
        
        if len(available_cols) >= 3:
            fig = go.Figure(data=[go.Scatter3d(
                x=df[available_cols['x']],
                y=df[available_cols['y']],
                z=df[available_cols['z']],
                mode='markers',
                marker=dict(
                    size=8,
                    color=df.get(ejes_config.get('color', available_cols['x']), df[available_cols['x']]),
                    colorscale='Viridis',
                    opacity=0.8
                ),
                text=df['area'],
                hoverinfo='text+x+y+z'
            )])
            
            fig.update_layout(
                title=ejes_config.get('titulo', 'Gráfico 3D'),
                scene=dict(
                    xaxis_title=available_cols.get('x'),
                    yaxis_title=available_cols.get('y'),
                    zaxis_title=available_cols.get('z')
                ),
                height=500
            )
            
            return fig
        else:
            return go.Figure()
            
    except Exception as e:
        st.error(f"Error creando gráfico 3D: {str(e)}")
        return go.Figure()

def crear_grafico_3d_scatter_mejorado(datos_combinados, ejes_config):
    """Crear gráfico 3D scatter mejorado"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_necesarias = [ejes_config['x'], ejes_config['y'], ejes_config['z']]
        columnas_existentes = [col for col in columnas_necesarias if col in df.columns]
        
        if len(columnas_existentes) < 3:
            return crear_grafico_bubble_chart(datos_combinados, ejes_config)
        
        fig = px.scatter_3d(
            df,
            x=ejes_config['x'],
            y=ejes_config['y'],
            z=ejes_config['z'],
            color=ejes_config.get('color', ejes_config['x']),
            size=ejes_config.get('size', ejes_config['x']),
            hover_name='area',
            title=ejes_config['titulo'],
            color_continuous_scale='Viridis',
            opacity=0.8,
            symbol_sequence=['circle', 'square', 'diamond', 'cross', 'x']
        )
        
        fig.update_layout(
            paper_bgcolor='white',
            scene=dict(
                bgcolor='white',
                xaxis_title=ejes_config['x'],
                yaxis_title=ejes_config['y'],
                zaxis_title=ejes_config['z'],
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray'),
                zaxis=dict(gridcolor='lightgray')
            ),
            height=600,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico 3D mejorado: {str(e)}")
        return go.Figure()

def crear_grafico_sankey(datos_combinados, categorias, titulo):
    """Crear diagrama de Sankey para flujos entre categorías"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Crear nodos para cada categoría
        all_labels = []
        for categoria in categorias.values():
            all_labels.append(f"{categoria} - Bajo")
            all_labels.append(f"{categoria} - Medio")
            all_labels.append(f"{categoria} - Alto")
        
        # Mapear índices
        label_to_index = {label: i for i, label in enumerate(all_labels)}
        
        # Crear enlaces (simplificado para demostración)
        sources = []
        targets = []
        values = []
        
        # Para un ejemplo simple, creamos enlaces entre categorías adyacentes
        for i in range(len(categorias) - 1):
            cat1 = list(categorias.values())[i]
            cat2 = list(categorias.values())[i + 1]
            
            for nivel in ['Bajo', 'Medio', 'Alto']:
                source_idx = label_to_index[f"{cat1} - {nivel}"]
                target_idx = label_to_index[f"{cat2} - {nivel}"]
                sources.append(source_idx)
                targets.append(target_idx)
                values.append(np.random.randint(1, 10))
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_labels,
                color=px.colors.qualitative.Set3
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(46, 139, 87, 0.3)"
            )
        )])
        
        fig.update_layout(
            title=titulo,
            font_size=10,
            height=400,
            paper_bgcolor='white'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando diagrama de Sankey: {str(e)}")
        return go.Figure()

def crear_dashboard_indicadores(datos_combinados):
    """Crear dashboard con múltiples gráficos en subplots"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        
        # Crear subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Distribución de Biodiversidad', 'Relación NDVI-Carbono',
                          'Correlaciones', 'Áreas por Estado'),
            specs=[[{'type': 'violin'}, {'type': 'scatter'}],
                   [{'type': 'heatmap'}, {'type': 'pie'}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # 1. Violin plot para biodiversidad
        if 'indice_shannon' in df.columns:
            fig.add_trace(
                go.Violin(y=df['indice_shannon'], name='Biodiversidad',
                         box_visible=True, meanline_visible=True,
                         fillcolor='lightseagreen', opacity=0.6),
                row=1, col=1
            )
        
        # 2. Scatter plot NDVI vs Carbono
        if 'ndvi' in df.columns and 'co2_total_ton' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['ndvi'], y=df['co2_total_ton'],
                          mode='markers', name='NDVI vs Carbono',
                          marker=dict(color=df['co2_total_ton'],
                                     colorscale='Viridis',
                                     size=10,
                                     showscale=True)),
                row=1, col=2
            )
        
        # 3. Heatmap de correlación simplificado
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:4]
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            fig.add_trace(
                go.Heatmap(z=corr_matrix.values,
                          x=numeric_cols,
                          y=numeric_cols,
                          colorscale='RdYlBu',
                          showscale=True),
                row=2, col=1
            )
        
        # 4. Pie chart simplificado
        if 'salud_vegetacion' in df.columns:
            estado_counts = df['salud_vegetacion'].value_counts()
            fig.add_trace(
                go.Pie(labels=estado_counts.index,
                      values=estado_counts.values,
                      name='Estado Vegetación'),
                row=2, col=2
            )
        
        fig.update_layout(
            height=700,
            showlegend=True,
            paper_bgcolor='white',
            plot_bgcolor='white',
            title_text="📊 Dashboard de Indicadores",
            title_font=dict(size=20, color='#2E8B57')
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando dashboard: {str(e)}")
        return go.Figure()

# ===============================
# 🧩 CLASE PRINCIPAL DE ANÁLISIS (COMPLETA)
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
            # Aproximación: 1 grado ≈ 111 km (en latitud)
            lat_centro = poligono.centroid.y
            cos_lat = math.cos(math.radians(lat_centro))
            area_km2 = area_grados * 111 * 111 * cos_lat
            return round(area_km2 * 100, 2)  # Convertir a hectáreas
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
                    
                    # Intersectar con el polígono original
                    interseccion = poligono.intersection(celda_rect)
                    if not interseccion.is_empty:
                        area_celda = self._calcular_area_hectareas(interseccion)
                        if area_celda > 0.01:  # Ignorar celdas muy pequeñas
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
        """Método principal para procesar el polígono y calcular todos los indicadores"""
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
                co2_total = carbono_ton_ha * area_ha * 3.67  # Convertir a CO2
                
                resultados_carbono.append({
                    'area': area_id,
                    'carbono_ton_ha': round(carbono_ton_ha, 2),
                    'co2_total_ton': round(co2_total, 2),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Biodiversidad (Índice de Shannon)
                biod_base = params['biodiversidad']
                indice_shannon = self._simular_distribucion_normal(biod_base * 2.5, 0.2)  # Escalar a rango 0-3
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
                # Relacionar con NDVI y tipo de vegetación
                disponibilidad_base = ndvi * 0.8 + params['resiliencia'] * 0.2
                disponibilidad = self._calcular_indicador_con_variacion(disponibilidad_base, 0.25)
                
                resultados_agua.append({
                    'area': area_id,
                    'disponibilidad_agua': round(disponibilidad, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Suelo (Salud)
                # Relacionar con vegetación y carbono
                salud_suelo_base = (ndvi * 0.6 + (carbono_ton_ha / carbono_max) * 0.4)
                salud_suelo = self._calcular_indicador_con_variacion(salud_suelo_base, 0.2)
                
                resultados_suelo.append({
                    'area': area_id,
                    'salud_suelo': round(salud_suelo, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
                
                # Conectividad ecológica
                # Depende del área y ubicación en la grilla
                # Áreas centrales tienen mejor conectividad
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
                # Inversamente relacionada con NDVI y conectividad
                presion_base = (1.0 - ndvi) * 0.7 + (1.0 - conectividad) * 0.3
                presion = self._calcular_indicador_con_variacion(presion_base, 0.25)
                
                resultados_presiones.append({
                    'area': area_id,
                    'presion_total': round(presion, 3),
                    'area_ha': area_ha,
                    'geometry': area['geometry']
                })
            
            # 3. Calcular métricas de resumen
            # Extraer arrays de valores para cálculo
            ndvi_vals = [r['ndvi'] for r in resultados_vegetacion]
            co2_vals = [r['co2_total_ton'] for r in resultados_carbono]
            shannon_vals = [r['indice_shannon'] for r in resultados_biodiversidad]
            agua_vals = [r['disponibilidad_agua'] for r in resultados_agua]
            suelo_vals = [r['salud_suelo'] for r in resultados_suelo]
            conect_vals = [r['conectividad_total'] for r in resultados_conectividad]
            presion_vals = [r['presion_total'] for r in resultados_presiones]
            
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
                'indice_biodiversidad_promedio': round(np.mean(shannon_vals) if shannon_vals else 0, 3),
                'disponibilidad_agua_promedio': round(np.mean(agua_vals) if agua_vals else 0, 3),
                'salud_suelo_promedio': round(np.mean(suelo_vals) if suelo_vals else 0, 3),
                'conectividad_promedio': round(promedio_conectividad, 3),
                'presion_antropica_promedio': round(promedio_presion, 3),
                'areas_analizadas': len(areas_analisis),
                'ndvi_promedio': round(promedio_ndvi, 3)
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
# 📁 MANEJO DE ARCHIVOS Y DESCARGAS CORREGIDO
# ===============================
def generar_geojson_indicador(datos, nombre_indicador):
    """Generar GeoJSON para un indicador específico"""
    try:
        datos_limpios = []
        for item in datos:
            item_limpio = item.copy()
            if 'centroid' in item_limpio:
                del item_limpio['centroid']
            if 'geometry' in item_limpio:
                item_limpio['geometry_wkt'] = item_limpio['geometry'].wkt
                del item_limpio['geometry']
            datos_limpios.append(item_limpio)
        
        df_limpio = pd.DataFrame(datos_limpios)
        json_str = df_limpio.to_json(orient='records', indent=2)
        return json_str
    except Exception as e:
        st.error(f"Error generando GeoJSON: {str(e)}")
        return None

def generar_geojson_completo(resultados):
    """Generar un GeoJSON completo con todos los indicadores - CORREGIDO"""
    try:
        todos_datos = []
        # Asumimos que todos los arrays tienen la misma longitud
        for i in range(len(resultados['resultados']['vegetacion'])):
            # Crear diccionario con todos los datos
            area_data = {
                'area': resultados['resultados']['vegetacion'][i]['area'],
                'geometry': resultados['resultados']['vegetacion'][i]['geometry'],
                'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                'salud_vegetacion': resultados['resultados']['vegetacion'][i]['salud_vegetacion'],
                'area_ha': resultados['resultados']['vegetacion'][i]['area_ha']
            }
            
            # Agregar carbono si existe
            if i < len(resultados['resultados']['carbono']):
                area_data['co2_total_ton'] = resultados['resultados']['carbono'][i]['co2_total_ton']
                area_data['carbono_ton_ha'] = resultados['resultados']['carbono'][i]['carbono_ton_ha']
            
            # Agregar biodiversidad si existe
            if i < len(resultados['resultados']['biodiversidad']):
                area_data['indice_shannon'] = resultados['resultados']['biodiversidad'][i]['indice_shannon']
                area_data['estado_biodiversidad'] = resultados['resultados']['biodiversidad'][i]['estado_biodiversidad']
            
            # Agregar agua si existe
            if i < len(resultados['resultados']['agua']):
                area_data['disponibilidad_agua'] = resultados['resultados']['agua'][i]['disponibilidad_agua']
            
            # Agregar suelo si existe
            if i < len(resultados['resultados']['suelo']):
                area_data['salud_suelo'] = resultados['resultados']['suelo'][i]['salud_suelo']
            
            # Agregar conectividad si existe
            if i < len(resultados['resultados']['conectividad']):
                area_data['conectividad_total'] = resultados['resultados']['conectividad'][i]['conectividad_total']
            
            # Agregar presiones si existe
            if i < len(resultados['resultados']['presiones']):
                area_data['presion_total'] = resultados['resultados']['presiones'][i]['presion_total']
            
            todos_datos.append(area_data)
        
        # Crear GeoDataFrame
        gdf = gpd.GeoDataFrame(todos_datos, geometry='geometry', crs="EPSG:4326")
        geojson_str = gdf.to_json()
        return geojson_str
    except Exception as e:
        st.error(f"Error generando GeoJSON completo: {str(e)}")
        return None

def crear_documento_word(resultados):
    """Crear documento Word con el informe completo"""
    if not DOCX_AVAILABLE:
        st.error("La librería python-docx no está disponible")
        return None
    
    try:
        doc = Document()
        title = doc.add_heading('Informe de Análisis de Biodiversidad', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        doc.add_paragraph()
        
        doc.add_heading('Resumen Ejecutivo', level=1)
        summary = resultados['resultados']['summary_metrics']
        resumen_text = f"""
        Este informe presenta los resultados del análisis integral de biodiversidad realizado en el área de estudio.
        Área total analizada: {resultados['area_hectareas']:,.2f} hectáreas
        Tipo de vegetación: {resultados['tipo_vegetacion']}
        Estado general del ecosistema: {summary['estado_general']}
        Carbono total almacenado: {summary['carbono_total_co2_ton']:,} ton CO₂
        Índice de biodiversidad promedio: {summary['indice_biodiversidad_promedio']}
        Áreas analizadas: {summary['areas_analizadas']}
        """
        doc.add_paragraph(resumen_text)
        doc.add_paragraph()
        
        doc.add_heading('Indicadores Principales', level=1)
        indicadores_data = [
            ('Carbono Total', f"{summary['carbono_total_co2_ton']:,} ton CO₂"),
            ('Biodiversidad', f"{summary['indice_biodiversidad_promedio']}"),
            ('Disponibilidad de Agua', f"{summary['disponibilidad_agua_promedio']}"),
            ('Salud del Suelo', f"{summary['salud_suelo_promedio']}"),
            ('Presión Antrópica', f"{summary['presion_antropica_promedio']}"),
            ('Conectividad', f"{summary['conectividad_promedio']}")
        ]
        
        for nombre, valor in indicadores_data:
            p = doc.add_paragraph()
            p.add_run(f"{nombre}: ").bold = True
            p.add_run(valor)
        
        doc.add_paragraph()
        
        doc.add_heading('Recomendaciones', level=1)
        if summary['estado_general'] in ['Crítico', 'Moderado']:
            recomendaciones = [
                "Implementar programas de restauración ecológica en áreas degradadas",
                "Establecer corredores biológicos para mejorar la conectividad",
                "Monitorear continuamente las presiones antrópicas",
                "Desarrollar estrategias de conservación de la biodiversidad",
                "Considerar programas de pago por servicios ambientales"
            ]
        else:
            recomendaciones = [
                "Mantener las prácticas actuales de conservación",
                "Continuar con el monitoreo periódico de indicadores",
                "Fortalecer la protección contra amenazas externas",
                "Promover la investigación científica en el área",
                "Considerar certificaciones de conservación"
            ]
        
        for rec in recomendaciones:
            doc.add_paragraph(rec, style='List Bullet')
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error generando documento Word: {str(e)}")
        return None

def crear_boton_descarga(data, filename, button_text, file_type):
    """Crear botón de descarga para diferentes tipos de archivos"""
    try:
        if file_type == 'geojson':
            if data is None:
                st.error(f"No hay datos para generar {filename}")
                return
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        elif file_type == 'word':
            if data is None:
                st.error(f"No hay datos para generar {filename}")
                return
            b64 = base64.b64encode(data.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        elif file_type == 'csv':
            b64 = base64.b64encode(data.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-btn">📥 {button_text}</a>'
        st.markdown(f'<div style="margin: 10px 0;">{href}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error creando botón de descarga: {str(e)}")

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
            hasattr(st.session_state.poligono_data, 'empty') and 
            not st.session_state.poligono_data.empty)

def sidebar_config():
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%); border-radius: 12px;'>
            <h2 style='color: white; margin-bottom: 0;'>🌿</h2>
            <h3 style='color: white; margin: 0;'>Análisis de Biodiversidad</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("🗺️ Cargar Polígono")
        
        with st.expander("📋 Formatos soportados"):
            st.markdown("""
            **Formatos recomendados:**
            - **GeoJSON (.geojson, .json)** - Mejor compatibilidad
            - **Shapefile (.zip)** - Comprimir todos los archivos del shapefile
            - **KML (.kml)** - Soporte limitado, puede requerir conversión
            
            **Recomendación:** Para mejores resultados, convierte tus archivos KML a GeoJSON.
            """)
        
        uploaded_file = st.file_uploader("Sube tu archivo territorial", 
                                        type=['kml', 'zip', 'geojson', 'json'])
        
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None and not gdf.empty:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False
                    st.success(f"✅ Polígono cargado exitosamente")
                    
                    with st.expander("📊 Información del polígono"):
                        st.write(f"**Tipo:** {gdf.geometry.iloc[0].geom_type}")
                        st.write(f"**Cantidad de polígonos:** {len(gdf)}")
                        bounds = gdf.total_bounds
                        st.write(f"**Extensión:**")
                        st.write(f"- Min Lon: {bounds[0]:.6f}")
                        st.write(f"- Min Lat: {bounds[1]:.6f}")
                        st.write(f"- Max Lon: {bounds[2]:.6f}")
                        st.write(f"- Max Lat: {bounds[3]:.6f}")
                    
                    st.rerun()
                else:
                    st.error("No se pudo procesar el archivo. Intenta con otro formato.")
        
        st.markdown("---")
        st.header("📊 Configuración de Análisis")
        vegetation_type = st.selectbox("🌿 Tipo de vegetación predominante", [
            'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
            'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
            'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
        ])
        divisiones = st.slider("🔲 Divisiones del área", 3, 8, 5,
                             help="Número de divisiones para crear la grilla de análisis")
        
        return uploaded_file, vegetation_type, divisiones

# ===============================
# 🎯 APLICACIÓN PRINCIPAL MEJORADA Y CORREGIDA
# ===============================
def main():
    aplicar_estilos_globales()
    crear_header()
    initialize_session_state()
    
    if not DOCX_AVAILABLE:
        st.warning("⚠️ La librería python-docx no está instalada. La generación de informes Word estará deshabilitada.")
    if not SCIPY_AVAILABLE:
        st.warning("⚠️ La librería scipy no está instalada. Algunas funciones de interpolación pueden no estar disponibles.")
    
    uploaded_file, vegetation_type, divisiones = sidebar_config()
    
    if tiene_poligono_data():
        gdf = st.session_state.poligono_data
        poligono = gdf.geometry.iloc[0]
        area_ha = st.session_state.analyzer._calcular_area_hectareas(poligono)
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📐 Información del Área de Estudio")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Área aproximada", f"{area_ha:,.2f} ha")
        with col2:
            st.metric("Tipo de vegetación", vegetation_type)
        with col3:
            st.metric("Áreas de análisis", f"{divisiones}x{divisiones}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    if tiene_poligono_data() and not st.session_state.analysis_complete:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        if st.button("🚀 EJECUTAR ANÁLISIS INTEGRAL", type="primary", use_container_width=True):
            with st.spinner("Realizando análisis integral de biodiversidad..."):
                resultados = st.session_state.analyzer.procesar_poligono(
                    st.session_state.poligono_data, vegetation_type, divisiones
                )
                if resultados:
                    st.session_state.results = resultados
                    st.session_state.analysis_complete = True
                    st.success("✅ Análisis completado exitosamente!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
        # SECCIÓN DE DESCARGAS
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📥 Descargas")
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            st.markdown("**🗺️ Mapas GeoJSON**")
            geojson_completo = generar_geojson_completo(resultados)
            if geojson_completo:
                crear_boton_descarga(
                    geojson_completo,
                    "mapa_completo.geojson",
                    "Descargar GeoJSON Completo",
                    'geojson'
                )
        
        with col_dl2:
            st.markdown("**📊 Datos Completos**")
            datos_combinados = []
            for i in range(len(resultados['resultados']['vegetacion'])):
                combo = {
                    'area': resultados['resultados']['vegetacion'][i]['area'],
                    'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                    'salud_vegetacion': resultados['resultados']['vegetacion'][i]['salud_vegetacion'],
                    'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton'],
                    'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                    'disponibilidad_agua': resultados['resultados']['agua'][i]['disponibilidad_agua'],
                    'salud_suelo': resultados['resultados']['suelo'][i]['salud_suelo'],
                    'conectividad_total': resultados['resultados']['conectividad'][i]['conectividad_total'],
                    'presion_total': resultados['resultados']['presiones'][i]['presion_total']
                }
                datos_combinados.append(combo)
            
            df_completo = pd.DataFrame(datos_combinados)
            csv = df_completo.to_csv(index=False)
            crear_boton_descarga(
                csv,
                "datos_analisis_completo.csv",
                "Descargar CSV Completo",
                'csv'
            )
        
        with col_dl3:
            st.markdown("**📄 Informe Ejecutivo**")
            if DOCX_AVAILABLE:
                doc_buffer = crear_documento_word(resultados)
                if doc_buffer:
                    crear_boton_descarga(
                        doc_buffer,
                        "informe_biodiversidad.docx",
                        "Descargar Informe Word",
                        'word'
                    )
            else:
                st.warning("⚠️ python-docx no disponible")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # RESUMEN EJECUTIVO MEJORADO
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📊 Resumen Ejecutivo del Análisis")
        
        # Métricas con iconos y colores
        cols = st.columns(4)
        metricas = [
            ("🌳 Carbono Total", f"{summary['carbono_total_co2_ton']:,}", "ton CO₂", "#006400"),
            ("🦋 Biodiversidad", f"{summary['indice_biodiversidad_promedio']:.2f}", "Índice", "#32CD32"),
            ("💧 Disponibilidad Agua", f"{summary['disponibilidad_agua_promedio']:.2f}", "Índice", "#1E90FF"),
            ("📈 Estado General", summary['estado_general'], "", "#2E8B57")
        ]
        
        for col, (titulo, valor, unidad, color) in zip(cols, metricas):
            with col:
                st.markdown(f"""
                <div style='background: {color}15; padding: 1rem; border-radius: 10px; border-left: 4px solid {color};'>
                    <h4 style='margin: 0; color: {color};'>{titulo.split()[0]}</h4>
                    <h2 style='margin: 0.5rem 0; color: {color};'>{valor}</h2>
                    <p style='margin: 0; color: #666;'>{titulo.split()[1] if len(titulo.split()) > 1 else ''} {unidad}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # CONFIGURACIÓN DE INDICADORES CON VISUALIZACIONES MEJORADAS
        indicadores_config = [
            {
                'key': 'carbono',
                'titulo': '🌳 Almacenamiento de Carbono',
                'columna': 'co2_total_ton',
                'descripcion': 'Potencial de captura y almacenamiento de CO₂ en toneladas',
                'colores': {
                    (0, 1000): '#ffffcc',
                    (1000, 5000): '#c2e699', 
                    (5000, 10000): '#78c679',
                    (10000, 50000): '#238443',
                    (50000, 1000000): '#00441b'
                },
                'leyenda': {
                    (0, 1000): 'Muy Bajo (<1K ton)',
                    (1000, 5000): 'Bajo (1K-5K ton)',
                    (5000, 10000): 'Moderado (5K-10K ton)',
                    (10000, 50000): 'Alto (10K-50K ton)',
                    (50000, 1000000): 'Muy Alto (>50K ton)'
                }
            },
            {
                'key': 'vegetacion',
                'titulo': '🌿 Salud de la Vegetación',
                'columna': 'ndvi',
                'descripcion': 'Índice de Vegetación de Diferencia Normalizada (NDVI)',
                'colores': {
                    (0, 0.3): '#FF4500',
                    (0.3, 0.5): '#FFD700',
                    (0.5, 0.7): '#32CD32', 
                    (0.7, 1.0): '#006400'
                },
                'leyenda': {
                    (0, 0.3): 'Degradada (0-0.3)',
                    (0.3, 0.5): 'Moderada (0.3-0.5)',
                    (0.5, 0.7): 'Buena (0.5-0.7)',
                    (0.7, 1.0): 'Excelente (0.7-1.0)'
                }
            },
            {
                'key': 'biodiversidad', 
                'titulo': '🦋 Índice de Biodiversidad',
                'columna': 'indice_shannon',
                'descripcion': 'Índice de Shannon-Wiener de diversidad de especies',
                'colores': {
                    (0, 1.0): '#FF4500',
                    (1.0, 1.5): '#FFD700',
                    (1.5, 2.0): '#32CD32',
                    (2.0, 3.0): '#006400'
                },
                'leyenda': {
                    (0, 1.0): 'Muy Bajo (0-1.0)',
                    (1.0, 1.5): 'Bajo (1.0-1.5)', 
                    (1.5, 2.0): 'Moderado (1.5-2.0)',
                    (2.0, 3.0): 'Alto (2.0-3.0)'
                }
            },
            {
                'key': 'agua',
                'titulo': '💧 Disponibilidad de Agua',
                'columna': 'disponibilidad_agua', 
                'descripcion': 'Disponibilidad relativa de recursos hídricos',
                'colores': {
                    (0, 0.3): '#FF4500',
                    (0.3, 0.5): '#FFD700',
                    (0.5, 0.7): '#87CEEB',
                    (0.7, 1.0): '#1E90FF'
                },
                'leyenda': {
                    (0, 0.3): 'Crítica (0-0.3)',
                    (0.3, 0.5): 'Baja (0.3-0.5)',
                    (0.5, 0.7): 'Moderada (0.5-0.7)',
                    (0.7, 1.0): 'Alta (0.7-1.0)'
                }
            }
        ]
        
        # MAPAS POR INDICADOR CON ZOOM AUTOMÁTICO
        for idx, config in enumerate(indicadores_config):
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.subheader(config['titulo'])
            st.markdown(f"*{config['descripcion']}*")
            
            # Mapa con zoom automático
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            mapa = crear_mapa_indicador(
                st.session_state.poligono_data,
                resultados['resultados'][config['key']],
                config
            )
            st_folium(mapa, width=900, height=500, key=f"map_{config['key']}_{idx}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Visualizaciones avanzadas
            col_viz1, col_viz2 = st.columns(2)
            with col_viz1:
                # Gráfico Ridge para distribución
                st.plotly_chart(
                    crear_grafico_ridge(
                        resultados['resultados'][config['key']],
                        config['columna'],
                        'area',
                        f"Distribución de {config['titulo']}"
                    ),
                    use_container_width=True,
                    key=f"ridge_{config['key']}_{idx}"
                )
            with col_viz2:
                # Gráfico de violín mejorado
                st.plotly_chart(
                    crear_grafico_violin_mejorado(
                        resultados['resultados'][config['key']],
                        config['columna'],
                        f"Distribución de {config['titulo']}"
                    ),
                    use_container_width=True,
                    key=f"violin_{config['key']}_{idx}"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # VISUALIZACIONES AVANZADAS MULTIVARIADO
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 Análisis Multivariado Avanzado")
        
        # Combinar datos para análisis multivariado
        datos_combinados = []
        for i in range(len(resultados['resultados']['vegetacion'])):
            combo = {
                'area': resultados['resultados']['vegetacion'][i]['area'],
                'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton'],
                'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                'disponibilidad_agua': resultados['resultados']['agua'][i]['disponibilidad_agua'],
                'salud_suelo': resultados['resultados']['suelo'][i]['salud_suelo'],
                'conectividad_total': resultados['resultados']['conectividad'][i]['conectividad_total'],
                'presion_total': resultados['resultados']['presiones'][i]['presion_total']
            }
            datos_combinados.append(combo)
        
        # DASHBOARD COMPLETO
        st.subheader("📊 Dashboard Integrado")
        st.plotly_chart(
            crear_dashboard_indicadores(datos_combinados),
            use_container_width=True,
            key="dashboard"
        )
        
        # GRÁFICOS DE RELACIÓN
        st.subheader("🔗 Relaciones entre Indicadores")
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            # Gráfico Radial Bar
            categorias_radar = {
                'ndvi': 'Vegetación',
                'indice_shannon': 'Biodiversidad',
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_grafico_radial_bar(datos_combinados, categorias_radar),
                use_container_width=True,
                key="radial_bar"
            )
        with col_rel2:
            # Gráfico de burbujas
            ejes_burbuja = {
                'x': 'ndvi',
                'y': 'indice_shannon', 
                'size': 'co2_total_ton',
                'color': 'salud_suelo',
                'titulo': 'Relación NDVI-Biodiversidad-Carbono'
            }
            st.plotly_chart(
                crear_grafico_bubble_chart(datos_combinados, ejes_burbuja),
                use_container_width=True,
                key="bubble_chart"
            )
        
        # GRÁFICO 3D MEJORADO
        st.subheader("🔍 Visualización Tridimensional")
        ejes_3d = {
            'x': 'ndvi',
            'y': 'indice_shannon', 
            'z': 'co2_total_ton',
            'color': 'salud_suelo',
            'size': 'disponibilidad_agua',
            'titulo': 'Relación Multidimensional de Indicadores'
        }
        st.plotly_chart(
            crear_grafico_3d_scatter_mejorado(datos_combinados, ejes_3d),
            use_container_width=True,
            height=600,
            key="3d_scatter"
        )
        
        # CORRELACIONES Y CATEGORÍAS PARALELAS
        col_corr1, col_corr2 = st.columns(2)
        with col_corr1:
            # Heatmap de correlación
            indicadores_corr = {
                'ndvi': 'Salud Vegetación',
                'co2_total_ton': 'Carbono',
                'indice_shannon': 'Biodiversidad', 
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_grafico_heatmap_correlacion(datos_combinados, indicadores_corr),
                use_container_width=True,
                key="heatmap"
            )
        with col_corr2:
            # Categorías paralelas
            st.plotly_chart(
                crear_grafico_parallel_categories(
                    datos_combinados,
                    ['ndvi', 'indice_shannon', 'co2_total_ton'],
                    "Relaciones Categóricas entre Indicadores"
                ),
                use_container_width=True,
                key="parallel_categories"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif not tiene_poligono_data():
        # Pantalla de bienvenida mejorada
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Análisis Integral de Biodiversidad!
        ### 🌿 Sistema de Evaluación Ecológica Avanzada
        
        **✨ Nuevas Características:**
        
        🗺️ **Mapas Inteligentes**
        - Zoom automático al área de estudio
        - Capas de satélite ESRI de alta resolución
        - Clúster de marcadores para mejor visualización
        - Leyendas interactivas
        
        📊 **Visualizaciones Avanzadas**
        - Gráficos Ridge para distribución de datos
        - Diagramas de Sankey para flujos
        - Categorías paralelas para análisis multidimensional
        - Heatmaps de correlación mejorados
        - Dashboard integrado con múltiples vistas
        
        🔍 **Análisis Multivariado**
        - Relaciones 3D entre indicadores
        - Gráficos de burbujas interactivos
        - Análisis de correlación avanzado
        - Visualizaciones radiales
        
        📈 **Resultados Ejecutivos**
        - Métricas con diseño moderno
        - Descargas en múltiples formatos
        - Informes Word automatizados
        - Exportación de datos completa
        
        **🎯 ¿Cómo empezar?**
        1. 📤 Carga tu polígono en el panel lateral
        2. ⚙️ Configura el tipo de vegetación
        3. 🚀 Ejecuta el análisis integral
        4. 📊 Explora los resultados interactivos
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

def crear_grafico_violin_mejorado(datos, columna_valor, titulo):
    """Gráfico de violín mejorado con más opciones"""
    if not datos or len(datos) == 0:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        
        fig = go.Figure()
        
        fig.add_trace(go.Violin(
            y=df[columna_valor],
            box_visible=True,
            meanline_visible=True,
            fillcolor='lightseagreen',
            opacity=0.6,
            line_color='black',
            x0=titulo,
            points='all',
            jitter=0.05,
            pointpos=-1.5,
            marker=dict(
                size=4,
                opacity=0.6
            )
        ))
        
        # Agregar estadísticas
        media = df[columna_valor].mean() if not df.empty else 0
        mediana = df[columna_valor].median() if not df.empty else 0
        std = df[columna_valor].std() if not df.empty else 0
        
        fig.add_annotation(
            x=0.5, y=1.05,
            xref="paper", yref="paper",
            text=f"Media: {media:.2f} | Mediana: {mediana:.2f} | Desv: {std:.2f}",
            showarrow=False,
            font=dict(size=10, color='#666')
        )
        
        fig.update_layout(
            title=titulo,
            yaxis_title=columna_valor,
            showlegend=False,
            height=400,
            paper_bgcolor='white',
            plot_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico de violín mejorado: {str(e)}")
        return go.Figure()

if __name__ == "__main__":
    main()
