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
from io import BytesIO, StringIO
from datetime import datetime, timedelta
import json
import base64
import warnings
import requests
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
# 📄 GENERADOR DE REPORTES COMPLETOS
# ===============================
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTPDF_AVAILABLE = True
except ImportError:
    REPORTPDF_AVAILABLE = False
    st.warning("ReportLab no está instalado. La generación de PDFs estará limitada.")

try:
    from docx import Document
    from docx.shared import Inches
    REPORTDOCX_AVAILABLE = True
except ImportError:
    REPORTDOCX_AVAILABLE = False
    st.warning("python-docx no está instalado. La generación de DOCX estará limitada.")

class GeneradorReportes:
    def __init__(self, resultados, gdf):
        self.resultados = resultados
        self.gdf = gdf
        self.buffer_pdf = BytesIO()
        self.buffer_docx = BytesIO()
        
    def _fig_to_png(self, fig):
        """Convierte un gráfico Plotly a PNG en BytesIO"""
        try:
            if fig is None:
                return None
            img_bytes = fig.to_image(format="png", width=800, height=500, scale=2)
            return BytesIO(img_bytes)
        except Exception as e:
            st.warning(f"No se pudo convertir el gráfico a PNG: {str(e)}")
            return None

    def _crear_graficos(self):
        """Pre-genera los gráficos necesarios"""
        vis = Visualizaciones()
        res = self.resultados

        graficos = {}

        # Gráfico de carbono
        if 'desglose_promedio' in res and res['desglose_promedio']:
            fig_carbono = vis.crear_grafico_barras_carbono(res['desglose_promedio'])
            graficos['carbono'] = self._fig_to_png(fig_carbono)

        # Gráfico de biodiversidad
        if 'puntos_biodiversidad' in res and res['puntos_biodiversidad']:
            if len(res['puntos_biodiversidad']) > 0:
                fig_biodiv = vis.crear_grafico_radar_biodiversidad(res['puntos_biodiversidad'][0])
                graficos['biodiv'] = self._fig_to_png(fig_biodiv)

        return graficos

    def generar_pdf(self):
        """Genera reporte en PDF"""
        if not REPORTPDF_AVAILABLE:
            st.error("ReportLab no está instalado. No se puede generar PDF.")
            return None
        
        try:
            doc = SimpleDocTemplate(self.buffer_pdf, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()

            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1
            )
            story.append(Paragraph("Informe Ambiental - Carbono y Biodiversidad", title_style))
            story.append(Spacer(1, 12))

            # Resumen ejecutivo
            res = self.resultados
            resumen = f"""
            <b>Área total:</b> {res.get('area_total_ha', 0):,.1f} ha<br/>
            <b>Carbono total almacenado:</b> {res.get('carbono_total_ton', 0):,.0f} ton C<br/>
            <b>CO₂ equivalente:</b> {res.get('co2_total_ton', 0):,.0f} ton CO₂e<br/>
            <b>Índice de Shannon promedio:</b> {res.get('shannon_promedio', 0):.3f}<br/>
            <b>Ecosistema:</b> {res.get('tipo_ecosistema', 'N/A')}<br/>
            <b>Puntos de muestreo:</b> {res.get('num_puntos', 0)}
            """
            story.append(Paragraph("Resumen Ejecutivo", styles['Heading2']))
            story.append(Paragraph(resumen, styles['Normal']))
            story.append(Spacer(1, 20))

            doc.build(story)
            self.buffer_pdf.seek(0)
            return self.buffer_pdf
        except Exception as e:
            st.error(f"Error generando PDF: {str(e)}")
            return None

    def generar_docx(self):
        """Genera reporte en DOCX"""
        if not REPORTDOCX_AVAILABLE:
            st.error("python-docx no está instalado. No se puede generar DOCX.")
            return None
        
        try:
            doc = Document()
            doc.add_heading('Informe Ambiental - Carbono y Biodiversidad', 0)
            doc.add_paragraph()

            # Resumen
            res = self.resultados
            doc.add_heading('Resumen Ejecutivo', level=1)
            doc.add_paragraph(f"Área total: {res.get('area_total_ha', 0):,.1f} ha")
            doc.add_paragraph(f"Carbono total almacenado: {res.get('carbono_total_ton', 0):,.0f} ton C")
            doc.add_paragraph(f"CO₂ equivalente: {res.get('co2_total_ton', 0):,.0f} ton CO₂e")
            doc.add_paragraph(f"Índice de Shannon promedio: {res.get('shannon_promedio', 0):.3f}")
            doc.add_paragraph(f"Ecosistema: {res.get('tipo_ecosistema', 'N/A')}")
            doc.add_paragraph(f"Puntos de muestreo: {res.get('num_puntos', 0)}")

            doc.save(self.buffer_docx)
            self.buffer_docx.seek(0)
            return self.buffer_docx
        except Exception as e:
            st.error(f"Error generando DOCX: {str(e)}")
            return None

    def generar_geojson(self):
        """Exporta el polígono original + atributos agregados"""
        try:
            gdf_out = self.gdf.copy()
            res = self.resultados
            
            if res:
                gdf_out['area_ha'] = res.get('area_total_ha', 0)
                gdf_out['carbono_total_ton'] = res.get('carbono_total_ton', 0)
                gdf_out['shannon_promedio'] = res.get('shannon_promedio', 0)
                gdf_out['ecosistema'] = res.get('tipo_ecosistema', 'N/A')
            
            geojson_str = gdf_out.to_json()
            return geojson_str
        except Exception as e:
            st.error(f"Error generando GeoJSON: {str(e)}")
            return json.dumps({"error": str(e)})

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
            abundancia = int((abundancia_total / max(riqueza_especies, 1)) * random.lognormvariate(0, 0.5))
            if abundancia > 0:
                especies.append({'especie_id': i+1, 'abundancia': abundancia})
                abundancia_acumulada += abundancia
        
        # Normalizar abundancias
        for especie in especies:
            especie['proporcion'] = especie['abundancia'] / abundancia_acumulada if abundancia_acumulada > 0 else 0
        
        # Calcular índice de Shannon
        shannon = 0
        for especie in especies:
            if especie['proporcion'] > 0:
                shannon -= especie['proporcion'] * math.log(especie['proporcion'])
        
        # Categorías de biodiversidad según Shannon
        if shannon > 3.5:
            categoria = "Muy Alta"
            color = "#10b981"
        elif shannon > 2.5:
            categoria = "Alta"
            color = "#3b82f6"
        elif shannon > 1.5:
            categoria = "Moderada"
            color = "#f59e0b"
        elif shannon > 0.5:
            categoria = "Baja"
            color = "#ef4444"
        else:
            categoria = "Muy Baja"
            color = "#991b1b"
        
        return {
            'indice_shannon': round(shannon, 3),
            'categoria': categoria,
            'color': color,
            'riqueza_especies': riqueza_especies,
            'abundancia_total': abundancia_acumulada,
            'especies_muestra': especies[:10]
        }

# ===============================
# 🗺️ SISTEMA DE MAPAS COMPLETO CON TODOS LOS HEATMAPS
# ===============================
class SistemaMapas:
    """Sistema de mapas completo con todos los heatmaps"""
    def __init__(self):
        self.capa_base = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    
    def crear_mapa_area(self, gdf):
        """Crea mapa básico con el área de estudio"""
        if gdf is None or gdf.empty:
            return None
        
        try:
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
        except Exception as e:
            st.warning(f"Error al crear mapa: {str(e)}")
            return None
    
    def crear_mapa_calor_carbono(self, puntos_carbono):
        """Crea mapa de calor para carbono"""
        if not puntos_carbono or len(puntos_carbono) == 0:
            return None
        
        try:
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
            
            # Gradiente personalizado para carbono
            gradient_carbono = {
                0.0: 'blue',
                0.2: 'cyan',
                0.4: 'lime',
                0.6: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }
            
            # Agregar heatmap
            HeatMap(
                heat_data,
                name='Carbono (ton C/ha)',
                min_opacity=0.4,
                radius=25,
                blur=20,
                gradient=gradient_carbono
            ).add_to(m)
            
            # Agregar leyenda
            self._agregar_leyenda_carbono(m)
            
            # Agregar algunos marcadores para referencia
            for p in puntos_carbono[:10]:  # Limitar a 10 marcadores
                folium.CircleMarker(
                    location=[p['lat'], p['lon']],
                    radius=5,
                    color='#065f46',
                    fill=True,
                    fill_color='#10b981',
                    fill_opacity=0.7,
                    popup=f"Carbono: {p['carbono_ton_ha']:.1f} ton C/ha<br>NDVI: {p.get('ndvi', 'N/A'):.3f}"
                ).add_to(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de carbono: {str(e)}")
            return None
    
    def crear_mapa_calor_ndvi(self, puntos_ndvi):
        """Crea mapa de calor para NDVI"""
        if not puntos_ndvi or len(puntos_ndvi) == 0:
            return None
        
        try:
            # Calcular centro
            centro = [puntos_ndvi[0]['lat'], puntos_ndvi[0]['lon']]
            
            m = folium.Map(
                location=centro,
                zoom_start=12,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Preparar datos para heatmap
            heat_data = [[p['lat'], p['lon'], p['ndvi']] for p in puntos_ndvi]
            
            # Gradiente para NDVI (rojo = bajo, verde = alto)
            gradient_ndvi = {
                0.0: '#8b0000',  # Rojo oscuro
                0.2: '#ff4500',  # Rojo anaranjado
                0.4: '#ffd700',  # Amarillo
                0.6: '#9acd32',  # Amarillo verdoso
                0.8: '#32cd32',  # Verde lima
                1.0: '#006400'   # Verde oscuro
            }
            
            # Agregar heatmap
            HeatMap(
                heat_data,
                name='NDVI',
                min_opacity=0.5,
                radius=25,
                blur=20,
                gradient=gradient_ndvi
            ).add_to(m)
            
            # Agregar leyenda
            self._agregar_leyenda_ndvi(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de NDVI: {str(e)}")
            return None
    
    def crear_mapa_calor_ndwi(self, puntos_ndwi):
        """Crea mapa de calor para NDWI"""
        if not puntos_ndwi or len(puntos_ndwi) == 0:
            return None
        
        try:
            # Calcular centro
            centro = [puntos_ndwi[0]['lat'], puntos_ndwi[0]['lon']]
            
            m = folium.Map(
                location=centro,
                zoom_start=12,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Preparar datos para heatmap
            heat_data = [[p['lat'], p['lon'], p['ndwi']] for p in puntos_ndwi]
            
            # Gradiente para NDWI (marrón = seco, azul = húmedo)
            gradient_ndwi = {
                0.0: '#8b4513',  # Marrón
                0.2: '#d2691e',  # Marrón chocolate
                0.4: '#f4a460',  # Arena
                0.6: '#87ceeb',  # Azul claro
                0.8: '#1e90ff',  # Azul dodger
                1.0: '#00008b'   # Azul oscuro
            }
            
            # Agregar heatmap
            HeatMap(
                heat_data,
                name='NDWI',
                min_opacity=0.5,
                radius=25,
                blur=20,
                gradient=gradient_ndwi
            ).add_to(m)
            
            # Agregar leyenda
            self._agregar_leyenda_ndwi(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de NDWI: {str(e)}")
            return None
    
    def crear_mapa_calor_biodiversidad(self, puntos_biodiversidad):
        """Crea mapa de calor para biodiversidad (Índice de Shannon)"""
        if not puntos_biodiversidad or len(puntos_biodiversidad) == 0:
            return None
        
        try:
            # Calcular centro
            centro = [puntos_biodiversidad[0]['lat'], puntos_biodiversidad[0]['lon']]
            
            m = folium.Map(
                location=centro,
                zoom_start=12,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Preparar datos para heatmap
            heat_data = [[p['lat'], p['lon'], p['indice_shannon']] for p in puntos_biodiversidad]
            
            # Gradiente para biodiversidad
            gradient_biodiv = {
                0.0: '#991b1b',   # Rojo oscuro (muy baja)
                0.2: '#ef4444',   # Rojo (baja)
                0.4: '#f59e0b',   # Naranja (moderada)
                0.6: '#3b82f6',   # Azul (alta)
                0.8: '#8b5cf6',   # Púrpura (muy alta)
                1.0: '#10b981'    # Verde (excelente)
            }
            
            # Agregar heatmap
            HeatMap(
                heat_data,
                name='Índice de Shannon',
                min_opacity=0.5,
                radius=25,
                blur=20,
                gradient=gradient_biodiv
            ).add_to(m)
            
            # Agregar leyenda
            self._agregar_leyenda_biodiversidad(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de biodiversidad: {str(e)}")
            return None
    
    def crear_mapa_combinado(self, puntos_carbono, puntos_ndvi, puntos_ndwi, puntos_biodiversidad):
        """Crea mapa con todas las capas de heatmap"""
        if not puntos_carbono or len(puntos_carbono) == 0:
            return None
        
        try:
            # Calcular centro
            centro = [puntos_carbono[0]['lat'], puntos_carbono[0]['lon']]
            
            m = folium.Map(
                location=centro,
                zoom_start=12,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Agregar capas de heatmap (inicialmente ocultas)
            capas = {}
            
            # Capa de carbono
            if puntos_carbono and len(puntos_carbono) > 0:
                heat_data_carbono = [[p['lat'], p['lon'], p['carbono_ton_ha']] for p in puntos_carbono]
                capas['carbono'] = HeatMap(
                    heat_data_carbono,
                    name='🌳 Carbono',
                    min_opacity=0.4,
                    radius=20,
                    blur=15,
                    gradient={
                        0.0: 'blue', 0.2: 'cyan', 0.4: 'lime', 
                        0.6: 'yellow', 0.8: 'orange', 1.0: 'red'
                    },
                    show=False
                )
                capas['carbono'].add_to(m)
            
            # Capa de NDVI
            if puntos_ndvi and len(puntos_ndvi) > 0:
                heat_data_ndvi = [[p['lat'], p['lon'], p['ndvi']] for p in puntos_ndvi]
                capas['ndvi'] = HeatMap(
                    heat_data_ndvi,
                    name='📈 NDVI',
                    min_opacity=0.4,
                    radius=20,
                    blur=15,
                    gradient={
                        0.0: '#8b0000', 0.2: '#ff4500', 0.4: '#ffd700',
                        0.6: '#9acd32', 0.8: '#32cd32', 1.0: '#006400'
                    },
                    show=False
                )
                capas['ndvi'].add_to(m)
            
            # Capa de NDWI
            if puntos_ndwi and len(puntos_ndwi) > 0:
                heat_data_ndwi = [[p['lat'], p['lon'], p['ndwi']] for p in puntos_ndwi]
                capas['ndwi'] = HeatMap(
                    heat_data_ndwi,
                    name='💧 NDWI',
                    min_opacity=0.4,
                    radius=20,
                    blur=15,
                    gradient={
                        0.0: '#8b4513', 0.2: '#d2691e', 0.4: '#f4a460',
                        0.6: '#87ceeb', 0.8: '#1e90ff', 1.0: '#00008b'
                    },
                    show=False
                )
                capas['ndwi'].add_to(m)
            
            # Capa de biodiversidad
            if puntos_biodiversidad and len(puntos_biodiversidad) > 0:
                heat_data_biodiv = [[p['lat'], p['lon'], p['indice_shannon']] for p in puntos_biodiversidad]
                capas['biodiversidad'] = HeatMap(
                    heat_data_biodiv,
                    name='🦋 Biodiversidad',
                    min_opacity=0.4,
                    radius=20,
                    blur=15,
                    gradient={
                        0.0: '#991b1b', 0.2: '#ef4444', 0.4: '#f59e0b',
                        0.6: '#3b82f6', 0.8: '#8b5cf6', 1.0: '#10b981'
                    },
                    show=True  # Mostrar esta capa por defecto
                )
                capas['biodiversidad'].add_to(m)
            
            # Control de capas
            folium.LayerControl().add_to(m)
            
            # Agregar leyenda combinada
            self._agregar_leyenda_combinada(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa combinado: {str(e)}")
            return None
    
    def _agregar_leyenda_carbono(self, mapa):
        """Agrega leyenda para el mapa de carbono"""
        try:
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
        except:
            pass
    
    def _agregar_leyenda_ndvi(self, mapa):
        """Agrega leyenda para el mapa de NDVI"""
        try:
            leyenda_html = '''
            <div style="position: fixed; 
                bottom: 50px; 
                left: 50px; 
                width: 250px;
                background-color: white;
                border: 2px solid #32cd32;
                z-index: 9999;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
                font-family: Arial;">
                <h4 style="margin-top: 0; color: #32cd32; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
                📈 NDVI (Índice de Vegetación)
                </h4>
                <div style="margin: 10px 0;">
                    <div style="height: 20px; background: linear-gradient(90deg, #8b0000, #ff4500, #ffd700, #9acd32, #32cd32, #006400); border: 1px solid #666;"></div>
                    <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 11px;">
                        <span>-1.0</span>
                        <span>0.0</span>
                        <span>+1.0</span>
                    </div>
                </div>
                <div style="font-size: 12px; color: #666;">
                    <div><span style="color: #8b0000; font-weight: bold;">■</span> Rojo: Vegetación escasa/muerta</div>
                    <div><span style="color: #32cd32; font-weight: bold;">■</span> Verde: Vegetación densa/sana</div>
                </div>
            </div>
            '''
            mapa.get_root().html.add_child(folium.Element(leyenda_html))
        except:
            pass
    
    def _agregar_leyenda_ndwi(self, mapa):
        """Agrega leyenda para el mapa de NDWI"""
        try:
            leyenda_html = '''
            <div style="position: fixed; 
                bottom: 50px; 
                left: 50px; 
                width: 250px;
                background-color: white;
                border: 2px solid #1e90ff;
                z-index: 9999;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
                font-family: Arial;">
                <h4 style="margin-top: 0; color: #1e90ff; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
                💧 NDWI (Índice de Agua)
                </h4>
                <div style="margin: 10px 0;">
                    <div style="height: 20px; background: linear-gradient(90deg, #8b4513, #d2691e, #f4a460, #87ceeb, #1e90ff, #00008b); border: 1px solid #666;"></div>
                    <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 11px;">
                        <span>Seco</span>
                        <span>Húmedo</span>
                    </div>
                </div>
                <div style="font-size: 12px; color: #666;">
                    <div><span style="color: #8b4513; font-weight: bold;">■</span> Marrón: Superficie seca</div>
                    <div><span style="color: #1e90ff; font-weight: bold;">■</span> Azul: Presencia de agua</div>
                </div>
            </div>
            '''
            mapa.get_root().html.add_child(folium.Element(leyenda_html))
        except:
            pass
    
    def _agregar_leyenda_biodiversidad(self, mapa):
        """Agrega leyenda para el mapa de biodiversidad"""
        try:
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
        except:
            pass
    
    def _agregar_leyenda_combinada(self, mapa):
        """Agrega leyenda combinada"""
        try:
            leyenda_html = '''
            <div style="position: fixed; 
                bottom: 50px; 
                left: 50px; 
                width: 320px;
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
                        <div style="width: 20px; height: 20px; background: linear-gradient(90deg, blue, cyan, lime, yellow, orange, red); margin-right: 10px; border: 1px solid #666;"></div>
                        <div>🌳 Carbono (ton C/ha)</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 20px; height: 20px; background: linear-gradient(90deg, #8b0000, #ff4500, #ffd700, #9acd32, #32cd32, #006400); margin-right: 10px; border: 1px solid #666;"></div>
                        <div>📈 NDVI</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 20px; height: 20px; background: linear-gradient(90deg, #8b4513, #d2691e, #f4a460, #87ceeb, #1e90ff, #00008b); margin-right: 10px; border: 1px solid #666;"></div>
                        <div>💧 NDWI</div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background: linear-gradient(90deg, #991b1b, #ef4444, #f59e0b, #3b82f6, #8b5cf6, #10b981); margin-right: 10px; border: 1px solid #666;"></div>
                        <div>🦋 Índice de Shannon</div>
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
        except:
            pass

# ===============================
# 📊 VISUALIZACIONES Y GRÁFICOS
# ===============================
class Visualizaciones:
    """Clase para generar visualizaciones"""
    
    @staticmethod
    def crear_grafico_barras_carbono(desglose: Dict):
        """Crea gráfico de barras para pools de carbono"""
        if not desglose:
            # Crear gráfico vacío
            fig = go.Figure()
            fig.update_layout(
                title='No hay datos de carbono disponibles',
                height=400
            )
            return fig
        
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
        if not shannon_data:
            # Crear gráfico vacío
            fig = go.Figure()
            fig.update_layout(
                title='No hay datos de biodiversidad disponibles',
                height=400
            )
            return fig
        
        categorias = ['Shannon', 'Riqueza', 'Abundancia', 'Equitatividad', 'Conservación']
        
        try:
            # Normalizar valores para el radar
            shannon_norm = min(shannon_data.get('indice_shannon', 0) / 4.0 * 100, 100)
            riqueza_norm = min(shannon_data.get('riqueza_especies', 0) / 200 * 100, 100)
            abundancia_norm = min(shannon_data.get('abundancia_total', 0) / 2000 * 100, 100)
            
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
        except Exception as e:
            # Gráfico de respaldo
            fig = go.Figure()
            fig.update_layout(
                title='Error al generar gráfico de biodiversidad',
                height=400
            )
            return fig
    
    @staticmethod
    def crear_grafico_comparativo(puntos_carbono, puntos_ndvi, puntos_ndwi, puntos_biodiversidad):
        """Crea gráfico comparativo de todas las variables"""
        if not puntos_carbono or not puntos_ndvi:
            return None
        
        try:
            # Tomar los primeros 50 puntos para no saturar
            n = min(50, len(puntos_carbono))
            
            # Crear subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Carbono vs NDVI', 'Carbono vs NDWI', 
                              'Shannon vs NDVI', 'Shannon vs NDWI'),
                vertical_spacing=0.15,
                horizontal_spacing=0.15
            )
            
            # Carbono vs NDVI
            carbono_vals = [p['carbono_ton_ha'] for p in puntos_carbono[:n]]
            ndvi_vals = [p['ndvi'] for p in puntos_ndvi[:n]]
            
            fig.add_trace(
                go.Scatter(
                    x=ndvi_vals,
                    y=carbono_vals,
                    mode='markers',
                    marker=dict(color='#10b981', size=8),
                    name='Carbono-NDVI'
                ),
                row=1, col=1
            )
            
            # Carbono vs NDWI
            ndwi_vals = [p['ndwi'] for p in puntos_ndwi[:n]]
            fig.add_trace(
                go.Scatter(
                    x=ndwi_vals,
                    y=carbono_vals,
                    mode='markers',
                    marker=dict(color='#3b82f6', size=8),
                    name='Carbono-NDWI'
                ),
                row=1, col=2
            )
            
            # Shannon vs NDVI
            shannon_vals = [p['indice_shannon'] for p in puntos_biodiversidad[:n]]
            fig.add_trace(
                go.Scatter(
                    x=ndvi_vals,
                    y=shannon_vals,
                    mode='markers',
                    marker=dict(color='#8b5cf6', size=8),
                    name='Shannon-NDVI'
                ),
                row=2, col=1
            )
            
            # Shannon vs NDWI
            fig.add_trace(
                go.Scatter(
                    x=ndwi_vals,
                    y=shannon_vals,
                    mode='markers',
                    marker=dict(color='#f59e0b', size=8),
                    name='Shannon-NDWI'
                ),
                row=2, col=2
            )
            
            # Actualizar layout
            fig.update_layout(
                height=700,
                showlegend=True,
                title_text="Comparación de Variables Ambientales"
            )
            
            # Actualizar ejes
            fig.update_xaxes(title_text="NDVI", row=1, col=1)
            fig.update_yaxes(title_text="Carbono (ton C/ha)", row=1, col=1)
            
            fig.update_xaxes(title_text="NDWI", row=1, col=2)
            fig.update_yaxes(title_text="Carbono (ton C/ha)", row=1, col=2)
            
            fig.update_xaxes(title_text="NDVI", row=2, col=1)
            fig.update_yaxes(title_text="Índice de Shannon", row=2, col=1)
            
            fig.update_xaxes(title_text="NDWI", row=2, col=2)
            fig.update_yaxes(title_text="Índice de Shannon", row=2, col=2)
            
            return fig
        except Exception as e:
            return None
    
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
    st.title("🌎 Sistema Satelital de Análisis Ambiental")
    st.markdown("### Metodología Verra VCS + Índice de Shannon + Análisis Multiespectral")
    
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
                with st.spinner("Analizando carbono, biodiversidad e índices espectrales..."):
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
            ### Sistema Integrado de Análisis Ambiental Satelital
            
            **Características principales:**
            
            1. **🌳 Metodología Verra VCS** para cálculo de carbono forestal
            2. **🦋 Índice de Shannon** para análisis de biodiversidad
            3. **📈 NDVI** (Índice de Vegetación de Diferencia Normalizada)
            4. **💧 NDWI** (Índice de Agua de Diferencia Normalizada)
            5. **🗺️ Mapas de calor** interactivos para todas las variables
            6. **📊 Visualizaciones comparativas** y análisis correlacionales
            
            **Variables analizadas:**
            - **Carbono almacenado** (ton C/ha)
            - **Biodiversidad** (Índice de Shannon)
            - **Salud vegetal** (NDVI: -1 a +1)
            - **Contenido de agua** (NDWI: -1 a +1)
            
            **Áreas de aplicación:**
            - Proyectos REDD+ y créditos de carbono
            - Monitoreo de conservación de biodiversidad
            - Detección de estrés hídrico en vegetación
            - Identificación de áreas prioritarias para conservación
            - Estudios de impacto ambiental integrales
            """)
    
    else:
        # Mostrar pestañas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🗺️ Mapas de Calor", 
            "📊 Dashboard", 
            "🌳 Carbono", 
            "🦋 Biodiversidad",
            "📈 Comparación"
        ])
        
        with tab1:
            mostrar_mapas_calor()
        
        with tab2:
            mostrar_dashboard()
        
        with tab3:
            mostrar_carbono()
        
        with tab4:
            mostrar_biodiversidad()
        
        with tab5:
            mostrar_comparacion()

# ===============================
# 📁 FUNCIONES AUXILIARES
# ===============================
def cargar_archivo(uploaded_file):
    """Carga un archivo geoespacial"""
    try:
        if uploaded_file.name.endswith('.kml'):
            # Para KML simple
            content = uploaded_file.read().decode('utf-8')
            
            # Buscar coordenadas
            import re
            coordinates = re.findall(r'<coordinates>(.*?)</coordinates>', content, re.DOTALL)
            
            if coordinates:
                coords_text = coordinates[0].strip()
                points = []
                for coord in coords_text.split():
                    parts = coord.split(',')
                    if len(parts) >= 2:
                        lon, lat = float(parts[0]), float(parts[1])
                        points.append((lon, lat))
                
                if len(points) >= 3:
                    polygon = Polygon(points)
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
        
        # Si no se pudo cargar, crear un polígono de prueba
        st.warning("No se pudo leer el archivo correctamente. Usando polígono de prueba.")
        polygon = Polygon([
            (-64.0, -34.0),
            (-63.5, -34.0),
            (-63.5, -34.5),
            (-64.0, -34.5),
            (-64.0, -34.0)
        ])
        gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
        return gdf
        
    except Exception as e:
        st.error(f"Error al cargar archivo: {str(e)}")
        # Crear un polígono de prueba por defecto
        polygon = Polygon([
            (-64.0, -34.0),
            (-63.5, -34.0),
            (-63.5, -34.5),
            (-64.0, -34.5),
            (-64.0, -34.0)
        ])
        gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
        return gdf

def ejecutar_analisis_completo(gdf, tipo_ecosistema, num_puntos):
    """Ejecuta análisis completo de carbono, biodiversidad e índices espectrales"""
    
    try:
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
        
        # Generar puntos de muestreo
        puntos_carbono = []
        puntos_biodiversidad = []
        puntos_ndvi = []
        puntos_ndwi = []
        
        carbono_total = 0
        co2_total = 0
        shannon_promedio = 0
        ndvi_promedio = 0
        ndwi_promedio = 0
        area_por_punto = max(area_total / num_puntos, 0.1)
        
        puntos_generados = 0
        max_intentos = num_puntos * 10
        
        while puntos_generados < num_puntos and len(puntos_carbono) < max_intentos:
            # Generar punto aleatorio
            lat = bounds[1] + random.random() * (bounds[3] - bounds[1])
            lon = bounds[0] + random.random() * (bounds[2] - bounds[0])
            point = Point(lon, lat)
            
            if poligono.contains(point):
                # Obtener datos climáticos
                datos_clima = clima.obtener_datos_climaticos(lat, lon)
                
                # Generar NDVI aleatorio pero realista
                ndvi = 0.5 + random.uniform(-0.2, 0.3)
                
                # Generar NDWI basado en precipitación y ubicación
                # NDWI típicamente entre -1 y 1, positivo indica presencia de agua
                base_ndwi = 0.1
                if datos_clima['precipitacion'] > 2000:
                    base_ndwi += 0.3
                elif datos_clima['precipitacion'] < 800:
                    base_ndwi -= 0.2
                
                ndwi = base_ndwi + random.uniform(-0.2, 0.2)
                ndwi = max(-0.5, min(0.8, ndwi))  # Mantener en rango razonable
                
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
                ndvi_promedio += ndvi
                ndwi_promedio += ndwi
                
                # Guardar puntos para carbono
                puntos_carbono.append({
                    'lat': lat,
                    'lon': lon,
                    'carbono_ton_ha': carbono_info['carbono_total_ton_ha'],
                    'ndvi': ndvi,
                    'precipitacion': datos_clima['precipitacion']
                })
                
                # Guardar puntos para biodiversidad
                biodiv_info['lat'] = lat
                biodiv_info['lon'] = lon
                puntos_biodiversidad.append(biodiv_info)
                
                # Guardar puntos para NDVI
                puntos_ndvi.append({
                    'lat': lat,
                    'lon': lon,
                    'ndvi': ndvi
                })
                
                # Guardar puntos para NDWI
                puntos_ndwi.append({
                    'lat': lat,
                    'lon': lon,
                    'ndwi': ndwi
                })
                
                puntos_generados += 1
        
        # Calcular promedios
        if puntos_generados > 0:
            shannon_promedio /= puntos_generados
            ndvi_promedio /= puntos_generados
            ndwi_promedio /= puntos_generados
        
        # Obtener desglose promedio de carbono
        carbono_promedio = verra.calcular_carbono_hectarea(ndvi_promedio, tipo_ecosistema, 1500)
        
        # Preparar resultados
        resultados = {
            'area_total_ha': area_total,
            'carbono_total_ton': round(carbono_total, 2),
            'co2_total_ton': round(co2_total, 2),
            'carbono_promedio_ha': round(carbono_total / area_total, 2) if area_total > 0 else 0,
            'shannon_promedio': round(shannon_promedio, 3),
            'ndvi_promedio': round(ndvi_promedio, 3),
            'ndwi_promedio': round(ndwi_promedio, 3),
            'puntos_carbono': puntos_carbono,
            'puntos_biodiversidad': puntos_biodiversidad,
            'puntos_ndvi': puntos_ndvi,
            'puntos_ndwi': puntos_ndwi,
            'tipo_ecosistema': tipo_ecosistema,
            'num_puntos': puntos_generados,
            'desglose_promedio': carbono_promedio['desglose'] if carbono_promedio else {}
        }
        
        return resultados
    except Exception as e:
        st.error(f"Error en ejecutar_analisis_completo: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# ===============================
# 🗺️ FUNCIONES DE VISUALIZACIÓN
# ===============================
def mostrar_mapas_calor():
    """Muestra todos los mapas de calor disponibles"""
    st.header("🗺️ Mapas de Calor - Análisis Multivariable")
    
    # CORREGIDO: Ahora hay 6 tabs y 6 variables
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌍 Área de Estudio", 
        "🌳 Carbono", 
        "📈 NDVI", 
        "💧 NDWI", 
        "🦋 Biodiversidad",
        "🎭 Combinado"
    ])
    
    with tab1:
        st.subheader("Área de Estudio")
        if st.session_state.mapa:
            folium_static(st.session_state.mapa, width=1000, height=600)
            st.info("Mapa base con el polígono del área de estudio")
        else:
            st.info("No hay mapa para mostrar")
    
    with tab2:
        st.subheader("🌳 Mapa de Calor - Carbono (ton C/ha)")
        if st.session_state.resultados and 'puntos_carbono' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_carbono = sistema_mapas.crear_mapa_calor_carbono(
                st.session_state.resultados['puntos_carbono']
            )
            
            if mapa_carbono:
                folium_static(mapa_carbono, width=1000, height=600)
                
                # Información adicional
                col1, col2, col3 = st.columns(3)
                with col1:
                    carb_min = min(p['carbono_ton_ha'] for p in st.session_state.resultados['puntos_carbono'])
                    carb_max = max(p['carbono_ton_ha'] for p in st.session_state.resultados['puntos_carbono'])
                    st.metric("Carbono promedio", f"{st.session_state.resultados.get('carbono_promedio_ha', 0):.1f} ton C/ha")
                with col2:
                    st.metric("Rango", f"{carb_min:.1f} - {carb_max:.1f} ton C/ha")
                with col3:
                    st.metric("Puntos muestreados", len(st.session_state.resultados['puntos_carbono']))
            else:
                st.warning("No se pudo generar el mapa de carbono.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de carbono")
    
    with tab3:
        st.subheader("📈 Mapa de Calor - NDVI (Índice de Vegetación)")
        if st.session_state.resultados and 'puntos_ndvi' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_ndvi = sistema_mapas.crear_mapa_calor_ndvi(
                st.session_state.resultados['puntos_ndvi']
            )
            
            if mapa_ndvi:
                folium_static(mapa_ndvi, width=1000, height=600)
                
                # Información adicional
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NDVI promedio", f"{st.session_state.resultados.get('ndvi_promedio', 0):.3f}")
                with col2:
                    ndvi_vals = [p['ndvi'] for p in st.session_state.resultados['puntos_ndvi']]
                    st.metric("Rango NDVI", f"{min(ndvi_vals):.2f} - {max(ndvi_vals):.2f}")
                with col3:
                    # Interpretación NDVI
                    ndvi_avg = st.session_state.resultados.get('ndvi_promedio', 0)
                    if ndvi_avg > 0.6:
                        interpretacion = "🌿 Vegetación densa"
                    elif ndvi_avg > 0.3:
                        interpretacion = "🌱 Vegetación moderada"
                    else:
                        interpretacion = "🍂 Vegetación escasa"
                    st.metric("Interpretación", interpretacion)
            else:
                st.warning("No se pudo generar el mapa de NDVI.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de NDVI")
    
    with tab4:
        st.subheader("💧 Mapa de Calor - NDWI (Índice de Agua)")
        if st.session_state.resultados and 'puntos_ndwi' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_ndwi = sistema_mapas.crear_mapa_calor_ndwi(
                st.session_state.resultados['puntos_ndwi']
            )
            
            if mapa_ndwi:
                folium_static(mapa_ndwi, width=1000, height=600)
                
                # Información adicional
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NDWI promedio", f"{st.session_state.resultados.get('ndwi_promedio', 0):.3f}")
                with col2:
                    ndwi_vals = [p['ndwi'] for p in st.session_state.resultados['puntos_ndwi']]
                    st.metric("Rango NDWI", f"{min(ndwi_vals):.2f} - {max(ndwi_vals):.2f}")
                with col3:
                    # Interpretación NDWI
                    ndwi_avg = st.session_state.resultados.get('ndwi_promedio', 0)
                    if ndwi_avg > 0.2:
                        interpretacion = "💧 Húmedo"
                    elif ndwi_avg > -0.1:
                        interpretacion = "⚖️ Moderado"
                    else:
                        interpretacion = "🏜️ Seco"
                    st.metric("Humedad", interpretacion)
            else:
                st.warning("No se pudo generar el mapa de NDWI.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de NDWI")
    
    with tab5:
        st.subheader("🦋 Mapa de Calor - Biodiversidad (Índice de Shannon)")
        if st.session_state.resultados and 'puntos_biodiversidad' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_biodiv = sistema_mapas.crear_mapa_calor_biodiversidad(
                st.session_state.resultados['puntos_biodiversidad']
            )
            
            if mapa_biodiv:
                folium_static(mapa_biodiv, width=1000, height=600)
                
                # Información adicional
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Shannon promedio", f"{st.session_state.resultados.get('shannon_promedio', 0):.3f}")
                with col2:
                    shannon_vals = [p['indice_shannon'] for p in st.session_state.resultados['puntos_biodiversidad']]
                    st.metric("Rango Shannon", f"{min(shannon_vals):.2f} - {max(shannon_vals):.2f}")
                with col3:
                    if st.session_state.resultados['puntos_biodiversidad']:
                        categoria = st.session_state.resultados['puntos_biodiversidad'][0]['categoria']
                        st.metric("Categoría", categoria)
                    else:
                        st.metric("Categoría", "N/A")
            else:
                st.warning("No se pudo generar el mapa de biodiversidad.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de biodiversidad")
    
    with tab6:
        st.subheader("🎭 Mapa Combinado - Todas las Capas")
        if st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_combinado = sistema_mapas.crear_mapa_combinado(
                st.session_state.resultados.get('puntos_carbono', []),
                st.session_state.resultados.get('puntos_ndvi', []),
                st.session_state.resultados.get('puntos_ndwi', []),
                st.session_state.resultados.get('puntos_biodiversidad', [])
            )
            
            if mapa_combinado:
                folium_static(mapa_combinado, width=1000, height=600)
                st.info("📌 Use el control en la esquina superior derecha para alternar entre las diferentes capas de mapas de calor")
            else:
                st.warning("No se pudo generar el mapa combinado.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa combinado")

def mostrar_dashboard():
    """Muestra dashboard ejecutivo"""
    st.header("📊 Dashboard Ejecutivo")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        # Métricas KPI
        html_kpi = Visualizaciones.crear_metricas_kpi(
            res.get('carbono_total_ton', 0),
            res.get('co2_total_ton', 0),
            res.get('shannon_promedio', 0),
            res.get('area_total_ha', 0)
        )
        st.markdown(html_kpi, unsafe_allow_html=True)
        
        # Métricas adicionales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 NDVI promedio", f"{res.get('ndvi_promedio', 0):.3f}")
        with col2:
            st.metric("💧 NDWI promedio", f"{res.get('ndwi_promedio', 0):.3f}")
        with col3:
            st.metric("🎯 Puntos analizados", res.get('num_puntos', 0))
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Carbono")
            fig_barras = Visualizaciones.crear_grafico_barras_carbono(res.get('desglose_promedio', {}))
            if fig_barras:
                st.plotly_chart(fig_barras, use_container_width=True)
            else:
                st.info("No hay datos de carbono para graficar")
        
        with col2:
            st.subheader("Perfil de Biodiversidad")
            if res.get('puntos_biodiversidad') and len(res['puntos_biodiversidad']) > 0:
                fig_radar = Visualizaciones.crear_grafico_radar_biodiversidad(res['puntos_biodiversidad'][0])
                if fig_radar:
                    st.plotly_chart(fig_radar, use_container_width=True)
                else:
                    st.info("No hay datos de biodiversidad para graficar")
            else:
                st.info("No hay datos de biodiversidad disponibles")
        
        # Tabla de resumen
        st.subheader("📋 Resumen del Análisis")
        
        data = {
            'Métrica': [
                'Área total',
                'Carbono total almacenado',
                'CO₂ equivalente',
                'Carbono promedio por hectárea',
                'Índice de Shannon (biodiversidad)',
                'NDVI promedio (vegetación)',
                'NDWI promedio (agua)',
                'Tipo de ecosistema',
                'Puntos de muestreo'
            ],
            'Valor': [
                f"{res.get('area_total_ha', 0):,.1f} ha",
                f"{res.get('carbono_total_ton', 0):,.0f} ton C",
                f"{res.get('co2_total_ton', 0):,.0f} ton CO₂e",
                f"{res.get('carbono_promedio_ha', 0):,.1f} ton C/ha",
                f"{res.get('shannon_promedio', 0):.3f}",
                f"{res.get('ndvi_promedio', 0):.3f}",
                f"{res.get('ndwi_promedio', 0):.3f}",
                res.get('tipo_ecosistema', 'N/A'),
                str(res.get('num_puntos', 0))
            ]
        }
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botones de descarga
        st.subheader("📥 Descargar Informe Completo")
        
        if st.session_state.resultados and st.session_state.poligono_data is not None:
            generador = GeneradorReportes(st.session_state.resultados, st.session_state.poligono_data)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if REPORTPDF_AVAILABLE:
                    pdf_buffer = generador.generar_pdf()
                    if pdf_buffer:
                        st.download_button(
                            label="📄 Descargar PDF",
                            data=pdf_buffer,
                            file_name="informe_ambiental.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.info("PDF no disponible (instale ReportLab)")
            
            with col2:
                if REPORTDOCX_AVAILABLE:
                    docx_buffer = generador.generar_docx()
                    if docx_buffer:
                        st.download_button(
                            label="📘 Descargar DOCX",
                            data=docx_buffer,
                            file_name="informe_ambiental.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.info("DOCX no disponible (instale python-docx)")
            
            with col3:
                geojson_str = generador.generar_geojson()
                if geojson_str:
                    st.download_button(
                        label="🌍 Descargar GeoJSON",
                        data=geojson_str,
                        file_name="area_analisis.geojson",
                        mime="application/geo+json"
                    )
        else:
            st.info("No hay datos para generar informes")
        
    else:
        st.info("Ejecute el análisis primero para ver el dashboard")

def mostrar_carbono():
    """Muestra análisis detallado de carbono"""
    st.header("🌳 Análisis de Carbono - Metodología Verra VCS")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        st.markdown("### Metodología Verra VCS para Proyectos REDD+")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Carbono Total", 
                f"{res.get('carbono_total_ton', 0):,.0f} ton C",
                "Almacenamiento total de carbono"
            )
        
        with col2:
            st.metric(
                "Potencial de Créditos", 
                f"{res.get('co2_total_ton', 0)/1000:,.1f} k",
                "Ton CO₂e / 1000 = Créditos potenciales"
            )
        
        with col3:
            valor_economico = res.get('co2_total_ton', 0) * 15
            st.metric(
                "Valor Económico Aprox.", 
                f"${valor_economico:,.0f}",
                "USD @ $15/ton CO₂"
            )
        
        # Distribución por pools
        st.subheader("Distribución por Pools de Carbono")
        
        if res.get('desglose_promedio'):
            pools_data = []
            desc = {
                'AGB': 'Biomasa Aérea Viva',
                'BGB': 'Biomasa de Raíces',
                'DW': 'Madera Muerta',
                'LI': 'Hojarasca',
                'SOC': 'Carbono Orgánico del Suelo'
            }
            
            total = sum(res['desglose_promedio'].values())
            
            for pool, valor in res['desglose_promedio'].items():
                porcentaje = (valor / total * 100) if total > 0 else 0
                pools_data.append({
                    'Pool': pool,
                    'Descripción': desc.get(pool, pool),
                    'Ton C/ha': valor,
                    'Porcentaje': f"{porcentaje:.1f}%"
                })
            
            df_pools = pd.DataFrame(pools_data)
            st.dataframe(df_pools, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de desglose de carbono disponibles")
        
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
        
        st.markdown("### Índice de Shannon para Diversidad Biológica")
        
        if res.get('puntos_biodiversidad') and len(res['puntos_biodiversidad']) > 0:
            biodiv = res['puntos_biodiversidad'][0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Índice de Shannon", 
                    f"{biodiv.get('indice_shannon', 0):.3f}",
                    f"Categoría: {biodiv.get('categoria', 'N/A')}"
                )
            
            with col2:
                st.metric(
                    "Riqueza de Especies", 
                    f"{biodiv.get('riqueza_especies', 0)}",
                    "Número estimado de especies"
                )
            
            with col3:
                st.metric(
                    "Abundancia Total", 
                    f"{biodiv.get('abundancia_total', 0):,}",
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
            
            categoria_actual = biodiv.get('categoria', 'N/A')
            for cat, desc in interpretaciones.items():
                if cat == categoria_actual:
                    st.success(f"**{cat}**: {desc}")
                else:
                    st.text(f"{cat}: {desc}")
            
            # Distribución de categorías
            st.subheader("Distribución de Categorías en Puntos de Muestreo")
            
            if res.get('puntos_biodiversidad'):
                categorias = {}
                for p in res['puntos_biodiversidad']:
                    cat = p.get('categoria', 'Desconocida')
                    categorias[cat] = categorias.get(cat, 0) + 1
                
                if categorias:
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
                else:
                    st.info("No hay datos de categorías disponibles")
            
            # Distribución del índice
            st.subheader("Distribución del Índice entre Puntos de Muestreo")
            
            if res.get('puntos_biodiversidad'):
                shannon_values = [p.get('indice_shannon', 0) for p in res['puntos_biodiversidad']]
                
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
            
            # Recomendaciones
            with st.expander("🌿 Recomendaciones para Conservación"):
                st.markdown(f"""
                Basado en el índice de Shannon de **{biodiv.get('indice_shannon', 0):.3f}** ({biodiv.get('categoria', 'N/A')}):
                
                **Medidas recomendadas:**
                """)
                
                categoria = biodiv.get('categoria', '')
                if categoria in ["Muy Baja", "Baja"]:
                    st.markdown("""
                    - **Restauración activa:** Plantación de especies nativas
                    - **Control de amenazas:** Manejo de incendios, control de especies invasoras
                    - **Conectividad:** Corredores biológicos con áreas conservadas
                    - **Monitoreo intensivo:** Seguimiento de indicadores clave
                    """)
                elif categoria == "Moderada":
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
        else:
            st.info("No hay datos de biodiversidad disponibles")
    
    else:
        st.info("Ejecute el análisis primero para ver los datos de biodiversidad")

def mostrar_comparacion():
    """Muestra análisis comparativo de todas las variables"""
    st.header("📈 Análisis Comparativo - Relaciones entre Variables")
    
    if st.session_state.resultados:
        res = st.session_state.resultados
        
        st.markdown("### Relaciones entre Carbono, Biodiversidad e Índices Espectrales")
        
        # Gráfico comparativo
        if all(k in res for k in ['puntos_carbono', 'puntos_ndvi', 'puntos_ndwi', 'puntos_biodiversidad']):
            fig_comparativo = Visualizaciones.crear_grafico_comparativo(
                res['puntos_carbono'],
                res['puntos_ndvi'],
                res['puntos_ndwi'],
                res['puntos_biodiversidad']
            )
            
            if fig_comparativo:
                st.plotly_chart(fig_comparativo, use_container_width=True)
            else:
                st.info("No se pudo generar el gráfico comparativo")
        
        # Correlaciones
        st.subheader("🔗 Correlaciones entre Variables")
        
        if all(k in res for k in ['puntos_carbono', 'puntos_ndvi', 'puntos_ndwi', 'puntos_biodiversidad']):
            # Calcular correlaciones
            try:
                # Tomar hasta 100 puntos para no saturar
                n = min(100, len(res['puntos_carbono']))
                
                carbono_vals = [p['carbono_ton_ha'] for p in res['puntos_carbono'][:n]]
                ndvi_vals = [p['ndvi'] for p in res['puntos_ndvi'][:n]]
                ndwi_vals = [p['ndwi'] for p in res['puntos_ndwi'][:n]]
                shannon_vals = [p['indice_shannon'] for p in res['puntos_biodiversidad'][:n]]
                
                # Calcular coeficientes de correlación
                corr_carbono_ndvi = np.corrcoef(carbono_vals, ndvi_vals)[0, 1] if len(carbono_vals) > 1 else 0
                corr_carbono_shannon = np.corrcoef(carbono_vals, shannon_vals)[0, 1] if len(carbono_vals) > 1 else 0
                corr_ndvi_shannon = np.corrcoef(ndvi_vals, shannon_vals)[0, 1] if len(ndvi_vals) > 1 else 0
                corr_ndwi_shannon = np.corrcoef(ndwi_vals, shannon_vals)[0, 1] if len(ndwi_vals) > 1 else 0
                
                # Mostrar en métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Carbono vs NDVI", f"{corr_carbono_ndvi:.3f}", 
                             "Positiva" if corr_carbono_ndvi > 0 else "Negativa")
                
                with col2:
                    st.metric("Carbono vs Shannon", f"{corr_carbono_shannon:.3f}",
                             "Positiva" if corr_carbono_shannon > 0 else "Negativa")
                
                with col3:
                    st.metric("NDVI vs Shannon", f"{corr_ndvi_shannon:.3f}",
                             "Positiva" if corr_ndvi_shannon > 0 else "Negativa")
                
                with col4:
                    st.metric("NDWI vs Shannon", f"{corr_ndwi_shannon:.3f}",
                             "Positiva" if corr_ndwi_shannon > 0 else "Negativa")
                
                # Interpretación de correlaciones
                with st.expander("📊 Interpretación de las Correlaciones"):
                    st.markdown("""
                    **Guía de interpretación:**
                    - **±0.7 a ±1.0:** Correlación fuerte
                    - **±0.4 a ±0.7:** Correlación moderada
                    - **±0.1 a ±0.4:** Correlación débil
                    - **±0.0 a ±0.1:** Sin correlación significativa
                    
                    **Implicaciones para la conservación:**
                    - **Correlación positiva fuerte Carbono-Shannon:** Estrategias que conservan carbono también protegen biodiversidad
                    - **Correlación positiva NDVI-Shannon:** Áreas con vegetación saludable tienen mayor biodiversidad
                    - **Correlación positiva NDWI-Shannon:** Disponibilidad de agua favorece la biodiversidad
                    """)
                    
            except Exception as e:
                st.warning(f"No se pudieron calcular correlaciones: {str(e)}")
        
        # Resumen de relaciones
        st.subheader("📋 Resumen de Relaciones")
        
        with st.expander("🌳 Relación Carbono-Biodiversidad"):
            st.markdown("""
            **Sinergias Carbono-Biodiversidad:**
            
            - **Bosques maduros:** Alto carbono + alta biodiversidad
            - **Restauración:** Aumenta ambos simultáneamente
            - **Manejo sostenible:** Mantiene equilibrio entre ambos
            
            **Potenciales Trade-offs:**
            
            - **Plantaciones monoespecíficas:** Alto carbono, baja biodiversidad
            - **Bosques secundarios:** Bajo carbono, alta biodiversidad
            - **Áreas protegidas:** Bajo carbono (si no son maduras), alta biodiversidad
            """)
        
        with st.expander("📈 NDVI como Indicador de Salud Ecosistémica"):
            st.markdown("""
            **Interpretación de NDVI:**
            
            - **> 0.6:** Vegetación densa y saludable
            - **0.3 - 0.6:** Vegetación moderada
            - **0.1 - 0.3:** Vegetación escasa/degradada
            - **< 0.1:** Suelo desnudo/agua/zonas urbanas
            
            **Relación con otras variables:**
            
            - **NDVI alto →** Generalmente carbono alto + biodiversidad alta
            - **NDVI bajo →** Puede indicar degradación, incendios, deforestación
            - **Cambios en NDVI →** Alertas tempranas de disturbios
            """)
        
        with st.expander("💧 NDWI como Indicador de Disponibilidad Hídrica"):
            st.markdown("""
            **Interpretación de NDWI:**
            
            - **> 0.2:** Presencia significativa de agua
            - **0.0 - 0.2:** Humedad moderada
            - **-0.1 - 0.0:** Condiciones secas
            - **< -0.1:** Muy seco
            
            **Importancia ecológica:**
            
            - **NDWI alto →** Favorece biodiversidad, especialmente anfibios y aves acuáticas
            - **NDWI bajo →** Puede limitar biodiversidad, indicar estrés hídrico
            - **Variaciones estacionales →** Importantes para dinámica ecosistémica
            """)
    
    else:
        st.info("Ejecute el análisis primero para ver las comparaciones")

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    main()
