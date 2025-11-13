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
        # Valores base para diferentes tipos de vegetación
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
    
    def procesar_poligono(self, gdf, vegetation_type, puntos_muestreo=50):
        """Procesar el polígono cargado y generar análisis integral"""
        
        if gdf is None or gdf.empty:
            return None
        
        try:
            # Obtener el polígono principal
            poligono = gdf.geometry.iloc[0]
            
            # Calcular área en hectáreas
            area_hectareas = self._calcular_area_hectareas(poligono)
            
            # Generar puntos de muestreo dentro del polígono
            puntos_muestreo_data = self._generar_puntos_muestreo(poligono, puntos_muestreo)
            
            # Realizar análisis integral en cada punto
            resultados = self._analisis_integral(puntos_muestreo_data, vegetation_type, area_hectareas)
            
            return {
                'poligono': poligono,
                'area_hectareas': area_hectareas,
                'puntos_muestreo': puntos_muestreo_data,
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
            return 1000  # Valor por defecto
    
    def _generar_puntos_muestreo(self, poligono, num_puntos):
        """Generar puntos de muestreo distribuidos dentro del polígono"""
        puntos = []
        bounds = poligono.bounds
        minx, miny, maxx, maxy = bounds
        
        puntos_generados = 0
        intentos = 0
        max_intentos = num_puntos * 10
        
        while puntos_generados < num_puntos and intentos < max_intentos:
            intentos += 1
            random_lon = np.random.uniform(minx, maxx)
            random_lat = np.random.uniform(miny, maxy)
            punto = Point(random_lon, random_lat)
            
            if poligono.contains(punto):
                puntos_generados += 1
                puntos.append({
                    'id': f"Punto_{puntos_generados}",
                    'lat': random_lat,
                    'lon': random_lon,
                    'geometry': punto
                })
        
        return puntos
    
    def _analisis_integral(self, puntos_muestreo, vegetation_type, area_total):
        """Realizar análisis integral con todos los indicadores"""
        
        # Obtener parámetros base del ecosistema
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
        
        for punto in puntos_muestreo:
            # 1. ANÁLISIS DE CARBONO
            carbono_info = self._analizar_carbono(punto, params, area_total / len(puntos_muestreo))
            carbono_data.append(carbono_info)
            
            # 2. ANÁLISIS DE VEGETACIÓN
            vegetacion_info = self._analizar_vegetacion(punto, params)
            vegetacion_data.append(vegetacion_info)
            
            # 3. ANÁLISIS DE BIODIVERSIDAD
            biodiversidad_info = self._analizar_biodiversidad(punto, params)
            biodiversidad_data.append(biodiversidad_info)
            
            # 4. ANÁLISIS HÍDRICO
            agua_info = self._analizar_recursos_hidricos(punto)
            agua_data.append(agua_info)
            
            # 5. ANÁLISIS DE SUELO
            suelo_info = self._analizar_suelo(punto)
            suelo_data.append(suelo_info)
            
            # 6. ANÁLISIS CLIMÁTICO
            clima_info = self._analizar_clima(punto)
            clima_data.append(clima_info)
            
            # 7. ANÁLISIS DE PRESIONES
            presiones_info = self._analizar_presiones(punto)
            presiones_data.append(presiones_info)
            
            # 8. ANÁLISIS DE CONECTIVIDAD
            conectividad_info = self._analizar_conectividad(punto)
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
    
    def _analizar_carbono(self, punto, params, area_punto):
        """Analizar indicadores de carbono"""
        base_carbon = np.random.uniform(params['carbono']['min'], params['carbono']['max'])
        ndvi = max(0.1, min(0.9, np.random.normal(params['ndvi_base'], 0.08)))
        
        # Ajustar carbono por salud de la vegetación
        carbono_ajustado = base_carbon * (0.3 + ndvi * 0.7)
        co2_potencial = carbono_ajustado * 3.67
        
        return {
            'area': punto['id'],
            'carbono_almacenado_tha': round(carbono_ajustado, 1),
            'co2_capturado_tha': round(co2_potencial, 1),
            'co2_total_ton': round(co2_potencial * area_punto, 1),
            'potencial_secuestro': 'Alto' if carbono_ajustado > 100 else 'Medio' if carbono_ajustado > 50 else 'Bajo',
            'ndvi': ndvi,
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_vegetacion(self, punto, params):
        """Analizar estado de la vegetación"""
        ndvi = max(0.1, min(0.9, np.random.normal(params['ndvi_base'], 0.08)))
        evi = ndvi * 0.9 + np.random.normal(0, 0.03)
        ndwi = (1 - ndvi) * 0.4 + np.random.normal(0, 0.02)
        lai = ndvi * 3 + np.random.normal(0, 0.5)  # Leaf Area Index
        
        # Clasificar salud de la vegetación
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
            'area': punto['id'],
            'ndvi': ndvi,
            'evi': evi,
            'ndwi': ndwi,
            'lai': lai,
            'salud_vegetacion': salud,
            'color_salud': color,
            'biomasa_tha': round(ndvi * 200 + np.random.uniform(0, 50), 1),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_biodiversidad(self, punto, params):
        """Analizar indicadores de biodiversidad"""
        # Índice de biodiversidad base según tipo de vegetación
        biodiversidad_base = params['biodiversidad']
        
        # Simular riqueza de especies
        riqueza_especies = int(biodiversidad_base * 100 + np.random.uniform(0, 30))
        
        # Índice de Shannon-Wiener
        shannon_index = biodiversidad_base * 2.5 + np.random.uniform(0, 0.5)
        
        # Especies endémicas
        endemismos = int(riqueza_especies * 0.1 + np.random.uniform(0, 5))
        
        # Estado de conservación
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
            'area': punto['id'],
            'riqueza_especies': riqueza_especies,
            'indice_shannon': round(shannon_index, 2),
            'especies_endemicas': endemismos,
            'estado_conservacion': estado,
            'color_estado': color,
            'diversidad_funcional': round(biodiversidad_base * 0.8 + np.random.uniform(0, 0.2), 2),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_recursos_hidricos(self, punto):
        """Analizar indicadores hídricos"""
        # Simular disponibilidad de agua
        disponibilidad_agua = np.random.uniform(0.2, 0.9)
        calidad_agua = np.random.uniform(0.3, 0.95)
        riesgo_sequia = 1 - disponibilidad_agua
        
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
            'area': punto['id'],
            'disponibilidad_agua': round(disponibilidad_agua, 2),
            'calidad_agua': round(calidad_agua, 2),
            'riesgo_sequia': round(riesgo_sequia, 2),
            'estado_hidrico': estado_agua,
            'color_estado_agua': color_agua,
            'infiltracion_suelo': round(np.random.uniform(0.1, 0.8), 2),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_suelo(self, punto):
        """Analizar calidad del suelo"""
        materia_organica = np.random.uniform(1.0, 8.0)
        erosion = np.random.uniform(0.1, 0.8)
        compactacion = np.random.uniform(0.1, 0.7)
        
        # Calcular salud del suelo
        salud_suelo = (materia_organica / 8.0 * 0.4 + 
                      (1 - erosion) * 0.3 + 
                      (1 - compactacion) * 0.3)
        
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
            'area': punto['id'],
            'materia_organica': round(materia_organica, 1),
            'erosión': round(erosion, 2),
            'compactacion': round(compactacion, 2),
            'salud_suelo': round(salud_suelo, 2),
            'estado_suelo': estado_suelo,
            'color_estado_suelo': color_suelo,
            'nutrientes': round(np.random.uniform(0.3, 0.9), 2),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_clima(self, punto):
        """Analizar indicadores climáticos"""
        # Simular datos climáticos
        temperatura = np.random.uniform(15, 35)
        precipitacion = np.random.uniform(500, 3000)
        humedad = np.random.uniform(40, 90)
        
        # Calcular vulnerabilidad climática
        vulnerabilidad = (temperatura - 15) / 20 * 0.4 + \
                        (3000 - precipitacion) / 2500 * 0.4 + \
                        (1 - humedad/100) * 0.2
        
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
            'area': punto['id'],
            'temperatura_promedio': round(temperatura, 1),
            'precipitacion_anual': round(precipitacion, 0),
            'humedad_relativa': round(humedad, 1),
            'vulnerabilidad_climatica': round(vulnerabilidad, 2),
            'riesgo_climatico': riesgo_climatico,
            'color_riesgo_clima': color_clima,
            'evapotranspiracion': round(precipitacion * 0.6 + np.random.uniform(-100, 100), 0),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_presiones(self, punto):
        """Analizar presiones antrópicas"""
        # Factores de presión
        presion_urbana = np.random.uniform(0, 1)
        presion_agricola = np.random.uniform(0, 1)
        presion_ganadera = np.random.uniform(0, 1)
        
        # Presión total
        presion_total = (presion_urbana * 0.4 + 
                        presion_agricola * 0.3 + 
                        presion_ganadera * 0.3)
        
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
            'area': punto['id'],
            'presion_urbana': round(presion_urbana, 2),
            'presion_agricola': round(presion_agricola, 2),
            'presion_ganadera': round(presion_ganadera, 2),
            'presion_total': round(presion_total, 2),
            'nivel_presion': nivel_presion,
            'color_presion': color_presion,
            'fragmentacion': round(presion_total * 0.8 + np.random.uniform(0, 0.2), 2),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _analizar_conectividad(self, punto):
        """Analizar conectividad ecológica"""
        # Factores de conectividad
        corredores = np.random.uniform(0.2, 0.9)
        fragmentacion = np.random.uniform(0.1, 0.8)
        permeabilidad = 1 - fragmentacion
        
        # Conectividad total
        conectividad = corredores * 0.5 + permeabilidad * 0.5
        
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
            'area': punto['id'],
            'corredores_ecologicos': round(corredores, 2),
            'fragmentacion': round(fragmentacion, 2),
            'permeabilidad': round(permeabilidad, 2),
            'conectividad_total': round(conectividad, 2),
            'estado_conectividad': estado_conectividad,
            'color_conectividad': color_conectividad,
            'movilidad_especies': round(conectividad * 0.9 + np.random.uniform(0, 0.1), 2),
            'lat': punto['lat'],
            'lon': punto['lon']
        }
    
    def _calcular_metricas_resumen(self, carbono, vegetacion, biodiversidad, agua, suelo, clima, presiones, conectividad):
        """Calcular métricas resumen para el dashboard"""
        
        # Métricas promedio
        avg_carbono = np.mean([p['co2_total_ton'] for p in carbono])
        avg_biodiversidad = np.mean([p['indice_shannon'] for p in biodiversidad])
        avg_agua = np.mean([p['disponibilidad_agua'] for p in agua])
        avg_suelo = np.mean([p['salud_suelo'] for p in suelo])
        avg_presiones = np.mean([p['presion_total'] for p in presiones])
        avg_conectividad = np.mean([p['conectividad_total'] for p in conectividad])
        
        # Distribución de estados
        estados_vegetacion = {}
        for p in vegetacion:
            estado = p['salud_vegetacion']
            estados_vegetacion[estado] = estados_vegetacion.get(estado, 0) + 1
        
        return {
            'carbono_total_co2_ton': round(avg_carbono * len(carbono), 1),
            'indice_biodiversidad_promedio': round(avg_biodiversidad, 2),
            'disponibilidad_agua_promedio': round(avg_agua, 2),
            'salud_suelo_promedio': round(avg_suelo, 2),
            'presion_antropica_promedio': round(avg_presiones, 2),
            'conectividad_promedio': round(avg_conectividad, 2),
            'distribucion_vegetacion': estados_vegetacion,
            'puntos_analizados': len(carbono),
            'estado_general': self._calcular_estado_general(avg_biodiversidad, avg_presiones, avg_conectividad)
        }
    
    def _calcular_estado_general(self, biodiversidad, presiones, conectividad):
        """Calcular estado general del ecosistema"""
        score = (biodiversidad / 2.5 * 0.4 + 
                (1 - presiones) * 0.4 + 
                conectividad * 0.2)
        
        if score > 0.7:
            return "Excelente"
        elif score > 0.5:
            return "Bueno"
        elif score > 0.3:
            return "Moderado"
        else:
            return "Crítico"

# ===============================
# 🗺️ FUNCIONES DE MAPAS Y VISUALIZACIONES
# ===============================

def crear_mapa_indicador(gdf, datos, indicador, columna, titulo, colores):
    """Crear mapa para un indicador específico"""
    if gdf is None or datos is None:
        return crear_mapa_base()
    
    try:
        centroide = gdf.geometry.iloc[0].centroid
        m = folium.Map(location=[centroide.y, centroide.x], zoom_start=12, tiles='OpenStreetMap')
        
        # Agregar polígono base
        poligono_geojson = gdf.__geo_interface__
        folium.GeoJson(
            poligono_geojson,
            style_function=lambda x: {
                'fillColor': '#2E8B57',
                'color': '#228B22',
                'weight': 2,
                'fillOpacity': 0.1
            }
        ).add_to(m)
        
        # Agregar puntos del indicador
        for punto in datos:
            valor = punto[columna]
            
            # Determinar color basado en el valor
            color = 'gray'
            for rango, color_rango in colores.items():
                if valor >= rango[0] and valor <= rango[1]:
                    color = color_rango
                    break
            
            popup_text = f"""
            <div style="min-width: 250px;">
                <h4>📍 {punto['area']}</h4>
                <p><b>{titulo}:</b> {valor}</p>
                <p><b>Coordenadas:</b> {punto['lat']:.4f}, {punto['lon']:.4f}</p>
            </div>
            """
            
            folium.CircleMarker(
                location=[punto['lat'], punto['lon']],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{punto['area']}: {valor}",
                color=color,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Error creando mapa: {str(e)}")
        return crear_mapa_base()

def crear_mapa_base():
    """Crear mapa base simple"""
    return folium.Map(location=[-14.0, -60.0], zoom_start=4, tiles='OpenStreetMap')

def crear_grafico_barras(datos, columna, titulo, color):
    """Crear gráfico de barras para un indicador"""
    if not datos:
        return go.Figure()
    
    df = pd.DataFrame(datos)
    fig = px.bar(df, x='area', y=columna, title=titulo, color_discrete_sequence=[color])
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', showlegend=False)
    return fig

def crear_grafico_pastel(datos, columna_valor, columna_etiqueta, titulo):
    """Crear gráfico de pastel para distribución"""
    if not datos:
        return go.Figure()
    
    df = pd.DataFrame(datos)
    conteo = df[columna_etiqueta].value_counts()
    
    fig = px.pie(values=conteo.values, names=conteo.index, title=titulo)
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
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
        
        puntos_muestreo = st.slider("🔍 Puntos de muestreo", 10, 200, 50)
        
        return uploaded_file, vegetation_type, puntos_muestreo

# ===============================
# 🎯 APLICACIÓN PRINCIPAL
# ===============================

def main():
    aplicar_estilos_globales()
    crear_header()
    initialize_session_state()
    
    # Sidebar
    uploaded_file, vegetation_type, puntos_muestreo = sidebar_config()
    
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
            st.metric("Puntos de muestreo", puntos_muestreo)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de análisis
    if tiene_poligono_data() and not st.session_state.analysis_complete:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        if st.button("🚀 EJECUTAR ANÁLISIS INTEGRAL", type="primary", use_container_width=True):
            with st.spinner("Realizando análisis integral de biodiversidad..."):
                resultados = st.session_state.analyzer.procesar_poligono(
                    st.session_state.poligono_data, vegetation_type, puntos_muestreo
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
            st.metric("🔍 Puntos Analizados", summary['puntos_analizados'])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # MAPAS Y ANÁLISIS POR INDICADOR
        indicadores = [
            {
                'key': 'carbono',
                'titulo': '🌳 Almacenamiento de Carbono',
                'columna': 'co2_total_ton',
                'colores': {(0, 1000): '#ffffcc', (1000, 5000): '#c2e699', (5000, 10000): '#78c679', (10000, 50000): '#238443', (50000, 1000000): '#00441b'}
            },
            {
                'key': 'vegetacion',
                'titulo': '🌿 Salud de la Vegetación (NDVI)',
                'columna': 'ndvi',
                'colores': {(0, 0.3): '#FF4500', (0.3, 0.5): '#FFD700', (0.5, 0.7): '#32CD32', (0.7, 1.0): '#006400'}
            },
            {
                'key': 'biodiversidad',
                'titulo': '🦋 Índice de Biodiversidad',
                'columna': 'indice_shannon',
                'colores': {(0, 1.0): '#FF4500', (1.0, 1.5): '#FFD700', (1.5, 2.0): '#32CD32', (2.0, 3.0): '#006400'}
            },
            {
                'key': 'agua',
                'titulo': '💧 Disponibilidad de Agua',
                'columna': 'disponibilidad_agua',
                'colores': {(0, 0.3): '#FF4500', (0.3, 0.5): '#FFD700', (0.5, 0.7): '#87CEEB', (0.7, 1.0): '#1E90FF'}
            },
            {
                'key': 'suelo',
                'titulo': '🌱 Salud del Suelo',
                'columna': 'salud_suelo',
                'colores': {(0, 0.3): '#FF4500', (0.3, 0.5): '#FFD700', (0.5, 0.7): '#CD853F', (0.7, 1.0): '#8B4513'}
            },
            {
                'key': 'presiones',
                'titulo': '⚠️ Presión Antrópica',
                'columna': 'presion_total',
                'colores': {(0, 0.3): '#32CD32', (0.3, 0.6): '#FFD700', (0.6, 1.0): '#FF4500'}
            }
        ]
        
        for indicador in indicadores:
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.subheader(indicador['titulo'])
            
            # Mapa
            mapa = crear_mapa_indicador(
                st.session_state.poligono_data,
                resultados['resultados'][indicador['key']],
                indicador['key'],
                indicador['columna'],
                indicador['titulo'],
                indicador['colores']
            )
            st_folium(mapa, width=800, height=400, key=f"map_{indicador['key']}")
            
            # Gráfico
            fig = crear_grafico_barras(
                resultados['resultados'][indicador['key']],
                indicador['columna'],
                f"Distribución de {indicador['titulo']}",
                list(indicador['colores'].values())[-1]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif not tiene_poligono_data():
        # Pantalla de bienvenida
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Análisis Integral de Biodiversidad!
        
        ### 🌿 Sistema de Evaluación Ecológica Completa
        
        Esta herramienta realiza un análisis **integral** de biodiversidad que incluye:
        
        **📊 Indicadores Analizados:**
        - 🌳 **Carbono**: Almacenamiento y secuestro de carbono
        - 🌿 **Vegetación**: Salud, biomasa y productividad
        - 🦋 **Biodiversidad**: Riqueza de especies y conservación
        - 💧 **Recursos Hídricos**: Disponibilidad y calidad del agua
        - 🌱 **Suelo**: Salud y calidad edáfica
        - ☀️ **Clima**: Vulnerabilidad y riesgos climáticos
        - ⚠️ **Presiones**: Impacto antrópico y fragmentación
        - 🔗 **Conectividad**: Corredores ecológicos y permeabilidad
        
        **🎯 Métodología:**
        1. **Carga tu polígono** en formato KML o Shapefile
        2. **Configura** el tipo de vegetación predominante
        3. **Ejecuta el análisis** con múltiples puntos de muestreo
        4. **Obtén resultados** detallados con mapas interactivos
        
        **¡Comienza cargando tu archivo en el sidebar!** ←
        """)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
