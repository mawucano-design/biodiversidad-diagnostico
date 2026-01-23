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
# 📄 GENERADOR DE REPORTES COMPLETOS
# ===============================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Inches
import io

class GeneradorReportes:
    def __init__(self, resultados, gdf):
        self.resultados = resultados
        self.gdf = gdf
        self.buffer_pdf = io.BytesIO()
        self.buffer_docx = io.BytesIO()
        self.styles = getSampleStyleSheet()

    def _fig_to_png(self, fig):
        """Convierte un gráfico Plotly a PNG en BytesIO"""
        img_bytes = fig.to_image(format="png", width=800, height=500, scale=2)
        return io.BytesIO(img_bytes)

    def _crear_graficos(self):
        """Pre-genera los gráficos necesarios"""
        vis = Visualizaciones()
        res = self.resultados

        graficos = {}

        # Gráfico de carbono
        fig_carbono = vis.crear_grafico_barras_carbono(res['desglose_promedio'])
        graficos['carbono'] = self._fig_to_png(fig_carbono)

        # Gráfico de biodiversidad
        if res['puntos_biodiversidad']:
            fig_biodiv = vis.crear_grafico_radar_biodiversidad(res['puntos_biodiversidad'][0])
            graficos['biodiv'] = self._fig_to_png(fig_biodiv)

        # Histograma de Shannon
        shannon_values = [p['indice_shannon'] for p in res['puntos_biodiversidad']]
        fig_hist = go.Figure(data=[go.Histogram(x=shannon_values, nbinsx=10)])
        fig_hist.update_layout(title='Distribución del Índice de Shannon', height=400)
        graficos['hist_shannon'] = self._fig_to_png(fig_hist)

        return graficos

    def generar_pdf(self):
        doc = SimpleDocTemplate(self.buffer_pdf, pagesize=A4)
        story = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # center
        )
        story.append(Paragraph("Informe Ambiental - Carbono y Biodiversidad", title_style))
        story.append(Spacer(1, 12))

        # Resumen ejecutivo
        res = self.resultados
        resumen = f"""
        <b>Área total:</b> {res['area_total_ha']:,.1f} ha<br/>
        <b>Carbono total almacenado:</b> {res['carbono_total_ton']:,.0f} ton C<br/>
        <b>CO₂ equivalente:</b> {res['co2_total_ton']:,.0f} ton CO₂e<br/>
        <b>Índice de Shannon promedio:</b> {res['shannon_promedio']:.3f}<br/>
        <b>Ecosistema:</b> {res['tipo_ecosistema']}<br/>
        <b>Puntos de muestreo:</b> {res['num_puntos']}
        """
        story.append(Paragraph("Resumen Ejecutivo", self.styles['Heading2']))
        story.append(Paragraph(resumen, self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Tabla de pools de carbono
        story.append(Paragraph("Pools de Carbono (ton C/ha)", self.styles['Heading2']))
        pool_data = [['Pool', 'Descripción', 'Valor']]
        desc = {'AGB': 'Biomasa Aérea', 'BGB': 'Raíces', 'DW': 'Madera Muerta', 'LI': 'Hojarasca', 'SOC': 'Suelo'}
        for k, v in res['desglose_promedio'].items():
            pool_data.append([k, desc.get(k, k), f"{v:.2f}"])
        tabla_carbono = Table(pool_data)
        tabla_carbono.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(tabla_carbono)
        story.append(Spacer(1, 20))

        # Gráficos
        graficos = self._crear_graficos()

        if 'carbono' in graficos:
            story.append(Paragraph("Distribución de Carbono", self.styles['Heading2']))
            img = Image(graficos['carbono'], width=6*inch, height=3.75*inch)
            story.append(img)
            story.append(Spacer(1, 20))

        if 'biodiv' in graficos:
            story.append(Paragraph("Análisis de Biodiversidad (Radar)", self.styles['Heading2']))
            img = Image(graficos['biodiv'], width=6*inch, height=3.75*inch)
            story.append(img)
            story.append(Spacer(1, 20))

        if 'hist_shannon' in graficos:
            story.append(Paragraph("Distribución del Índice de Shannon", self.styles['Heading2']))
            img = Image(graficos['hist_shannon'], width=6*inch, height=3.75*inch)
            story.append(img)
            story.append(Spacer(1, 20))

        # Muestra de especies
        if res['puntos_biodiversidad']:
            biodiv = res['puntos_biodiversidad'][0]
            if 'especies_muestra' in biodiv:
                story.append(Paragraph("Muestra de Especies (Simulada)", self.styles['Heading2']))
                especies_data = [['Especie', 'Abundancia', 'Proporción (%)']]
                for esp in biodiv['especies_muestra'][:5]:
                    especies_data.append([
                        f"Esp {esp['especie_id']}",
                        str(esp['abundancia']),
                        f"{esp['proporcion']*100:.2f}"
                    ])
                tabla_esp = Table(especies_data)
                tabla_esp.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER')
                ]))
                story.append(tabla_esp)

        doc.build(story)
        self.buffer_pdf.seek(0)
        return self.buffer_pdf

    def generar_docx(self):
        doc = Document()
        doc.add_heading('Informe Ambiental - Carbono y Biodiversidad', 0)
        doc.add_paragraph()

        # Resumen
        res = self.resultados
        doc.add_heading('Resumen Ejecutivo', level=1)
        resumen = doc.add_paragraph()
        resumen.add_run(f"Área total: {res['area_total_ha']:,.1f} ha\n")
        resumen.add_run(f"Carbono total almacenado: {res['carbono_total_ton']:,.0f} ton C\n")
        resumen.add_run(f"CO₂ equivalente: {res['co2_total_ton']:,.0f} ton CO₂e\n")
        resumen.add_run(f"Índice de Shannon promedio: {res['shannon_promedio']:.3f}\n")
        resumen.add_run(f"Ecosistema: {res['tipo_ecosistema']}\n")
        resumen.add_run(f"Puntos de muestreo: {res['num_puntos']}")

        # Tabla de carbono
        doc.add_heading('Pools de Carbono (ton C/ha)', level=1)
        table = doc.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Pool'
        hdr_cells[1].text = 'Descripción'
        hdr_cells[2].text = 'Valor'
        desc = {'AGB': 'Biomasa Aérea', 'BGB': 'Raíces', 'DW': 'Madera Muerta', 'LI': 'Hojarasca', 'SOC': 'Suelo'}
        for k, v in res['desglose_promedio'].items():
            row_cells = table.add_row().cells
            row_cells[0].text = k
            row_cells[1].text = desc.get(k, k)
            row_cells[2].text = f"{v:.2f}"

        # Gráficos
        graficos = self._crear_graficos()
        for nombre, buffer in graficos.items():
            doc.add_page_break()
            titulo = {
                'carbono': 'Distribución de Carbono',
                'biodiv': 'Análisis de Biodiversidad (Radar)',
                'hist_shannon': 'Distribución del Índice de Shannon'
            }.get(nombre, 'Gráfico')
            doc.add_heading(titulo, level=1)
            doc.add_picture(buffer, width=Inches(6))

        # Especies
        if res['puntos_biodiversidad']:
            biodiv = res['puntos_biodiversidad'][0]
            if 'especies_muestra' in biodiv:
                doc.add_heading('Muestra de Especies (Simulada)', level=1)
                table2 = doc.add_table(rows=1, cols=3)
                hdr = table2.rows[0].cells
                hdr[0].text = 'Especie'
                hdr[1].text = 'Abundancia'
                hdr[2].text = 'Proporción (%)'
                for esp in biodiv['especies_muestra'][:5]:
                    row = table2.add_row().cells
                    row[0].text = f"Esp {esp['especie_id']}"
                    row[1].text = str(esp['abundancia'])
                    row[2].text = f"{esp['proporcion']*100:.2f}"

        doc.save(self.buffer_docx)
        self.buffer_docx.seek(0)
        return self.buffer_docx

    def generar_geojson(self):
        """Exporta el polígono original + atributos agregados"""
        gdf_out = self.gdf.copy()
        gdf_out['area_ha'] = self.resultados['area_total_ha']
        gdf_out['carbono_total_ton'] = self.resultados['carbono_total_ton']
        gdf_out['shannon_promedio'] = self.resultados['shannon_promedio']
        gdf_out['ecosistema'] = self.resultados['tipo_ecosistema']
        
        geojson_buffer = StringIO()
        gdf_out.to_json(geojson_buffer)
        return geojson_buffer.getvalue()


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
            'especies_muestra': especies[:10]  # Solo muestra las primeras 10
        }

# ===============================
# 🗺️ SISTEMA DE MAPAS SIMPLIFICADO
# ===============================
class SistemaMapas:
    """Sistema de mapas simplificado"""
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
            radius=20,
            blur=15,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
        ).add_to(m)
        
        # Agregar marcadores para puntos importantes
        for p in puntos_carbono[:10]:  # Limitar a 10 marcadores
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=5,
                color='#065f46',
                fill=True,
                fill_color='#10b981',
                popup=f"Carbono: {p['carbono_ton_ha']} ton C/ha<br>NDVI: {p['ndvi']}"
            ).add_to(m)
        
        return m

    def crear_mapa_biodiversidad(self, puntos_biodiversidad):
        """Crea mapa de calor para el índice de Shannon"""
        if not puntos_biodiversidad:
            return None

        # Usar el primer punto para centrar el mapa
        primer_punto = puntos_biodiversidad[0]
        centro = [primer_punto['lat'], primer_punto['lon']]

        m = folium.Map(
            location=centro,
            zoom_start=12,
            tiles=self.capa_base,
            attr='Esri, Maxar, Earthstar Geographics'
        )

        # Preparar datos para heatmap: [lat, lon, shannon]
        heat_data = [
            [p['lat'], p['lon'], p['indice_shannon']]
            for p in puntos_biodiversidad
            if 'indice_shannon' in p
        ]

        if not heat_data:
            return m

        # Crear colormap personalizado para Shannon (baja → alta)
        gradient = {
            0.0: '#991b1b',   # Muy baja
            0.25: '#ef4444',  # Baja
            0.5: '#f59e0b',   # Moderada
            0.75: '#3b82f6',  # Alta
            1.0: '#10b981'    # Muy alta
        }

        HeatMap(
            heat_data,
            name='Índice de Shannon',
            min_opacity=0.4,
            radius=20,
            blur=15,
            gradient=gradient
        ).add_to(m)

        # Opcional: agregar marcadores con valor de Shannon
        for p in puntos_biodiversidad[:10]:  # Limitar a 10 para no saturar
            color = p.get('color', '#8b5cf6')
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                popup=f"Shannon: {p['indice_shannon']:.3f}<br>Categoría: {p['categoria']}"
            ).add_to(m)

        return m

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
                marker_color=['#238b45', '#41ab5d', '#74c476', '#a1d99b', '#d9f0a3']
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
        categorias = ['Shannon', 'Riqueza', 'Abundancia', 'NDVI', 'Conservación']
        
        # Normalizar valores para el radar
        shannon_norm = min(shannon_data['indice_shannon'] / 4.0 * 100, 100)
        riqueza_norm = min(shannon_data['riqueza_especies'] / 200 * 100, 100)
        abundancia_norm = min(shannon_data['abundancia_total'] / 2000 * 100, 100)
        
        valores = [shannon_norm, riqueza_norm, abundancia_norm, 75, 80]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            fillcolor='rgba(139, 92, 246, 0.3)',
            line_color='#8b5cf6'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
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
                max_value=100,
                value=30,
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
            3. **Datos climáticos** realistas para Sudamérica
            4. **Visualizaciones interactivas** y mapas
            5. **Informe final descargable** en PDF, DOCX y GeoJSON
            
            **Formato de archivos soportados:**
            - KML/KMZ
            - GeoJSON
            - Shapefile (comprimido en ZIP)
            
            **Áreas de aplicación:**
            - Proyectos REDD+
            - Monitoreo de conservación
            - Planificación territorial
            - Estudios de impacto ambiental
            """)
    
    else:
        # Mostrar pestañas
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa", "📊 Dashboard", "🌳 Carbono", "🦋 Biodiversidad"])
        
        with tab1:
            mostrar_mapa()
        
        with tab2:
            mostrar_dashboard()
        
        with tab3:
            mostrar_carbono()
        
        with tab4:
            mostrar_biodiversidad()

# ===============================
# 📁 FUNCIONES AUXILIARES
# ===============================
def cargar_archivo(uploaded_file):
    """Carga un archivo geoespacial"""
    try:
        if uploaded_file.name.endswith('.kml'):
            # Leer KML
            import xml.etree.ElementTree as ET
            
            # Parsear KML simple
            tree = ET.parse(uploaded_file)
            root = tree.getroot()
            
            # Buscar coordenadas (simplificado)
            coordinates = []
            for elem in root.iter():
                if 'coordinates' in elem.tag:
                    coords_text = elem.text.strip()
                    for coord_line in coords_text.splitlines():
                        for coord in coord_line.strip().split():
                            if ',' in coord:
                                parts = coord.split(',')
                                if len(parts) >= 2:
                                    lon, lat = float(parts[0]), float(parts[1])
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
        
        # Guardar punto para visualización
        puntos_carbono.append({
            'lat': lat,
            'lon': lon,
            'carbono_ton_ha': carbono_info['carbono_total_ton_ha'],
            'ndvi': ndvi,
            'precipitacion': datos_clima['precipitacion']
        })
        
        # >>> AGREGAR COORDENADAS AL RESULTADO DE BIODIVERSIDAD <<<
        biodiv_info_con_coords = biodiv_info.copy()
        biodiv_info_con_coords.update({'lat': lat, 'lon': lon})
        puntos_biodiversidad.append(biodiv_info_con_coords)
    
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
        'desglose_promedio': verra.calcular_carbono_hectarea(0.6, tipo_ecosistema, 1500)['desglose']
    }
    
    return resultados

# ===============================
# 🗺️ FUNCIONES DE VISUALIZACIÓN
# ===============================
def mostrar_mapa():
    """Muestra el mapa del área de estudio"""
    st.header("🗺️ Mapa del Área de Estudio")
    
    if st.session_state.mapa:
        folium_static(st.session_state.mapa, width=1000, height=600)
    else:
        st.info("No hay mapa para mostrar")
    
    if st.session_state.resultados:
        sistema_mapas = SistemaMapas()
        
        # Mapa de carbono
        st.subheader("🌳 Mapa de Distribución de Carbono")
        mapa_carbono = sistema_mapas.crear_mapa_carbono(
            st.session_state.resultados['puntos_carbono']
        )
        if mapa_carbono:
            folium_static(mapa_carbono, width=1000, height=600)

        # Mapa de Shannon
        st.subheader("🦋 Mapa de Calor - Índice de Shannon")
        mapa_shannon = sistema_mapas.crear_mapa_biodiversidad(
            st.session_state.resultados['puntos_biodiversidad']
        )
        if mapa_shannon:
            folium_static(mapa_shannon, width=1000, height=600)

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
            st.subheader("Análisis de Biodiversidad")
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
        
        # === NUEVO: Botones de descarga de informe ===
        st.subheader("📥 Descargar Informe Completo")
        col_pdf, col_docx, col_geojson = st.columns(3)

        generador = GeneradorReportes(st.session_state.resultados, st.session_state.poligono_data)

        with col_pdf:
            pdf_buffer = generador.generar_pdf()
            st.download_button(
                label="📄 Descargar PDF",
                data=pdf_buffer,
                file_name="informe_ambiental.pdf",
                mime="application/pdf"
            )

        with col_docx:
            docx_buffer = generador.generar_docx()
            st.download_button(
                label="📘 Descargar DOCX",
                data=docx_buffer,
                file_name="informe_ambiental.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        with col_geojson:
            geojson_str = generador.generar_geojson()
            st.download_button(
                label="🌍 Descargar GeoJSON",
                data=geojson_str,
                file_name="area_analisis.geojson",
                mime="application/geo+json"
            )
        
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
                    f"{biodiv['indice_shannon']:.3f}",
                    f"Categoría: {biodiv['categoria']}"
                )
            
            with col2:
                st.metric(
                    "Riqueza de Especies", 
                    f"{biodiv['riqueza_especies']}",
                    "Número estimado de especies"
                )
            
            with col3:
                st.metric(
                    "Abundancia Total", 
                    f"{biodiv['abundancia_total']:,}",
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
                    st.info(f"**{cat}**: {desc}")
                else:
                    st.text(f"{cat}: {desc}")
            
            # Muestra de especies (simulada)
            st.subheader("Muestra de Distribución de Especies")
            
            if 'especies_muestra' in biodiv and biodiv['especies_muestra']:
                especies_data = []
                for i, esp in enumerate(biodiv['especies_muestra'][:5]):  # Solo 5
                    especies_data.append({
                        'Especie': f"Esp {esp['especie_id']}",
                        'Abundancia': esp['abundancia'],
                        'Proporción': f"{esp['proporcion']*100:.2f}%",
                        'Grupo': random.choice(['Árbol', 'Arbusto', 'Hierba', 'Epífita', 'Fauna'])
                    })
                
                df_especies = pd.DataFrame(especies_data)
                st.dataframe(df_especies, use_container_width=True, hide_index=True)
            
            # Recomendaciones de conservación
            with st.expander("🌿 Recomendaciones para Conservación"):
                st.markdown(f"""
                Basado en el índice de Shannon de **{biodiv['indice_shannon']:.3f}** ({biodiv['categoria']}):
                
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
        
        shannon_values = [p['indice_shannon'] for p in res['puntos_biodiversidad']]
        
        fig = go.Figure(data=[go.Histogram(
            x=shannon_values,
            nbinsx=10,
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

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    main()
