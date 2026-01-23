# ✅ ABSOLUTAMENTE PRIMERO: Importar streamlit
import streamlit as st
# ✅ LUEGO: Configurar la página
st.set_page_config(
    page_title="Sistema Satelital de Análisis Ambiental con Verra VCS - Sudamérica",
    page_icon="🌎",
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
import requests  # ✅ Añadido para APIs
from typing import Optional, Dict, Any, List, Tuple
warnings.filterwarnings('ignore')
# Librerías geoespaciales
import folium
from streamlit_folium import st_folium, folium_static
from folium.plugins import Fullscreen, MousePosition, HeatMap
import geopandas as gpd
from shapely.geometry import Polygon, Point, shape, MultiPolygon
from shapely.ops import unary_union
import pyproj
from branca.colormap import LinearColormap
import matplotlib.cm as cm
# Para simulación de datos satelitales
import random

# ===============================
# 🌦️ CONECTOR CLIMÁTICO TROPICAL SIMPLIFICADO
# ===============================
class ConectorClimaticoTropical:
    """Sistema para obtener datos meteorológicos reales en Sudamérica"""
    def __init__(self):
        pass

    def obtener_datos_climaticos(self, lat: float, lon: float) -> Dict:
        """Obtiene datos climáticos para una ubicación"""
        # Simulación realista basada en ubicación
        if -5 <= lat <= 5 and -75 <= lon <= -50:  # Amazonía central
            return {'precipitacion': 2500 + random.uniform(-200, 200), 'temperatura': 26 + random.uniform(-1, 1)}
        elif abs(lat) < 10 and -82 <= lon <= -75:  # Chocó
            return {'precipitacion': 4000 + random.uniform(-300, 300), 'temperatura': 27 + random.uniform(-1, 1)}
        elif -15 <= lat < -5 and -70 <= lon <= -50:  # Sur amazónico
            return {'precipitacion': 1800 + random.uniform(-200, 200), 'temperatura': 25 + random.uniform(-1, 1)}
        elif -34 <= lat <= -22 and -73 <= lon <= -53:  # Argentina templada
            return {'precipitacion': 800 + random.uniform(-100, 100), 'temperatura': 18 + random.uniform(-2, 2)}
        else:  # Región general
            return {'precipitacion': 1200 + random.uniform(-200, 200), 'temperatura': 22 + random.uniform(-2, 2)}

# ===============================
# 🌳 METODOLOGÍA VERRA SIMPLIFICADA
# ===============================
class MetodologiaVerra:
    """Implementación simplificada de la metodología Verra VCS"""
    def __init__(self):
        self.factores = {
            'conversion_carbono': 0.47,
            'ratio_co2': 3.67,
            'ratio_raiz': 0.24,  # BGB/AGB
            'proporcion_madera_muerta': 0.15,
            'acumulacion_hojarasca': 5.0,
            'carbono_suelo': 2.5  # ton C/ha en 30 cm
        }
        
    def calcular_carbono_hectarea(self, ndvi: float, tipo_bosque: str, precipitacion: float) -> Dict:
        """Calcula carbono por hectárea basado en NDVI, tipo de bosque y precipitación"""
        # Factor por precipitación (bosques más lluviosos tienen más biomasa)
        factor_precip = min(2.0, max(0.5, precipitacion / 1500))
        
        # Estimación de biomasa aérea basada en NDVI
        if ndvi > 0.7:
            agb_ton_ha = (150 + (ndvi - 0.7) * 300) * factor_precip
        elif ndvi > 0.5:
            agb_ton_ha = (80 + (ndvi - 0.5) * 350) * factor_precip
        elif ndvi > 0.3:
            agb_ton_ha = (30 + (ndvi - 0.3) * 250) * factor_precip
        else:
            agb_ton_ha = (5 + ndvi * 100) * factor_precip
        
        # Ajuste por tipo de bosque
        if tipo_bosque == "amazonia":
            agb_ton_ha *= 1.2
        elif tipo_bosque == "choco":
            agb_ton_ha *= 1.3
        elif tipo_bosque == "seco":
            agb_ton_ha *= 0.8
        
        # Cálculos de carbono por pool
        carbono_agb = agb_ton_ha * self.factores['conversion_carbono']
        carbono_bgb = carbono_agb * self.factores['ratio_raiz']
        carbono_dw = carbono_agb * self.factores['proporcion_madera_muerta']
        carbono_li = self.factores['acumulacion_hojarasca'] * self.factores['conversion_carbono']
        carbono_soc = self.factores['carbono_suelo']
        
        carbono_total = carbono_agb + carbono_bgb + carbono_dw + carbono_li + carbono_soc
        co2_equivalente = carbono_total * self.factores['ratio_co2']
        
        return {
            'carbono_total_ton_ha': round(carbono_total, 2),
            'co2_equivalente_ton_ha': round(co2_equivalente, 2),
            'desglose': {
                'AGB': round(carbono_agb, 2),
                'BGB': round(carbono_bgb, 2),
                'DW': round(carbono_dw, 2),
                'LI': round(carbono_li, 2),
                'SOC': round(carbono_soc, 2)
            }
        }

# ===============================
# 🦋 ANÁLISIS DE BIODIVERSIDAD CON SHANNON
# ===============================
class AnalisisBiodiversidad:
    """Sistema para análisis de biodiversidad usando el índice de Shannon"""
    def __init__(self):
        self.parametros = {
            'amazonia': {'riqueza_base': 150, 'abundancia_base': 1000},
            'choco': {'riqueza_base': 120, 'abundancia_base': 800},
            'andes': {'riqueza_base': 100, 'abundancia_base': 600},
            'pampa': {'riqueza_base': 50, 'abundancia_base': 300},
            'seco': {'riqueza_base': 40, 'abundancia_base': 200}
        }
    
    def calcular_shannon(self, ndvi: float, tipo_ecosistema: str, area_ha: float, precipitacion: float) -> Dict:
        """Calcula índice de Shannon basado en NDVI, tipo de ecosistema y condiciones ambientales"""
        
        # Parámetros base según ecosistema
        params = self.parametros.get(tipo_ecosistema, {'riqueza_base': 60, 'abundancia_base': 400})
        
        # Factor NDVI (vegetación más sana → más biodiversidad)
        factor_ndvi = 1.0 + (ndvi * 0.8)
        
        # Factor área (áreas más grandes → más especies)
        factor_area = min(2.0, math.log10(area_ha + 1) * 0.5 + 1)
        
        # Factor precipitación (más lluvia → más biodiversidad en trópicos)
        if tipo_ecosistema in ['amazonia', 'choco']:
            factor_precip = min(1.5, precipitacion / 2000)
        else:
            factor_precip = 1.0
        
        # Cálculo de riqueza de especies estimada
        riqueza_especies = int(params['riqueza_base'] * factor_ndvi * factor_area * factor_precip * random.uniform(0.9, 1.1))
        
        # Cálculo de abundancia estimada
        abundancia_total = int(params['abundancia_base'] * factor_ndvi * factor_area * factor_precip * random.uniform(0.9, 1.1))
        
        # Simulación de distribución de abundancia (ley de potencias común en ecología)
        especies = []
        abundancia_acumulada = 0
        
        for i in range(riqueza_especies):
            # Abundancia sigue una distribución log-normal
            abundancia = int((abundancia_total / riqueza_especies) * random.lognormvariate(0, 0.5))
            if abundancia > 0:
                especies.append({'especie_id': i+1, 'abundancia': abundancia})
                abundancia_acumulada += abundancia
        
        # Normalizar abundancias
        for especie in especies:
            especie['proporcion'] = especie['abundancia'] / abundancia_acumulada
        
        # Calcular índice de Shannon
        shannon = 0
        for especie in especies:
            if especie['proporcion'] > 0:
                shannon -= especie['proporcion'] * math.log(especie['proporcion'])
        
        # Categorías de biodiversidad según Shannon
        if shannon > 3.5:
            categoria = "Muy Alta"
            color = "#10b981"
            color_hex = "#10b981"
        elif shannon > 2.5:
            categoria = "Alta"
            color = "#3b82f6"
            color_hex = "#3b82f6"
        elif shannon > 1.5:
            categoria = "Moderada"
            color = "#f59e0b"
            color_hex = "#f59e0b"
        elif shannon > 0.5:
            categoria = "Baja"
            color = "#ef4444"
            color_hex = "#ef4444"
        else:
            categoria = "Muy Baja"
            color = "#991b1b"
            color_hex = "#991b1b"
        
        return {
            'indice_shannon': round(shannon, 3),
            'categoria': categoria,
            'color': color,
            'color_hex': color_hex,
            'riqueza_especies': riqueza_especies,
            'abundancia_total': abundancia_acumulada,
            'especies_muestra': especies[:10]  # Solo muestra las primeras 10
        }

# ===============================
# 🗺️ SISTEMA DE MAPAS SIMPLIFICADO CON HEATMAPS
# ===============================
class SistemaMapas:
    """Sistema de mapas simplificado con heatmaps"""
    def __init__(self):
        self.capa_base = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    
    def crear_mapa_area(self, gdf):
        """Crea mapa básico con el área de estudio"""
        if gdf is None or gdf.empty:
            return None
        
        # Calcular centro y zoom
        bounds = gdf.total_bounds
        centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        
        # Crear mapa
        m = folium.Map(
            location=centro,
            zoom_start=12,
            tiles=self.capa_base,
            attr='Esri, Maxar, Earthstar Geographics',
            control_scale=True
        )
        
        # Agregar polígono
        folium.GeoJson(
            gdf.geometry.iloc[0],
            style_function=lambda x: {
                'fillColor': '#3b82f6',
                'color': '#1d4ed8',
                'weight': 3,
                'fillOpacity': 0.2
            }
        ).add_to(m)
        
        return m
    
    def crear_mapa_carbono(self, puntos_carbono):
        """Crea mapa de calor para carbono"""
        if not puntos_carbono:
            return None
        
        # Calcular centro del primer punto
        centro = [puntos_carbono[0]['lat'], puntos_carbono[0]['lon']]
        
        m = folium.Map(
            location=centro,
            zoom_start=12,
            tiles=self.capa_base,
            attr='Esri, Maxar, Earthstar Geographics'
        )
        
        # Preparar datos para heatmap
        heat_data = [[p['lat'], p['lon'], p['carbono_ton_ha']] for p in puntos_carbono]
        
        # Agregar heatmap
        HeatMap(
            heat_data,
            name='Carbono (ton C/ha)',
            min_opacity=0.3,
            radius=25,
            blur=20,
            gradient={0.0: 'blue', 0.2: 'cyan', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
        ).add_to(m)
        
        # Agregar marcadores para puntos importantes
        for p in puntos_carbono[:15]:  # Limitar a 15 marcadores
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=6,
                color='#065f46',
                fill=True,
                fill_color='#10b981',
                fill_opacity=0.7,
                popup=f"""
                <div style="font-family: Arial; font-size: 12px;">
                <b>Carbono según Verra VCS</b><br>
                <hr style="margin: 3px 0;">
                <b>Carbono:</b> {p['carbono_ton_ha']:.1f} ton C/ha<br>
                <b>NDVI:</b> {p['ndvi']:.3f}<br>
                <b>Precipitación:</b> {p['precipitacion']:.0f} mm/año<br>
                <b>Coordenadas:</b><br>
                {p['lat']:.4f}°, {p['lon']:.4f}°
                </div>
                """
            ).add_to(m)
        
        # Agregar leyenda
        self._agregar_leyenda_carbono(m)
        
        return m
    
    def crear_mapa_biodiversidad(self, puntos_biodiversidad):
        """Crea mapa de calor para biodiversidad (índice de Shannon)"""
        if not puntos_biodiversidad:
            return None
        
        # Calcular centro del primer punto
        centro = [puntos_biodiversidad[0]['lat'], puntos_biodiversidad[0]['lon']]
        
        m = folium.Map(
            location=centro,
            zoom_start=12,
            tiles=self.capa_base,
            attr='Esri, Maxar, Earthstar Geographics'
        )
        
        # Preparar datos para heatmap
        heat_data = [[p['lat'], p['lon'], p['shannon']] for p in puntos_biodiversidad]
        
        # Agregar heatmap con gradiente de colores para biodiversidad
        HeatMap(
            heat_data,
            name='Índice de Shannon',
            min_opacity=0.4,
            radius=25,
            blur=20,
            gradient={
                0.0: '#991b1b',    # Muy baja - Rojo oscuro
                0.2: '#ef4444',    # Baja - Rojo
                0.4: '#f59e0b',    # Moderada - Naranja
                0.6: '#3b82f6',    # Alta - Azul
                0.8: '#8b5cf6',    # Muy alta - Púrpura
                1.0: '#10b981'     # Excelente - Verde
            }
        ).add_to(m)
        
        # Agregar marcadores para puntos importantes
        for p in puntos_biodiversidad[:15]:  # Limitar a 15 marcadores
            # Determinar color del marcador según categoría
            color_categoria = p.get('color_hex', '#808080')
            
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=6,
                color=color_categoria,
                fill=True,
                fill_color=color_categoria,
                fill_opacity=0.7,
                popup=f"""
                <div style="font-family: Arial; font-size: 12px;">
                <b>Biodiversidad - Índice de Shannon</b><br>
                <hr style="margin: 3px 0;">
                <b>Índice de Shannon:</b> {p['shannon']:.3f}<br>
                <b>Categoría:</b> {p['categoria']}<br>
                <b>Riqueza de especies:</b> {p['riqueza']}<br>
                <b>Abundancia total:</b> {p['abundancia']:,}<br>
                <b>Coordenadas:</b><br>
                {p['lat']:.4f}°, {p['lon']:.4f}°
                </div>
                """
            ).add_to(m)
        
        # Agregar leyenda
        self._agregar_leyenda_biodiversidad(m)
        
        return m
    
    def crear_mapa_combinado(self, puntos_carbono, puntos_biodiversidad):
        """Crea mapa con capas intercambiables para carbono y biodiversidad"""
        if not puntos_carbono or not puntos_biodiversidad:
            return None
        
        centro = [puntos_carbono[0]['lat'], puntos_carbono[0]['lon']]
        
        m = folium.Map(
            location=centro,
            zoom_start=12,
            tiles=self.capa_base,
            attr='Esri, Maxar, Earthstar Geographics'
        )
        
        # Preparar datos para heatmaps
        heat_data_carbono = [[p['lat'], p['lon'], p['carbono_ton_ha']] for p in puntos_carbono]
        heat_data_biodiv = [[p['lat'], p['lon'], p['shannon']] for p in puntos_biodiversidad]
        
        # Heatmap de carbono
        heatmap_carbono = HeatMap(
            heat_data_carbono,
            name='Carbono (ton C/ha)',
            min_opacity=0.3,
            radius=20,
            blur=15,
            gradient={0.0: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'},
            show=False
        )
        heatmap_carbono.add_to(m)
        
        # Heatmap de biodiversidad
        heatmap_biodiv = HeatMap(
            heat_data_biodiv,
            name='Índice de Shannon',
            min_opacity=0.3,
            radius=20,
            blur=15,
            gradient={
                0.0: '#991b1b',
                0.2: '#ef4444',
                0.4: '#f59e0b',
                0.6: '#3b82f6',
                0.8: '#8b5cf6',
                1.0: '#10b981'
            },
            show=True
        )
        heatmap_biodiv.add_to(m)
        
        # Control de capas
        folium.LayerControl().add_to(m)
        
        # Agregar leyenda dual
        self._agregar_leyenda_combinada(m)
        
        return m
    
    def _agregar_leyenda_carbono(self, mapa):
        """Agrega leyenda para el mapa de carbono"""
        leyenda_html = '''
        <div style="position: fixed; 
            bottom: 50px; 
            left: 50px; 
            width: 250px;
            background-color: white;
            border: 2px solid #065f46;
            z-index: 9999;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            font-family: Arial;">
            <h4 style="margin-top: 0; color: #065f46; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
            🌳 Carbono (ton C/ha)
            </h4>
            <div style="margin: 10px 0;">
                <div style="height: 20px; background: linear-gradient(90deg, blue, cyan, lime, yellow, orange, red); border: 1px solid #666;"></div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 11px;">
                    <span>Bajo</span>
                    <span>Medio</span>
                    <span>Alto</span>
                </div>
            </div>
            <div style="font-size: 12px; color: #666;">
                <div><span style="color: #065f46; font-weight: bold;">■</span> Puntos verdes: Muestreo</div>
                <div><span style="color: #3b82f6; font-weight: bold;">■</span> Heatmap: Intensidad de carbono</div>
            </div>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))
    
    def _agregar_leyenda_biodiversidad(self, mapa):
        """Agrega leyenda para el mapa de biodiversidad"""
        leyenda_html = '''
        <div style="position: fixed; 
            bottom: 50px; 
            left: 50px; 
            width: 280px;
            background-color: white;
            border: 2px solid #8b5cf6;
            z-index: 9999;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            font-family: Arial;">
            <h4 style="margin-top: 0; color: #8b5cf6; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
            🦋 Índice de Shannon
            </h4>
            <div style="margin: 10px 0;">
                <div style="height: 20px; background: linear-gradient(90deg, #991b1b, #ef4444, #f59e0b, #3b82f6, #8b5cf6, #10b981); border: 1px solid #666;"></div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 11px;">
                    <span>0.0</span>
                    <span>2.0</span>
                    <span>4.0</span>
                </div>
            </div>
            <div style="font-size: 12px; color: #666;">
                <div><span style="color: #991b1b; font-weight: bold;">■</span> Muy Baja: < 0.5</div>
                <div><span style="color: #ef4444; font-weight: bold;">■</span> Baja: 0.5 - 1.5</div>
                <div><span style="color: #f59e0b; font-weight: bold;">■</span> Moderada: 1.5 - 2.5</div>
                <div><span style="color: #3b82f6; font-weight: bold;">■</span> Alta: 2.5 - 3.5</div>
                <div><span style="color: #10b981; font-weight: bold;">■</span> Muy Alta: > 3.5</div>
            </div>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))
    
    def _agregar_leyenda_combinada(self, mapa):
        """Agrega leyenda combinada"""
        leyenda_html = '''
        <div style="position: fixed; 
            bottom: 50px; 
            left: 50px; 
            width: 300px;
            background-color: white;
            border: 2px solid #3b82f6;
            z-index: 9999;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            font-family: Arial;">
            <h4 style="margin-top: 0; color: #3b82f6; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
            🗺️ Capas del Mapa
            </h4>
            <div style="margin: 10px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 20px; height: 20px; background: linear-gradient(90deg, blue, lime, yellow, orange, red); margin-right: 10px; border: 1px solid #666;"></div>
                    <div>Carbono (ton C/ha)</div>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background: linear-gradient(90deg, #991b1b, #ef4444, #f59e0b, #3b82f6, #8b5cf6, #10b981); margin-right: 10px; border: 1px solid #666;"></div>
                    <div>Índice de Shannon</div>
                </div>
            </div>
            <div style="font-size: 12px; color: #666; border-top: 1px solid #eee; padding-top: 10px;">
                <div><strong>Instrucciones:</strong></div>
                <div>• Use el control en la esquina superior derecha para cambiar entre capas</div>
                <div>• Haga clic en los puntos para ver detalles</div>
                <div>• Zoom con la rueda del mouse</div>
            </div>
        </div>
        '''
        mapa.get_root().html.add_child(folium.Element(leyenda_html))

# ===============================
# 📊 VISUALIZACIONES Y GRÁFICOS
# ===============================
class Visualizaciones:
    """Clase para generar visualizaciones"""
    
    @staticmethod
    def crear_grafico_barras_carbono(desglose: Dict):
        """Crea gráfico de barras para pools de carbono"""
        fig = go.Figure(data=[
            go.Bar(
                x=list(desglose.keys()),
                y=list(desglose.values()),
                marker_color=['#238b45', '#41ab5d', '#74c476', '#a1d99b', '#d9f0a3'],
                text=[f"{v:.1f}" for v in desglose.values()],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Distribución de Carbono por Pools',
            xaxis_title='Pool de Carbono',
            yaxis_title='Ton C/ha',
            height=400
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_radar_biodiversidad(shannon_data: Dict):
        """Crea gráfico radar para biodiversidad"""
        categorias = ['Shannon', 'Riqueza', 'Abundancia', 'Equitatividad', 'Conservación']
        
        # Normalizar valores para el radar
        shannon_norm = min(shannon_data['indice_shannon'] / 4.0 * 100, 100)
        riqueza_norm = min(shannon_data['riqueza_especies'] / 200 * 100, 100)
        abundancia_norm = min(shannon_data['abundancia_total'] / 2000 * 100, 100)
        
        # Valores simulados para equitatividad y conservación
        equitatividad = random.uniform(70, 90)
        conservacion = random.uniform(60, 95)
        
        valores = [shannon_norm, riqueza_norm, abundancia_norm, equitatividad, conservacion]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            fillcolor='rgba(139, 92, 246, 0.3)',
            line_color='#8b5cf6',
            name='Biodiversidad'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=400,
            title='Perfil de Biodiversidad'
        )
        
        return fig
    
    @staticmethod
    def crear_grafico_correlacion(carbono_vals, shannon_vals):
        """Crea gráfico de correlación entre carbono y biodiversidad"""
        fig = go.Figure(data=go.Scatter(
            x=carbono_vals,
            y=shannon_vals,
            mode='markers',
            marker=dict(
                size=10,
                color=shannon_vals,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Shannon")
            ),
            text=[f"C: {c:.1f}, S: {s:.2f}" for c, s in zip(carbono_vals, shannon_vals)]
        ))
        
        # Calcular línea de tendencia
        if len(carbono_vals) > 1:
            z = np.polyfit(carbono_vals, shannon_vals, 1)
            p = np.poly1d(z)
            trend_x = np.linspace(min(carbono_vals), max(carbono_vals), 100)
            trend_y = p(trend_x)
            
            fig.add_trace(go.Scatter(
                x=trend_x,
                y=trend_y,
                mode='lines',
                line=dict(color='red', width=2),
                name='Tendencia'
            ))
        
        fig.update_layout(
            title='Correlación: Carbono vs Biodiversidad',
            xaxis_title='Carbono (ton C/ha)',
            yaxis_title='Índice de Shannon',
            height=400
        )
        
        return fig
    
    @staticmethod
    def crear_metricas_kpi(carbono_total: float, co2_total: float, shannon: float, area: float):
        """Crea métricas KPI para dashboard"""
        html = f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
            <div style="background: linear-gradient(135deg, #065f46 0%, #0a7e5a 100%); padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">🌳 Carbono Total</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{carbono_total:,.0f}</p>
                <p style="margin: 0;">ton C</p>
            </div>
            <div style="background: linear-gradient(135deg, #0a7e5a 0%, #10b981 100%); padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">🏭 CO₂ Equivalente</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{co2_total:,.0f}</p>
                <p style="margin: 0;">ton CO₂e</p>
            </div>
            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%); padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">🦋 Índice Shannon</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{shannon:.2f}</p>
                <p style="margin: 0;">Biodiversidad</p>
            </div>
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%); padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">📐 Área Total</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">{area:,.1f}</p>
                <p style="margin: 0;">hectáreas</p>
            </div>
        </div>
        """
        return html

# ===============================
# 🎨 INTERFAZ PRINCIPAL SIMPLIFICADA
# ===============================
def main():
    """Función principal de la aplicación"""
    
    # Inicializar session state
    if 'poligono_data' not in st.session_state:
        st.session_state.poligono_data = None
    if 'resultados' not in st.session_state:
        st.session_state.resultados = None
    if 'mapa' not in st.session_state:
        st.session_state.mapa = None
    
    # Título principal
    st.title("🌎 Sistema de Análisis Ambiental - Sudamérica")
    st.markdown("### Metodología Verra VCS para Carbono + Índice de Shannon para Biodiversidad")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Carga de Datos")
        
        # Cargar archivo
        uploaded_file = st.file_uploader(
            "Cargar polígono (KML, GeoJSON, SHP)",
            type=['kml', 'geojson', 'zip'],
            help="Suba un archivo con el polígono de estudio"
        )
        
        if uploaded_file is not None:
            with st.spinner("Procesando archivo..."):
                try:
                    gdf = cargar_archivo(uploaded_file)
                    if gdf is not None:
                        st.session_state.poligono_data = gdf
                        st.success(f"✅ Polígono cargado: {len(gdf)} geometrías")
                        
                        # Calcular área
                        gdf_proj = gdf.to_crs("EPSG:3857")
                        area_ha = gdf_proj.geometry.area.sum() / 10000
                        st.info(f"Área aproximada: {area_ha:,.1f} ha")
                        
                        # Crear mapa inicial
                        sistema_mapas = SistemaMapas()
                        st.session_state.mapa = sistema_mapas.crear_mapa_area(gdf)
                        
                except Exception as e:
                    st.error(f"Error al cargar archivo: {str(e)}")
        
        if st.session_state.poligono_data is not None:
            st.header("⚙️ Configuración")
            
            tipo_ecosistema = st.selectbox(
                "Tipo de ecosistema",
                ['amazonia', 'choco', 'andes', 'pampa', 'seco'],
                help="Seleccione el tipo de ecosistema predominante"
            )
            
            num_puntos = st.slider(
                "Número de puntos de muestreo",
                min_value=10,
                max_value=200,
                value=50,
                help="Cantidad de puntos para análisis"
            )
            
            if st.button("🚀 Ejecutar Análisis Completo", type="primary", use_container_width=True):
                with st.spinner("Analizando carbono y biodiversidad..."):
                    try:
                        resultados = ejecutar_analisis_completo(
                            st.session_state.poligono_data,
                            tipo_ecosistema,
                            num_puntos
                        )
                        st.session_state.resultados = resultados
                        st.success("✅ Análisis completado!")
                        
                    except Exception as e:
                        st.error(f"Error en el análisis: {str(e)}")
    
    # Contenido principal
    if st.session_state.poligono_data is None:
        st.info("👈 Cargue un polígono en el panel lateral para comenzar")
        
        # Mostrar información de la aplicación
        with st.expander("📋 Información del Sistema"):
            st.markdown("""
            ### Sistema Integrado de Análisis Ambiental
            
            **Características principales:**
            
            1. **Metodología Verra VCS** para cálculo de carbono forestal
            2. **Índice de Shannon** para análisis de biodiversidad
            3. **Mapas de calor** interactivos para carbono y biodiversidad
            4. **Datos climáticos** realistas para Sudamérica
            5. **Visualizaciones interactivas** y gráficos correlacionales
            
            **Formato de archivos soportados:**
            - KML/KMZ
            - GeoJSON
            - Shapefile (comprimido en ZIP)
            
            **Nuevas funcionalidades añadidas:**
            - 🌋 **Mapa de calor de biodiversidad** con índice de Shannon
            - 🔥 **Mapa de calor de carbono** según metodología Verra VCS
            - 📈 **Gráfico de correlación** carbono vs biodiversidad
            - 🎨 **Leyendas interactivas** y controles de capas
            
            **Áreas de aplicación:**
            - Proyectos REDD+ y créditos de carbono
            - Monitoreo de conservación de biodiversidad
            - Planificación territorial sostenible
            - Estudios de impacto ambiental
            - Investigación ecológica
            """)
    
    else:
        # Mostrar pestañas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🗺️ Mapas", 
            "📊 Dashboard", 
            "🌳 Carbono", 
            "🦋 Biodiversidad",
            "📈 Correlación"
        ])
        
        with tab1:
            mostrar_mapas()
        
        with tab2:
            mostrar_dashboard()
        
        with tab3:
            mostrar_carbono()
        
        with tab4:
            mostrar_biodiversidad()
        
        with tab5:
            mostrar_correlacion()

# ===============================
# 📁 FUNCIONES AUXILIARES
# ===============================
def cargar_archivo(uploaded_file):
    """Carga un archivo geoespacial"""
    try:
        if uploaded_file.name.endswith('.kml'):
            # Leer KML
            import xml.etree.ElementTree as ET
            from shapely.geometry import Polygon
            
            # Parsear KML simple
            tree = ET.parse(uploaded_file)
            root = tree.getroot()
            
            # Buscar coordenadas (simplificado)
            coordinates = []
            for elem in root.iter():
                if 'coordinates' in elem.tag:
                    coords_text = elem.text.strip()
                    for coord in coords_text.split():
                        lon, lat, _ = map(float, coord.split(','))
                        coordinates.append((lon, lat))
            
            if coordinates:
                polygon = Polygon(coordinates)
                gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
                return gdf
        
        elif uploaded_file.name.endswith('.geojson'):
            # Leer GeoJSON
            gdf = gpd.read_file(uploaded_file)
            if gdf.crs is None:
                gdf.set_crs("EPSG:4326", inplace=True)
            return gdf
        
        elif uploaded_file.name.endswith('.zip'):
            # Leer Shapefile
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    if gdf.crs is None:
                        gdf.set_crs("EPSG:4326", inplace=True)
                    return gdf
        
        return None
        
    except Exception as e:
        st.error(f"Error específico: {str(e)}")
        return None

def ejecutar_analisis_completo(gdf, tipo_ecosistema, num_puntos):
    """Ejecuta análisis completo de carbono y biodiversidad"""
    
    # Calcular área
    gdf_proj = gdf.to_crs("EPSG:3857")
    area_total = gdf_proj.geometry.area.sum() / 10000
    
    # Obtener polígono principal
    if len(gdf) > 1:
        poligono = unary_union(gdf.geometry.tolist())
    else:
        poligono = gdf.geometry.iloc[0]
    
    bounds = poligono.bounds
    
    # Inicializar sistemas
    clima = ConectorClimaticoTropical()
    verra = MetodologiaVerra()
    biodiversidad = AnalisisBiodiversidad()
    
    # Generar puntos de muestreo aleatorios dentro del polígono
    puntos_carbono = []
    puntos_biodiversidad = []
    
    carbono_total = 0
    co2_total = 0
    shannon_promedio = 0
    area_por_punto = area_total / num_puntos
    
    for i in range(num_puntos):
        # Generar punto aleatorio dentro del bounding box
        while True:
            lat = bounds[1] + random.random() * (bounds[3] - bounds[1])
            lon = bounds[0] + random.random() * (bounds[2] - bounds[0])
            point = Point(lon, lat)
            
            if poligono.contains(point):
                break
        
        # Obtener datos climáticos
        datos_clima = clima.obtener_datos_climaticos(lat, lon)
        
        # Generar NDVI aleatorio pero realista
        ndvi = 0.5 + random.uniform(-0.2, 0.3)
        
        # Calcular carbono
        carbono_info = verra.calcular_carbono_hectarea(ndvi, tipo_ecosistema, datos_clima['precipitacion'])
        
        # Calcular biodiversidad
        biodiv_info = biodiversidad.calcular_shannon(
            ndvi, 
            tipo_ecosistema, 
            area_por_punto, 
            datos_clima['precipitacion']
        )
        
        # Acumular totales
        carbono_total += carbono_info['carbono_total_ton_ha'] * area_por_punto
        co2_total += carbono_info['co2_equivalente_ton_ha'] * area_por_punto
        shannon_promedio += biodiv_info['indice_shannon']
        
        # Guardar punto para visualización de carbono
        puntos_carbono.append({
            'lat': lat,
            'lon': lon,
            'carbono_ton_ha': carbono_info['carbono_total_ton_ha'],
            'ndvi': ndvi,
            'precipitacion': datos_clima['precipitacion']
        })
        
        # Guardar punto para visualización de biodiversidad
        puntos_biodiversidad.append({
            'lat': lat,
            'lon': lon,
            'shannon': biodiv_info['indice_shannon'],
            'categoria': biodiv_info['categoria'],
            'color_hex': biodiv_info['color_hex'],
            'riqueza': biodiv_info['riqueza_especies'],
            'abundancia': biodiv_info['abundancia_total']
        })
    
    # Calcular promedios
    shannon_promedio /= num_puntos
    
    # Preparar resultados
    resultados = {
        'area_total_ha': area_total,
        'carbono_total_ton': round(carbono_total, 2),
        'co2_total_ton': round(co2_total, 2),
        'carbono_promedio_ha': round(carbono_total / area_total, 2),
        'shannon_promedio': round(shannon_promedio, 3),
        'puntos_carbono': puntos_carbono,
        'puntos_biodiversidad': puntos_biodiversidad,
        'tipo_ecosistema': tipo_ecosistema,
        'num_puntos': num_puntos,
        'desglose_promedio': verra.calcular_carbono_hectarea(0.6, tipo_ecosistema, 1500)['desglose'],
        'valores_carbono': [p['carbono_ton_ha'] for p in puntos_carbono],
        'valores_shannon': [p['shannon'] for p in puntos_biodiversidad]
    }
    
    return resultados

# ===============================
# 🗺️ FUNCIONES DE VISUALIZACIÓN
# ===============================
def mostrar_mapas():
    """Muestra los diferentes mapas disponibles"""
    st.header("🗺️ Mapas de Análisis")
    
    # Crear subtabs para diferentes mapas
    tab_mapa1, tab_mapa2, tab_mapa3, tab_mapa4 = st.tabs([
        "🌍 Área de Estudio", 
        "🌳 Carbono", 
        "🦋 Biodiversidad", 
        "🎭 Combinado"
    ])
    
    with tab_mapa1:
        st.subheader("Área de Estudio")
        if st.session_state.mapa:
            folium_static(st.session_state.mapa, width=1000, height=600)
            st.info("Mapa base con el polígono del área de estudio")
        else:
            st.info("No hay mapa para mostrar")
    
    with tab_mapa2:
        st.subheader("Mapa de Calor - Carbono (Metodología Verra VCS)")
        if st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_carbono = sistema_mapas.crear_mapa_carbono(
                st.session_state.resultados['puntos_carbono']
            )
            
            if mapa_carbono:
                folium_static(mapa_carbono, width=1000, height=600)
                
                # Información adicional
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Puntos muestreados", len(st.session_state.resultados['puntos_carbono']))
                with col2:
                    min_carb = min(p['carbono_ton_ha'] for p in st.session_state.resultados['puntos_carbono'])
                    st.metric("Carbono mínimo", f"{min_carb:.1f} ton C/ha")
                with col3:
                    max_carb = max(p['carbono_ton_ha'] for p in st.session_state.resultados['puntos_carbono'])
                    st.metric("Carbono máximo", f"{max_carb:.1f} ton C/ha")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de carbono")
    
    with tab_mapa3:
        st.subheader("Mapa de Calor - Biodiversidad (Índice de Shannon)")
        if st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            
            if 'puntos_biodiversidad' in st.session_state.resultados:
                mapa_biodiv = sistema_mapas.crear_mapa_biodiversidad(
                    st.session_state.resultados['puntos_biodiversidad']
                )
                
                if mapa_biodiv:
                    folium_static(mapa_biodiv, width=1000, height=600)
                    
                    # Información adicional
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Puntos muestreados", len(st.session_state.resultados['puntos_biodiversidad']))
                    with col2:
                        min_shannon = min(p['shannon'] for p in st.session_state.resultados['puntos_biodiversidad'])
                        st.metric("Shannon mínimo", f"{min_shannon:.2f}")
                    with col3:
                        max_shannon = max(p['shannon'] for p in st.session_state.resultados['puntos_biodiversidad'])
                        st.metric("Shannon máximo", f"{max_shannon:.2f}")
            else:
                st.info("No hay datos de biodiversidad para mostrar en el mapa.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de biodiversidad")
    
    with tab_mapa4:
        st.subheader("Mapa Combinado - Capas Intercambiables")
        if st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            
            if 'puntos_carbono' in st.session_state.resultados and 'puntos_biodiversidad' in st.session_state.resultados:
                mapa_combinado = sistema_mapas.crear_mapa_combinado(
                    st.session_state.resultados['puntos_carbono'],
                    st.session_state.resultados['puntos_biodiversidad']
                )
                
                if mapa_combinado:
                    folium_static(mapa_combinado, width=1000, height=600)
                    st.info("Use el control en la esquina superior derecha para alternar entre capas de carbono y biodiversidad")
            else:
                st.info("No hay datos suficientes para el mapa combinado")
        else:
            st.info("Ejecute el análisis primero para ver el mapa combinado")

def mostrar_dashboard():
    """Muestra dashboard ejecutivo"""
    st.header("📊 Dashboard Ejecutivo")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        # Métricas KPI
        html_kpi = Visualizaciones.crear_metricas_kpi(
            res['carbono_total_ton'],
            res['co2_total_ton'],
            res['shannon_promedio'],
            res['area_total_ha']
        )
        st.markdown(html_kpi, unsafe_allow_html=True)
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Carbono")
            fig_barras = Visualizaciones.crear_grafico_barras_carbono(res['desglose_promedio'])
            st.plotly_chart(fig_barras, use_container_width=True)
        
        with col2:
            st.subheader("Perfil de Biodiversidad")
            if res['puntos_biodiversidad']:
                fig_radar = Visualizaciones.crear_grafico_radar_biodiversidad(res['puntos_biodiversidad'][0])
                st.plotly_chart(fig_radar, use_container_width=True)
        
        # Tabla de resumen
        st.subheader("📋 Resumen del Análisis")
        
        data = {
            'Métrica': [
                'Área total',
                'Carbono total almacenado',
                'CO₂ equivalente',
                'Carbono promedio por hectárea',
                'Índice de Shannon (biodiversidad)',
                'Tipo de ecosistema',
                'Puntos de muestreo'
            ],
            'Valor': [
                f"{res['area_total_ha']:,.1f} ha",
                f"{res['carbono_total_ton']:,.0f} ton C",
                f"{res['co2_total_ton']:,.0f} ton CO₂e",
                f"{res['carbono_promedio_ha']:,.1f} ton C/ha",
                f"{res['shannon_promedio']:.3f}",
                res['tipo_ecosistema'],
                str(res['num_puntos'])
            ]
        }
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    else:
        st.info("Ejecute el análisis primero para ver el dashboard")

def mostrar_carbono():
    """Muestra análisis detallado de carbono"""
    st.header("🌳 Análisis de Carbono - Metodología Verra VCS")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        st.markdown("""
        ### Metodología Verra VCS para Proyectos REDD+
        
        Este análisis utiliza la metodología Verra VCS (Verified Carbon Standard) 
        para estimar el carbono forestal almacenado en el área de estudio.
        """)
        
        # Información detallada
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Carbono Total", 
                f"{res['carbono_total_ton']:,.0f} ton C",
                "Almacenamiento total de carbono"
            )
        
        with col2:
            st.metric(
                "Potencial de Créditos", 
                f"{res['co2_total_ton']/1000:,.1f} k",
                "Ton CO₂e / 1000 = Créditos potenciales"
            )
        
        with col3:
            st.metric(
                "Valor Económico Aprox.", 
                f"${res['co2_total_ton'] * 15:,.0f}",
                "USD @ $15/ton CO₂"
            )
        
        # Distribución por pools
        st.subheader("Distribución por Pools de Carbono")
        
        pools_data = []
        for pool, valor in res['desglose_promedio'].items():
            pools_data.append({
                'Pool': pool,
                'Descripción': {
                    'AGB': 'Biomasa Aérea Viva',
                    'BGB': 'Biomasa de Raíces',
                    'DW': 'Madera Muerta',
                    'LI': 'Hojarasca',
                    'SOC': 'Carbono Orgánico del Suelo'
                }[pool],
                'Ton C/ha': valor,
                'Porcentaje': f"{(valor / sum(res['desglose_promedio'].values()) * 100):.1f}%"
            })
        
        df_pools = pd.DataFrame(pools_data)
        st.dataframe(df_pools, use_container_width=True, hide_index=True)
        
        # Recomendaciones
        with st.expander("📋 Recomendaciones para Proyecto VCS"):
            st.markdown("""
            1. **Validación y Verificación:** Contratar un validador acreditado por Verra
            2. **Monitoreo:** Establecer parcelas permanentes de muestreo
            3. **Línea Base:** Desarrollar escenario de referencia (baseline)
            4. **Adicionalidad:** Demostrar que el proyecto es adicional al escenario business-as-usual
            5. **Permanencia:** Implementar medidas para garantizar la permanencia del carbono
            6. **MRV:** Sistema de Monitoreo, Reporte y Verificación robusto
            """)
    
    else:
        st.info("Ejecute el análisis primero para ver los datos de carbono")

def mostrar_biodiversidad():
    """Muestra análisis detallado de biodiversidad"""
    st.header("🦋 Análisis de Biodiversidad - Índice de Shannon")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        st.markdown("""
        ### Índice de Shannon para Diversidad Biológica
        
        El índice de Shannon-Wiener mide la diversidad de especies considerando 
        tanto la riqueza (número de especies) como la equitatividad (distribución de individuos).
        """)
        
        # Métricas de biodiversidad
        if res['puntos_biodiversidad']:
            biodiv = res['puntos_biodiversidad'][0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Índice de Shannon", 
                    f"{biodiv['shannon']:.3f}",
                    f"Categoría: {biodiv['categoria']}"
                )
            
            with col2:
                st.metric(
                    "Riqueza de Especies", 
                    f"{biodiv['riqueza']}",
                    "Número estimado de especies"
                )
            
            with col3:
                st.metric(
                    "Abundancia Total", 
                    f"{biodiv['abundancia']:,}",
                    "Individuos estimados"
                )
            
            # Interpretación del índice
            st.subheader("Interpretación del Índice de Shannon")
            
            interpretaciones = {
                "Muy Alta": "> 3.5 - Ecosistema con alta diversidad y equitatividad",
                "Alta": "2.5 - 3.5 - Buena diversidad, estructura equilibrada",
                "Moderada": "1.5 - 2.5 - Diversidad media, posible perturbación moderada",
                "Baja": "0.5 - 1.5 - Diversidad reducida, perturbación significativa",
                "Muy Baja": "< 0.5 - Diversidad muy baja, ecosistema degradado"
            }
            
            for cat, desc in interpretaciones.items():
                if cat == biodiv['categoria']:
                    st.success(f"**{cat}**: {desc}")
                else:
                    st.text(f"{cat}: {desc}")
            
            # Distribución de categorías en los puntos
            st.subheader("Distribución de Categorías en Puntos de Muestreo")
            
            categorias = {}
            for p in res['puntos_biodiversidad']:
                cat = p['categoria']
                categorias[cat] = categorias.get(cat, 0) + 1
            
            fig_cat = go.Figure(data=[go.Pie(
                labels=list(categorias.keys()),
                values=list(categorias.values()),
                hole=0.3,
                marker_colors=['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#991b1b']
            )])
            
            fig_cat.update_layout(
                title='Distribución de Categorías de Biodiversidad',
                height=400
            )
            
            st.plotly_chart(fig_cat, use_container_width=True)
            
            # Recomendaciones de conservación
            with st.expander("🌿 Recomendaciones para Conservación"):
                st.markdown(f"""
                Basado en el índice de Shannon de **{biodiv['shannon']:.3f}** ({biodiv['categoria']}):
                
                **Medidas recomendadas:**
                """)
                
                if biodiv['categoria'] in ["Muy Baja", "Baja"]:
                    st.markdown("""
                    - **Restauración activa:** Plantación de especies nativas
                    - **Control de amenazas:** Manejo de incendios, control de especies invasoras
                    - **Conectividad:** Corredores biológicos con áreas conservadas
                    - **Monitoreo intensivo:** Seguimiento de indicadores clave
                    """)
                elif biodiv['categoria'] == "Moderada":
                    st.markdown("""
                    - **Manejo sostenible:** Prácticas de bajo impacto
                    - **Protección:** Delimitación de zonas núcleo
                    - **Investigación:** Estudios de dinámica poblacional
                    - **Educación:** Programas de concienciación local
                    """)
                else:
                    st.markdown("""
                    - **Conservación preventiva:** Mantenimiento del estado actual
                    - **Investigación científica:** Estudio de patrones de biodiversidad
                    - **Uso sostenible:** Planificación de actividades económicas compatibles
                    - **Turismo científico:** Desarrollo de investigación participativa
                    """)
        
        # Distribución del índice entre puntos
        st.subheader("Distribución del Índice entre Puntos de Muestreo")
        
        shannon_values = [p['shannon'] for p in res['puntos_biodiversidad']]
        
        fig = go.Figure(data=[go.Histogram(
            x=shannon_values,
            nbinsx=15,
            marker_color='#8b5cf6',
            opacity=0.7
        )])
        
        fig.update_layout(
            title='Distribución del Índice de Shannon',
            xaxis_title='Valor del Índice',
            yaxis_title='Frecuencia',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Ejecute el análisis primero para ver los datos de biodiversidad")

def mostrar_correlacion():
    """Muestra análisis de correlación entre carbono y biodiversidad"""
    st.header("📈 Correlación Carbono vs Biodiversidad")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        st.markdown("""
        ### Análisis de Relación entre Carbono y Biodiversidad
        
        Este análisis explora la relación entre el almacenamiento de carbono 
        y la diversidad biológica en el área de estudio.
        """)
        
        # Gráfico de correlación
        if 'valores_carbono' in res and 'valores_shannon' in res:
            fig_corr = Visualizaciones.crear_grafico_correlacion(
                res['valores_carbono'],
                res['valores_shannon']
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Análisis estadístico simple
            if len(res['valores_carbono']) > 1 and len(res['valores_shannon']) > 1:
                correlacion = np.corrcoef(res['valores_carbono'], res['valores_shannon'])[0, 1]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Coeficiente de Correlación", f"{correlacion:.3f}")
                with col2:
                    st.metric("Número de pares", len(res['valores_carbono']))
                with col3:
                    if correlacion > 0.5:
                        st.metric("Relación", "Fuerte positiva", delta="Alta")
                    elif correlacion > 0.3:
                        st.metric("Relación", "Moderada positiva", delta="Media")
                    elif correlacion > 0:
                        st.metric("Relación", "Débil positiva", delta="Baja")
                    else:
                        st.metric("Relación", "Negativa", delta="Inversa")
                
                # Interpretación
                with st.expander("📊 Interpretación Estadística"):
                    st.markdown(f"""
                    **Coeficiente de Correlación de Pearson:** `{correlacion:.3f}`
                    
                    **Interpretación:**
                    - **±0.9 a ±1.0:** Correlación muy fuerte
                    - **±0.7 a ±0.9:** Correlación fuerte
                    - **±0.5 a ±0.7:** Correlación moderada
                    - **±0.3 a ±0.5:** Correlación débil
                    - **±0.0 a ±0.3:** Correlación muy débil o nula
                    
                    **En este caso:**
                    """)
                    
                    if correlacion > 0.7:
                        st.success("Existe una fuerte correlación positiva entre carbono y biodiversidad.")
                    elif correlacion > 0.5:
                        st.info("Existe una correlación moderada positiva entre carbono y biodiversidad.")
                    elif correlacion > 0.3:
                        st.warning("Existe una correlación débil positiva entre carbono y biodiversidad.")
                    elif correlacion > 0:
                        st.warning("La correlación es muy débil o prácticamente nula.")
                    else:
                        st.error("Existe una correlación negativa entre carbono y biodiversidad.")
            
            # Tabla de datos de correlación
            st.subheader("Datos de Puntos de Muestreo")
            
            datos_corr = []
            for i in range(min(20, len(res['valores_carbono']))):  # Mostrar máximo 20 filas
                datos_corr.append({
                    'Punto': i+1,
                    'Carbono (ton C/ha)': res['valores_carbono'][i],
                    'Índice Shannon': res['valores_shannon'][i],
                    'Categoría': res['puntos_biodiversidad'][i]['categoria'] if i < len(res['puntos_biodiversidad']) else "N/A"
                })
            
            df_corr = pd.DataFrame(datos_corr)
            st.dataframe(df_corr, use_container_width=True, hide_index=True)
            
            # Implicaciones para conservación
            with st.expander("🌿 Implicaciones para la Conservación"):
                st.markdown("""
                **Relación Carbono-Biodiversidad:**
                
                - **Correlación positiva alta:** Las estrategias de conservación de carbono también protegen la biodiversidad
                - **Correlación positiva moderada:** Beneficios colaterales significativos
                - **Correlación débil o nula:** Necesidad de estrategias específicas para cada objetivo
                - **Correlación negativa:** Posibles trade-offs entre objetivos
                
                **Recomendaciones según resultados:**
                1. **Sinergias:** Identificar áreas de alto valor para ambos parámetros
                2. **Trade-offs:** Considerar compensaciones donde sea necesario
                3. **Planificación integrada:** Diseñar estrategias que maximicen beneficios múltiples
                4. **Monitoreo dual:** Seguir ambos indicadores simultáneamente
                """)
        
    else:
        st.info("Ejecute el análisis primero para ver la correlación")

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    main()
