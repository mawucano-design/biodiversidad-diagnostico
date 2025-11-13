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
# 🧩 CLASE PRINCIPAL DE ANÁLISIS
# ===============================

class AnalizadorBiodiversidad:
    """Analizador integral de biodiversidad para el polígono cargado"""
    
    def __init__(self):
        self.parametros_ecosistemas = {
            'Bosque Denso Primario': {
                'carbono': {'min': 180, 'max': 320},
                'biodiversidad': 0.9,
                'ndvi_base': 0.85,
                'resiliencia': 0.8
            },
            'Bosque Secundario': {
                'carbono': {'min': 80, 'max': 160},
                'biodiversidad': 0.7,
                'ndvi_base': 0.75,
                'resiliencia': 0.6
            },
            'Bosque Ripario': {
                'carbono': {'min': 120, 'max': 220},
                'biodiversidad': 0.8,
                'ndvi_base': 0.80,
                'resiliencia': 0.7
            },
            'Matorral Denso': {
                'carbono': {'min': 40, 'max': 70},
                'biodiversidad': 0.5,
                'ndvi_base': 0.65,
                'resiliencia': 0.5
            },
            'Matorral Abierto': {
                'carbono': {'min': 20, 'max': 40},
                'biodiversidad': 0.3,
                'ndvi_base': 0.45,
                'resiliencia': 0.4
            },
            'Sabana Arborizada': {
                'carbono': {'min': 25, 'max': 45},
                'biodiversidad': 0.4,
                'ndvi_base': 0.35,
                'resiliencia': 0.5
            },
            'Herbazal Natural': {
                'carbono': {'min': 8, 'max': 18},
                'biodiversidad': 0.2,
                'ndvi_base': 0.25,
                'resiliencia': 0.3
            },
            'Zona de Transición': {
                'carbono': {'min': 15, 'max': 30},
                'biodiversidad': 0.3,
                'ndvi_base': 0.30,
                'resiliencia': 0.4
            },
            'Área de Restauración': {
                'carbono': {'min': 30, 'max': 90},
                'biodiversidad': 0.6,
                'ndvi_base': 0.55,
                'resiliencia': 0.7
            }
        }
    
    def procesar_poligono(self, gdf, vegetation_type, divisiones=5):
        """Procesar el polígono cargado dividiéndolo en áreas regulares"""
        
        if gdf is None or gdf.empty:
            return None
        
        try:
            # Obtener el polígono principal
            poligono = gdf.geometry.iloc[0]
            
            # Calcular área en hectáreas
            area_hectareas = self._calcular_area_hectareas(poligono)
            
            # Generar áreas regulares dentro del polígono
            areas_data = self._generar_areas_regulares(poligono, divisiones)
            
            # Realizar análisis integral en cada área
            resultados = self._analisis_integral(areas_data, vegetation_type, area_hectareas)
            
            return {
                'poligono': poligono,
                'area_hectareas': area_hectareas,
                'areas_analisis': areas_data,
                'resultados': resultados,
                'centroide': poligono.centroid,
                'tipo_vegetacion': vegetation_type
            }
        except Exception as e:
            st.error(f"Error procesando polígono: {str(e)}")
            return None
    
    def _calcular_area_hectareas(self, poligono):
        """Calcular área en hectáreas"""
        try:
            bounds = poligono.bounds
            area_aproximada = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) * 11100 * 11100 * 0.8
            return round(area_aproximada / 10000, 2)
        except:
            return 1000
    
    def _generar_areas_regulares(self, poligono, divisiones):
        """Generar áreas regulares (grid) dentro del polígono"""
        areas = []
        bounds = poligono.bounds
        minx, miny, maxx, maxy = bounds
        
        # Calcular tamaño de cada celda
        delta_x = (maxx - minx) / divisiones
        delta_y = (maxy - miny) / divisiones
        
        for i in range(divisiones):
            for j in range(divisiones):
                # Crear polígono de la celda
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
                
                # Verificar si la celda intersecta con el polígono principal
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
        
        # Inicializar listas de resultados
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
            
            # 1. ANÁLISIS DE CARBONO
            carbono_info = self._analizar_carbono(area, params, area['area_ha'])
            carbono_data.append(carbono_info)
            
            # 2. ANÁLISIS DE VEGETACIÓN
            vegetacion_info = self._analizar_vegetacion(area, params)
            vegetacion_data.append(vegetacion_info)
            
            # 3. ANÁLISIS DE BIODIVERSIDAD
            biodiversidad_info = self._analizar_biodiversidad(area, params)
            biodiversidad_data.append(biodiversidad_info)
            
            # 4. ANÁLISIS HÍDRICO
            agua_info = self._analizar_recursos_hidricos(area)
            agua_data.append(agua_info)
            
            # 5. ANÁLISIS DE SUELO
            suelo_info = self._analizar_suelo(area)
            suelo_data.append(suelo_info)
            
            # 6. ANÁLISIS CLIMÁTICO
            clima_info = self._analizar_clima(area)
            clima_data.append(clima_info)
            
            # 7. ANÁLISIS DE PRESIONES
            presiones_info = self._analizar_presiones(area)
            presiones_data.append(presiones_info)
            
            # 8. ANÁLISIS DE CONECTIVIDAD
            conectividad_info = self._analizar_conectividad(area)
            conectividad_data.append(conectividad_info)
        
        # Calcular métricas resumen
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
    
    def _analizar_biodiversidad(self, area, params):
        """Analizar indicadores de biodiversidad"""
        biodiversidad_base = params['biodiversidad']
        riqueza_especies = int(biodiversidad_base * 100 + np.random.uniform(0, 30))
        shannon_index = biodiversidad_base * 2.5 + np.random.uniform(0, 0.5)
        
        if biodiversidad_base > 0.7:
            estado = "Alto"
            color = '#006400'
        elif biodiversidad_base > 0.5:
            estado = "Medio"
            color = '#32CD32'
        elif biodiversidad_base > 0.3:
            estado = "Bajo"
            color = '#FFD700'
        else:
            estado = "Crítico"
            color = '#FF4500'
        
        return {
            'area': area['id'],
            'riqueza_especies': riqueza_especies,
            'indice_shannon': round(shannon_index, 2),
            'estado_conservacion': estado,
            'color_estado': color,
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
        
        avg_carbono = np.mean([p['co2_total_ton'] for p in carbono])
        avg_biodiversidad = np.mean([p['indice_shannon'] for p in biodiversidad])
        avg_agua = np.mean([p['disponibilidad_agua'] for p in agua])
        avg_suelo = np.mean([p['salud_suelo'] for p in suelo])
        avg_presiones = np.mean([p['presion_total'] for p in presiones])
        avg_conectividad = np.mean([p['conectividad_total'] for p in conectividad])
        
        return {
            'carbono_total_co2_ton': round(avg_carbono * len(carbono), 1),
            'indice_biodiversidad_promedio': round(avg_biodiversidad, 2),
            'disponibilidad_agua_promedio': round(avg_agua, 2),
            'salud_suelo_promedio': round(avg_suelo, 2),
            'presion_antropica_promedio': round(avg_presiones, 2),
            'conectividad_promedio': round(avg_conectividad, 2),
            'areas_analizadas': len(carbono),
            'estado_general': self._calcular_estado_general(avg_biodiversidad, avg_presiones, avg_conectividad)
        }
    
    def _calcular_estado_general(self, biodiversidad, presiones, conectividad):
        score = (biodiversidad / 2.5 * 0.4 + (1 - presiones) * 0.4 + conectividad * 0.2)
        if score > 0.7: return "Excelente"
        elif score > 0.5: return "Bueno"
        elif score > 0.3: return "Moderado"
        else: return "Crítico"

# ===============================
# 🗺️ FUNCIONES DE MAPAS MEJORADAS
# ===============================

def crear_mapa_indicador(gdf, datos, indicador_config):
    """Crear mapa con áreas para un indicador específico usando ESRI Satellite"""
    if gdf is None or datos is None:
        return crear_mapa_base()
    
    try:
        centroide = gdf.geometry.iloc[0].centroid
        m = folium.Map(
            location=[centroide.y, centroide.x], 
            zoom_start=12, 
            tiles=None  # Desactivamos tiles por defecto
        )
        
        # Agregar ESRI Satellite como capa base
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite ESRI',
            overlay=False
        ).add_to(m)
        
        # Agregar OpenStreetMap como alternativa
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap'
        ).add_to(m)
        
        # Agregar áreas del indicador
        for area_data in datos:
            valor = area_data[indicador_config['columna']]
            geometry = area_data['geometry']
            
            # Determinar color basado en el valor
            color = 'gray'
            for rango, color_rango in indicador_config['colores'].items():
                if valor >= rango[0] and valor <= rango[1]:
                    color = color_rango
                    break
            
            # Crear GeoJSON para el área
            area_geojson = gpd.GeoSeries([geometry]).__geo_interface__
            
            folium.GeoJson(
                area_geojson,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': color,
                    'weight': 2,
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
        
        # Agregar leyenda detallada
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
        folium.LayerControl().add_to(m)
        
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
# 📊 FUNCIONES DE VISUALIZACIÓN MEJORADAS
# ===============================

def crear_grafico_radar(datos, categorias):
    """Crear gráfico radar para comparación de indicadores"""
    if not datos:
        return go.Figure()
    
    fig = go.Figure()
    
    for area in datos[:5]:  # Mostrar solo las primeras 5 áreas para claridad
        valores = [area.get(cat, 0) for cat in categorias.keys()]
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=list(categorias.values()),
            fill='toself',
            name=area['area']
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
    
    df = pd.DataFrame(datos)
    conteo_estado = df[columna_estado].value_counts()
    
    fig = px.sunburst(
        names=conteo_estado.index,
        parents=[''] * len(conteo_estado),
        values=conteo_estado.values,
        title=titulo
    )
    
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
    return fig

def crear_grafico_3d_scatter(datos, ejes_config):
    """Crear gráfico 3D scatter para relación entre indicadores"""
    if not datos:
        return go.Figure()
    
    df = pd.DataFrame(datos)
    
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

def crear_heatmap_correlacion(datos, indicadores):
    """Crear heatmap de correlación entre indicadores"""
    if not datos:
        return go.Figure()
    
    df = pd.DataFrame(datos)
    correlaciones = df[list(indicadores.keys())].corr()
    
    fig = ff.create_annotated_heatmap(
        z=correlaciones.values,
        x=list(indicadores.values()),
        y=list(indicadores.values()),
        annotation_text=correlaciones.round(2).values,
        colorscale='Viridis'
    )
    
    fig.update_layout(title="Correlación entre Indicadores")
    return fig

# ===============================
# 📁 MANEJO DE ARCHIVOS
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
        uploaded_file = st.file_uploader("Sube tu archivo territorial", type=['kml', 'zip'])
        
        if uploaded_file is not None and not st.session_state.file_processed:
            with st.spinner("Procesando archivo..."):
                gdf = procesar_archivo_cargado(uploaded_file)
                if gdf is not None:
                    st.session_state.poligono_data = gdf
                    st.session_state.file_processed = True
                    st.session_state.analysis_complete = False
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
            st.metric("Área aproximada", f"{area_ha:,} ha")
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
                    st.success("✅ Análisis completado exitosamente!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar resultados del análisis
    if st.session_state.analysis_complete and st.session_state.results:
        resultados = st.session_state.results
        summary = resultados['resultados']['summary_metrics']
        
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
                    (0, 1.0): 'Baja (0-1.0)',
                    (1.0, 1.5): 'Moderada (1.0-1.5)', 
                    (1.5, 2.0): 'Alta (1.5-2.0)',
                    (2.0, 3.0): 'Muy Alta (2.0-3.0)'
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
        
        # MAPAS POR INDICADOR
        for config in indicadores_config:
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.subheader(config['titulo'])
            
            # Mapa con áreas
            mapa = crear_mapa_indicador(
                st.session_state.poligono_data,
                resultados['resultados'][config['key']],
                config
            )
            st_folium(mapa, width=800, height=500, key=f"map_{config['key']}")
            
            # Visualizaciones alternativas
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                # Gráfico Sunburst para distribución
                st.plotly_chart(
                    crear_grafico_sunburst(
                        resultados['resultados'][config['key']],
                        config['columna'],
                        next((k for k in resultados['resultados'][config['key']][0].keys() if 'estado' in k), config['columna']),
                        f"Distribución de {config['titulo']}"
                    ),
                    use_container_width=True
                )
            
            with col_viz2:
                # Heatmap de correlación para los primeros indicadores
                if config['key'] in ['carbono', 'vegetacion']:
                    indicadores_corr = {
                        'ndvi': 'Salud Vegetación',
                        'co2_total_ton': 'Carbono',
                        'indice_shannon': 'Biodiversidad', 
                        'disponibilidad_agua': 'Agua'
                    }
                    st.plotly_chart(
                        crear_heatmap_correlacion(
                            resultados['resultados'][config['key']],
                            indicadores_corr
                        ),
                        use_container_width=True
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # VISUALIZACIONES AVANZADAS
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 Análisis Multivariado")
        
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            # Gráfico Radar
            categorias_radar = {
                'ndvi': 'Vegetación',
                'indice_shannon': 'Biodiversidad',
                'disponibilidad_agua': 'Agua',
                'salud_suelo': 'Suelo',
                'conectividad_total': 'Conectividad'
            }
            st.plotly_chart(
                crear_grafico_radar(resultados['resultados']['vegetacion'], categorias_radar),
                use_container_width=True
            )
        
        with col_adv2:
            # Gráfico 3D
            ejes_3d = {
                'x': 'ndvi',
                'y': 'indice_shannon', 
                'z': 'co2_total_ton',
                'color': 'ndvi',
                'size': 'co2_total_ton',
                'titulo': 'Relación Vegetación-Biodiversidad-Carbono'
            }
            # Combinar datos para 3D
            datos_combinados = []
            for i in range(len(resultados['resultados']['vegetacion'])):
                combo = {
                    'area': resultados['resultados']['vegetacion'][i]['area'],
                    'ndvi': resultados['resultados']['vegetacion'][i]['ndvi'],
                    'indice_shannon': resultados['resultados']['biodiversidad'][i]['indice_shannon'],
                    'co2_total_ton': resultados['resultados']['carbono'][i]['co2_total_ton']
                }
                datos_combinados.append(combo)
            
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
        - 📊 **Visualizaciones Avanzadas** - Gráficos 3D, radar, sunburst
        - 🎨 **Leyendas Detalladas** - Información clara y comprensible
        - 🔗 **Análisis Multivariado** - Relaciones entre indicadores
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
