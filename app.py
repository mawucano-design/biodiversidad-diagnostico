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

# Librerías para análisis geoespacial
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen, MousePosition
import geopandas as gpd
from shapely.geometry import Polygon, Point
import pyproj

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
    /* Estilos para la visualización 3D */
    .tree-3d-container {
        background: linear-gradient(135deg, #1a2a3a 0%, #0d1b2a 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .tree-3d-header {
        color: white;
        text-align: center;
        margin-bottom: 20px;
        font-size: 1.5rem;
        font-weight: bold;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
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
# 🌳 CLASE PARA VISUALIZACIÓN 3D DE ÁRBOLES (SIMILAR A LiDAR)
# ===============================

class Visualizador3DArboles:
    """Clase para crear visualizaciones 3D de árboles similares a LiDAR"""
    
    def __init__(self):
        self.especies_colores = {
            'Pino': {'tronco': '#8B4513', 'copa': '#228B22'},
            'Roble': {'tronco': '#654321', 'copa': '#006400'},
            'Encina': {'tronco': '#A0522D', 'copa': '#2E8B57'},
            'Eucalipto': {'tronco': '#D2691E', 'copa': '#32CD32'},
            'Cedro': {'tronco': '#5D4037', 'copa': '#388E3C'},
            'Palm': {'tronco': '#795548', 'copa': '#4CAF50'},
            'Abeto': {'tronco': '#5D4037', 'copa': '#2E7D32'},
            'Mangle': {'tronco': '#8D6E63', 'copa': '#43A047'}
        }
        
        self.especies_formas = {
            'Pino': 'cono',      # Forma cónica para pinos
            'Roble': 'esfera',   # Forma esférica para robles
            'Encina': 'cubo',    # Forma cubica para encinas
            'Eucalipto': 'cilindro',
            'Cedro': 'cono',
            'Palm': 'cilindro',
            'Abeto': 'cono',
            'Mangle': 'cilindro'
        }
    
    def generar_datos_arboles(self, area_hectareas, ndvi_promedio, indice_biodiversidad, num_arboles=100):
        """Generar datos simulados de árboles basados en indicadores ecológicos"""
        arboles = []
        
        # Determinar densidad de árboles basada en NDVI
        if ndvi_promedio > 0.7:
            densidad = 500  # Alta densidad (bosque denso)
        elif ndvi_promedio > 0.5:
            densidad = 300  # Media densidad
        elif ndvi_promedio > 0.3:
            densidad = 150  # Baja densidad
        else:
            densidad = 50   # Muy baja densidad
            
        # Ajustar por área
        num_arboles = min(int(area_hectareas * densidad / 100), 1000)
        num_arboles = max(num_arboles, 50)
        
        especies = list(self.especies_colores.keys())
        # Ajustar diversidad de especies basada en índice de biodiversidad
        num_especies = max(2, int(indice_biodiversidad * 5))
        especies_activas = especies[:num_especies]
        
        for i in range(num_arboles):
            # Determinar especie basada en biodiversidad
            if indice_biodiversidad > 0.7:
                especie = random.choice(especies_activas)
            else:
                # Menor biodiversidad = dominancia de pocas especies
                especie = random.choice(especies_activas[:2])
            
            # Generar altura basada en NDVI
            altura_base = 5 + (ndvi_promedio * 25)  # 5-30 metros
            altura = np.random.normal(altura_base, altura_base * 0.2)
            altura = max(3, min(40, altura))
            
            # Generar diámetro basado en altura
            diametro_tronco = altura * 0.08 + np.random.normal(0, 0.1)
            diametro_tronco = max(0.2, min(1.5, diametro_tronco))
            
            # Generar diámetro de copa
            diametro_copa = altura * 0.6 + np.random.normal(0, 2)
            diametro_copa = max(2, min(15, diametro_copa))
            
            # Generar posición aleatoria
            x = np.random.uniform(-area_hectareas**0.5, area_hectareas**0.5)
            y = np.random.uniform(-area_hectareas**0.5, area_hectareas**0.5)
            
            # Determinar salud basada en NDVI
            salud = np.random.normal(ndvi_promedio, 0.1)
            salud = max(0.1, min(1.0, salud))
            
            arboles.append({
                'id': i,
                'especie': especie,
                'altura': altura,
                'diametro_tronco': diametro_tronco,
                'diametro_copa': diametro_copa,
                'posicion': [x, y, 0],
                'salud': salud,
                'edad': np.random.uniform(1, 100),
                'biomasa': altura * diametro_tronco * 50,
                'color_tronco': self.especies_colores[especie]['tronco'],
                'color_copa': self.especies_colores[especie]['copa'],
                'forma_copa': self.especies_formas[especie]
            })
        
        return arboles
    
    def crear_tronco_3d(self, arbol):
        """Crear geometría 3D para el tronco del árbol"""
        x, y, z_base = arbol['posicion']
        altura = arbol['altura']
        diametro = arbol['diametro_tronco']
        color = arbol['color_tronco']
        
        # Crear cilindro para el tronco
        theta = np.linspace(0, 2*np.pi, 8)
        z = np.linspace(0, altura, 3)
        
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = diametro/2 * np.cos(theta_grid) + x
        y_grid = diametro/2 * np.sin(theta_grid) + y
        
        return {
            'x': x_grid.flatten(),
            'y': y_grid.flatten(),
            'z': np.tile(z_grid.flatten(), 1) + z_base,
            'color': color,
            'opacity': 0.9
        }
    
    def crear_copa_3d(self, arbol):
        """Crear geometría 3D para la copa del árbol"""
        x, y, z_base = arbol['posicion']
        altura = arbol['altura']
        diametro = arbol['diametro_copa']
        color = arbol['color_copa']
        forma = arbol['forma_copa']
        salud = arbol['salud']
        
        # Ajustar color basado en salud
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r = int(r * salud)
        g = int(g * (0.7 + salud * 0.3))
        b = int(b * 0.8)
        color_ajustado = f'rgb({r},{g},{b})'
        
        z_copa = z_base + altura * 0.7  # La copa comienza a 70% de la altura
        
        if forma == 'cono':
            # Crear cono para la copa
            theta = np.linspace(0, 2*np.pi, 16)
            r = np.linspace(0, diametro/2, 8)
            
            theta_grid, r_grid = np.meshgrid(theta, r)
            x_grid = r_grid * np.cos(theta_grid) + x
            y_grid = r_grid * np.sin(theta_grid) + y
            z_grid = altura * 0.3 * (1 - r_grid/(diametro/2)) + z_copa
            
            return {
                'type': 'mesh3d',
                'x': x_grid.flatten(),
                'y': y_grid.flatten(),
                'z': z_grid.flatten(),
                'color': color_ajustado,
                'opacity': 0.7,
                'intensity': np.ones_like(x_grid.flatten()) * salud
            }
            
        elif forma == 'esfera':
            # Crear esfera para la copa
            phi = np.linspace(0, np.pi, 8)
            theta = np.linspace(0, 2*np.pi, 16)
            
            phi_grid, theta_grid = np.meshgrid(phi, theta)
            radius = diametro/3
            
            x_grid = radius * np.sin(phi_grid) * np.cos(theta_grid) + x
            y_grid = radius * np.sin(phi_grid) * np.sin(theta_grid) + y
            z_grid = radius * np.cos(phi_grid) + z_copa + radius/2
            
            return {
                'type': 'mesh3d',
                'x': x_grid.flatten(),
                'y': y_grid.flatten(),
                'z': z_grid.flatten(),
                'color': color_ajustado,
                'opacity': 0.6,
                'intensity': np.ones_like(x_grid.flatten()) * salud
            }
            
        else:  # cilindro por defecto
            # Crear cilindro para la copa
            theta = np.linspace(0, 2*np.pi, 12)
            z = np.linspace(0, altura * 0.3, 4)
            
            theta_grid, z_grid = np.meshgrid(theta, z)
            x_grid = diametro/2 * np.cos(theta_grid) + x
            y_grid = diametro/2 * np.sin(theta_grid) + y
            
            return {
                'type': 'mesh3d',
                'x': x_grid.flatten(),
                'y': y_grid.flatten(),
                'z': z_grid.flatten() + z_copa,
                'color': color_ajustado,
                'opacity': 0.65,
                'intensity': np.ones_like(x_grid.flatten()) * salud
            }
    
    def crear_visualizacion_3d(self, arboles, max_arboles=200):
        """Crear visualización 3D completa similar a LiDAR"""
        if len(arboles) > max_arboles:
            # Muestrear árboles para mejor rendimiento
            arboles = random.sample(arboles, max_arboles)
        
        fig = go.Figure()
        
        # Crear terreno base
        self._agregar_terreno(fig, arboles)
        
        # Agregar árboles
        for i, arbol in enumerate(arboles[:150]):  # Limitar para rendimiento
            # Agregar tronco
            tronco = self.crear_tronco_3d(arbol)
            fig.add_trace(go.Mesh3d(
                x=tronco['x'],
                y=tronco['y'],
                z=tronco['z'],
                color=tronco['color'],
                opacity=tronco['opacity'],
                flatshading=True,
                name=f"Tronco {arbol['especie']}",
                showlegend=False
            ))
            
            # Agregar copa
            copa = self.crear_copa_3d(arbol)
            if copa['type'] == 'mesh3d':
                fig.add_trace(go.Mesh3d(
                    x=copa['x'],
                    y=copa['y'],
                    z=copa['z'],
                    color=copa['color'],
                    opacity=copa['opacity'],
                    intensity=copa['intensity'],
                    colorscale=[[0, 'rgb(150,50,50)'], [0.5, 'rgb(100,150,100)'], [1, copa['color']]],
                    showscale=False,
                    name=f"Copa {arbol['especie']}",
                    showlegend=False
                ))
        
        # Configurar layout 3D
        self._configurar_layout_3d(fig, arboles)
        
        return fig
    
    def _agregar_terreno(self, fig, arboles):
        """Agregar terreno base a la visualización 3D"""
        if not arboles:
            return
        
        # Crear terreno ondulado
        x_vals = [arbol['posicion'][0] for arbol in arboles]
        y_vals = [arbol['posicion'][1] for arbol in arboles]
        
        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)
        
        # Extender el terreno un poco más allá de los árboles
        x_range = x_max - x_min
        y_range = y_max - y_min
        x_min -= x_range * 0.1
        x_max += x_range * 0.1
        y_min -= y_range * 0.1
        y_max += y_range * 0.1
        
        # Crear grid para el terreno
        x_grid = np.linspace(x_min, x_max, 20)
        y_grid = np.linspace(y_min, y_max, 20)
        x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
        
        # Crear ondulaciones naturales
        z_terreno = np.zeros_like(x_mesh)
        for i in range(3):  # 3 ondulaciones
            freq = np.random.uniform(0.5, 2.0)
            amp = np.random.uniform(0.1, 0.5)
            z_terreno += amp * np.sin(freq * x_mesh + np.random.uniform(0, np.pi)) * \
                         np.cos(freq * y_mesh + np.random.uniform(0, np.pi))
        
        # Suavizar el terreno
        z_terreno = np.clip(z_terreno, -1, 1)
        
        # Agregar terreno a la figura
        fig.add_trace(go.Surface(
            x=x_mesh,
            y=y_mesh,
            z=z_terreno,
            colorscale=[[0, '#8B4513'], [0.5, '#A0522D'], [1, '#D2691E']],
            opacity=0.9,
            showscale=False,
            name='Terreno',
            contours={
                "z": {"show": True, "usecolormap": True, "highlightcolor": "limegreen", "project": {"z": True}}
            }
        ))
    
    def _configurar_layout_3d(self, fig, arboles):
        """Configurar el layout de la visualización 3D"""
        if not arboles:
            return
        
        # Calcular límites de la escena
        x_vals = [arbol['posicion'][0] for arbol in arboles]
        y_vals = [arbol['posicion'][1] for arbol in arboles]
        z_vals = [arbol['altura'] for arbol in arboles]
        
        x_range = max(x_vals) - min(x_vals)
        y_range = max(y_vals) - min(y_vals)
        
        # Configurar cámara 3D (similar al video)
        camera = dict(
            eye=dict(x=2, y=2, z=1.5),  # Vista aérea oblicua
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0)
        )
        
        fig.update_layout(
            title={
                'text': '🌳 Visualización 3D de Estructura Forestal (Similar a LiDAR)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24, 'color': 'white'}
            },
            scene=dict(
                xaxis=dict(
                    title='X (m)',
                    backgroundcolor='rgba(0, 0, 0, 0)',
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    showbackground=True,
                    zerolinecolor='rgba(100, 100, 100, 0.5)'
                ),
                yaxis=dict(
                    title='Y (m)',
                    backgroundcolor='rgba(0, 0, 0, 0)',
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    showbackground=True,
                    zerolinecolor='rgba(100, 100, 100, 0.5)'
                ),
                zaxis=dict(
                    title='Altura (m)',
                    backgroundcolor='rgba(0, 0, 0, 0)',
                    gridcolor='rgba(100, 100, 100, 0.3)',
                    showbackground=True,
                    zerolinecolor='rgba(100, 100, 100, 0.5)'
                ),
                aspectmode='manual',
                aspectratio=dict(x=2, y=2, z=1),
                camera=camera,
                bgcolor='rgba(10, 20, 30, 1)'
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0, 0, 0, 0.7)',
                bordercolor='rgba(255, 255, 255, 0.3)',
                borderwidth=1,
                font=dict(color='white')
            ),
            paper_bgcolor='rgba(0, 0, 0, 0)',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            height=700,
            margin=dict(l=0, r=0, t=80, b=0)
        )
    
    def crear_visualizacion_nube_puntos(self, arboles):
        """Crear visualización alternativa tipo nube de puntos 3D"""
        if not arboles:
            return go.Figure()
        
        # Preparar datos
        datos = []
        for arbol in arboles[:500]:  # Limitar para rendimiento
            x, y, z = arbol['posicion']
            altura = arbol['altura']
            salud = arbol['salud']
            
            # Puntos para tronco
            for z_tr in np.linspace(0, altura * 0.7, 5):
                datos.append({
                    'x': x,
                    'y': y,
                    'z': z_tr,
                    'tipo': 'tronco',
                    'especie': arbol['especie'],
                    'altura': altura,
                    'salud': salud,
                    'color': arbol['color_tronco']
                })
            
            # Puntos para copa
            num_puntos_copa = int(arbol['diametro_copa'] * 3)
            for _ in range(num_puntos_copa):
                angulo = np.random.uniform(0, 2*np.pi)
                radio = np.random.uniform(0, arbol['diametro_copa']/2)
                z_copa = altura * 0.7 + np.random.uniform(0, altura * 0.3)
                
                x_copa = x + radio * np.cos(angulo)
                y_copa = y + radio * np.sin(angulo)
                
                datos.append({
                    'x': x_copa,
                    'y': y_copa,
                    'z': z_copa,
                    'tipo': 'copa',
                    'especie': arbol['especie'],
                    'altura': altura,
                    'salud': salud,
                    'color': arbol['color_copa']
                })
        
        df = pd.DataFrame(datos)
        
        if df.empty:
            return go.Figure()
        
        # Crear figura de dispersión 3D
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color='especie',
            size='altura',
            hover_data=['especie', 'altura', 'salud'],
            title='🌳 Nube de Puntos 3D - Distribución de Árboles'
        )
        
        # Configurar estilo similar a LiDAR
        fig.update_traces(
            marker=dict(
                size=3,
                opacity=0.7,
                line=dict(width=0)
            )
        )
        
        fig.update_layout(
            scene=dict(
                xaxis_title='X (m)',
                yaxis_title='Y (m)',
                zaxis_title='Altura (m)',
                bgcolor='rgba(0, 0, 0, 1)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1)
                )
            ),
            paper_bgcolor='rgba(0, 0, 0, 0)',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            font=dict(color='white'),
            height=600
        )
        
        return fig

# ===============================
# 🧩 CLASE PRINCIPAL DE ANÁLISIS MEJORADA
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
        self.visualizador_3d = Visualizador3DArboles()
    
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
    
    def procesar_poligono(self, gdf, vegetation_type, divisiones=5):
        """Procesar el polígono cargado dividiéndolo en áreas regulares"""
        if gdf is None or gdf.empty:
            return None
        
        try:
            poligono = gdf.geometry.iloc[0]
            area_hectareas = self._calcular_area_hectareas(poligono)
            st.info(f"**Área calculada:** {area_hectareas:,.2f} hectáreas")
            areas_data = self._generar_areas_regulares(poligono, divisiones)
            resultados = self._analisis_integral(areas_data, vegetation_type, area_hectareas)
            
            # Generar datos para visualización 3D
            arboles_3d = self._generar_datos_3d(resultados, area_hectareas)
            
            return {
                'poligono': poligono,
                'area_hectareas': area_hectareas,
                'areas_analisis': areas_data,
                'resultados': resultados,
                'centroide': poligono.centroid,
                'tipo_vegetacion': vegetation_type,
                'arboles_3d': arboles_3d
            }
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None
    
    def _generar_datos_3d(self, resultados, area_hectareas):
        """Generar datos para visualización 3D de árboles"""
        try:
            # Calcular promedios para toda el área
            if 'summary_metrics' in resultados:
                summary = resultados['summary_metrics']
                ndvi_promedio = summary.get('ndvi_promedio', 0.5)
                indice_biodiversidad = summary.get('indice_biodiversidad_promedio', 0.5)
            else:
                # Si no hay summary, calcular de los datos disponibles
                ndvi_promedio = np.mean([v['ndvi'] for v in resultados.get('vegetacion', [])]) if resultados.get('vegetacion') else 0.5
                indice_biodiversidad = np.mean([b['indice_shannon']/3.0 for b in resultados.get('biodiversidad', [])]) if resultados.get('biodiversidad') else 0.5
            
            # Generar árboles 3D
            arboles = self.visualizador_3d.generar_datos_arboles(
                area_hectareas=area_hectareas,
                ndvi_promedio=ndvi_promedio,
                indice_biodiversidad=indice_biodiversidad,
                num_arboles=min(int(area_hectareas * 10), 500)
            )
            
            return {
                'arboles': arboles,
                'estadisticas': {
                    'total_arboles': len(arboles),
                    'ndvi_promedio': ndvi_promedio,
                    'indice_biodiversidad': indice_biodiversidad,
                    'area_hectareas': area_hectareas
                }
            }
        except Exception as e:
            st.warning(f"No se pudieron generar datos 3D: {str(e)}")
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
    
    def _analisis_integral(self, areas_data, vegetation_type, area_total):
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
        """Analizar indicadores de biodiversidad de forma más realista"""
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

def crear_mapa_indicador(gdf, datos, indicador_config, zoom_config=None):
    """Crear mapa con áreas para un indicador específico usando ESRI Satellite con zoom automático"""
    if gdf is None or datos is None:
        return crear_mapa_base()
    
    try:
        if zoom_config is None:
            zoom_config = calcular_bounds_optimos(gdf, datos)
        
        m = folium.Map(
            location=zoom_config['center'], 
            zoom_start=zoom_config['zoom'],
            tiles=None,
            control_scale=True
        )
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite ESRI',
            overlay=False
        ).add_to(m)
        
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap'
        ).add_to(m)
        
        if hasattr(gdf, 'geometry') and not gdf.empty:
            try:
                poligono_geojson = gdf.__geo_interface__
                folium.GeoJson(
                    poligono_geojson,
                    style_function=lambda x: {
                        'fillColor': 'transparent',
                        'color': '#FFD700',
                        'weight': 3,
                        'fillOpacity': 0.0,
                        'dashArray': '5, 5'
                    },
                    name='Polígono Principal',
                    tooltip='Área de estudio'
                ).add_to(m)
            except Exception as e:
                st.warning(f"No se pudo agregar el polígono principal: {str(e)}")
        
        for area_data in datos:
            valor = area_data[indicador_config['columna']]
            geometry = area_data['geometry']
            color = 'gray'
            for rango, color_rango in indicador_config['colores'].items():
                if valor >= rango[0] and valor <= rango[1]:
                    color = color_rango
                    break
            
            area_geojson = gpd.GeoSeries([geometry]).__geo_interface__
            folium.GeoJson(
                area_geojson,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': color,
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(
                    f"""
                    <div style="min-width: 250px;">
                        <h4>📍 {area_data['area']}</h4>
                        <p><b>{indicador_config['titulo']}:</b> {valor}</p>
                        <p><b>Estado:</b> {area_data.get('estado', 'N/A')}</p>
                        <p><b>Área:</b> {area_data.get('area_ha', 'N/A')} ha</p>
                    </div>
                    """, 
                    max_width=300
                ),
                tooltip=f"{area_data['area']}: {valor}"
            ).add_to(m)
        
        legend_html = f'''
        <div style="position: fixed; bottom: 50px; left: 50px; width: 300px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 8px; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        <h4 style="margin:0 0 10px 0; color: #2E8B57;">{indicador_config['titulo']}</h4>
        <p style="margin:5px 0; font-size:12px; color: #666;">{indicador_config['descripcion']}</p>
        '''
        
        for rango, color in indicador_config['colores'].items():
            label = indicador_config['leyenda'].get(rango, f"{rango[0]} - {rango[1]}")
            legend_html += f'<p style="margin:5px 0;"><i style="background:{color}; width: 20px; height: 20px; display: inline-block; border-radius: 4px; margin-right: 8px;"></i> {label}</p>'
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        
        reset_html = f'''
        <div style="position: fixed; top: 50px; right: 50px; z-index:9999;">
            <button onclick="resetMapView()" style="background-color: white; border: 2px solid #2E8B57; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-weight: bold; color: #2E8B57;">
                🔍 Restaurar Vista
            </button>
        </div>
        <script>
        function resetMapView() {{
            if (typeof currentMap !== 'undefined') {{
                currentMap.setView([{zoom_config['center'][0]}, {zoom_config['center'][1]}], {zoom_config['zoom']});
            }}
        }}
        </script>
        '''
        
        m.get_root().html.add_child(folium.Element(reset_html))
        folium.LayerControl().add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
        return crear_mapa_base()

def crear_mapa_base(center=None, zoom=None):
    """Crear mapa base con ESRI Satellite"""
    if center is None:
        center = [-14.0, -60.0]
    if zoom is None:
        zoom = 4
    
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite ESRI'
    ).add_to(m)
    folium.TileLayer('OpenStreetMap').add_to(m)
    Fullscreen().add_to(m)
    MousePosition().add_to(m)
    folium.LayerControl().add_to(m)
    return m

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
    if 'show_3d_visualization' not in st.session_state:
        st.session_state.show_3d_visualization = False

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
                    st.session_state.show_3d_visualization = False
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
        
        # Configuración para visualización 3D
        st.markdown("---")
        st.header("🌳 Visualización 3D")
        mostrar_3d = st.checkbox("Mostrar visualización 3D de árboles", 
                                help="Visualización similar a LiDAR de la estructura forestal")
        st.session_state.show_3d_visualization = mostrar_3d
        
        if mostrar_3d:
            st.info("La visualización 3D mostrará una representación de la estructura forestal basada en los indicadores analizados.")
        
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
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de análisis
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
                    
                    # Calcular configuración de zoom
                    st.session_state.zoom_config = calcular_bounds_optimos(
                        st.session_state.poligono_data,
                        resultados['areas_analisis']
                    )
                    
                    st.success("✅ Análisis completado exitosamente!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar resultados del análisis
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
        # SECCIÓN DE VISUALIZACIÓN 3D DE ÁRBOLES (Similar a LiDAR)
        if st.session_state.show_3d_visualization and 'arboles_3d' in resultados:
            st.markdown('<div class="tree-3d-container">', unsafe_allow_html=True)
            st.markdown('<div class="tree-3d-header">🌳 VISUALIZACIÓN 3D DE ESTRUCTURA FORESTAL</div>', unsafe_allow_html=True)
            
            arboles_3d = resultados['arboles_3d']
            
            if arboles_3d and 'arboles' in arboles_3d:
                col_3d1, col_3d2, col_3d3 = st.columns([2, 1, 1])
                
                with col_3d1:
                    st.markdown("**📊 Estadísticas Forestales:**")
                    if 'estadisticas' in arboles_3d:
                        stats = arboles_3d['estadisticas']
                        st.metric("Total de árboles simulados", f"{stats.get('total_arboles', 0):,}")
                        st.metric("NDVI promedio", f"{stats.get('ndvi_promedio', 0):.2f}")
                        st.metric("Índice biodiversidad", f"{stats.get('indice_biodiversidad', 0):.2f}")
                
                with col_3d2:
                    st.markdown("**🎨 Configuración 3D:**")
                    tipo_visualizacion = st.radio(
                        "Tipo de visualización:",
                        ["Modelado 3D", "Nube de puntos"],
                        index=0,
                        horizontal=True
                    )
                    
                    densidad = st.slider(
                        "Densidad de visualización:",
                        1, 5, 3,
                        help="Controla el nivel de detalle de la visualización 3D"
                    )
                
                with col_3d3:
                    st.markdown("**📐 Vista de cámara:**")
                    vista_camara = st.selectbox(
                        "Ángulo de vista:",
                        ["Vista aérea", "Vista frontal", "Vista isométrica"],
                        index=0
                    )
                    
                    if st.button("🔄 Actualizar visualización", type="secondary"):
                        st.rerun()
                
                # Separador visual
                st.markdown("---")
                
                # Mostrar visualización 3D
                with st.spinner("Generando visualización 3D..."):
                    try:
                        if tipo_visualizacion == "Modelado 3D":
                            # Filtrar árboles según densidad
                            arboles_filtrados = arboles_3d['arboles']
                            if densidad < 5:
                                factor = [1.0, 0.7, 0.5, 0.3, 0.2][densidad-1]
                                num_arboles = int(len(arboles_filtrados) * factor)
                                arboles_filtrados = random.sample(arboles_filtrados, num_arboles)
                            
                            # Crear visualización 3D
                            fig_3d = st.session_state.analyzer.visualizador_3d.crear_visualizacion_3d(arboles_filtrados)
                            st.plotly_chart(fig_3d, use_container_width=True, height=700)
                        else:
                            # Visualización de nube de puntos
                            fig_puntos = st.session_state.analyzer.visualizador_3d.crear_visualizacion_nube_puntos(arboles_3d['arboles'])
                            st.plotly_chart(fig_puntos, use_container_width=True, height=600)
                        
                        # Leyenda de especies
                        st.markdown("**🌿 Leyenda de especies:**")
                        especies_col = st.columns(4)
                        especies = st.session_state.analyzer.visualizador_3d.especies_colores
        
                        for idx, (especie, colores) in enumerate(especies_colores.items()):
                            with especies_col[idx % 4]:
                                st.markdown(f"""
                                <div style="background: {colores['copa']}; padding: 8px; border-radius: 6px; margin: 5px 0; color: white; text-align: center;">
                                    {especie}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    except Exception as e:
                        st.error(f"Error generando visualización 3D: {str(e)}")
                        st.info("Intente reducir la densidad de visualización o actualice la página.")
            
            else:
                st.warning("No se pudieron generar datos 3D para la visualización.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # CONFIGURACIÓN DE INDICADORES CON LEYENDAS MEJORADAS
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
        for config in indicadores_config:
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.subheader(config['titulo'])
            
            mapa = crear_mapa_indicador(
                st.session_state.poligono_data,
                resultados['resultados'][config['key']],
                config,
                st.session_state.zoom_config
            )
            st_folium(mapa, width=800, height=500, key=f"map_{config['key']}")
            
            with st.expander("ℹ️ Información de la vista del mapa"):
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    if st.session_state.zoom_config:
                        st.metric("Centro", f"{st.session_state.zoom_config['center'][0]:.4f}, {st.session_state.zoom_config['center'][1]:.4f}")
                    else:
                        st.metric("Centro", "No disponible")
                with col_info2:
                    if st.session_state.zoom_config:
                        st.metric("Nivel de Zoom", st.session_state.zoom_config['zoom'])
                    else:
                        st.metric("Nivel de Zoom", "No disponible")
                with col_info3:
                    if st.session_state.zoom_config and 'lat_span' in st.session_state.zoom_config:
                        span_km = st.session_state.zoom_config['lat_span'] * 111
                        st.metric("Extensión", f"{span_km:.1f} km")
                    else:
                        st.metric("Extensión", "No disponible")
            
            col_viz1, col_viz2 = st.columns(2)
            with col_viz1:
                estado_col = next((k for k in resultados['resultados'][config['key']][0].keys() if 'estado' in k), None)
                st.plotly_chart(
                    crear_grafico_sunburst(
                        resultados['resultados'][config['key']],
                        config['columna'],
                        estado_col,
                        f"Distribución de {config['titulo']}"
                    ),
                    use_container_width=True
                )
            
            with col_viz2:
                st.plotly_chart(
                    crear_grafico_treemap(
                        resultados['resultados'][config['key']],
                        config['columna'],
                        estado_col,
                        f"Distribución Jerárquica - {config['titulo']}"
                    ),
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # VISUALIZACIONES AVANZADAS
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
        - 🌳 **VISUALIZACIÓN 3D LiDAR** - Representación de estructura forestal en 3D similar a escaneo LiDAR
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
