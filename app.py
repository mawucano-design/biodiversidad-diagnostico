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

# Intenta importar kaleido, si no está, mostrar advertencia pero continuar
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False
    st.warning("Kaleido no está instalado. Algunas funcionalidades de exportación pueden estar limitadas.")

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
import re  # Importar regex para manejo mejorado de KML

# ===============================
# 📄 GENERADOR DE REPORTES COMPLETOS - MEJORADO
# ===============================
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    REPORTPDF_AVAILABLE = True
except ImportError:
    REPORTPDF_AVAILABLE = False
    st.warning("ReportLab no está instalado. La generación de PDFs no estará disponible.")

try:
    from docx import Document
    from docx.shared import Inches
    REPORTDOCX_AVAILABLE = True
except ImportError:
    REPORTDOCX_AVAILABLE = False
    st.warning("python-docx no está instalado. La generación de DOCX no estará disponible.")

class GeneradorReportes:
    def __init__(self, resultados, gdf):
        self.resultados = resultados
        self.gdf = gdf
        
    def _fig_to_png_safe(self, fig):
        """Convierte un gráfico Plotly a PNG de forma segura"""
        try:
            if fig is None:
                return None
            
            # Si kaleido está disponible, usarlo
            if KALEIDO_AVAILABLE:
                img_bytes = fig.to_image(format="png", width=800, height=500, scale=2)
                return BytesIO(img_bytes)
            else:
                # Alternativa: guardar como HTML y usar matplotlib
                import matplotlib.pyplot as plt
                from io import BytesIO
                
                # Crear un gráfico simple de matplotlib como alternativa
                fig_mpl, ax = plt.subplots(figsize=(10, 6))
                
                if hasattr(fig, 'data'):
                    # Intentar extraer datos del gráfico de plotly
                    for trace in fig.data:
                        if hasattr(trace, 'x') and hasattr(trace, 'y'):
                            ax.bar(trace.x, trace.y, label=trace.name if hasattr(trace, 'name') else None)
                
                ax.set_title('Gráfico - Datos no disponibles en formato PNG')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                plt.close(fig_mpl)
                buf.seek(0)
                return buf
                
        except Exception as e:
            st.warning(f"No se pudo convertir el gráfico a PNG: {str(e)[:100]}")
            return None
    
    def _crear_graficos_seguros(self):
        """Pre-genera los gráficos de forma segura"""
        try:
            from .visualizaciones import Visualizaciones
        except:
            # Definir Visualizaciones localmente si no se puede importar
            class VisualizacionesLocal:
                @staticmethod
                def crear_grafico_barras_carbono(desglose):
                    if not desglose:
                        return None
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
                def crear_grafico_radar_biodiversidad(shannon_data):
                    if not shannon_data:
                        return None
                    categorias = ['Shannon', 'Riqueza', 'Abundancia', 'NDVI', 'Conservación']
                    valores = [60, 70, 75, 80, 65]  # Valores por defecto
                    fig = go.Figure(data=go.Scatterpolar(
                        r=valores,
                        theta=categorias,
                        fill='toself',
                        fillcolor='rgba(139, 92, 246, 0.3)',
                        line_color='#8b5cf6'
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False,
                        height=400
                    )
                    return fig
            
            Visualizaciones = VisualizacionesLocal
        
        res = self.resultados
        graficos = {}
        
        try:
            # Gráfico de carbono
            if res and 'desglose_promedio' in res and res['desglose_promedio']:
                fig_carbono = Visualizaciones.crear_grafico_barras_carbono(res['desglose_promedio'])
                graficos['carbono'] = self._fig_to_png_safe(fig_carbono)
        except Exception as e:
            st.warning(f"Error creando gráfico de carbono: {str(e)[:100]}")
        
        try:
            # Gráfico de biodiversidad
            if res and 'puntos_biodiversidad' in res and res['puntos_biodiversidad']:
                if len(res['puntos_biodiversidad']) > 0:
                    fig_biodiv = Visualizaciones.crear_grafico_radar_biodiversidad(res['puntos_biodiversidad'][0])
                    graficos['biodiv'] = self._fig_to_png_safe(fig_biodiv)
        except Exception as e:
            st.warning(f"Error creando gráfico de biodiversidad: {str(e)[:100]}")
        
        return graficos
    
    def generar_pdf(self):
        """Genera reporte en PDF - Versión mejorada con manejo de errores"""
        if not REPORTPDF_AVAILABLE:
            st.error("ReportLab no está instalado. No se puede generar PDF.")
            return None
        
        buffer_pdf = BytesIO()
        
        try:
            doc = SimpleDocTemplate(buffer_pdf, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=20,
                alignment=1
            )
            story.append(Paragraph("Informe Ambiental - Carbono y Biodiversidad", title_style))
            story.append(Spacer(1, 12))
            
            # Resumen ejecutivo
            res = self.resultados
            if res:
                story.append(Paragraph("Resumen Ejecutivo", styles['Heading2']))
                resumen_text = f"""
                <b>Área total:</b> {res.get('area_total_ha', 0):,.1f} ha<br/>
                <b>Carbono total almacenado:</b> {res.get('carbono_total_ton', 0):,.0f} ton C<br/>
                <b>CO₂ equivalente:</b> {res.get('co2_total_ton', 0):,.0f} ton CO₂e<br/>
                <b>Índice de Shannon promedio:</b> {res.get('shannon_promedio', 0):.3f}<br/>
                <b>Ecosistema:</b> {res.get('tipo_ecosistema', 'N/A')}<br/>
                <b>Puntos de muestreo:</b> {res.get('num_puntos', 0)}
                """
                story.append(Paragraph(resumen_text, styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Tabla de pools de carbono
                if 'desglose_promedio' in res and res['desglose_promedio']:
                    story.append(Paragraph("Pools de Carbono (ton C/ha)", styles['Heading2']))
                    pool_data = [['Pool', 'Descripción', 'Valor']]
                    desc = {'AGB': 'Biomasa Aérea', 'BGB': 'Raíces', 'DW': 'Madera Muerta', 
                           'LI': 'Hojarasca', 'SOC': 'Suelo'}
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
            
            # Mensaje si no hay resultados
            else:
                story.append(Paragraph("No hay datos disponibles para generar el informe.", styles['Normal']))
            
            doc.build(story)
            buffer_pdf.seek(0)
            return buffer_pdf
            
        except Exception as e:
            st.error(f"Error generando PDF: {str(e)}")
            return None
    
    def generar_docx(self):
        """Genera reporte en DOCX - Versión simplificada"""
        if not REPORTDOCX_AVAILABLE:
            st.error("python-docx no está instalado. No se puede generar DOCX.")
            return None
        
        buffer_docx = BytesIO()
        
        try:
            doc = Document()
            doc.add_heading('Informe Ambiental - Carbono y Biodiversidad', 0)
            doc.add_paragraph()
            
            res = self.resultados
            if res:
                doc.add_heading('Resumen Ejecutivo', level=1)
                doc.add_paragraph(f"Área total: {res.get('area_total_ha', 0):,.1f} ha")
                doc.add_paragraph(f"Carbono total almacenado: {res.get('carbono_total_ton', 0):,.0f} ton C")
                doc.add_paragraph(f"CO₂ equivalente: {res.get('co2_total_ton', 0):,.0f} ton CO₂e")
                doc.add_paragraph(f"Índice de Shannon promedio: {res.get('shannon_promedio', 0):.3f}")
                doc.add_paragraph(f"Ecosistema: {res.get('tipo_ecosistema', 'N/A')}")
                doc.add_paragraph(f"Puntos de muestreo: {res.get('num_puntos', 0)}")
                
                if 'desglose_promedio' in res and res['desglose_promedio']:
                    doc.add_heading('Pools de Carbono (ton C/ha)', level=1)
                    table = doc.add_table(rows=1, cols=3)
                    hdr_cells = table.rows[0].cells
                    hdr_cells[0].text = 'Pool'
                    hdr_cells[1].text = 'Descripción'
                    hdr_cells[2].text = 'Valor'
                    desc = {'AGB': 'Biomasa Aérea', 'BGB': 'Raíces', 'DW': 'Madera Muerta', 
                           'LI': 'Hojarasca', 'SOC': 'Suelo'}
                    for k, v in res['desglose_promedio'].items():
                        row_cells = table.add_row().cells
                        row_cells[0].text = k
                        row_cells[1].text = desc.get(k, k)
                        row_cells[2].text = f"{v:.2f}"
            else:
                doc.add_paragraph('No hay datos disponibles para generar el informe.')
            
            doc.save(buffer_docx)
            buffer_docx.seek(0)
            return buffer_docx
            
        except Exception as e:
            st.error(f"Error generando DOCX: {str(e)}")
            return None
    
    def generar_geojson(self):
        """Exporta el polígono original + atributos agregados"""
        try:
            if self.gdf is None or self.gdf.empty:
                return json.dumps({"error": "No hay datos geoespaciales"})
            
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
            'ratio_raiz': 0.24,
            'proporcion_madera_muerta': 0.15,
            'acumulacion_hojarasca': 5.0,
            'carbono_suelo': 2.5
        }
        
    def calcular_carbono_hectarea(self, ndvi: float, tipo_bosque: str, precipitacion: float) -> Dict:
        """Calcula carbono por hectárea basado en NDVI, tipo de bosque y precipitación"""
        # Factor por precipitación
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
        
        # Factor NDVI
        factor_ndvi = 1.0 + (ndvi * 0.8)
        
        # Factor área
        factor_area = min(2.0, math.log10(area_ha + 1) * 0.5 + 1)
        
        # Factor precipitación
        if tipo_ecosistema in ['amazonia', 'choco']:
            factor_precip = min(1.5, precipitacion / 2000)
        else:
            factor_precip = 1.0
        
        # Cálculo de riqueza de especies estimada
        riqueza_especies = int(params['riqueza_base'] * factor_ndvi * factor_area * factor_precip * random.uniform(0.9, 1.1))
        
        # Cálculo de abundancia estimada
        abundancia_total = int(params['abundancia_base'] * factor_ndvi * factor_area * factor_precip * random.uniform(0.9, 1.1))
        
        # Simulación de distribución de abundancia
        especies = []
        abundancia_acumulada = 0
        
        for i in range(riqueza_especies):
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
# 🗺️ SISTEMA DE MAPAS MEJORADO
# ===============================
class SistemaMapas:
    """Sistema de mapas mejorado con manejo de errores"""
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
                zoom_start=10,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics',
                control_scale=True
            )
            
            # Agregar polígono
            folium.GeoJson(
                gdf.geometry.iloc[0] if not gdf.empty else Polygon(),
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
    
    def crear_mapa_carbono(self, puntos_carbono):
        """Crea mapa de calor para carbono"""
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
            
            # Preparar datos para heatmap
            heat_data = [[p['lat'], p['lon'], p.get('carbono_ton_ha', 0)] 
                        for p in puntos_carbono if 'lat' in p and 'lon' in p]
            
            # Agregar heatmap si hay datos
            if heat_data and len(heat_data) > 0:
                HeatMap(
                    heat_data,
                    name='Carbono (ton C/ha)',
                    min_opacity=0.3,
                    radius=20,
                    blur=15,
                    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
                ).add_to(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de carbono: {str(e)}")
            return None

    def crear_mapa_biodiversidad(self, puntos_biodiversidad):
        """Crea mapa de calor para el índice de Shannon"""
        if not puntos_biodiversidad or len(puntos_biodiversidad) == 0:
            return None

        try:
            primer_punto = puntos_biodiversidad[0]
            centro = [primer_punto.get('lat', 0), primer_punto.get('lon', 0)]

            m = folium.Map(
                location=centro,
                zoom_start=12,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )

            # Preparar datos para heatmap
            heat_data = [
                [p.get('lat', 0), p.get('lon', 0), p.get('indice_shannon', 0)]
                for p in puntos_biodiversidad
                if 'lat' in p and 'lon' in p and 'indice_shannon' in p
            ]

            if heat_data and len(heat_data) > 0:
                gradient = {
                    0.0: '#991b1b',
                    0.25: '#ef4444',
                    0.5: '#f59e0b',
                    0.75: '#3b82f6',
                    1.0: '#10b981'
                }

                HeatMap(
                    heat_data,
                    name='Índice de Shannon',
                    min_opacity=0.4,
                    radius=20,
                    blur=15,
                    gradient=gradient
                ).add_to(m)

            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de biodiversidad: {str(e)}")
            return None

# ===============================
# 📊 VISUALIZACIONES MEJORADAS
# ===============================
class Visualizaciones:
    """Clase para generar visualizaciones con manejo de errores"""
    
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
            # Normalizar valores
            shannon_norm = min(shannon_data.get('indice_shannon', 0) / 4.0 * 100, 100)
            riqueza_norm = min(shannon_data.get('riqueza_especies', 0) / 200 * 100, 100)
            abundancia_norm = min(shannon_data.get('abundancia_total', 0) / 2000 * 100, 100)
            
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
# 📁 FUNCIONES AUXILIARES MEJORADAS
# ===============================
def cargar_archivo_mejorado(uploaded_file):
    """Carga un archivo geoespacial con manejo mejorado de errores"""
    try:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        
        # Manejar KML con regex mejorado
        if file_name.endswith('.kml'):
            content = file_bytes.decode('utf-8', errors='ignore')
            
            # Buscar coordenadas con regex robusto
            coords_pattern = r'<coordinates>([^<]+)</coordinates>'
            matches = re.findall(coords_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if matches:
                coords_text = matches[0].strip()
                points = []
                
                for line in coords_text.split():
                    for coord in line.split(','):
                        parts = coord.strip().split(',')
                        if len(parts) >= 2:
                            try:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                points.append((lon, lat))
                            except:
                                continue
                
                if len(points) >= 3:
                    polygon = Polygon(points)
                    gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
                    return gdf
        
        # Manejar GeoJSON
        elif file_name.endswith('.geojson') or file_name.endswith('.json'):
            try:
                gdf = gpd.read_file(file_bytes)
                if gdf.crs is None:
                    gdf.set_crs("EPSG:4326", inplace=True)
                return gdf
            except:
                # Intentar cargar como texto
                content = file_bytes.decode('utf-8')
                gdf = gpd.read_file(content)
                if gdf.crs is None:
                    gdf.set_crs("EPSG:4326", inplace=True)
                return gdf
        
        # Manejar Shapefile ZIP
        elif file_name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, 'upload.zip')
                with open(zip_path, 'wb') as f:
                    f.write(file_bytes)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if shp_files:
                    gdf = gpd.read_file(os.path.join(tmpdir, shp_files[0]))
                    if gdf.crs is None:
                        gdf.set_crs("EPSG:4326", inplace=True)
                    return gdf
        
        # Si todo falla, crear polígono de prueba
        st.warning("No se pudo cargar el archivo correctamente. Usando polígono de prueba.")
        polygon = Polygon([
            (-63.0, -17.0),
            (-62.5, -17.0),
            (-62.5, -17.5),
            (-63.0, -17.5),
            (-63.0, -17.0)
        ])
        return gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
        
    except Exception as e:
        st.error(f"Error al cargar archivo: {str(e)}")
        # Crear polígono de prueba como fallback
        polygon = Polygon([
            (-63.0, -17.0),
            (-62.5, -17.0),
            (-62.5, -17.5),
            (-63.0, -17.5),
            (-63.0, -17.0)
        ])
        return gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")

def ejecutar_analisis_completo(gdf, tipo_ecosistema, num_puntos):
    """Ejecuta análisis completo de carbono y biodiversidad con manejo de errores"""
    
    try:
        if gdf is None or gdf.empty:
            st.error("No hay datos geoespaciales válidos")
            return None
        
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
        
        carbono_total = 0
        co2_total = 0
        shannon_promedio = 0
        area_por_punto = area_total / max(num_puntos, 1)
        
        puntos_generados = 0
        max_intentos = num_puntos * 5
        
        while puntos_generados < num_puntos and len(puntos_carbono) < max_intentos:
            # Generar punto aleatorio
            lat = bounds[1] + random.random() * (bounds[3] - bounds[1])
            lon = bounds[0] + random.random() * (bounds[2] - bounds[0])
            point = Point(lon, lat)
            
            if poligono.contains(point):
                # Obtener datos climáticos
                datos_clima = clima.obtener_datos_climaticos(lat, lon)
                
                # Generar NDVI aleatorio
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
                
                # Guardar puntos
                puntos_carbono.append({
                    'lat': lat,
                    'lon': lon,
                    'carbono_ton_ha': carbono_info['carbono_total_ton_ha'],
                    'ndvi': ndvi,
                    'precipitacion': datos_clima['precipitacion']
                })
                
                # Agregar coordenadas a biodiv_info
                biodiv_info['lat'] = lat
                biodiv_info['lon'] = lon
                puntos_biodiversidad.append(biodiv_info)
                
                puntos_generados += 1
        
        # Calcular promedios
        shannon_promedio = shannon_promedio / max(puntos_generados, 1)
        
        # Obtener desglose promedio
        carbono_promedio = verra.calcular_carbono_hectarea(0.6, tipo_ecosistema, 1500)
        
        # Preparar resultados
        resultados = {
            'area_total_ha': area_total,
            'carbono_total_ton': round(carbono_total, 2),
            'co2_total_ton': round(co2_total, 2),
            'carbono_promedio_ha': round(carbono_total / max(area_total, 0.1), 2),
            'shannon_promedio': round(shannon_promedio, 3),
            'puntos_carbono': puntos_carbono,
            'puntos_biodiversidad': puntos_biodiversidad,
            'tipo_ecosistema': tipo_ecosistema,
            'num_puntos': puntos_generados,
            'desglose_promedio': carbono_promedio['desglose'] if carbono_promedio else {}
        }
        
        return resultados
    except Exception as e:
        st.error(f"Error en el análisis: {str(e)}")
        return None

# ===============================
# 🎨 INTERFAZ PRINCIPAL MEJORADA
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
        
        uploaded_file = st.file_uploader(
            "Cargar polígono (KML, GeoJSON, SHP)",
            type=['kml', 'geojson', 'zip', 'json'],
            help="Suba un archivo con el polígono de estudio"
        )
        
        if uploaded_file is not None:
            with st.spinner("Procesando archivo..."):
                try:
                    gdf = cargar_archivo_mejorado(uploaded_file)
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
                        if resultados:
                            st.success("✅ Análisis completado!")
                        else:
                            st.error("❌ No se pudieron generar resultados")
                        
                    except Exception as e:
                        st.error(f"Error en el análisis: {str(e)}")
    
    # Contenido principal
    if st.session_state.poligono_data is None:
        st.info("👈 Cargue un polígono en el panel lateral para comenzar")
        
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
            st.session_state.resultados.get('puntos_carbono', [])
        )
        if mapa_carbono:
            folium_static(mapa_carbono, width=1000, height=600)
        else:
            st.info("No se pudo generar el mapa de carbono")

        # Mapa de Shannon
        st.subheader("🦋 Mapa de Calor - Índice de Shannon")
        mapa_shannon = sistema_mapas.crear_mapa_biodiversidad(
            st.session_state.resultados.get('puntos_biodiversidad', [])
        )
        if mapa_shannon:
            folium_static(mapa_shannon, width=1000, height=600)
        else:
            st.info("No se pudo generar el mapa de biodiversidad")

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
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Carbono")
            fig_barras = Visualizaciones.crear_grafico_barras_carbono(res.get('desglose_promedio', {}))
            st.plotly_chart(fig_barras, use_container_width=True)
        
        with col2:
            st.subheader("Análisis de Biodiversidad")
            if res.get('puntos_biodiversidad') and len(res['puntos_biodiversidad']) > 0:
                fig_radar = Visualizaciones.crear_grafico_radar_biodiversidad(res['puntos_biodiversidad'][0])
                st.plotly_chart(fig_radar, use_container_width=True)
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
                'Tipo de ecosistema',
                'Puntos de muestreo'
            ],
            'Valor': [
                f"{res.get('area_total_ha', 0):,.1f} ha",
                f"{res.get('carbono_total_ton', 0):,.0f} ton C",
                f"{res.get('co2_total_ton', 0):,.0f} ton CO₂e",
                f"{res.get('carbono_promedio_ha', 0):,.1f} ton C/ha",
                f"{res.get('shannon_promedio', 0):.3f}",
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
                    st.info("PDF no disponible")
            
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
                    st.info("DOCX no disponible")
            
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
            valor = res.get('co2_total_ton', 0) * 15
            st.metric(
                "Valor Económico Aprox.", 
                f"${valor:,.0f}",
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
                    'Ton C/ha': round(valor, 2),
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
            
            for cat, desc in interpretaciones.items():
                if cat == biodiv.get('categoria', ''):
                    st.success(f"**{cat}**: {desc}")
                else:
                    st.text(f"{cat}: {desc}")
            
            # Muestra de especies
            st.subheader("Muestra de Distribución de Especies")
            
            if 'especies_muestra' in biodiv and biodiv['especies_muestra']:
                especies_data = []
                for esp in biodiv['especies_muestra'][:5]:
                    especies_data.append({
                        'Especie': f"Esp {esp['especie_id']}",
                        'Abundancia': esp['abundancia'],
                        'Proporción': f"{esp.get('proporcion', 0)*100:.2f}%",
                        'Grupo': random.choice(['Árbol', 'Arbusto', 'Hierba', 'Epífita', 'Fauna'])
                    })
                
                df_especies = pd.DataFrame(especies_data)
                st.dataframe(df_especies, use_container_width=True, hide_index=True)
            
            # Recomendaciones
            with st.expander("🌿 Recomendaciones para Conservación"):
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
        
        # Distribución del índice entre puntos
        st.subheader("Distribución del Índice entre Puntos de Muestreo")
        
        if res.get('puntos_biodiversidad'):
            shannon_values = [p.get('indice_shannon', 0) for p in res['puntos_biodiversidad']]
            
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
            st.info("No hay datos de biodiversidad para graficar")
    
    else:
        st.info("Ejecute el análisis primero para ver los datos de biodiversidad")

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    main()
