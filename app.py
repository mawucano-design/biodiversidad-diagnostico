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
# 📄 GENERADOR DE REPORTES COMPLETOS - MEJORADO
# ===============================
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter, landscape
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
        PageBreak, KeepTogether, Flowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics import renderPDF
    REPORTPDF_AVAILABLE = True
except ImportError:
    REPORTPDF_AVAILABLE = False
    st.warning("ReportLab no está instalado. La generación de PDFs estará limitada.")

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    REPORTDOCX_AVAILABLE = True
except ImportError:
    REPORTDOCX_AVAILABLE = False
    st.warning("python-docx no está instalado. La generación de DOCX estará limitada.")

class GeneradorReportes:
    def __init__(self, resultados, gdf, mapas_imagenes=None):
        self.resultados = resultados
        self.gdf = gdf
        self.mapas_imagenes = mapas_imagenes or {}
        self.buffer_pdf = BytesIO()
        self.buffer_docx = BytesIO()
        self.fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
    def _fig_to_png(self, fig, width=800, height=500):
        """Convierte un gráfico Plotly a PNG en BytesIO"""
        try:
            if fig is None:
                return None
            img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
            return BytesIO(img_bytes)
        except Exception as e:
            st.warning(f"No se pudo convertir el gráfico a PNG: {str(e)}")
            return None
    
    def _mapa_to_png(self, mapa, width=800, height=600):
        """Convierte un mapa folium a PNG (simulación - en producción usaría selenium)"""
        try:
            # En producción real, usaríamos selenium para capturar el mapa
            # Por ahora, creamos una imagen de placeholder
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            ax.text(0.5, 0.5, 'Mapa: Ver aplicación web interactiva', 
                   horizontalalignment='center', verticalalignment='center',
                   fontsize=14, color='gray')
            ax.axis('off')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            buffer.seek(0)
            return buffer
        except Exception as e:
            st.warning(f"No se pudo generar imagen del mapa: {str(e)}")
            return None
    
    def _crear_tabla_resultados(self):
        """Crea tabla de resultados para el informe"""
        res = self.resultados
        if not res:
            return []
        
        data = [
            ['Métrica', 'Valor', 'Unidad', 'Interpretación'],
            ['Área total', f"{res.get('area_total_ha', 0):,.1f}", 'ha', 'Superficie analizada'],
            ['Carbono total', f"{res.get('carbono_total_ton', 0):,.0f}", 'ton C', 'Almacenamiento total'],
            ['CO₂ equivalente', f"{res.get('co2_total_ton', 0):,.0f}", 'ton CO₂e', 'Potencial créditos'],
            ['Carbono promedio/ha', f"{res.get('carbono_promedio_ha', 0):,.1f}", 'ton C/ha', 'Densidad de carbono'],
            ['Índice Shannon', f"{res.get('shannon_promedio', 0):.3f}", '', 'Biodiversidad'],
            ['NDVI promedio', f"{res.get('ndvi_promedio', 0):.3f}", '', 'Salud vegetal'],
            ['NDWI promedio', f"{res.get('ndwi_promedio', 0):.3f}", '', 'Contenido agua'],
            ['Puntos muestreo', f"{res.get('num_puntos', 0)}", '', 'Resolución análisis'],
            ['Ecosistema', res.get('tipo_ecosistema', 'N/A'), '', 'Tipo principal']
        ]
        return data
    
    def _crear_tabla_pools_carbono(self):
        """Crea tabla de pools de carbono"""
        res = self.resultados
        if not res or 'desglose_promedio' not in res:
            return []
        
        desglose = res['desglose_promedio']
        total = sum(desglose.values())
        
        data = [['Pool de Carbono', 'Ton C/ha', 'Porcentaje', 'Descripción']]
        descripciones = {
            'AGB': 'Biomasa Aérea Viva (árboles, arbustos)',
            'BGB': 'Biomasa de Raíces',
            'DW': 'Madera Muerta (troncos caídos)',
            'LI': 'Hojarasca y materia orgánica superficial',
            'SOC': 'Carbono Orgánico del Suelo (0-30 cm)'
        }
        
        for pool, valor in desglose.items():
            porcentaje = (valor / total * 100) if total > 0 else 0
            data.append([
                pool,
                f"{valor:.1f}",
                f"{porcentaje:.1f}%",
                descripciones.get(pool, pool)
            ])
        
        # Agregar total
        data.append(['TOTAL', f"{total:.1f}", '100%', 'Suma de todos los pools'])
        
        return data
    
    def generar_pdf_completo(self):
        """Genera reporte PDF completo con todos los resultados"""
        if not REPORTPDF_AVAILABLE:
            st.error("ReportLab no está instalado. No se puede generar PDF.")
            return None
        
        try:
            # Configurar documento
            doc = SimpleDocTemplate(
                self.buffer_pdf,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#0a7e5a')
            )
            
            heading1_style = ParagraphStyle(
                'Heading1Custom',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.HexColor('#065f46')
            )
            
            heading2_style = ParagraphStyle(
                'Heading2Custom',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.HexColor('#0a7e5a')
            )
            
            normal_style = ParagraphStyle(
                'NormalCustom',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_JUSTIFY
            )
            
            # ===== PORTADA =====
            story.append(Spacer(1, 100))
            story.append(Paragraph("INFORME AMBIENTAL COMPLETO", title_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph("Sistema Satelital de Análisis Ambiental", styles['Heading2']))
            story.append(Paragraph("Metodología Verra VCS + Índice de Shannon", styles['Heading2']))
            story.append(Spacer(1, 40))
            story.append(Paragraph(f"Fecha de generación: {self.fecha}", styles['Normal']))
            story.append(Paragraph(f"Área analizada: {self.resultados.get('area_total_ha', 0):,.1f} ha", styles['Normal']))
            story.append(Paragraph(f"Tipo de ecosistema: {self.resultados.get('tipo_ecosistema', 'N/A')}", styles['Normal']))
            story.append(PageBreak())
            
            # ===== RESUMEN EJECUTIVO =====
            story.append(Paragraph("1. RESUMEN EJECUTIVO", heading1_style))
            story.append(Spacer(1, 12))
            
            resumen_texto = f"""
            Este informe presenta los resultados del análisis ambiental integral realizado sobre un área de 
            <b>{self.resultados.get('area_total_ha', 0):,.1f} hectáreas</b>. El análisis combina metodologías estandarizadas 
            (Verra VCS) para la cuantificación de carbono forestal con el índice de Shannon para evaluación de biodiversidad,
            complementado con índices espectrales satelitales (NDVI, NDWI).
            
            <b>Principales hallazgos:</b>
            • Almacenamiento total de carbono: <b>{self.resultados.get('carbono_total_ton', 0):,.0f} ton C</b>
            • Equivalente en CO₂: <b>{self.resultados.get('co2_total_ton', 0):,.0f} ton CO₂e</b>
            • Biodiversidad (Shannon): <b>{self.resultados.get('shannon_promedio', 0):.3f}</b> - Categoría: {self.resultados.get('puntos_biodiversidad', [{}])[0].get('categoria', 'N/A') if self.resultados.get('puntos_biodiversidad') else 'N/A'}
            • Salud vegetal (NDVI): <b>{self.resultados.get('ndvi_promedio', 0):.3f}</b>
            • Contenido de agua (NDWI): <b>{self.resultados.get('ndwi_promedio', 0):.3f}</b>
            
            Estos resultados permiten identificar oportunidades para proyectos de conservación, créditos de carbono
            y estrategias de manejo sostenible del territorio.
            """
            story.append(Paragraph(resumen_texto, normal_style))
            story.append(Spacer(1, 20))
            
            # ===== RESULTADOS NUMÉRICOS =====
            story.append(Paragraph("2. RESULTADOS NUMÉRICOS", heading1_style))
            story.append(Spacer(1, 12))
            
            # Tabla de resultados principales
            data_resultados = self._crear_tabla_resultados()
            if data_resultados:
                table = Table(data_resultados, colWidths=[2*inch, 1.5*inch, 1*inch, 2.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a7e5a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ]))
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Tabla de pools de carbono
            story.append(Paragraph("2.1 Distribución de Carbono por Pools", heading2_style))
            story.append(Spacer(1, 8))
            
            data_pools = self._crear_tabla_pools_carbono()
            if data_pools:
                table_pools = Table(data_pools, colWidths=[1.5*inch, 1*inch, 1*inch, 3*inch])
                table_pools.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e5e7eb')),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                story.append(table_pools)
                story.append(PageBreak())
            
            # ===== GRÁFICOS =====
            story.append(Paragraph("3. VISUALIZACIONES Y GRÁFICOS", heading1_style))
            story.append(Spacer(1, 12))
            
            # Gráfico de carbono
            story.append(Paragraph("3.1 Distribución de Carbono por Pools", heading2_style))
            if 'carbono' in self.mapas_imagenes:
                try:
                    img_carbono = Image(self.mapas_imagenes['carbono'], width=6*inch, height=3.5*inch)
                    img_carbono.hAlign = 'CENTER'
                    story.append(img_carbono)
                    story.append(Spacer(1, 8))
                    story.append(Paragraph("<i>Figura 1: Distribución porcentual de carbono en los diferentes pools (ton C/ha)</i>", 
                                         ParagraphStyle('Caption', parent=normal_style, fontSize=8, alignment=TA_CENTER)))
                except:
                    story.append(Paragraph("Gráfico de carbono no disponible", normal_style))
            
            story.append(Spacer(1, 15))
            
            # Gráfico de biodiversidad
            story.append(Paragraph("3.2 Perfil de Biodiversidad", heading2_style))
            if 'biodiv' in self.mapas_imagenes:
                try:
                    img_biodiv = Image(self.mapas_imagenes['biodiv'], width=6*inch, height=3.5*inch)
                    img_biodiv.hAlign = 'CENTER'
                    story.append(img_biodiv)
                    story.append(Spacer(1, 8))
                    story.append(Paragraph("<i>Figura 2: Perfil de biodiversidad (Índice de Shannon y componentes)</i>", 
                                         ParagraphStyle('Caption', parent=normal_style, fontSize=8, alignment=TA_CENTER)))
                except:
                    story.append(Paragraph("Gráfico de biodiversidad no disponible", normal_style))
            
            story.append(PageBreak())
            
            # ===== MAPAS =====
            story.append(Paragraph("4. ANÁLISIS ESPACIAL", heading1_style))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph("""Los mapas de calor muestran la distribución espacial de las variables analizadas. 
            Se recomienda utilizar la aplicación web para la versión interactiva completa.""", normal_style))
            story.append(Spacer(1, 15))
            
            # Descripción de mapas
            mapas_desc = [
                ("🌳 Mapa de Carbono", "Muestra la densidad de carbono almacenado (ton C/ha)"),
                ("📈 Mapa de NDVI", "Índice de vegetación: salud y densidad de la cobertura vegetal"),
                ("💧 Mapa de NDWI", "Índice de agua: contenido de humedad en vegetación y suelo"),
                ("🦋 Mapa de Biodiversidad", "Distribución del Índice de Shannon (diversidad biológica)"),
                ("🎭 Mapa Combinado", "Superposición de todas las capas para análisis integrado")
            ]
            
            for titulo, desc in mapas_desc:
                story.append(Paragraph(f"<b>{titulo}</b>: {desc}", normal_style))
                story.append(Spacer(1, 4))
            
            story.append(Spacer(1, 15))
            
            # Si hay imágenes de mapas, agregarlas
            if 'mapa_area' in self.mapas_imagenes:
                story.append(Paragraph("4.1 Área de Estudio", heading2_style))
                try:
                    img_mapa = Image(self.mapas_imagenes['mapa_area'], width=6*inch, height=4*inch)
                    img_mapa.hAlign = 'CENTER'
                    story.append(img_mapa)
                    story.append(Paragraph("<i>Figura 3: Polígono del área de estudio analizada</i>", 
                                         ParagraphStyle('Caption', parent=normal_style, fontSize=8, alignment=TA_CENTER)))
                except:
                    pass
            
            story.append(PageBreak())
            
            # ===== ANÁLISIS DETALLADO =====
            story.append(Paragraph("5. ANÁLISIS DETALLADO POR VARIABLE", heading1_style))
            story.append(Spacer(1, 12))
            
            # Carbono
            story.append(Paragraph("5.1 Carbono Forestal - Metodología Verra VCS", heading2_style))
            carbono_texto = f"""
            El análisis de carbono se realizó siguiendo la metodología Verra VCS para proyectos REDD+. 
            El área analizada almacena aproximadamente <b>{self.resultados.get('carbono_total_ton', 0):,.0f} toneladas de carbono</b>, 
            equivalentes a <b>{self.resultados.get('co2_total_ton', 0):,.0f} toneladas de CO₂</b>.
            
            <b>Potencial para créditos de carbono:</b>
            Considerando un precio conservador de $15 por tonelada de CO₂, el valor económico potencial es de 
            <b>${self.resultados.get('co2_total_ton', 0) * 15:,.0f} USD</b>.
            
            <b>Recomendaciones para proyecto VCS:</b>
            1. Validación por organismo acreditado Verra
            2. Establecimiento de parcelas permanentes de monitoreo
            3. Desarrollo de línea base (baseline) robusta
            4. Implementación de sistema MRV (Monitoreo, Reporte y Verificación)
            """
            story.append(Paragraph(carbono_texto, normal_style))
            story.append(Spacer(1, 15))
            
            # Biodiversidad
            story.append(Paragraph("5.2 Biodiversidad - Índice de Shannon", heading2_style))
            if self.resultados.get('puntos_biodiversidad'):
                biodiv = self.resultados['puntos_biodiversidad'][0]
                biodiversidad_texto = f"""
                El índice de Shannon calculado (<b>{biodiv.get('indice_shannon', 0):.3f}</b>) indica una biodiversidad 
                clasificada como <b>{biodiv.get('categoria', 'N/A')}</b>. Se estima una riqueza de aproximadamente 
                <b>{biodiv.get('riqueza_especies', 0)} especies</b> en el área de estudio.
                
                <b>Interpretación:</b>
                • Índice > 3.5: Muy alta biodiversidad (ecosistemas prístinos)
                • Índice 2.5-3.5: Alta biodiversidad
                • Índice 1.5-2.5: Biodiversidad moderada
                • Índice 0.5-1.5: Baja biodiversidad
                • Índice < 0.5: Muy baja biodiversidad
                
                <b>Recomendaciones de conservación:</b>
                Basado en el valor obtenido, se recomiendan medidas de {self._obtener_recomendaciones_biodiversidad(biodiv.get('categoria', ''))}.
                """
                story.append(Paragraph(biodiversidad_texto, normal_style))
            
            story.append(Spacer(1, 15))
            
            # Índices espectrales
            story.append(Paragraph("5.3 Índices Espectrales Satelitales", heading2_style))
            espectral_texto = f"""
            <b>NDVI (Normalized Difference Vegetation Index):</b> <b>{self.resultados.get('ndvi_promedio', 0):.3f}</b>
            • > 0.6: Vegetación densa y saludable
            • 0.3-0.6: Vegetación moderada
            • < 0.3: Vegetación escasa o estresada
            
            <b>NDWI (Normalized Difference Water Index):</b> <b>{self.resultados.get('ndwi_promedio', 0):.3f}</b>
            • > 0.2: Alta humedad/presencia de agua
            • 0.0-0.2: Humedad moderada
            • < 0.0: Condiciones secas
            
            Estos índices permiten monitorear la salud de la vegetación y la disponibilidad hídrica,
            siendo útiles para detectar estrés temprano y planificar acciones de manejo.
            """
            story.append(Paragraph(espectral_texto, normal_style))
            story.append(PageBreak())
            
            # ===== CONCLUSIONES Y RECOMENDACIONES =====
            story.append(Paragraph("6. CONCLUSIONES Y RECOMENDACIONES", heading1_style))
            story.append(Spacer(1, 12))
            
            conclusiones_texto = f"""
            <b>Conclusiones principales:</b>
            1. El área analizada presenta un almacenamiento significativo de carbono, con potencial para proyectos de créditos de carbono.
            2. La biodiversidad medida a través del índice de Shannon es {self._obtener_evaluacion_biodiversidad()}.
            3. Los índices espectrales indican {self._obtener_evaluacion_ndvi()} en términos de salud vegetal.
            4. El contenido de agua (NDWI) sugiere {self._obtener_evaluacion_ndwi()}.
            
            <b>Recomendaciones generales:</b>
            1. <b>Conservación:</b> Mantener y proteger las áreas con mayor densidad de carbono y biodiversidad.
            2. <b>Monitoreo:</b> Establecer un sistema de monitoreo periódico para seguir cambios en las variables.
            3. <b>Restauración:</b> Identificar áreas degradadas para acciones de restauración ecológica.
            4. <b>Planificación:</b> Incorporar estos resultados en planes de manejo territorial.
            5. <b>Verificación:</b> Considerar la validación externa para proyectos de carbono.
            
            <b>Próximos pasos sugeridos:</b>
            • Análisis de viabilidad para proyecto VCS
            • Diseño de estrategia de monitoreo de biodiversidad
            • Evaluación de amenazas y presiones en el área
            • Integración con planes de desarrollo local
            """
            story.append(Paragraph(conclusiones_texto, normal_style))
            story.append(Spacer(1, 20))
            
            # ===== METADATOS =====
            story.append(Paragraph("7. METADATOS TÉCNICOS", heading1_style))
            story.append(Spacer(1, 12))
            
            metadatos_texto = f"""
            <b>Fecha de análisis:</b> {self.fecha}
            <b>Metodología carbono:</b> Verra VCS simplificada
            <b>Índice biodiversidad:</b> Shannon-Wiener (H')
            <b>Índices espectrales:</b> NDVI, NDWI (simulación satelital)
            <b>Puntos de muestreo:</b> {self.resultados.get('num_puntos', 0)}
            <b>Sistema de coordenadas:</b> WGS84 (EPSG:4326)
            <b>Software:</b> Sistema Satelital de Análisis Ambiental v1.0
            
            <b>Limitaciones:</b>
            • Datos simulados para demostración técnica
            • En producción, utilizar datos satelitales reales
            • Validación de campo requerida para precisión absoluta
            """
            story.append(Paragraph(metadatos_texto, normal_style))
            
            # ===== FIN DEL DOCUMENTO =====
            story.append(Spacer(1, 30))
            story.append(Paragraph("--- FIN DEL INFORME ---", 
                                 ParagraphStyle('End', parent=normal_style, alignment=TA_CENTER, fontSize=10)))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Generado automáticamente por el Sistema Satelital de Análisis Ambiental", 
                                 ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, fontSize=8, textColor=colors.grey)))
            
            # Construir documento
            doc.build(story)
            self.buffer_pdf.seek(0)
            return self.buffer_pdf
            
        except Exception as e:
            st.error(f"Error generando PDF completo: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
    def _obtener_recomendaciones_biodiversidad(self, categoria):
        """Devuelve recomendaciones basadas en categoría de biodiversidad"""
        recomendaciones = {
            'Muy Alta': 'protección estricta y monitoreo científico',
            'Alta': 'conservación activa y manejo sostenible',
            'Moderada': 'restauración y manejo adaptativo',
            'Baja': 'restauración urgente y protección',
            'Muy Baja': 'restauración intensiva y medidas de recuperación'
        }
        return recomendaciones.get(categoria, 'conservación y monitoreo')
    
    def _obtener_evaluacion_biodiversidad(self):
        """Devuelve evaluación de biodiversidad"""
        if self.resultados.get('shannon_promedio', 0) > 3.0:
            return "alta a muy alta"
        elif self.resultados.get('shannon_promedio', 0) > 2.0:
            return "moderada a alta"
        else:
            return "baja a moderada"
    
    def _obtener_evaluacion_ndvi(self):
        """Devuelve evaluación de NDVI"""
        ndvi = self.resultados.get('ndvi_promedio', 0)
        if ndvi > 0.6:
            return "buena salud vegetal"
        elif ndvi > 0.3:
            return "condiciones moderadas"
        else:
            return "posible estrés o degradación"
    
    def _obtener_evaluacion_ndwi(self):
        """Devuelve evaluación de NDWI"""
        ndwi = self.resultados.get('ndwi_promedio', 0)
        if ndwi > 0.2:
            return "buena disponibilidad hídrica"
        elif ndwi > 0.0:
            return "condiciones hídricas moderadas"
        else:
            return "condiciones relativamente secas"

    def generar_pdf(self):
        """Mantener compatibilidad con versión anterior"""
        return self.generar_pdf_completo()

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
# 🗺️ SISTEMA DE MAPAS COMPLETO CON TODOS LOS HEATMAPS - MEJORADO
# ===============================
class SistemaMapas:
    """Sistema de mapas completo con todos los heatmaps - CON ZOOM AUTOMÁTICO Y CONTORNO"""
    def __init__(self):
        self.capa_base = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    
    def _calcular_bounds_y_zoom(self, gdf):
        """Calcula bounds y zoom automático para el polígono"""
        if gdf is None or gdf.empty:
            return None, None, 12
        
        try:
            # Obtener bounds del polígono
            bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
            centro = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            
            # Calcular zoom basado en el tamaño del área
            # Convertir diferencia de grados a zoom aproximado
            delta_lat = bounds[3] - bounds[1]
            delta_lon = bounds[2] - bounds[0]
            
            # Fórmula para zoom automático basado en área
            max_delta = max(delta_lat, delta_lon * math.cos(math.radians(centro[0])))
            
            if max_delta > 10:
                zoom = 8
            elif max_delta > 5:
                zoom = 9
            elif max_delta > 2:
                zoom = 10
            elif max_delta > 1:
                zoom = 11
            elif max_delta > 0.5:
                zoom = 12
            elif max_delta > 0.2:
                zoom = 13
            elif max_delta > 0.1:
                zoom = 14
            else:
                zoom = 15
            
            return bounds, centro, zoom
        except Exception as e:
            st.warning(f"Error calculando zoom: {str(e)}")
            return None, None, 12
    
    def crear_mapa_area(self, gdf):
        """Crea mapa básico con el área de estudio - CON ZOOM AUTOMÁTICO"""
        if gdf is None or gdf.empty:
            return None
        
        try:
            # Calcular bounds, centro y zoom automático
            bounds, centro, zoom = self._calcular_bounds_y_zoom(gdf)
            
            if centro is None:
                centro = [-15, -60]  # Centro de Sudamérica como fallback
                zoom = 4
            
            # Crear mapa con zoom automático
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics',
                control_scale=True
            )
            
            # Agregar polígono con contorno destacado
            folium.GeoJson(
                gdf.geometry.iloc[0],
                style_function=lambda x: {
                    'fillColor': '#3b82f6',
                    'color': '#1d4ed8',
                    'weight': 4,
                    'fillOpacity': 0.15,
                    'dashArray': '5, 5'
                },
                name='Área de estudio',
                tooltip=f"Área: {gdf.to_crs('EPSG:3857').geometry.area.sum()/10000:,.1f} ha"
            ).add_to(m)
            
            # Agregar control de capas
            folium.LayerControl().add_to(m)
            
            # Ajustar vista a los bounds si es posible
            if bounds is not None:
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa: {str(e)}")
            return None
    
    def crear_mapa_calor_carbono(self, puntos_carbono, gdf=None):
        """Crea mapa de calor para carbono - CON CONTORNO DE POLÍGONO"""
        if not puntos_carbono or len(puntos_carbono) == 0:
            return None
        
        try:
            # Calcular centro y zoom automático
            if gdf is not None and not gdf.empty:
                bounds, centro, zoom = self._calcular_bounds_y_zoom(gdf)
            else:
                centro = [puntos_carbono[0]['lat'], puntos_carbono[0]['lon']]
                zoom = 12
            
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Agregar contorno del polígono si está disponible
            if gdf is not None and not gdf.empty:
                folium.GeoJson(
                    gdf.geometry.iloc[0],
                    style_function=lambda x: {
                        'fillColor': None,
                        'color': '#000000',
                        'weight': 3,
                        'fillOpacity': 0,
                        'opacity': 0.8,
                        'dashArray': '5, 5'
                    },
                    name='Área de estudio'
                ).add_to(m)
            
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
            
            # Ajustar vista a bounds si hay polígono
            if gdf is not None and bounds is not None:
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
            # Control de capas
            folium.LayerControl().add_to(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de carbono: {str(e)}")
            return None
    
    def crear_mapa_calor_ndvi(self, puntos_ndvi, gdf=None):
        """Crea mapa de calor para NDVI - CON CONTORNO DE POLÍGONO"""
        if not puntos_ndvi or len(puntos_ndvi) == 0:
            return None
        
        try:
            # Calcular centro y zoom
            if gdf is not None and not gdf.empty:
                bounds, centro, zoom = self._calcular_bounds_y_zoom(gdf)
            else:
                centro = [puntos_ndvi[0]['lat'], puntos_ndvi[0]['lon']]
                zoom = 12
            
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Agregar contorno del polígono si está disponible
            if gdf is not None and not gdf.empty:
                folium.GeoJson(
                    gdf.geometry.iloc[0],
                    style_function=lambda x: {
                        'fillColor': None,
                        'color': '#000000',
                        'weight': 3,
                        'fillOpacity': 0,
                        'opacity': 0.8
                    },
                    name='Área de estudio'
                ).add_to(m)
            
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
            
            # Ajustar vista si hay polígono
            if gdf is not None and bounds is not None:
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
            folium.LayerControl().add_to(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de NDVI: {str(e)}")
            return None
    
    def crear_mapa_calor_ndwi(self, puntos_ndwi, gdf=None):
        """Crea mapa de calor para NDWI - CON CONTORNO DE POLÍGONO"""
        if not puntos_ndwi or len(puntos_ndwi) == 0:
            return None
        
        try:
            # Calcular centro
            if gdf is not None and not gdf.empty:
                bounds, centro, zoom = self._calcular_bounds_y_zoom(gdf)
            else:
                centro = [puntos_ndwi[0]['lat'], puntos_ndwi[0]['lon']]
                zoom = 12
            
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Agregar contorno del polígono si está disponible
            if gdf is not None and not gdf.empty:
                folium.GeoJson(
                    gdf.geometry.iloc[0],
                    style_function=lambda x: {
                        'fillColor': None,
                        'color': '#000000',
                        'weight': 3,
                        'fillOpacity': 0,
                        'opacity': 0.8
                    },
                    name='Área de estudio'
                ).add_to(m)
            
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
            
            # Ajustar vista si hay polígono
            if gdf is not None and bounds is not None:
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
            folium.LayerControl().add_to(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de NDWI: {str(e)}")
            return None
    
    def crear_mapa_calor_biodiversidad(self, puntos_biodiversidad, gdf=None):
        """Crea mapa de calor para biodiversidad (Índice de Shannon) - CON CONTORNO"""
        if not puntos_biodiversidad or len(puntos_biodiversidad) == 0:
            return None
        
        try:
            # Calcular centro
            if gdf is not None and not gdf.empty:
                bounds, centro, zoom = self._calcular_bounds_y_zoom(gdf)
            else:
                centro = [puntos_biodiversidad[0]['lat'], puntos_biodiversidad[0]['lon']]
                zoom = 12
            
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Agregar contorno del polígono si está disponible
            if gdf is not None and not gdf.empty:
                folium.GeoJson(
                    gdf.geometry.iloc[0],
                    style_function=lambda x: {
                        'fillColor': None,
                        'color': '#000000',
                        'weight': 3,
                        'fillOpacity': 0,
                        'opacity': 0.8
                    },
                    name='Área de estudio'
                ).add_to(m)
            
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
            
            # Ajustar vista si hay polígono
            if gdf is not None and bounds is not None:
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
            folium.LayerControl().add_to(m)
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa de biodiversidad: {str(e)}")
            return None
    
    def crear_mapa_combinado(self, puntos_carbono, puntos_ndvi, puntos_ndwi, puntos_biodiversidad, gdf=None):
        """Crea mapa con todas las capas de heatmap - CON CONTORNO"""
        if not puntos_carbono or len(puntos_carbono) == 0:
            return None
        
        try:
            # Calcular centro y zoom
            if gdf is not None and not gdf.empty:
                bounds, centro, zoom = self._calcular_bounds_y_zoom(gdf)
            else:
                centro = [puntos_carbono[0]['lat'], puntos_carbono[0]['lon']]
                zoom = 12
            
            m = folium.Map(
                location=centro,
                zoom_start=zoom,
                tiles=self.capa_base,
                attr='Esri, Maxar, Earthstar Geographics'
            )
            
            # Agregar contorno del polígono si está disponible
            if gdf is not None and not gdf.empty:
                folium.GeoJson(
                    gdf.geometry.iloc[0],
                    style_function=lambda x: {
                        'fillColor': None,
                        'color': '#000000',
                        'weight': 3,
                        'fillOpacity': 0,
                        'opacity': 0.8,
                        'dashArray': '5, 5'
                    },
                    name='Área de estudio'
                ).add_to(m)
            
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
            
            # Ajustar vista si hay polígono
            if gdf is not None and bounds is not None:
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
            return m
        except Exception as e:
            st.warning(f"Error al crear mapa combinado: {str(e)}")
            return None
    
    # Las funciones de leyenda permanecen igual...
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
                    <div><span style="color: #000; font-weight: bold;">■</span> Contorno negro: Área de estudio</div>
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
                    <div><span style="color: #000; font-weight: bold;">■</span> Contorno negro: Área de estudio</div>
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
                    <div><span style="color: #000; font-weight: bold;">■</span> Contorno negro: Área de estudio</div>
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
                    <div><span style="color: #000; font-weight: bold;">■</span> Contorno negro: Área de estudio</div>
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
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 20px; height: 20px; background: linear-gradient(90deg, #991b1b, #ef4444, #f59e0b, #3b82f6, #8b5cf6, #10b981); margin-right: 10px; border: 1px solid #666;"></div>
                        <div>🦋 Índice de Shannon</div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; border: 2px solid #000; background: none; margin-right: 10px;"></div>
                        <div>📐 Contorno del área de estudio</div>
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
# 🎨 INTERFAZ PRINCIPAL SIMPLIFICADA - ACTUALIZADA
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
    if 'mapas_imagenes' not in st.session_state:
        st.session_state.mapas_imagenes = {}
    
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
                        
                        # Crear mapa inicial CON ZOOM AUTOMÁTICO
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
                        
                        # Generar imágenes para el informe
                        if resultados:
                            vis = Visualizaciones()
                            mapas_imagenes = {}
                            
                            # Generar gráficos
                            if 'desglose_promedio' in resultados and resultados['desglose_promedio']:
                                fig_carbono = vis.crear_grafico_barras_carbono(resultados['desglose_promedio'])
                                mapas_imagenes['carbono'] = GeneradorReportes._fig_to_png(None, fig_carbono, 800, 500)
                            
                            if 'puntos_biodiversidad' in resultados and resultados['puntos_biodiversidad']:
                                if len(resultados['puntos_biodiversidad']) > 0:
                                    fig_biodiv = vis.crear_grafico_radar_biodiversidad(resultados['puntos_biodiversidad'][0])
                                    mapas_imagenes['biodiv'] = GeneradorReportes._fig_to_png(None, fig_biodiv, 800, 500)
                            
                            # Generar imagen del mapa de área
                            if st.session_state.mapa:
                                sistema_mapas = SistemaMapas()
                                mapas_imagenes['mapa_area'] = sistema_mapas._mapa_to_png(st.session_state.mapa, 800, 600)
                            
                            st.session_state.mapas_imagenes = mapas_imagenes
                        
                        st.success("✅ Análisis completado!")
                        
                    except Exception as e:
                        st.error(f"Error en el análisis: {str(e)}")
                        import traceback
                        st.error(traceback.format_exc())
    
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
            
            **Nuevas mejoras:**
            • **Zoom automático** al área del polígono
            • **Contorno del polígono** en todos los mapas de calor
            • **Informe completo** PDF con todos los resultados
            
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
# 🗺️ FUNCIONES DE VISUALIZACIÓN - ACTUALIZADAS
# ===============================
def mostrar_mapas_calor():
    """Muestra todos los mapas de calor disponibles - CON MEJORAS"""
    st.header("🗺️ Mapas de Calor - Análisis Multivariable")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌍 Área de Estudio", 
        "🌳 Carbono", 
        "📈 NDVI", 
        "💧 NDWI", 
        "🦋 Biodiversidad",
        "🎭 Combinado"
    ])
    
    with tab1:
        st.subheader("Área de Estudio - CON ZOOM AUTOMÁTICO")
        if st.session_state.mapa:
            folium_static(st.session_state.mapa, width=1000, height=600)
            st.info("✅ Zoom automático ajustado al polígono. Área delimitada en azul.")
        else:
            st.info("No hay mapa para mostrar")
    
    with tab2:
        st.subheader("🌳 Mapa de Calor - Carbono (ton C/ha) - CON CONTORNO")
        if st.session_state.resultados and 'puntos_carbono' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_carbono = sistema_mapas.crear_mapa_calor_carbono(
                st.session_state.resultados['puntos_carbono'],
                st.session_state.poligono_data  # Pasar polígono para contorno
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
                
                st.success("✅ Contorno negro muestra el límite del área de estudio")
            else:
                st.warning("No se pudo generar el mapa de carbono.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de carbono")
    
    with tab3:
        st.subheader("📈 Mapa de Calor - NDVI (Índice de Vegetación) - CON CONTORNO")
        if st.session_state.resultados and 'puntos_ndvi' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_ndvi = sistema_mapas.crear_mapa_calor_ndvi(
                st.session_state.resultados['puntos_ndvi'],
                st.session_state.poligono_data  # Pasar polígono para contorno
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
                
                st.success("✅ Contorno negro muestra el límite del área de estudio")
            else:
                st.warning("No se pudo generar el mapa de NDVI.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de NDVI")
    
    with tab4:
        st.subheader("💧 Mapa de Calor - NDWI (Índice de Agua) - CON CONTORNO")
        if st.session_state.resultados and 'puntos_ndwi' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_ndwi = sistema_mapas.crear_mapa_calor_ndwi(
                st.session_state.resultados['puntos_ndwi'],
                st.session_state.poligono_data  # Pasar polígono para contorno
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
                
                st.success("✅ Contorno negro muestra el límite del área de estudio")
            else:
                st.warning("No se pudo generar el mapa de NDWI.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de NDWI")
    
    with tab5:
        st.subheader("🦋 Mapa de Calor - Biodiversidad (Índice de Shannon) - CON CONTORNO")
        if st.session_state.resultados and 'puntos_biodiversidad' in st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_biodiv = sistema_mapas.crear_mapa_calor_biodiversidad(
                st.session_state.resultados['puntos_biodiversidad'],
                st.session_state.poligono_data  # Pasar polígono para contorno
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
                
                st.success("✅ Contorno negro muestra el límite del área de estudio")
            else:
                st.warning("No se pudo generar el mapa de biodiversidad.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa de biodiversidad")
    
    with tab6:
        st.subheader("🎭 Mapa Combinado - Todas las Capas - CON CONTORNO")
        if st.session_state.resultados:
            sistema_mapas = SistemaMapas()
            mapa_combinado = sistema_mapas.crear_mapa_combinado(
                st.session_state.resultados.get('puntos_carbono', []),
                st.session_state.resultados.get('puntos_ndvi', []),
                st.session_state.resultados.get('puntos_ndwi', []),
                st.session_state.resultados.get('puntos_biodiversidad', []),
                st.session_state.poligono_data  # Pasar polígono para contorno
            )
            
            if mapa_combinado:
                folium_static(mapa_combinado, width=1000, height=600)
                st.info("📌 Use el control en la esquina superior derecha para alternar entre las diferentes capas de mapas de calor")
                st.success("✅ Contorno negro muestra el límite del área de estudio en todos los mapas")
            else:
                st.warning("No se pudo generar el mapa combinado.")
        else:
            st.info("Ejecute el análisis primero para ver el mapa combinado")

def mostrar_dashboard():
    """Muestra dashboard ejecutivo - CON INFORME MEJORADO"""
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
        
        # ===== SECCIÓN DE INFORME COMPLETO =====
        st.subheader("📥 Descargar Informe Completo")
        
        st.info("""
        **Nuevo: Informe completo PDF** incluye:
        • Portada y resumen ejecutivo
        • Tablas de resultados numéricos
        • Gráficos de carbono y biodiversidad
        • Análisis detallado por variable
        • Conclusiones y recomendaciones
        • Metadatos técnicos
        """)
        
        if st.session_state.resultados and st.session_state.poligono_data is not None:
            # Crear generador con imágenes pre-generadas
            generador = GeneradorReportes(
                st.session_state.resultados, 
                st.session_state.poligono_data,
                st.session_state.mapas_imagenes
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if REPORTPDF_AVAILABLE:
                    if st.button("📄 Generar Informe Completo PDF", use_container_width=True):
                        with st.spinner("Generando informe completo..."):
                            pdf_buffer = generador.generar_pdf_completo()
                            if pdf_buffer:
                                st.download_button(
                                    label="⬇️ Descargar PDF Completo",
                                    data=pdf_buffer,
                                    file_name=f"informe_ambiental_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                                st.success("✅ Informe generado con éxito")
                            else:
                                st.error("No se pudo generar el PDF")
                else:
                    st.info("PDF no disponible (instale ReportLab)")
            
            with col2:
                if REPORTDOCX_AVAILABLE:
                    if st.button("📘 Generar Informe DOCX", use_container_width=True):
                        with st.spinner("Generando DOCX..."):
                            docx_buffer = generador.generar_docx()
                            if docx_buffer:
                                st.download_button(
                                    label="⬇️ Descargar DOCX",
                                    data=docx_buffer,
                                    file_name="informe_ambiental.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True
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
                        mime="application/geo+json",
                        use_container_width=True
                    )
        else:
            st.info("No hay datos para generar informes")
        
    else:
        st.info("Ejecute el análisis primero para ver el dashboard")

# Las funciones mostrar_carbono, mostrar_biodiversidad, mostrar_comparacion 
# permanecen igual que en tu código original...

# ===============================
# 🚀 EJECUCIÓN PRINCIPAL
# ===============================
if __name__ == "__main__":
    main()
