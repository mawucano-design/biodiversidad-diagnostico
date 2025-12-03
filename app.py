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
import plotly.figure_factory as ff
from io import BytesIO
from datetime import datetime, timedelta
import json
import requests
from PIL import Image
import rasterio
from rasterio.plot import show
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import rasterstats
import warnings
warnings.filterwarnings('ignore')

# Librerías para análisis geoespacial y altimetría
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition, MeasureControl
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString, MultiLineString, box
import pyproj
from owslib.wms import WebMapService
import xml.etree.ElementTree as ET
from scipy import interpolate
import matplotlib.cm as cm

# Manejo de la librería docx con fallback
try:
    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    st.warning("⚠️ La librería python-docx no está instalada. La generación de informes Word estará deshabilitada.")

import base64
import random
from typing import List, Dict, Any
import hashlib
import time

# ===============================
# 🌿 CONFIGURACIÓN Y ESTILOS GLOBALES
# ===============================

st.set_page_config(
    page_title="Análisis Integral de Biodiversidad",
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
    .satellite-card {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #4361ee;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .elevation-container {
        background: linear-gradient(135deg, #1a2a3a 0%, #0d1b2a 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .elevation-header {
        color: white;
        text-align: center;
        margin-bottom: 20px;
        font-size: 1.5rem;
        font-weight: bold;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    .contour-line {
        stroke: #4CAF50;
        stroke-width: 1.5;
        fill: none;
    }
    .contour-label {
        fill: white;
        font-size: 10px;
        font-weight: bold;
        text-shadow: 1px 1px 2px black;
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
# 🏔️ CLASE PARA ANÁLISIS DE ALTIMETRÍA Y CURVAS DE NIVEL
# ===============================

class AnalizadorAltimetria:
    """Clase para analizar altimetría y generar curvas de nivel"""
    
    def __init__(self):
        # Configuración de curvas de nivel
        self.intervalos_curvas = {
            'detallado': 10,      # Cada 10 metros
            'normal': 25,         # Cada 25 metros  
            'general': 50,        # Cada 50 metros
            'esquematico': 100    # Cada 100 metros
        }
        
        # Colores para mapas de elevación
        self.escalas_colores = {
            'topografico': ['#006400', '#32CD32', '#FFD700', '#FF8C00', '#8B4513', '#A9A9A9'],
            'hipso': ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FFA500', '#FF0000'],
            'terrain': ['#8B4513', '#D2691E', '#F4A460', '#FFD700', '#32CD32', '#006400'],
            'viridis': ['#440154', '#3B528B', '#21918C', '#5DC863', '#FDE725']
        }
        
        # Parámetros de terreno
        self.tipos_terreno = {
            'montañoso': {'min_elev': 500, 'max_elev': 3000, 'rugosidad': 0.8},
            'colinoso': {'min_elev': 200, 'max_elev': 800, 'rugosidad': 0.5},
            'ondulado': {'min_elev': 100, 'max_elev': 300, 'rugosidad': 0.3},
            'plano': {'min_elev': 0, 'max_elev': 100, 'rugosidad': 0.1}
        }
    
    def generar_dem_simulado(self, bounds, tipo_terreno='colinoso', resolucion=100):
        """Generar un Modelo Digital de Elevación (DEM) simulado"""
        try:
            minx, miny, maxx, maxy = bounds
            
            # Parámetros según tipo de terreno
            params = self.tipos_terreno.get(tipo_terreno, self.tipos_terreno['colinoso'])
            
            # Calcular tamaño en metros (aproximado)
            width_deg = maxx - minx
            height_deg = maxy - miny
            lat_media = (miny + maxy) / 2
            
            # Aproximación: 1 grado ≈ 111km
            width_m = width_deg * 111000 * abs(math.cos(math.radians(lat_media)))
            height_m = height_deg * 111000
            
            # Número de celdas basado en resolución
            n_cols = int(width_m / resolucion)
            n_rows = int(height_m / resolucion)
            
            # Asegurar tamaño mínimo
            n_cols = max(n_cols, 50)
            n_rows = max(n_rows, 50)
            
            # Crear grid de coordenadas
            x = np.linspace(minx, maxx, n_cols)
            y = np.linspace(miny, maxy, n_rows)
            X, Y = np.meshgrid(x, y)
            
            # Generar elevación base
            elev_base = params['min_elev'] + (params['max_elev'] - params['min_elev']) * 0.5
            
            # Crear patrones de terreno
            elevacion = np.zeros((n_rows, n_cols))
            
            # Patrón 1: Ondulaciones principales
            for i in range(3):
                freq_x = np.random.uniform(0.5, 2.0)
                freq_y = np.random.uniform(0.5, 2.0)
                phase_x = np.random.uniform(0, 2*np.pi)
                phase_y = np.random.uniform(0, 2*np.pi)
                
                pattern = np.sin(freq_x * X + phase_x) * np.cos(freq_y * Y + phase_y)
                elevacion += pattern * (params['max_elev'] - params['min_elev']) * 0.1
            
            # Patrón 2: Rugosidad
            rugosidad = np.random.randn(n_rows, n_cols) * params['rugosidad'] * 50
            
            # Combinar patrones
            elevacion = elev_base + elevacion + rugosidad
            
            # Asegurar valores positivos
            elevacion = np.maximum(elevacion, 0)
            
            # Suavizar el terreno
            from scipy.ndimage import gaussian_filter
            elevacion = gaussian_filter(elevacion, sigma=1)
            
            # Crear diccionario de transformación
            transform = rasterio.transform.from_bounds(minx, miny, maxx, maxy, n_cols, n_rows)
            
            return {
                'elevacion': elevacion,
                'bounds': bounds,
                'transform': transform,
                'crs': 'EPSG:4326',
                'resolucion': resolucion,
                'n_cols': n_cols,
                'n_rows': n_rows,
                'x_coords': x,
                'y_coords': y
            }
            
        except Exception as e:
            st.error(f"Error generando DEM simulado: {str(e)}")
            return None
    
    def calcular_curvas_nivel(self, dem_data, intervalo=25):
        """Calcular curvas de nivel a partir del DEM"""
        try:
            elevacion = dem_data['elevacion']
            x = dem_data['x_coords']
            y = dem_data['y_coords']
            
            # Determinar niveles de contorno
            min_elev = np.min(elevacion)
            max_elev = np.max(elevacion)
            
            # Ajustar intervalo si es necesario
            if intervalo <= 0:
                intervalo = 25
            
            # Crear niveles
            niveles = np.arange(
                np.floor(min_elev / intervalo) * intervalo,
                np.ceil(max_elev / intervalo) * intervalo + intervalo,
                intervalo
            )
            
            # Crear figura para extraer contornos
            fig, ax = plt.subplots(figsize=(10, 8))
            contorno = ax.contour(x, y, elevacion, levels=niveles, colors='green', linewidths=1)
            plt.close(fig)
            
            # Extraer paths de contornos
            curvas_nivel = []
            
            for i, nivel in enumerate(contorno.levels):
                paths = contorno.collections[i].get_paths()
                for path in paths:
                    vertices = path.vertices
                    if len(vertices) > 1:
                        # Crear LineString para cada segmento
                        line = LineString(vertices)
                        curvas_nivel.append({
                            'nivel': float(nivel),
                            'geometry': line,
                            'longitud': line.length,
                            'color': self._obtener_color_nivel(nivel, min_elev, max_elev)
                        })
            
            # Estadísticas
            estadisticas = {
                'min_elevacion': float(min_elev),
                'max_elevacion': float(max_elev),
                'rango_elevacion': float(max_elev - min_elev),
                'niveles_calculados': len(niveles),
                'intervalo': intervalo,
                'numero_curvas': len(curvas_nivel),
                'longitud_total_curvas': sum(c['longitud'] for c in curvas_nivel)
            }
            
            return {
                'curvas': curvas_nivel,
                'niveles': niveles.tolist(),
                'estadisticas': estadisticas,
                'dem_data': dem_data
            }
            
        except Exception as e:
            st.error(f"Error calculando curvas de nivel: {str(e)}")
            return None
    
    def _obtener_color_nivel(self, nivel, min_elev, max_elev):
        """Obtener color para una curva de nivel basado en la elevación"""
        # Normalizar elevación
        if max_elev == min_elev:
            norm = 0.5
        else:
            norm = (nivel - min_elev) / (max_elev - min_elev)
        
        # Escala de colores topográfica
        if norm < 0.2:
            return '#006400'  # Verde oscuro (bajas elevaciones)
        elif norm < 0.4:
            return '#32CD32'  # Verde (media-baja)
        elif norm < 0.6:
            return '#FFD700'  # Amarillo (media)
        elif norm < 0.8:
            return '#FF8C00'  # Naranja (media-alta)
        else:
            return '#8B4513'  # Marrón (altas elevaciones)
    
    def crear_mapa_curvas_nivel(self, gdf_poligono, curvas_nivel_data, zoom_config=None):
        """Crear mapa interactivo con curvas de nivel"""
        try:
            # Obtener centro del polígono
            centroide = gdf_poligono.geometry.iloc[0].centroid
            
            # Configurar mapa base
            if zoom_config:
                m = folium.Map(
                    location=zoom_config['center'],
                    zoom_start=zoom_config['zoom'],
                    tiles=None,
                    control_scale=True
                )
            else:
                m = folium.Map(
                    location=[centroide.y, centroide.x],
                    zoom_start=12,
                    tiles=None,
                    control_scale=True
                )
            
            # Capa base ESRI Satellite
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satélite',
                overlay=False
            ).add_to(m)
            
            # Capa OpenStreetMap
            folium.TileLayer(
                tiles='OpenStreetMap',
                name='OpenStreetMap'
            ).add_to(m)
            
            # Capa de relieve
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Topográfico',
                overlay=True
            ).add_to(m)
            
            # Agregar polígono principal
            poligono_geojson = gdf_poligono.__geo_interface__
            folium.GeoJson(
                poligono_geojson,
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': '#FFD700',
                    'weight': 3,
                    'fillOpacity': 0.0,
                    'dashArray': '5, 5'
                },
                name='Área de estudio',
                tooltip='Polígono de análisis'
            ).add_to(m)
            
            # Agregar curvas de nivel
            if curvas_nivel_data and 'curvas' in curvas_nivel_data:
                curvas = curvas_nivel_data['curvas']
                estadisticas = curvas_nivel_data['estadisticas']
                
                # Agrupar curvas por nivel para mejor rendimiento
                niveles_unicos = sorted(set(c['nivel'] for c in curvas))
                
                for nivel in niveles_unicos:
                    # Filtrar curvas de este nivel
                    curvas_nivel = [c for c in curvas if c['nivel'] == nivel]
                    
                    # Crear MultiLineString para este nivel
                    line_strings = [c['geometry'] for c in curvas_nivel]
                    if line_strings:
                        multi_line = MultiLineString(line_strings)
                        
                        # Obtener color para este nivel
                        color = curvas_nivel[0]['color']
                        
                        # Crear capa GeoJSON
                        geojson_data = gpd.GeoSeries([multi_line]).__geo_interface__
                        
                        folium.GeoJson(
                            geojson_data,
                            style_function=lambda x, color=color: {
                                'color': color,
                                'weight': 1.5,
                                'opacity': 0.7,
                                'fillOpacity': 0.0
                            },
                            name=f'Curvas {nivel}m',
                            tooltip=f'Curva de nivel: {nivel} m',
                            popup=folium.Popup(f'Elevación: {nivel} m')
                        ).add_to(m)
            
            # Agregar controles de medición
            MeasureControl(
                position='topleft',
                primary_length_unit='meters',
                secondary_length_unit='kilometers',
                primary_area_unit='sqmeters',
                secondary_area_unit='hectares'
            ).add_to(m)
            
            # Control de capas
            folium.LayerControl().add_to(m)
            
            # Controles adicionales
            Fullscreen().add_to(m)
            MousePosition().add_to(m)
            
            # Leyenda de elevación
            if curvas_nivel_data and 'estadisticas' in curvas_nivel_data:
                stats = curvas_nivel_data['estadisticas']
                legend_html = f'''
                <div style="position: fixed; bottom: 50px; left: 50px; width: 300px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px; border-radius: 8px; 
                            box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                <h4 style="margin:0 0 10px 0; color: #2E8B57;">🏔️ Curvas de Nivel</h4>
                <p style="margin:5px 0; font-size:12px; color: #666;">Intervalo: {stats.get('intervalo', 0)}m</p>
                <p style="margin:5px 0;"><i style="background:#006400; width: 20px; height: 20px; display: inline-block; border-radius: 4px; margin-right: 8px;"></i> Baja elevación</p>
                <p style="margin:5px 0;"><i style="background:#32CD32; width: 20px; height: 20px; display: inline-block; border-radius: 4px; margin-right: 8px;"></i> Media baja</p>
                <p style="margin:5px 0;"><i style="background:#FFD700; width: 20px; height: 20px; display: inline-block; border-radius: 4px; margin-right: 8px;"></i> Media</p>
                <p style="margin:5px 0;"><i style="background:#FF8C00; width: 20px; height: 20px; display: inline-block; border-radius: 4px; margin-right: 8px;"></i> Media alta</p>
                <p style="margin:5px 0;"><i style="background:#8B4513; width: 20px; height: 20px; display: inline-block; border-radius: 4px; margin-right: 8px;"></i> Alta elevación</p>
                <hr style="margin: 10px 0;">
                <p style="margin:5px 0; font-size:12px;"><b>Min:</b> {stats.get('min_elevacion', 0):.1f} m</p>
                <p style="margin:5px 0; font-size:12px;"><b>Max:</b> {stats.get('max_elevacion', 0):.1f} m</p>
                <p style="margin:5px 0; font-size:12px;"><b>Rango:</b> {stats.get('rango_elevacion', 0):.1f} m</p>
                <p style="margin:5px 0; font-size:12px;"><b>Curvas:</b> {stats.get('numero_curvas', 0)}</p>
                </div>
                '''
                m.get_root().html.add_child(folium.Element(legend_html))
            
            return m
            
        except Exception as e:
            st.error(f"Error creando mapa de curvas de nivel: {str(e)}")
            return None
    
    def crear_visualizacion_3d_terreno(self, dem_data, curvas_nivel_data=None):
        """Crear visualización 3D del terreno"""
        try:
            elevacion = dem_data['elevacion']
            x = dem_data['x_coords']
            y = dem_data['y_coords']
            
            # Crear meshgrid para 3D
            X, Y = np.meshgrid(x, y)
            
            # Crear figura 3D
            fig = go.Figure()
            
            # Superficie 3D con colores por elevación
            fig.add_trace(go.Surface(
                x=X,
                y=Y,
                z=elevacion,
                colorscale=self.escalas_colores['terrain'],
                showscale=True,
                colorbar=dict(
                    title="Elevación (m)",
                    titleside="right",
                    titlefont=dict(color="white"),
                    tickfont=dict(color="white")
                ),
                name="Terreno",
                opacity=0.9,
                contours={
                    "z": {
                        "show": True,
                        "usecolormap": True,
                        "highlightcolor": "limegreen",
                        "project": {"z": True}
                    }
                }
            ))
            
            # Agregar curvas de nivel si están disponibles
            if curvas_nivel_data and 'curvas' in curvas_nivel_data:
                curvas = curvas_nivel_data['curvas']
                for curva in curvas[:50]:  # Limitar para rendimiento
                    geometry = curva['geometry']
                    coords = list(geometry.coords)
                    if coords:
                        x_vals = [coord[0] for coord in coords]
                        y_vals = [coord[1] for coord in coords]
                        
                        # Interpolar elevación para las curvas
                        z_vals = [curva['nivel']] * len(x_vals)
                        
                        fig.add_trace(go.Scatter3d(
                            x=x_vals,
                            y=y_vals,
                            z=z_vals,
                            mode='lines',
                            line=dict(
                                color=curva['color'],
                                width=3
                            ),
                            name=f'Curva {curva["nivel"]}m',
                            showlegend=False
                        ))
            
            # Configurar layout
            fig.update_layout(
                title={
                    'text': '🏔️ Visualización 3D del Terreno',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 24, 'color': 'white'}
                },
                scene=dict(
                    xaxis=dict(
                        title='Longitud',
                        backgroundcolor='rgba(0, 0, 0, 0.8)',
                        gridcolor='rgba(100, 100, 100, 0.5)',
                        showbackground=True,
                        zerolinecolor='rgba(100, 100, 100, 0.5)'
                    ),
                    yaxis=dict(
                        title='Latitud',
                        backgroundcolor='rgba(0, 0, 0, 0.8)',
                        gridcolor='rgba(100, 100, 100, 0.5)',
                        showbackground=True,
                        zerolinecolor='rgba(100, 100, 100, 0.5)'
                    ),
                    zaxis=dict(
                        title='Elevación (m)',
                        backgroundcolor='rgba(0, 0, 0, 0.8)',
                        gridcolor='rgba(100, 100, 100, 0.5)',
                        showbackground=True,
                        zerolinecolor='rgba(100, 100, 100, 0.5)'
                    ),
                    aspectmode='manual',
                    aspectratio=dict(x=2, y=2, z=0.5),
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1)
                    ),
                    bgcolor='rgba(10, 20, 30, 1)'
                ),
                showlegend=True,
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                height=700,
                margin=dict(l=0, r=0, t=80, b=0)
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error creando visualización 3D: {str(e)}")
            return None
    
    def crear_perfil_longitudinal(self, dem_data, punto_inicio, punto_fin, num_puntos=100):
        """Crear perfil longitudinal entre dos puntos"""
        try:
            # Extraer datos
            elevacion = dem_data['elevacion']
            x = dem_data['x_coords']
            y = dem_data['y_coords']
            
            # Crear función de interpolación
            from scipy.interpolate import RegularGridInterpolator
            interp_func = RegularGridInterpolator((y, x), elevacion, method='linear')
            
            # Generar puntos a lo largo de la línea
            lon_vals = np.linspace(punto_inicio[0], punto_fin[0], num_puntos)
            lat_vals = np.linspace(punto_inicio[1], punto_fin[1], num_puntos)
            
            # Calcular distancias
            distances = np.zeros(num_puntos)
            for i in range(1, num_puntos):
                # Distancia en grados (aproximación)
                dx = lon_vals[i] - lon_vals[i-1]
                dy = lat_vals[i] - lat_vals[i-1]
                # Convertir a metros (aproximado)
                lat_mean = (lat_vals[i] + lat_vals[i-1]) / 2
                meters_per_degree_lon = 111320 * abs(math.cos(math.radians(lat_mean)))
                meters_per_degree_lat = 111320
                
                dist_m = math.sqrt((dx * meters_per_degree_lon)**2 + (dy * meters_per_degree_lat)**2)
                distances[i] = distances[i-1] + dist_m
            
            # Interpolar elevaciones
            elev_vals = []
            for lon, lat in zip(lon_vals, lat_vals):
                elev = interp_func([[lat, lon]])
                elev_vals.append(float(elev[0]))
            
            # Calcular pendientes
            slopes = []
            for i in range(1, len(elev_vals)):
                if distances[i] != distances[i-1]:
                    slope = (elev_vals[i] - elev_vals[i-1]) / (distances[i] - distances[i-1]) * 100
                else:
                    slope = 0
                slopes.append(slope)
            slopes.append(slopes[-1] if slopes else 0)
            
            # Crear figura
            fig = go.Figure()
            
            # Perfil de elevación
            fig.add_trace(go.Scatter(
                x=distances,
                y=elev_vals,
                mode='lines',
                name='Elevación',
                line=dict(color='green', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 100, 0, 0.2)'
            ))
            
            # Línea de pendiente promedio
            slope_mean = np.mean(slopes) if slopes else 0
            fig.add_trace(go.Scatter(
                x=[distances[0], distances[-1]],
                y=[elev_vals[0], elev_vals[0] + slope_mean/100 * distances[-1]],
                mode='lines',
                name=f'Pendiente media: {slope_mean:.1f}%',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title='📏 Perfil Longitudinal del Terreno',
                xaxis_title='Distancia (m)',
                yaxis_title='Elevación (m)',
                hovermode='x unified',
                showlegend=True,
                height=400
            )
            
            # Estadísticas
            estadisticas = {
                'distancia_total': float(distances[-1]),
                'elevacion_inicio': float(elev_vals[0]),
                'elevacion_fin': float(elev_vals[-1]),
                'desnivel_total': float(elev_vals[-1] - elev_vals[0]),
                'pendiente_promedio': float(slope_mean),
                'pendiente_maxima': float(max(slopes)) if slopes else 0,
                'pendiente_minima': float(min(slopes)) if slopes else 0
            }
            
            return fig, estadisticas
            
        except Exception as e:
            st.error(f"Error creando perfil longitudinal: {str(e)}")
            return None, {}
    
    def analizar_caracteristicas_terreno(self, dem_data):
        """Analizar características del terreno"""
        try:
            elevacion = dem_data['elevacion']
            
            # Estadísticas básicas
            estadisticas = {
                'min': float(np.min(elevacion)),
                'max': float(np.max(elevacion)),
                'mean': float(np.mean(elevacion)),
                'std': float(np.std(elevacion)),
                'median': float(np.median(elevacion))
            }
            
            # Calcular pendientes (simplificado)
            grad_y, grad_x = np.gradient(elevacion)
            slope = np.sqrt(grad_x**2 + grad_y**2)
            
            # Clasificación del terreno
            slope_deg = np.degrees(np.arctan(slope))
            
            # Porcentajes por clase de pendiente
            plano = np.sum(slope_deg < 5) / slope_deg.size * 100
            suave = np.sum((slope_deg >= 5) & (slope_deg < 15)) / slope_deg.size * 100
            moderado = np.sum((slope_deg >= 15) & (slope_deg < 30)) / slope_deg.size * 100
            pronunciado = np.sum(slope_deg >= 30) / slope_deg.size * 100
            
            estadisticas.update({
                'porcentaje_plano': float(plano),
                'porcentaje_suave': float(suave),
                'porcentaje_moderado': float(moderado),
                'porcentaje_pronunciado': float(pronunciado),
                'rugosidad': float(np.std(slope))
            })
            
            return estadisticas
            
        except Exception as e:
            st.error(f"Error analizando características del terreno: {str(e)}")
            return {}

# ===============================
# 🛰️ CLASE PARA ANÁLISIS DE IMÁGENES PLANETSCOPE
# ===============================

class AnalizadorPlanetScope:
    """Clase para analizar imágenes PlanetScope"""
    
    def __init__(self):
        # Bandas de PlanetScope
        self.bandas_planetscope = {
            'blue': {'center': 490, 'range': (455, 525)},
            'green': {'center': 540, 'range': (500, 590)},
            'red': {'center': 670, 'range': (590, 670)},
            'nir': {'center': 860, 'range': (780, 860)}
        }
        
        # Fechas de adquisición simuladas
        self.fechas_adquisicion = [
            (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d')
        ]
        
        # Parámetros de calidad
        self.parametros_calidad = {
            'cloud_cover': [0.1, 0.3, 0.5, 0.8],
            'sun_azimuth': [45, 90, 135, 180],
            'sun_elevation': [30, 45, 60, 75],
            'resolution': 3.0,
            'bit_depth': 16
        }
    
    def simular_imagen_planetscope(self, bounds, size=(256, 256), fecha_idx=0):
        """Simular una imagen PlanetScope basada en los bounds del área"""
        try:
            minx, miny, maxx, maxy = bounds
            
            # Crear arrays para cada banda
            img_shape = (4, size[0], size[1])
            np.random.seed(int(minx * 1000 + miny))
            
            # Base para simulación de vegetación
            x = np.linspace(0, 2*np.pi, size[0])
            y = np.linspace(0, 2*np.pi, size[1])
            X, Y = np.meshgrid(x, y)
            vegetation_pattern = 0.5 + 0.3 * np.sin(X) * np.cos(Y)
            vegetation_pattern += 0.2 * np.sin(2*X) * np.cos(2*Y)
            
            # Crear bandas
            band_data = {}
            
            # Banda azul
            blue = np.clip(0.4 + 0.3 * np.random.normal(0, 0.1, (size[0], size[1])) - 0.3 * vegetation_pattern, 0.1, 1.0)
            band_data['blue'] = (blue * 4000).astype(np.uint16)
            
            # Banda verde
            green = np.clip(0.5 + 0.4 * vegetation_pattern + 0.2 * np.random.normal(0, 0.1, (size[0], size[1])), 0.1, 1.0)
            band_data['green'] = (green * 4000).astype(np.uint16)
            
            # Banda roja
            red = np.clip(0.4 + 0.3 * np.random.normal(0, 0.1, (size[0], size[1])) - 0.2 * vegetation_pattern, 0.1, 1.0)
            band_data['red'] = (red * 4000).astype(np.uint16)
            
            # Banda NIR
            nir = np.clip(0.6 + 0.5 * vegetation_pattern + 0.3 * np.random.normal(0, 0.1, (size[0], size[1])), 0.1, 1.0)
            band_data['nir'] = (nir * 4000).astype(np.uint16)
            
            # Metadata
            metadata = {
                'bounds': bounds,
                'size': size,
                'fecha_adquisicion': self.fechas_adquisicion[fecha_idx],
                'cloud_cover': np.random.choice(self.parametros_calidad['cloud_cover']),
                'sun_azimuth': np.random.choice(self.parametros_calidad['sun_azimuth']),
                'sun_elevation': np.random.choice(self.parametros_calidad['sun_elevation']),
                'resolution': self.parametros_calidad['resolution'],
                'crs': 'EPSG:4326'
            }
            
            return {
                'bandas': band_data,
                'metadata': metadata,
                'transform': rasterio.transform.from_bounds(minx, miny, maxx, maxy, size[1], size[0])
            }
            
        except Exception as e:
            st.error(f"Error simulando imagen PlanetScope: {str(e)}")
            return None

# ===============================
# 🧩 CLASE PRINCIPAL DE ANÁLISIS CON ALTIMETRÍA
# ===============================

class AnalizadorBiodiversidad:
    """Analizador integral de biodiversidad con altimetría"""
    
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
        
        self.analizador_planetscope = AnalizadorPlanetScope()
        self.analizador_altimetria = AnalizadorAltimetria()
        
        # Historial de análisis
        self.historial_analisis = {}
    
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
        """Cálculo aproximado mejorado cuando falla la proyección"""
        try:
            bounds = poligono.bounds
            minx, miny, maxx, maxy = bounds
            lat_media = (miny + maxy) / 2
            metros_por_grado_lat = 111320
            metros_por_grado_lon = 111320 * math.cos(math.radians(lat_media))
            ancho_m = (maxx - minx) * metros_por_grado_lon
            alto_m = (maxy - miny) * metros_por_grado_lat
            area_bbox_m2 = ancho_m * alto_m
            bbox_area_grados = (maxx - minx) * (maxy - miny)
            if bbox_area_grados > 0:
                relacion_aproximada = 0.75
                area_m2_ajustada = area_bbox_m2 * relacion_aproximada
            else:
                area_m2_ajustada = area_bbox_m2
            area_hectareas = area_m2_ajustada / 10000
            return round(max(area_hectareas, 0.01), 2)
        except Exception as e:
            st.error(f"Error en cálculo aproximado: {str(e)}")
            return 1000
    
    def procesar_poligono(self, gdf, vegetation_type, divisiones=5, usar_planetscope=True):
        """Procesar el polígono cargado con análisis de altimetría"""
        if gdf is None or gdf.empty:
            return None
        
        try:
            poligono = gdf.geometry.iloc[0]
            area_hectareas = self._calcular_area_hectareas(poligono)
            st.info(f"**Área calculada:** {area_hectareas:,.2f} hectáreas")
            
            # Generar áreas regulares
            areas_data = self._generar_areas_regulares(poligono, divisiones)
            
            # Análisis PlanetScope si está habilitado
            analisis_planetscope = None
            if usar_planetscope:
                analisis_planetscope = self._analisis_planetscope(poligono, areas_data)
            
            # Análisis de altimetría
            analisis_altimetria = self._analisis_altimetria(poligono)
            
            # Realizar análisis integral
            resultados = self._analisis_integral(areas_data, vegetation_type, area_hectareas, analisis_planetscope, analisis_altimetria)
            
            # Integrar resultados
            if analisis_planetscope:
                resultados['planetscope'] = analisis_planetscope
            
            if analisis_altimetria:
                resultados['altimetria'] = analisis_altimetria
            
            # Almacenar en historial
            analisis_id = f"analisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.historial_analisis[analisis_id] = {
                'fecha': datetime.now().isoformat(),
                'area_hectareas': area_hectareas,
                'tipo_vegetacion': vegetation_type,
                'divisiones': divisiones,
                'usar_planetscope': usar_planetscope
            }
            
            return {
                'poligono': poligono,
                'area_hectareas': area_hectareas,
                'areas_analisis': areas_data,
                'resultados': resultados,
                'centroide': poligono.centroid,
                'tipo_vegetacion': vegetation_type,
                'analisis_id': analisis_id
            }
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None
    
    def _analisis_altimetria(self, poligono):
        """Realizar análisis de altimetría"""
        try:
            st.info("🏔️ Analizando altimetría del área...")
            
            # Obtener bounds del polígono
            bounds = poligono.bounds
            
            # Determinar tipo de terreno basado en área
            area_hectareas = self._calcular_area_hectareas(poligono)
            
            # Determinar tipo de terreno según área
            if area_hectareas > 10000:
                tipo_terreno = 'montañoso'
            elif area_hectareas > 1000:
                tipo_terreno = 'colinoso'
            elif area_hectareas > 100:
                tipo_terreno = 'ondulado'
            else:
                tipo_terreno = 'plano'
            
            # Generar DEM simulado
            dem_data = self.analizador_altimetria.generar_dem_simulado(
                bounds, 
                tipo_terreno=tipo_terreno,
                resolucion=100  # 100m de resolución
            )
            
            if not dem_data:
                return None
            
            # Calcular curvas de nivel
            curvas_nivel = self.analizador_altimetria.calcular_curvas_nivel(
                dem_data, 
                intervalo=25  # Curvas cada 25 metros
            )
            
            # Analizar características del terreno
            caracteristicas = self.analizador_altimetria.analizar_caracteristicas_terreno(dem_data)
            
            return {
                'dem': dem_data,
                'curvas_nivel': curvas_nivel,
                'caracteristicas_terreno': caracteristicas,
                'tipo_terreno': tipo_terreno,
                'bounds': bounds
            }
            
        except Exception as e:
            st.error(f"Error en análisis de altimetría: {str(e)}")
            return None
    
    def _analisis_planetscope(self, poligono, areas_data):
        """Realizar análisis con imágenes PlanetScope"""
        try:
            st.info("🛰️ Iniciando análisis con PlanetScope...")
            bounds = poligono.bounds
            
            # Simular imagen PlanetScope
            imagen = self.analizador_planetscope.simular_imagen_planetscope(bounds)
            
            if not imagen:
                st.warning("No se pudo generar imagen PlanetScope")
                return None
            
            return {
                'imagen': imagen,
                'metadata': imagen['metadata'],
                'bounds': bounds
            }
            
        except Exception as e:
            st.error(f"Error en análisis PlanetScope: {str(e)}")
            return None
    
    def _generar_areas_regulares(self, poligono, divisiones):
        """Generar áreas regulares (grid) dentro del polígono"""
        areas = []
        bounds = poligono.bounds
        minx, miny, maxx, maxy = bounds
        delta_x = (maxx - minx) / divisiones
        delta_y = (maxy - miny) / divisiones
        
        for i in range(divisiones):
            for j in range(divisiones):
                cell_minx = minx + i * delta_x
                cell_maxx = minx + (i + 1) * delta_x
                cell_miny = miny + j * delta_y
                cell_maxy = miny + (j + 1) * delta_y
                
                cell_polygon = Polygon([
                    (cell_minx, cell_miny),
                    (cell_maxx, cell_miny),
                    (cell_maxx, cell_maxy),
                    (cell_minx, cell_maxy),
                    (cell_minx, cell_miny)
                ])
                
                if poligono.intersects(cell_polygon):
                    intersection = poligono.intersection(cell_polygon)
                    if not intersection.is_empty:
                        centroid = intersection.centroid
                        areas.append({
                            'id': f"Area_{i+1}_{j+1}",
                            'geometry': intersection,
                            'centroid': centroid,
                            'area_ha': self._calcular_area_hectareas(intersection),
                            'bounds': intersection.bounds
                        })
        return areas
    
    def _analisis_integral(self, areas_data, vegetation_type, area_total, analisis_planetscope=None, analisis_altimetria=None):
        """Realizar análisis integral con todos los indicadores"""
        params = self.parametros_ecosistemas.get(vegetation_type, self.parametros_ecosistemas['Bosque Secundario'])
        
        carbono_data = []
        vegetacion_data = []
        biodiversidad_data = []
        agua_data = []
        suelo_data = []
        clima_data = []
        presiones_data = []
        conectividad_data = []
        
        for area in areas_data:
            centroid = area['centroid']
            
            carbono_info = self._analizar_carbono(area, params, area['area_ha'])
            carbono_data.append(carbono_info)
            
            vegetacion_info = self._analizar_vegetacion(area, params)
            vegetacion_data.append(vegetacion_info)
            
            biodiversidad_info = self._analizar_biodiversidad(area, params, area['area_ha'])
            biodiversidad_data.append(biodiversidad_info)
            
            agua_info = self._analizar_recursos_hidricos(area)
            agua_data.append(agua_info)
            
            suelo_info = self._analizar_suelo(area)
            suelo_data.append(suelo_info)
            
            clima_info = self._analizar_clima(area)
            clima_data.append(clima_info)
            
            presiones_info = self._analizar_presiones(area)
            presiones_data.append(presiones_info)
            
            conectividad_info = self._analizar_conectividad(area)
            conectividad_data.append(conectividad_info)
        
        summary_metrics = self._calcular_metricas_resumen(
            carbono_data, vegetacion_data, biodiversidad_data, agua_data,
            suelo_data, clima_data, presiones_data, conectividad_data
        )
        
        # Integrar datos de altimetría
        if analisis_altimetria and 'caracteristicas_terreno' in analisis_altimetria:
            terreno_stats = analisis_altimetria['caracteristicas_terreno']
            summary_metrics.update({
                'altura_minima': terreno_stats.get('min', 0),
                'altura_maxima': terreno_stats.get('max', 0),
                'altura_promedio': terreno_stats.get('mean', 0),
                'pendiente_promedio': terreno_stats.get('porcentaje_moderado', 0),
                'tipo_terreno': analisis_altimetria.get('tipo_terreno', 'desconocido')
            })
        
        return {
            'carbono': carbono_data,
            'vegetacion': vegetacion_data,
            'biodiversidad': biodiversidad_data,
            'agua': agua_data,
            'suelo': suelo_data,
            'clima': clima_data,
            'presiones': presiones_data,
            'conectividad': conectividad_data,
            'summary_metrics': summary_metrics
        }
    
    def _analizar_carbono(self, area, params, area_ha):
        """Analizar indicadores de carbono"""
        base_carbon = np.random.uniform(params['carbono']['min'], params['carbono']['max'])
        ndvi = max(0.1, min(0.9, np.random.normal(params['ndvi_base'], 0.08)))
        carbono_ajustado = base_carbon * (0.3 + ndvi * 0.7)
        co2_potencial = carbono_ajustado * 3.67
        
        return {
            'area': area['id'],
            'carbono_almacenado_tha': round(carbono_ajustado, 1),
            'co2_capturado_tha': round(co2_potencial, 1),
            'co2_total_ton': round(co2_potencial * area_ha, 1),
            'potencial_secuestro': 'Alto' if carbono_ajustado > 100 else 'Medio' if carbono_ajustado > 50 else 'Bajo',
            'ndvi': ndvi,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_vegetacion(self, area, params):
        """Analizar estado de la vegetación"""
        ndvi = max(0.1, min(0.9, np.random.normal(params['ndvi_base'], 0.08)))
        evi = ndvi * 0.9 + np.random.normal(0, 0.03)
        
        if ndvi > 0.7:
            salud = "Excelente"
            color = '#006400'
        elif ndvi > 0.5:
            salud = "Buena"
            color = '#32CD32'
        elif ndvi > 0.3:
            salud = "Moderada"
            color = '#FFD700'
        else:
            salud = "Degradada"
            color = '#FF4500'
        
        return {
            'area': area['id'],
            'ndvi': ndvi,
            'evi': evi,
            'salud_vegetacion': salud,
            'color_salud': color,
            'biomasa_tha': round(ndvi * 200 + np.random.uniform(0, 50), 1),
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_biodiversidad(self, area, params, area_ha):
        """Analizar indicadores de biodiversidad"""
        factor_area = min(1.0, math.log(area_ha + 1) / 6)
        factor_conectividad = np.random.uniform(0.6, 0.9)
        factor_perturbacion = np.random.uniform(0.7, 0.95)
        
        if params['biodiversidad'] > 0.7:
            riqueza_base = 150
        elif params['biodiversidad'] > 0.5:
            riqueza_base = 80
        elif params['biodiversidad'] > 0.3:
            riqueza_base = 40
        else:
            riqueza_base = 20
        
        riqueza_especies = int(riqueza_base * factor_area * factor_conectividad * factor_perturbacion)
        
        if params['biodiversidad'] > 0.7:
            shannon_base = 3.0
        elif params['biodiversidad'] > 0.5:
            shannon_base = 2.2
        elif params['biodiversidad'] > 0.3:
            shannon_base = 1.5
        else:
            shannon_base = 0.8
        
        shannon_index = shannon_base * factor_conectividad * factor_perturbacion
        
        if shannon_index > 2.5:
            estado = "Muy Alto"
            color = '#006400'
        elif shannon_index > 2.0:
            estado = "Alto"
            color = '#32CD32'
        elif shannon_index > 1.5:
            estado = "Moderado"
            color = '#FFD700'
        elif shannon_index > 1.0:
            estado = "Bajo"
            color = '#FFA500'
        else:
            estado = "Muy Bajo"
            color = '#FF4500'
        
        return {
            'area': area['id'],
            'riqueza_especies': riqueza_especies,
            'indice_shannon': round(shannon_index, 2),
            'estado_conservacion': estado,
            'color_estado': color,
            'factor_area': round(factor_area, 2),
            'factor_conectividad': round(factor_conectividad, 2),
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_recursos_hidricos(self, area):
        """Analizar indicadores hídricos"""
        disponibilidad_agua = np.random.uniform(0.2, 0.9)
        
        if disponibilidad_agua > 0.7:
            estado_agua = "Alta"
            color_agua = '#1E90FF'
        elif disponibilidad_agua > 0.5:
            estado_agua = "Moderada"
            color_agua = '#87CEEB'
        elif disponibilidad_agua > 0.3:
            estado_agua = "Baja"
            color_agua = '#FFA500'
        else:
            estado_agua = "Crítica"
            color_agua = '#FF4500'
        
        return {
            'area': area['id'],
            'disponibilidad_agua': round(disponibilidad_agua, 2),
            'estado_hidrico': estado_agua,
            'color_estado_agua': color_agua,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_suelo(self, area):
        """Analizar calidad del suelo"""
        materia_organica = np.random.uniform(1.0, 8.0)
        salud_suelo = materia_organica / 8.0 * 0.6 + np.random.uniform(0, 0.4)
        
        if salud_suelo > 0.7:
            estado_suelo = "Excelente"
            color_suelo = '#8B4513'
        elif salud_suelo > 0.5:
            estado_suelo = "Buena"
            color_suelo = '#A0522D'
        elif salud_suelo > 0.3:
            estado_suelo = "Moderada"
            color_suelo = '#CD853F'
        else:
            estado_suelo = "Degradado"
            color_suelo = '#D2691E'
        
        return {
            'area': area['id'],
            'salud_suelo': round(salud_suelo, 2),
            'estado_suelo': estado_suelo,
            'color_estado_suelo': color_suelo,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_presiones(self, area):
        """Analizar presiones antrópicas"""
        presion_total = np.random.uniform(0, 1)
        
        if presion_total < 0.3:
            nivel_presion = "Bajo"
            color_presion = '#32CD32'
        elif presion_total < 0.6:
            nivel_presion = "Moderado"
            color_presion = '#FFD700'
        else:
            nivel_presion = "Alto"
            color_presion = '#FF4500'
        
        return {
            'area': area['id'],
            'presion_total': round(presion_total, 2),
            'nivel_presion': nivel_presion,
            'color_presion': color_presion,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_conectividad(self, area):
        """Analizar conectividad ecológica"""
        conectividad = np.random.uniform(0.2, 0.9)
        
        if conectividad > 0.7:
            estado_conectividad = "Alta"
            color_conectividad = '#006400'
        elif conectividad > 0.5:
            estado_conectividad = "Moderada"
            color_conectividad = '#32CD32'
        elif conectividad > 0.3:
            estado_conectividad = "Baja"
            color_conectividad = '#FFD700'
        else:
            estado_conectividad = "Crítica"
            color_conectividad = '#FF4500'
        
        return {
            'area': area['id'],
            'conectividad_total': round(conectividad, 2),
            'estado_conectividad': estado_conectividad,
            'color_conectividad': color_conectividad,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _analizar_clima(self, area):
        """Analizar indicadores climáticos"""
        temperatura = np.random.uniform(15, 35)
        vulnerabilidad = (temperatura - 15) / 20
        
        if vulnerabilidad < 0.3:
            riesgo_climatico = "Bajo"
            color_clima = '#32CD32'
        elif vulnerabilidad < 0.6:
            riesgo_climatico = "Moderado"
            color_clima = '#FFD700'
        else:
            riesgo_climatico = "Alto"
            color_clima = '#FF4500'
        
        return {
            'area': area['id'],
            'vulnerabilidad_climatica': round(vulnerabilidad, 2),
            'riesgo_climatico': riesgo_climatico,
            'color_riesgo_clima': color_clima,
            'geometry': area['geometry'],
            'centroid': area['centroid']
        }
    
    def _calcular_metricas_resumen(self, carbono, vegetacion, biodiversidad, agua, suelo, clima, presiones, conectividad):
        """Calcular métricas resumen para el dashboard"""
        avg_carbono = np.mean([p['co2_total_ton'] for p in carbono]) if carbono else 0
        avg_biodiversidad = np.mean([p['indice_shannon'] for p in biodiversidad]) if biodiversidad else 0
        avg_agua = np.mean([p['disponibilidad_agua'] for p in agua]) if agua else 0
        avg_suelo = np.mean([p['salud_suelo'] for p in suelo]) if suelo else 0
        avg_presiones = np.mean([p['presion_total'] for p in presiones]) if presiones else 0
        avg_conectividad = np.mean([p['conectividad_total'] for p in conectividad]) if conectividad else 0
        avg_ndvi = np.mean([v['ndvi'] for v in vegetacion]) if vegetacion else 0
        
        return {
            'carbono_total_co2_ton': round(avg_carbono * len(carbono), 1),
            'indice_biodiversidad_promedio': round(avg_biodiversidad, 2),
            'disponibilidad_agua_promedio': round(avg_agua, 2),
            'salud_suelo_promedio': round(avg_suelo, 2),
            'presion_antropica_promedio': round(avg_presiones, 2),
            'conectividad_promedio': round(avg_conectividad, 2),
            'ndvi_promedio': round(avg_ndvi, 2),
            'areas_analizadas': len(carbono),
            'estado_general': self._calcular_estado_general(avg_biodiversidad, avg_presiones, avg_conectividad)
        }
    
    def _calcular_estado_general(self, biodiversidad, presiones, conectividad):
        score = (biodiversidad / 3.0 * 0.4 + (1 - presiones) * 0.4 + conectividad * 0.2)
        if score > 0.7: return "Excelente"
        elif score > 0.5: return "Bueno"
        elif score > 0.3: return "Moderado"
        else: return "Crítico"

# ===============================
# 🗺️ FUNCIONES DE MAPAS MEJORADAS CON ZOOM AUTOMÁTICO
# ===============================

def calcular_bounds_optimos(gdf, datos_areas=None, padding_factor=0.1):
    """Calcular los límites óptimos para el zoom del mapa"""
    try:
        if datos_areas and len(datos_areas) > 0:
            geometrias = [area['geometry'] for area in datos_areas]
            gdf_areas = gpd.GeoDataFrame(geometry=geometrias, crs="EPSG:4326")
            bounds = gdf_areas.total_bounds
        else:
            bounds = gdf.total_bounds
        
        minx, miny, maxx, maxy = bounds
        center_lat = (miny + maxy) / 2
        center_lon = (minx + maxx) / 2
        lat_span = maxy - miny
        lon_span = maxx - minx
        lat_padding = lat_span * padding_factor
        lon_padding = lon_span * padding_factor
        
        bounds_padded = [
            minx - lon_padding,
            miny - lat_padding,
            maxx + lon_padding,
            maxy + lat_padding
        ]
        
        max_span = max(lat_span, lon_span)
        
        if max_span < 0.01:
            zoom = 15
        elif max_span < 0.05:
            zoom = 13
        elif max_span < 0.1:
            zoom = 12
        elif max_span < 0.5:
            zoom = 10
        elif max_span < 1.0:
            zoom = 9
        else:
            zoom = 8
        
        return {
            'center': [center_lat, center_lon],
            'bounds': bounds_padded,
            'zoom': min(max(zoom, 8), 18),
            'lat_span': lat_span,
            'lon_span': lon_span
        }
    except Exception as e:
        st.warning(f"Error calculando bounds: {str(e)}")
        return {
            'center': [-14.0, -60.0],
            'bounds': None,
            'zoom': 12,
            'lat_span': 0.1,
            'lon_span': 0.1
        }

# ===============================
# 📊 FUNCIONES DE VISUALIZACIÓN MEJORADAS
# ===============================

def crear_grafico_radar(datos_combinados, categorias):
    """Crear gráfico radar para comparación de indicadores"""
    if not datos_combinados:
        return go.Figure()
    
    fig = go.Figure()
    
    for area_data in datos_combinados[:5]:
        valores = [area_data.get(cat, 0) for cat in categorias.keys()]
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=list(categorias.values()),
            fill='toself',
            name=area_data['area']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1])
        ),
        showlegend=True,
        title="Comparación de Indicadores por Área",
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    return fig

def crear_grafico_sunburst(datos, columna_valor, columna_estado, titulo):
    """Crear gráfico sunburst para distribución jerárquica"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        if columna_estado in df.columns:
            conteo_estado = df[columna_estado].value_counts()
        else:
            df['categoria'] = pd.cut(df[columna_valor], bins=4, labels=['Bajo', 'Medio', 'Alto', 'Muy Alto'])
            conteo_estado = df['categoria'].value_counts()
        
        fig = px.sunburst(
            names=conteo_estado.index,
            parents=[''] * len(conteo_estado),
            values=conteo_estado.values,
            title=titulo
        )
        
        fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_trace(go.Pie(
            values=[1],
            labels=['Datos no disponibles'],
            title=titulo
        ))
        return fig

def crear_grafico_3d_scatter(datos_combinados, ejes_config):
    """Crear gráfico 3D scatter para relación entre indicadores"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_necesarias = [ejes_config['x'], ejes_config['y'], ejes_config['z']]
        columnas_existentes = [col for col in columnas_necesarias if col in df.columns]
        
        if len(columnas_existentes) < 3:
            st.warning(f"Faltan columnas para el gráfico 3D: {set(columnas_necesarias) - set(columnas_existentes)}")
            return go.Figure()
        
        fig = px.scatter_3d(
            df,
            x=ejes_config['x'],
            y=ejes_config['y'],
            z=ejes_config['z'],
            color=ejes_config.get('color', ejes_config['x']),
            size=ejes_config.get('size', ejes_config['x']),
            hover_name='area',
            title=ejes_config['titulo']
        )
        
        fig.update_layout(paper_bgcolor='white', scene=dict(bgcolor='white'))
        return fig
    except Exception as e:
        st.error(f"Error creando gráfico 3D: {str(e)}")
        return go.Figure()

def crear_heatmap_correlacion(datos_combinados, indicadores):
    """Crear heatmap de correlación entre indicadores"""
    if not datos_combinados:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos_combinados)
        columnas_existentes = [col for col in indicadores.keys() if col in df.columns]
        
        if len(columnas_existentes) < 2:
            st.warning("No hay suficientes indicadores para calcular correlaciones")
            return go.Figure()
        
        correlaciones = df[columnas_existentes].corr()
        
        fig = ff.create_annotated_heatmap(
            z=correlaciones.values,
            x=[indicadores[col] for col in columnas_existentes],
            y=[indicadores[col] for col in columnas_existentes],
            annotation_text=correlaciones.round(2).values,
            colorscale='Viridis'
        )
        
        fig.update_layout(
            title="Correlación entre Indicadores",
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        return fig
    except Exception as e:
        st.error(f"Error creando heatmap: {str(e)}")
        return go.Figure()

def crear_grafico_treemap(datos, columna_valor, columna_estado, titulo):
    """Crear gráfico treemap para visualización jerárquica"""
    if not datos:
        return go.Figure()
    
    try:
        df = pd.DataFrame(datos)
        if columna_estado in df.columns:
            grouped = df.groupby(columna_estado).agg({columna_valor: 'sum', 'area': 'count'}).reset_index()
            fig = px.treemap(
                grouped,
                path=[columna_estado],
                values=columna_valor,
                title=titulo,
                color=columna_valor,
                color_continuous_scale='Viridis'
            )
        else:
            fig = px.treemap(
                df,
                path=['area'],
                values=columna_valor,
                title=titulo,
                color=columna_valor,
                color_continuous_scale='Viridis'
            )
        
        fig.update_layout(paper_bgcolor='white')
        return fig
    except Exception as e:
        st.error(f"Error creando treemap: {str(e)}")
        return go.Figure()

# ===============================
# 📁 MANEJO DE ARCHIVOS Y DESCARGAS
# ===============================

def procesar_archivo_cargado(uploaded_file):
    """Procesar archivo KML/ZIP cargado"""
    try:
        if uploaded_file.name.endswith('.kml'):
            gdf = gpd.read_file(uploaded_file, driver='KML')
            return gdf
        elif uploaded_file.name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    return gdf
        return None
    except Exception as e:
        st.error(f"Error procesando archivo: {str(e)}")
        return None

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
    """Generar un GeoJSON completo con todos los indicadores"""
    try:
        todos_datos = []
        for i in range(len(resultados['resultados']['vegetacion'])):
            area_id = resultados['resultados']['vegetacion'][i]['area']
            geometry = None
            for area in resultados['areas_analisis']:
                if area['id'] == area_id:
                    geometry = area['geometry']
                    break
            
            if geometry:
                area_data = {
                    'area': area_id,
                    'geometry': geometry,
                    'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                    'salud_vegetacion': resultados['resultados']['vegetacion'][i]['salud_vegetacion'],
                    'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton'],
                    'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                    'disponibilidad_agua': resultados['resultados']['agua'][i]['disponibilidad_agua'],
                    'salud_suelo': resultados['resultados']['suelo'][i]['salud_suelo'],
                    'conectividad_total': resultados['resultados']['conectividad'][i]['conectividad_total'],
                    'presion_total': resultados['resultados']['presiones'][i]['presion_total']
                }
                todos_datos.append(area_data)
        
        gdf = gpd.GeoDataFrame(todos_datos, geometry='geometry')
        gdf.crs = "EPSG:4326"
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
    if 'zoom_config' not in st.session_state:
        st.session_state.zoom_config = None
    if 'show_elevation' not in st.session_state:
        st.session_state.show_elevation = True
    if 'usar_planetscope' not in st.session_state:
        st.session_state.usar_planetscope = True

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
        uploaded_file = st.file_uploader("Sube tu archivo territorial", type=['kml', 'zip'])
        
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False
                    st.session_state.zoom_config = None
                    st.success(f"✅ Polígono cargado: {uploaded_file.name}")
                    st.rerun()
        
        st.markdown("---")
        st.header("📊 Configuración de Análisis")
        
        vegetation_type = st.selectbox("🌿 Tipo de vegetación predominante", [
            'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
            'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
            'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
        ])
        
        divisiones = st.slider("🔲 Divisiones del área", 3, 8, 5,
                             help="Número de divisiones para crear la grilla de análisis")
        
        # Configuración para PlanetScope
        st.markdown("---")
        st.header("🛰️ PlanetScope")
        
        usar_planetscope = st.checkbox("Usar imágenes PlanetScope", value=True,
                                      help="Incluir análisis con imágenes satelitales de alta resolución")
        st.session_state.usar_planetscope = usar_planetscope
        
        if usar_planetscope:
            col1, col2 = st.columns(2)
            with col1:
                fechas_analisis = st.selectbox(
                    "Fechas de análisis",
                    ["Último mes", "Últimos 3 meses", "Últimos 6 meses"],
                    index=1
                )
            with col2:
                resolucion = st.selectbox(
                    "Resolución",
                    ["3m (PlanetScope)", "5m (RapidEye)", "10m (Sentinel-2)"],
                    index=0
                )
        
        # Configuración para altimetría
        st.markdown("---")
        st.header("🏔️ Análisis de Altimetría")
        mostrar_altimetria = st.checkbox("Mostrar análisis de altimetría", value=True,
                                        help="Visualización de curvas de nivel y modelo 3D del terreno")
        st.session_state.show_elevation = mostrar_altimetria
        
        if mostrar_altimetria:
            intervalo_curvas = st.selectbox(
                "Intervalo curvas de nivel",
                ["10m (detallado)", "25m (normal)", "50m (general)", "100m (esquemático)"],
                index=1
            )
            
            tipo_terreno = st.selectbox(
                "Tipo de terreno esperado",
                ["Plano", "Ondulado", "Colinoso", "Montañoso"],
                index=2
            )
        
        return uploaded_file, vegetation_type, divisiones

# ===============================
# 🎯 APLICACIÓN PRINCIPAL
# ===============================

def main():
    aplicar_estilos_globales()
    crear_header()
    initialize_session_state()
    
    # Sidebar
    uploaded_file, vegetation_type, divisiones = sidebar_config()
    
    # Mostrar información del polígono si está cargado
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
        
        # Información PlanetScope si está habilitado
        if st.session_state.usar_planetscope:
            st.markdown("---")
            st.subheader("🛰️ Configuración PlanetScope")
            col_ps1, col_ps2 = st.columns(2)
            with col_ps1:
                st.metric("Resolución", "3 metros")
                st.metric("Bandas", "4 (RGB + NIR)")
            with col_ps2:
                st.metric("Frecuencia", "Diaria")
                st.metric("Cloud Cover", "< 20%")
        
        # Información Altimetría si está habilitado
        if st.session_state.show_elevation:
            st.markdown("---")
            st.subheader("🏔️ Configuración Altimetría")
            col_alt1, col_alt2 = st.columns(2)
            with col_alt1:
                st.metric("Resolución DEM", "100 metros")
                st.metric("Intervalo curvas", "25 metros")
            with col_alt2:
                st.metric("Análisis 3D", "Habilitado")
                st.metric("Perfiles", "Disponible")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de análisis
    if tiene_poligono_data() and not st.session_state.analysis_complete:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            btn_text = "🚀 EJECUTAR ANÁLISIS INTEGRAL"
            if st.session_state.usar_planetscope:
                btn_text += " (con PlanetScope)"
            if st.session_state.show_elevation:
                btn_text += " + Altimetría"
            
            if st.button(btn_text, type="primary", use_container_width=True):
                with st.spinner("Realizando análisis integral de biodiversidad..."):
                    resultados = st.session_state.analyzer.procesar_poligono(
                        st.session_state.poligono_data, 
                        vegetation_type, 
                        divisiones,
                        usar_planetscope=st.session_state.usar_planetscope
                    )
                    if resultados:
                        st.session_state.results = resultados
                        st.session_state.analysis_complete = True
                        
                        # Calcular configuración de zoom
                        st.session_state.zoom_config = calcular_bounds_optimos(
                            st.session_state.poligono_data,
                            resultados['areas_analisis']
                        )
                        
                        st.success("✅ Análisis completado exitosamente!")
                        st.rerun()
        
        with col_btn2:
            if st.button("🔄 Reiniciar", type="secondary", use_container_width=True):
                st.session_state.analysis_complete = False
                st.session_state.results = None
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar resultados del análisis
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
        # SECCIÓN DE ANÁLISIS DE ALTIMETRÍA
        if st.session_state.show_elevation and 'altimetria' in resultados:
            analisis_alt = resultados['altimetria']
            
            st.markdown('<div class="elevation-container">', unsafe_allow_html=True)
            st.markdown('<div class="elevation-header">🏔️ ANÁLISIS DE ALTIMETRÍA</div>', unsafe_allow_html=True)
            
            if analisis_alt and 'dem' in analisis_alt and 'curvas_nivel' in analisis_alt:
                dem_data = analisis_alt['dem']
                curvas_data = analisis_alt['curvas_nivel']
                caracteristicas = analisis_alt.get('caracteristicas_terreno', {})
                
                # Estadísticas de elevación
                col_alt1, col_alt2, col_alt3, col_alt4 = st.columns(4)
                with col_alt1:
                    st.metric("Elevación mínima", f"{caracteristicas.get('min', 0):.1f} m")
                with col_alt2:
                    st.metric("Elevación máxima", f"{caracteristicas.get('max', 0):.1f} m")
                with col_alt3:
                    st.metric("Elevación promedio", f"{caracteristicas.get('mean', 0):.1f} m")
                with col_alt4:
                    st.metric("Desnivel total", f"{caracteristicas.get('max', 0) - caracteristicas.get('min', 0):.1f} m")
                
                # Análisis de pendientes
                col_slope1, col_slope2, col_slope3, col_slope4 = st.columns(4)
                with col_slope1:
                    st.metric("Terreno plano", f"{caracteristicas.get('porcentaje_plano', 0):.1f}%")
                with col_slope2:
                    st.metric("Pendiente suave", f"{caracteristicas.get('porcentaje_suave', 0):.1f}%")
                with col_slope3:
                    st.metric("Pendiente moderada", f"{caracteristicas.get('porcentaje_moderado', 0):.1f}%")
                with col_slope4:
                    st.metric("Pendiente pronunciada", f"{caracteristicas.get('porcentaje_pronunciado', 0):.1f}%")
                
                st.markdown("---")
                
                # Mapa con curvas de nivel
                st.subheader("🗺️ Mapa con Curvas de Nivel")
                mapa_curvas = st.session_state.analyzer.analizador_altimetria.crear_mapa_curvas_nivel(
                    st.session_state.poligono_data,
                    curvas_data,
                    st.session_state.zoom_config
                )
                
                if mapa_curvas:
                    st_folium(mapa_curvas, width=800, height=500, key="mapa_curvas_nivel")
                
                # Visualización 3D del terreno
                st.markdown("---")
                st.subheader("🌄 Visualización 3D del Terreno")
                
                col_3d1, col_3d2 = st.columns([3, 1])
                with col_3d1:
                    # Crear visualización 3D
                    fig_3d = st.session_state.analyzer.analizador_altimetria.crear_visualizacion_3d_terreno(
                        dem_data, 
                        curvas_data
                    )
                    if fig_3d:
                        st.plotly_chart(fig_3d, use_container_width=True, height=600)
                
                with col_3d2:
                    st.markdown("**🎨 Configuración 3D:**")
                    vista_camara = st.selectbox(
                        "Vista de cámara:",
                        ["Perspectiva", "Ortogonal", "Vista aérea"],
                        key="vista_camara"
                    )
                    
                    escala_colores = st.selectbox(
                        "Escala de colores:",
                        ["Topográfica", "Hipso", "Terreno", "Viridis"],
                        key="escala_colores"
                    )
                    
                    if st.button("🔄 Actualizar vista 3D", type="secondary"):
                        st.rerun()
                
                # Perfiles longitudinales
                st.markdown("---")
                st.subheader("📏 Perfiles Longitudinales")
                
                st.info("Seleccione dos puntos en el mapa para generar un perfil longitudinal")
                
                col_perfil1, col_perfil2 = st.columns(2)
                with col_perfil1:
                    # Coordenadas de inicio (por defecto)
                    inicio_lon = st.number_input("Longitud inicio", value=dem_data['x_coords'][0], format="%.6f")
                    inicio_lat = st.number_input("Latitud inicio", value=dem_data['y_coords'][0], format="%.6f")
                
                with col_perfil2:
                    # Coordenadas de fin (por defecto)
                    fin_lon = st.number_input("Longitud fin", value=dem_data['x_coords'][-1], format="%.6f")
                    fin_lat = st.number_input("Latitud fin", value=dem_data['y_coords'][-1], format="%.6f")
                
                if st.button("📊 Generar perfil", type="primary"):
                    with st.spinner("Calculando perfil..."):
                        punto_inicio = (inicio_lon, inicio_lat)
                        punto_fin = (fin_lon, fin_lat)
                        
                        fig_perfil, stats_perfil = st.session_state.analyzer.analizador_altimetria.crear_perfil_longitudinal(
                            dem_data, punto_inicio, punto_fin
                        )
                        
                        if fig_perfil:
                            st.plotly_chart(fig_perfil, use_container_width=True)
                            
                            # Mostrar estadísticas del perfil
                            col_stats1, col_stats2, col_stats3 = st.columns(3)
                            with col_stats1:
                                st.metric("Distancia total", f"{stats_perfil.get('distancia_total', 0):.1f} m")
                            with col_stats2:
                                st.metric("Desnivel total", f"{stats_perfil.get('desnivel_total', 0):.1f} m")
                            with col_stats3:
                                st.metric("Pendiente promedio", f"{stats_perfil.get('pendiente_promedio', 0):.1f}%")
            
            else:
                st.warning("No se pudieron generar datos de altimetría para esta área.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # SECCIÓN DE ANÁLISIS PLANETSCOPE (mantener igual que antes)
        if st.session_state.usar_planetscope and 'planetscope' in resultados:
            # ... (código de PlanetScope existente)
            pass
        
        # SECCIÓN DE DESCARGAS MEJORADA
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
            
            # Agregar curvas de nivel si existen
            if 'altimetria' in resultados and 'curvas_nivel' in resultados['altimetria']:
                try:
                    curvas = resultados['altimetria']['curvas_nivel']['curvas']
                    curvas_geojson = {
                        'type': 'FeatureCollection',
                        'features': []
                    }
                    
                    for curva in curvas:
                        feature = {
                            'type': 'Feature',
                            'geometry': {
                                'type': 'LineString',
                                'coordinates': list(curva['geometry'].coords)
                            },
                            'properties': {
                                'nivel': curva['nivel'],
                                'color': curva['color'],
                                'longitud': curva['longitud']
                            }
                        }
                        curvas_geojson['features'].append(feature)
                    
                    curvas_json = json.dumps(curvas_geojson, indent=2)
                    crear_boton_descarga(
                        curvas_json,
                        "curvas_nivel.geojson",
                        "Descargar Curvas de Nivel",
                        'geojson'
                    )
                except Exception as e:
                    st.warning(f"No se pudieron exportar curvas de nivel: {str(e)}")
            
            indicadores_geojson = [
                ('carbono', 'Carbono', 'co2_total_ton'),
                ('vegetacion', 'Vegetación', 'ndvi'),
                ('biodiversidad', 'Biodiversidad', 'indice_shannon'),
                ('agua', 'Recursos Hídricos', 'disponibilidad_agua')
            ]
            
            for key, nombre, columna in indicadores_geojson:
                geojson_data = generar_geojson_indicador(
                    resultados['resultados'][key], 
                    f"indicador_{key}"
                )
                if geojson_data:
                    crear_boton_descarga(
                        geojson_data,
                        f"datos_{key}.json",
                        f"Descargar {nombre} (JSON)",
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
            
            datos_resumen = {
                'Metrica': [
                    'Área Total (ha)', 'Tipo Vegetación', 'Estado General',
                    'Carbono Total (ton CO₂)', 'Índice Biodiversidad',
                    'Disponibilidad Agua', 'Salud Suelo', 'Presión Antrópica', 'Conectividad'
                ],
                'Valor': [
                    resultados['area_hectareas'],
                    resultados['tipo_vegetacion'],
                    summary['estado_general'],
                    summary['carbono_total_co2_ton'],
                    summary['indice_biodiversidad_promedio'],
                    summary['disponibilidad_agua_promedio'],
                    summary['salud_suelo_promedio'],
                    summary['presion_antropica_promedio'],
                    summary['conectividad_promedio']
                ]
            }
            
            # Agregar datos de altimetría si existen
            if 'altimetria' in resultados and 'caracteristicas_terreno' in resultados['altimetria']:
                caracteristicas = resultados['altimetria']['caracteristicas_terreno']
                datos_resumen['Metrica'].extend([
                    'Elevación Mínima (m)', 'Elevación Máxima (m)', 
                    'Elevación Promedio (m)', 'Pendiente Promedio (%)',
                    'Terreno Plano (%)', 'Terreno Pronunciado (%)'
                ])
                datos_resumen['Valor'].extend([
                    caracteristicas.get('min', 0),
                    caracteristicas.get('max', 0),
                    caracteristicas.get('mean', 0),
                    caracteristicas.get('porcentaje_moderado', 0),
                    caracteristicas.get('porcentaje_plano', 0),
                    caracteristicas.get('porcentaje_pronunciado', 0)
                ])
            
            df_resumen = pd.DataFrame(datos_resumen)
            csv_resumen = df_resumen.to_csv(index=False)
            crear_boton_descarga(
                csv_resumen,
                "resumen_ejecutivo.csv",
                "Descargar Resumen CSV",
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
                
            informe_texto = f"""
INFORME DE ANÁLISIS DE BIODIVERSIDAD
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

RESUMEN EJECUTIVO:
Área analizada: {resultados['area_hectareas']:,.2f} ha
Tipo de vegetación: {resultados['tipo_vegetacion']}
Estado general: {summary['estado_general']}

INDICADORES PRINCIPALES:
- Carbono total: {summary['carbono_total_co2_ton']:,} ton CO₂
- Biodiversidad: {summary['indice_biodiversidad_promedio']}
- Disponibilidad agua: {summary['disponibilidad_agua_promedio']}
- Salud suelo: {summary['salud_suelo_promedio']}
- Presión antrópica: {summary['presion_antropica_promedio']}
- Conectividad: {summary['conectividad_promedio']}

Áreas analizadas: {summary['areas_analizadas']}
"""
            # Agregar datos de altimetría al informe
            if 'altimetria' in resultados and 'caracteristicas_terreno' in resultados['altimetria']:
                caracteristicas = resultados['altimetria']['caracteristicas_terreno']
                informe_texto += f"""

CARACTERÍSTICAS DEL TERRENO:
- Elevación mínima: {caracteristicas.get('min', 0):.1f} m
- Elevación máxima: {caracteristicas.get('max', 0):.1f} m
- Elevación promedio: {caracteristicas.get('mean', 0):.1f} m
- Rango de elevación: {caracteristicas.get('max', 0) - caracteristicas.get('min', 0):.1f} m
- Terreno plano: {caracteristicas.get('porcentaje_plano', 0):.1f}%
- Pendiente moderada: {caracteristicas.get('porcentaje_moderado', 0):.1f}%
"""
            
            crear_boton_descarga(
                informe_texto,
                "informe_biodiversidad.txt",
                "Descargar Informe Texto",
                'csv'
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # RESUMEN EJECUTIVO
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📊 Resumen Ejecutivo del Análisis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌳 Carbono Total", f"{summary['carbono_total_co2_ton']:,} ton CO₂")
        with col2:
            st.metric("🦋 Biodiversidad", f"{summary['indice_biodiversidad_promedio']}")
        with col3:
            st.metric("💧 Disponibilidad Agua", f"{summary['disponibilidad_agua_promedio']}")
        with col4:
            st.metric("📈 Estado General", summary['estado_general'])
        
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("🌱 Salud Suelo", f"{summary['salud_suelo_promedio']}")
        with col6:
            st.metric("⚠️ Presión Antrópica", f"{summary['presion_antropica_promedio']}")
        with col7:
            st.metric("🔗 Conectividad", f"{summary['conectividad_promedio']}")
        with col8:
            st.metric("🔍 Áreas Analizadas", summary['areas_analizadas'])
        
        # Indicadores de altimetría si están disponibles
        if 'altimetria' in resultados and 'caracteristicas_terreno' in resultados['altimetria']:
            st.markdown("---")
            st.subheader("🏔️ Indicadores de Altimetría")
            col_alt1, col_alt2, col_alt3, col_alt4 = st.columns(4)
            
            caracteristicas = resultados['altimetria']['caracteristicas_terreno']
            with col_alt1:
                st.metric("Elevación mínima", f"{caracteristicas.get('min', 0):.1f} m")
            with col_alt2:
                st.metric("Elevación máxima", f"{caracteristicas.get('max', 0):.1f} m")
            with col_alt3:
                st.metric("Rango elevación", f"{caracteristicas.get('max', 0) - caracteristicas.get('min', 0):.1f} m")
            with col_alt4:
                st.metric("Pendiente promedio", f"{caracteristicas.get('porcentaje_moderado', 0):.1f}%")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # VISUALIZACIONES AVANZADAS (mantener igual que antes)
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 Análisis Multivariado")
        
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
        
        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            categorias_radar = {
                'ndvi': 'Vegetación',
                'indice_shannon': 'Biodiversidad',
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_grafico_radar(datos_combinados, categorias_radar),
                use_container_width=True
            )
        
        with col_adv2:
            indicadores_corr = {
                'ndvi': 'Salud Vegetación',
                'co2_total_ton': 'Carbono',
                'indice_shannon': 'Biodiversidad', 
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_heatmap_correlacion(datos_combinados, indicadores_corr),
                use_container_width=True
            )
        
        st.subheader("🔍 Relación Tridimensional de Indicadores")
        ejes_3d = {
            'x': 'ndvi',
            'y': 'indice_shannon', 
            'z': 'co2_total_ton',
            'color': 'ndvi',
            'size': 'co2_total_ton',
            'titulo': 'Relación Vegetación-Biodiversidad-Carbono'
        }
        
        st.plotly_chart(
            crear_grafico_3d_scatter(datos_combinados, ejes_3d),
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif not tiene_poligono_data():
        # Pantalla de bienvenida
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Análisis Integral de Biodiversidad!
        
        ### 🌿 Sistema de Evaluación Ecológica Avanzada
        
        **Nuevas Características:**
        - 🗺️ **Mapas con ESRI Satellite** - Imágenes satelitales de alta calidad
        - 🔲 **Análisis por Áreas** - Divisiones regulares del territorio
        - 📊 **Visualizaciones Avanzadas** - Gráficos 3D, radar, sunburst, treemap
        - 🎨 **Leyendas Detalladas** - Información clara y comprensible
        - 🔗 **Análisis Multivariado** - Relaciones entre indicadores
        - 📥 **Descargas Mejoradas** - GeoJSON + Informes Word ejecutivos
        - 🔍 **Zoom Automático** - Los mapas se ajustan automáticamente al polígono
        - 🛰️ **INTEGRACIÓN PLANETSCOPE** - Análisis con imágenes satelitales de alta resolución
        - 🏔️ **ANÁLISIS DE ALTIMETRÍA** - Curvas de nivel y visualización 3D del terreno
        
        **🏔️ Características de Altimetría:**
        - **Curvas de nivel** - Generación automática cada 25 metros
        - **Modelo 3D del terreno** - Visualización interactiva en 3D
        - **Perfiles longitudinales** - Análisis de pendientes y desniveles
        - **Análisis de pendientes** - Clasificación del terreno por inclinación
        - **Exportación GeoJSON** - Descarga de curvas de nivel vectoriales
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
