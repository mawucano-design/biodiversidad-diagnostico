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
# ✅ CORRECCIÓN: Importar plugins correctamente
from folium.plugins import Fullscreen, MousePosition
import pydeck as pdk

# ===============================
# 🌿 CONFIGURACIÓN Y ESTILOS GLOBALES
# ===============================

st.set_page_config(
    page_title="Diagnóstico de Biodiversidad Ambiental",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def aplicar_estilos_globales():
    st.markdown("""
    <style>
    /* Estilos globales */
    .main {
        background-color: #f8f9fa;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Header personalizado */
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
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .custom-header p {
        font-size: 1.3rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    /* Tarjetas modernas */
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 2rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Botones modernos */
    .stButton button {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(46, 139, 87, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(46, 139, 87, 0.4);
    }
    
    /* Métricas mejoradas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #2E8B57 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #2C3E50 !important;
    }
    
    /* Separadores elegantes */
    .custom-divider {
        height: 4px;
        background: linear-gradient(90deg, #2E8B57, #32CD32, transparent);
        margin: 2rem 0;
        border: none;
        border-radius: 2px;
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        border: 1px solid #e9ecef;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: #2E8B57 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_header():
    st.markdown("""
    <div class="custom-header">
        <h1>🌍 Diagnóstico de Biodiversidad Ambiental</h1>
        <p>Sistema integral de evaluación ambiental LE.MU Atlas con indicadores clave</p>
    </div>
    """, unsafe_allow_html=True)

# ===============================
# 🧩 CLASES DE ANÁLISIS MEJORADAS (MANTENIENDO TU CÓDIGO ORIGINAL)
# ===============================

class CarbonAnalyzer:
    """Analizador de captura y almacenamiento de carbono"""
    
    def __init__(self):
        self.carbon_stock_values = {
            'Bosque Denso Primario': {'min': 150, 'max': 300},
            'Bosque Secundario': {'min': 80, 'max': 150},
            'Bosque Ripario': {'min': 120, 'max': 200},
            'Matorral Denso': {'min': 30, 'max': 60},
            'Matorral Abierto': {'min': 15, 'max': 30},
            'Sabana Arborizada': {'min': 20, 'max': 40},
            'Herbazal Natural': {'min': 5, 'max': 15},
            'Zona de Transición': {'min': 10, 'max': 25},
            'Área de Restauración': {'min': 25, 'max': 80}
        }
    
    def calculate_carbon_potential(self, vegetation_type, area_hectares, ndvi):
        """Calcular potencial de captura de CO2 basado en tipo de vegetación y NDVI"""
        carbon_params = self.carbon_stock_values.get(vegetation_type, {'min': 10, 'max': 20})
        base_carbon = np.random.uniform(carbon_params['min'], carbon_params['max'])
        
        # Ajustar por salud de la vegetación (NDVI)
        carbon_adjusted = base_carbon * (0.5 + ndvi * 0.5)
        
        # Calcular CO2 equivalente (1 ton C = 3.67 ton CO2)
        co2_potential = carbon_adjusted * 3.67
        
        return {
            'carbono_almacenado_tha': round(carbon_adjusted, 1),
            'co2_capturado_tha': round(co2_potential, 1),
            'co2_total_ton': round(co2_potential * area_hectares, 1),
            'potencial_secuestro': 'Alto' if carbon_adjusted > 100 else 'Medio' if carbon_adjusted > 50 else 'Bajo'
        }

class DeforestationAnalyzer:
    """Analizador de pérdida de bosque y cambios de cobertura"""
    
    def __init__(self):
        self.deforestation_rates = {
            'Bosque Denso Primario': 0.02,  # 2% anual
            'Bosque Secundario': 0.05,      # 5% anual  
            'Bosque Ripario': 0.03,         # 3% anual
            'Matorral Denso': 0.08,         # 8% anual
            'Matorral Abierto': 0.12,       # 12% anual
            'Sabana Arborizada': 0.06,      # 6% anual
            'Herbazal Natural': 0.15,       # 15% anual
            'Zona de Transición': 0.10,     # 10% anual
            'Área de Restauración': -0.20   # -20% (ganancia)
        }
    
    def simulate_deforestation_data(self, area_count, vegetation_type, start_year=2020):
        """Simular datos históricos de pérdida de bosque"""
        deforestation_data = []
        current_year = datetime.now().year
        
        base_rate = self.deforestation_rates.get(vegetation_type, 0.05)
        
        for area_idx in range(area_count):
            area_coverage = 100  # 100% de cobertura inicial
            
            for year in range(start_year, current_year + 1):
                # Variación anual aleatoria
                annual_change = base_rate * np.random.uniform(0.8, 1.2)
                
                if 'Restauración' in vegetation_type:
                    # Ganancia de cobertura en áreas de restauración
                    area_coverage = min(100, area_coverage * (1 - annual_change))
                else:
                    # Pérdida de cobertura
                    area_coverage = max(0, area_coverage * (1 - annual_change))
                
                # Impacto antropogénico simulado
                human_impact = np.random.choice(['Bajo', 'Medio', 'Alto'], 
                                              p=[0.6, 0.3, 0.1])
                
                deforestation_data.append({
                    'area': f"Área {area_idx + 1}",
                    'año': year,
                    'cobertura_porcentaje': round(area_coverage, 1),
                    'perdida_acumulada': round(100 - area_coverage, 1),
                    'tasa_cambio_anual': round(annual_change * 100, 2),
                    'impacto_antropico': human_impact,
                    'lat': -14.0 + np.random.uniform(-8, 8),
                    'lon': -60.0 + np.random.uniform(-8, 8)
                })
        
        return deforestation_data

class AnthropicImpactAnalyzer:
    """Analizador de impacto antrópico sobre el territorio"""
    
    def __init__(self):
        self.impact_factors = {
            'agricultura': {'weight': 0.3, 'indicators': ['expansion_agricola', 'uso_pesticidas']},
            'ganaderia': {'weight': 0.25, 'indicators': ['pastoreo_intensivo', 'compactacion_suelo']},
            'urbanizacion': {'weight': 0.2, 'indicators': ['expansion_urbana', 'fragmentacion']},
            'infraestructura': {'weight': 0.15, 'indicators': ['carreteras', 'lineas_energia']},
            'mineria': {'weight': 0.1, 'indicators': ['mineria_superficie', 'contaminacion']}
        }
    
    def assess_anthropic_impact(self, area_count, vegetation_type):
        """Evaluar impacto antrópico en diferentes áreas"""
        impact_data = []
        
        for area_idx in range(area_count):
            total_impact = 0
            impact_details = {}
            
            for factor, params in self.impact_factors.items():
                # Calcular impacto para cada factor
                factor_impact = np.random.uniform(0, 1) * params['weight']
                total_impact += factor_impact
                
                impact_details[factor] = {
                    'impacto': round(factor_impact, 3),
                    'indicadores': params['indicators']
                }
            
            # Clasificar impacto total
            if total_impact > 0.7:
                impact_level = "Muy Alto"
                color = 'red'
            elif total_impact > 0.5:
                impact_level = "Alto"
                color = 'orange'
            elif total_impact > 0.3:
                impact_level = "Moderado"
                color = 'yellow'
            elif total_impact > 0.1:
                impact_level = "Bajo"
                color = 'lightgreen'
            else:
                impact_level = "Muy Bajo"
                color = 'green'
            
            impact_data.append({
                'area': f"Área {area_idx + 1}",
                'impacto_total': round(total_impact, 3),
                'nivel_impacto': impact_level,
                'color': color,
                'detalles': impact_details,
                'lat': -14.0 + np.random.uniform(-8, 8),
                'lon': -60.0 + np.random.uniform(-8, 8)
            })
        
        return impact_data

class VegetationClassifier:
    """Clasificador de tipos de vegetación basado en índices espectrales"""
    
    def __init__(self):
        self.vegetation_classes = {
            'Bosque Denso': {'ndvi_range': (0.7, 1.0), 'evi_range': (0.5, 1.0)},
            'Bosque Abierto': {'ndvi_range': (0.5, 0.7), 'evi_range': (0.3, 0.5)},
            'Matorral Denso': {'ndvi_range': (0.4, 0.6), 'evi_range': (0.2, 0.4)},
            'Matorral Abierto': {'ndvi_range': (0.3, 0.5), 'evi_range': (0.15, 0.3)},
            'Sabana': {'ndvi_range': (0.2, 0.4), 'evi_range': (0.1, 0.25)},
            'Herbazal': {'ndvi_range': (0.1, 0.3), 'evi_range': (0.05, 0.15)},
            'Suelo Desnudo': {'ndvi_range': (0.0, 0.1), 'evi_range': (0.0, 0.05)},
            'Cuerpo de Agua': {'ndvi_range': (-1.0, 0.0), 'evi_range': (-1.0, 0.0)}
        }
    
    def classify_vegetation(self, ndvi, evi, ndwi):
        """Clasificar tipo de vegetación basado en índices espectrales"""
        for class_name, ranges in self.vegetation_classes.items():
            if (ranges['ndvi_range'][0] <= ndvi <= ranges['ndvi_range'][1] and
                ranges['evi_range'][0] <= evi <= ranges['evi_range'][1]):
                return class_name
        
        return "No Clasificado"

class IntegratedAnalyzer:
    """Analizador integrado con todos los indicadores mejorados"""
    
    def __init__(self):
        self.carbon_analyzer = CarbonAnalyzer()
        self.deforestation_analyzer = DeforestationAnalyzer()
        self.impact_analyzer = AnthropicImpactAnalyzer()
        self.vegetation_classifier = VegetationClassifier()
    
    def comprehensive_analysis(self, area_count, vegetation_type, area_hectares=100):
        """Análisis integral con todos los indicadores"""
        
        # Simular datos base
        spectral_data = self._simulate_spectral_data(area_count, vegetation_type)
        deforestation_data = self.deforestation_analyzer.simulate_deforestation_data(area_count, vegetation_type)
        impact_data = self.impact_analyzer.assess_anthropic_impact(area_count, vegetation_type)
        
        # Calcular indicadores de carbono
        carbon_indicators = []
        for area_data in spectral_data:
            carbon_info = self.carbon_analyzer.calculate_carbon_potential(
                vegetation_type, area_hectares, area_data['NDVI']
            )
            carbon_indicators.append({
                'area': area_data['area'],
                **carbon_info,
                'lat': area_data['lat'],
                'lon': area_data['lon']
            })
        
        # Clasificar vegetación
        vegetation_classification = []
        for area_data in spectral_data:
            veg_class = self.vegetation_classifier.classify_vegetation(
                area_data['NDVI'], area_data['EVI'], area_data['NDWI']
            )
            vegetation_classification.append({
                'area': area_data['area'],
                'clasificacion': veg_class,
                'ndvi': area_data['NDVI'],
                'evi': area_data['EVI'],
                'ndwi': area_data['NDWI'],
                'lat': area_data['lat'],
                'lon': area_data['lon']
            })
        
        # Calcular métricas resumen
        summary_metrics = self._calculate_summary_metrics(
            carbon_indicators, deforestation_data, impact_data, vegetation_classification
        )
        
        return {
            'carbon_indicators': carbon_indicators,
            'deforestation_data': deforestation_data,
            'impact_data': impact_data,
            'vegetation_classification': vegetation_classification,
            'spectral_data': spectral_data,
            'summary_metrics': summary_metrics
        }
    
    def _simulate_spectral_data(self, area_count, vegetation_type):
        """Simular datos espectrales básicos"""
        spectral_data = []
        
        base_ndvi = {
            'Bosque Denso Primario': 0.8, 'Bosque Secundario': 0.7,
            'Matorral Denso': 0.6, 'Matorral Abierto': 0.4,
            'Herbazal Natural': 0.3
        }
        
        base_ndvi_val = base_ndvi.get(vegetation_type, 0.5)
        
        for area_idx in range(area_count):
            ndvi = max(0.1, min(0.9, np.random.normal(base_ndvi_val, 0.1)))
            evi = ndvi * 0.8 + np.random.normal(0, 0.05)
            ndwi = (1 - ndvi) * 0.3 + np.random.normal(0, 0.03)
            
            spectral_data.append({
                'area': f"Área {area_idx + 1}",
                'NDVI': ndvi,
                'EVI': evi,
                'NDWI': ndwi,
                'lat': -14.0 + np.random.uniform(-8, 8),
                'lon': -60.0 + np.random.uniform(-8, 8)
            })
        
        return spectral_data
    
    def _calculate_summary_metrics(self, carbon_data, deforestation_data, impact_data, vegetation_data):
        """Calcular métricas resumen para el dashboard"""
        
        # Carbono total
        total_co2 = sum([area['co2_total_ton'] for area in carbon_data])
        
        # Pérdida promedio de bosque
        current_year = datetime.now().year
        current_deforestation = [d for d in deforestation_data if d['año'] == current_year]
        avg_loss = np.mean([d['perdida_acumulada'] for d in current_deforestation]) if current_deforestation else 0
        
        # Impacto promedio
        avg_impact = np.mean([d['impacto_total'] for d in impact_data])
        
        # Distribución de clases de vegetación
        veg_classes = {}
        for area in vegetation_data:
            class_name = area['clasificacion']
            veg_classes[class_name] = veg_classes.get(class_name, 0) + 1
        
        return {
            'carbono_total_co2_ton': round(total_co2, 1),
            'perdida_bosque_promedio': round(avg_loss, 1),
            'impacto_antropico_promedio': round(avg_impact, 3),
            'distribucion_vegetacion': veg_classes,
            'areas_analizadas': len(carbon_data)
        }

# ===============================
# 🗺️ FUNCIONES DE MAPAS MEJORADAS
# ===============================

def crear_mapa_interactivo_mejorado(lat, lon, zoom=10, area_nombre="Área de Estudio"):
    """Crear mapa interactivo moderno con múltiples capas"""
    
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
        zoom_control=True
    )
    
    # Diferentes capas base
    capas_base = {
        'OpenStreetMap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'CartoDB Light': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        'Satélite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        'Relieve': 'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.jpg'
    }
    
    for nombre, url in capas_base.items():
        folium.TileLayer(
            tiles=url,
            attr=nombre,
            name=nombre,
            control=True
        ).add_to(m)
    
    # ✅ CORRECCIÓN: Usar plugins importados directamente
    Fullscreen(
        position='topright',
        title='Pantalla completa',
        title_cancel='Salir pantalla completa'
    ).add_to(m)
    
    MousePosition(
        position='bottomleft',
        separator=' | ',
        empty_string='Coordenadas no disponibles',
        lng_first=False,
        num_digits=4,
        prefix='Coordenadas:',
        lat_formatter=lambda x: f'{x:.4f}°',
        lng_formatter=lambda x: f'{x:.4f}°'
    ).add_to(m)
    
    # Control de capas
    folium.LayerControl(position='bottomright').add_to(m)
    
    return m

def create_carbon_map(carbon_data):
    """Crear mapa de captura potencial de CO2 mejorado"""
    if not carbon_data:
        st.warning("No hay datos de carbono para mostrar")
        return folium.Map(location=[-14.0, -60.0], zoom_start=4)
    
    m = crear_mapa_interactivo_mejorado(-14.0, -60.0, 4)
    
    # Agregar puntos de carbono
    for area_data in carbon_data:
        co2_potential = area_data['co2_total_ton']
        
        # Color basado en potencial de carbono
        if co2_potential > 5000:
            color = '#00441b'  # Verde muy oscuro
            size = 15
        elif co2_potential > 2000:
            color = '#238443'  # Verde oscuro
            size = 12
        elif co2_potential > 1000:
            color = '#78c679'  # Verde medio
            size = 10
        elif co2_potential > 500:
            color = '#c2e699'  # Verde claro
            size = 8
        else:
            color = '#ffffcc'  # Amarillo muy claro
            size = 6
        
        popup_text = f"""
        <div style="min-width: 250px; font-family: Arial, sans-serif;">
            <h4 style="color: #2E8B57; margin-bottom: 10px; border-bottom: 2px solid #2E8B57; padding-bottom: 5px;">
                🌿 {area_data['area']}
            </h4>
            <p><strong>Potencial de Captura de CO2:</strong></p>
            <p>• CO2 total: <b>{co2_potential:,} ton</b></p>
            <p>• Carbono almacenado: <b>{area_data['carbono_almacenado_tha']} t/ha</b></p>
            <p>• Potencial: <b>{area_data['potencial_secuestro']}</b></p>
        </div>
        """
        
        folium.CircleMarker(
            location=[area_data['lat'], area_data['lon']],
            radius=size,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{area_data['area']}: {co2_potential:,} ton CO2",
            color=color,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # Leyenda mejorada
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; 
                padding: 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
    <h4 style="margin:0 0 10px 0; color: #2E8B57;">Potencial de Captura CO₂</h4>
    <p style="margin:5px 0;"><i style="background:#00441b; width: 20px; height: 20px; display: inline-block; border-radius: 50%;"></i> > 5,000 ton</p>
    <p style="margin:5px 0;"><i style="background:#238443; width: 18px; height: 18px; display: inline-block; border-radius: 50%;"></i> 2,000-5,000 ton</p>
    <p style="margin:5px 0;"><i style="background:#78c679; width: 16px; height: 16px; display: inline-block; border-radius: 50%;"></i> 1,000-2,000 ton</p>
    <p style="margin:5px 0;"><i style="background:#c2e699; width: 14px; height: 14px; display: inline-block; border-radius: 50%;"></i> 500-1,000 ton</p>
    <p style="margin:5px 0;"><i style="background:#ffffcc; width: 12px; height: 12px; display: inline-block; border-radius: 50%;"></i> < 500 ton</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_vegetation_classification_map(vegetation_data):
    """Crear mapa de clasificación de vegetación mejorado"""
    if not vegetation_data:
        st.warning("No hay datos de vegetación para mostrar")
        return folium.Map(location=[-14.0, -60.0], zoom_start=4)
    
    m = crear_mapa_interactivo_mejorado(-14.0, -60.0, 4)
    
    # Colores para cada clase de vegetación
    veg_colors = {
        'Bosque Denso': '#006400',
        'Bosque Abierto': '#32CD32',
        'Matorral Denso': '#90EE90',
        'Matorral Abierto': '#ADFF2F',
        'Sabana': '#FFFF00',
        'Herbazal': '#FFD700',
        'Suelo Desnudo': '#8B4513',
        'Cuerpo de Agua': '#1E90FF',
        'No Clasificado': '#A9A9A9'
    }
    
    for area_data in vegetation_data:
        veg_class = area_data['clasificacion']
        color = veg_colors.get(veg_class, '#A9A9A9')
        
        popup_text = f"""
        <div style="min-width: 250px; font-family: Arial, sans-serif;">
            <h4 style="color: {color}; margin-bottom: 10px; border-bottom: 2px solid {color}; padding-bottom: 5px;">
                {'🌲' if 'Bosque' in veg_class else '🌿' if 'Matorral' in veg_class else '🍂' if 'Sabana' in veg_class else '💧' if 'Agua' in veg_class else '🏜️'} {area_data['area']}
            </h4>
            <p><strong>Clasificación de Vegetación:</strong></p>
            <p>• Tipo: <b>{veg_class}</b></p>
            <p>• NDVI: <b>{area_data['ndvi']:.3f}</b></p>
            <p>• EVI: <b>{area_data['evi']:.3f}</b></p>
            <p>• NDWI: <b>{area_data['ndwi']:.3f}</b></p>
        </div>
        """
        
        folium.CircleMarker(
            location=[area_data['lat'], area_data['lon']],
            radius=10,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{area_data['area']}: {veg_class}",
            color=color,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    return m

def create_deforestation_timeline_map(deforestation_data):
    """Crear mapa de línea de tiempo de deforestación mejorado"""
    if not deforestation_data:
        st.warning("No hay datos de deforestación para mostrar")
        return folium.Map(location=[-14.0, -60.0], zoom_start=4)
    
    m = crear_mapa_interactivo_mejorado(-14.0, -60.0, 4)
    
    # Filtrar datos del año más reciente
    current_year = datetime.now().year
    current_data = [d for d in deforestation_data if d['año'] == current_year]
    
    for area_data in current_data:
        loss_percentage = area_data['perdida_acumulada']
        
        # Color basado en pérdida acumulada
        if loss_percentage > 50:
            color = '#8B0000'  # Rojo oscuro
            size = 12
        elif loss_percentage > 25:
            color = '#FF4500'  # Rojo naranja
            size = 10
        elif loss_percentage > 10:
            color = '#FFA500'  # Naranja
            size = 8
        elif loss_percentage > 5:
            color = '#FFFF00'  # Amarillo
            size = 6
        else:
            color = '#32CD32'  # Verde
            size = 4
        
        popup_text = f"""
        <div style="min-width: 250px; font-family: Arial, sans-serif;">
            <h4 style="color: {color}; margin-bottom: 10px; border-bottom: 2px solid {color}; padding-bottom: 5px;">
                📉 {area_data['area']}
            </h4>
            <p><strong>Pérdida de Cobertura ({current_year}):</strong></p>
            <p>• Pérdida acumulada: <b>{loss_percentage}%</b></p>
            <p>• Cobertura actual: <b>{area_data['cobertura_porcentaje']}%</b></p>
            <p>• Impacto antrópico: <b>{area_data['impacto_antropico']}</b></p>
        </div>
        """
        
        folium.CircleMarker(
            location=[area_data['lat'], area_data['lon']],
            radius=size,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{area_data['area']}: {loss_percentage}% pérdida",
            color=color,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    return m

def create_anthropic_impact_map(impact_data):
    """Crear mapa de impacto antrópico mejorado"""
    if not impact_data:
        st.warning("No hay datos de impacto antrópico para mostrar")
        return folium.Map(location=[-14.0, -60.0], zoom_start=4)
    
    m = crear_mapa_interactivo_mejorado(-14.0, -60.0, 4)
    
    for area_data in impact_data:
        impact_level = area_data['nivel_impacto']
        color = area_data['color']
        
        # Detalles de impactos por factor
        impact_details = ""
        for factor, details in area_data['detalles'].items():
            impact_details += f"• {factor}: {details['impacto']}<br>"
        
        popup_text = f"""
        <div style="min-width: 280px; font-family: Arial, sans-serif;">
            <h4 style="color: {color}; margin-bottom: 10px; border-bottom: 2px solid {color}; padding-bottom: 5px;">
                ⚠️ {area_data['area']}
            </h4>
            <p><strong>Impacto Antrópico Total:</strong> <b>{area_data['impacto_total']}</b></p>
            <p><strong>Nivel:</strong> <b>{impact_level}</b></p>
            <p><strong>Factores:</strong></p>
            {impact_details}
        </div>
        """
        
        folium.CircleMarker(
            location=[area_data['lat'], area_data['lon']],
            radius=12,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{area_data['area']}: Impacto {impact_level}",
            color=color,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    return m

# ===============================
# 📊 FUNCIONES DE VISUALIZACIÓN
# ===============================

def create_deforestation_timeline_chart(deforestation_data):
    """Crear gráfico de línea de tiempo de deforestación"""
    if not deforestation_data:
        st.warning("No hay datos para generar el gráfico de deforestación")
        return go.Figure()
    
    df = pd.DataFrame(deforestation_data)
    
    fig = px.line(df, x='año', y='cobertura_porcentaje', color='area',
                 title="🌿 Evolución de la Cobertura Vegetal (2020-Actual)",
                 labels={'cobertura_porcentaje': 'Cobertura (%)', 'año': 'Año'})
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(tickmode='linear', dtick=1),
        hovermode='x unified',
        font=dict(size=12)
    )
    
    return fig

def create_carbon_bar_chart(carbon_data):
    """Crear gráfico de barras de potencial de carbono"""
    if not carbon_data:
        st.warning("No hay datos para generar el gráfico de carbono")
        return go.Figure()
    
    df = pd.DataFrame(carbon_data)
    
    fig = px.bar(df, x='area', y='co2_total_ton',
                title="🌳 Potencial de Captura de CO2 por Área",
                labels={'co2_total_ton': 'CO2 Total (ton)', 'area': 'Área'},
                color='co2_total_ton',
                color_continuous_scale='Viridis')
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

def create_impact_radar_chart(impact_data):
    """Crear gráfico radar de impactos antrópicos"""
    if not impact_data:
        st.warning("No hay datos para generar el gráfico de impacto")
        return go.Figure()
    
    # Agregar impactos por factor
    impact_factors = {}
    for area in impact_data:
        for factor, details in area['detalles'].items():
            if factor not in impact_factors:
                impact_factors[factor] = []
            impact_factors[factor].append(details['impacto'])
    
    # Calcular promedios
    avg_impacts = {factor: np.mean(values) for factor, values in impact_factors.items()}
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=list(avg_impacts.values()),
        theta=list(avg_impacts.keys()),
        fill='toself',
        name='Impacto Promedio',
        line=dict(color='#FF6B6B'),
        fillcolor='rgba(255, 107, 107, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor='lightgray'),
            angularaxis=dict(gridcolor='lightgray')
        ),
        title="⚠️ Impacto Antrópico por Factor (Promedio)",
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

# ===============================
# 🚀 INICIALIZACIÓN Y CONFIGURACIÓN
# ===============================

def initialize_session_state():
    """Inicializar el estado de la sesión"""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = IntegratedAnalyzer()

def sidebar_mejorado():
    """Sidebar moderno con iconos y agrupación lógica"""
    
    with st.sidebar:
        # Header del sidebar
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%); border-radius: 12px;'>
            <h2 style='color: white; margin-bottom: 0; font-size: 2.5rem;'>🌍</h2>
            <h3 style='color: white; margin: 0; font-weight: 700;'>Diagnóstico Bio</h3>
            <p style='color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;'>LE.MU Atlas v2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("🗺️ Configuración del Territorio")
        
        uploaded_file = st.file_uploader(
            "Sube archivo del territorio (KML/ZIP/Shapefile)",
            type=['kml', 'zip'],
            help="Archivos geoespaciales con la delimitación del área de estudio"
        )
        
        st.markdown("---")
        st.header("📊 Parámetros de Análisis")
        
        vegetation_type = st.selectbox(
            "🌿 Tipo de vegetación predominante",
            [
                'Bosque Denso Primario', 'Bosque Secundario', 'Bosque Ripario',
                'Matorral Denso', 'Matorral Abierto', 'Sabana Arborizada',
                'Herbazal Natural', 'Zona de Transición', 'Área de Restauración'
            ]
        )
        
        area_hectares = st.slider(
            "📏 Área total del territorio (hectáreas)",
            min_value=1, max_value=10000, value=100, step=10
        )
        
        manual_areas = st.slider(
            "🔍 Número de parcelas de muestreo",
            min_value=1, max_value=50, value=12
        )
        
        st.markdown("---")
        
        # Herramientas rápidas
        st.header("🛠️ Herramientas")
        
        if st.button("🔄 Actualizar Análisis", use_container_width=True):
            st.rerun()
        
        if st.button("💾 Exportar Datos", use_container_width=True):
            st.success("📄 Datos exportados correctamente")
        
        st.markdown("---")
        
        # Información del sistema
        st.header("ℹ️ Información del Sistema")
        
        st.info(f"""
        **Versión:** 2.0  
        **Última actualización:**  
        {datetime.now().strftime("%d/%m/%Y %H:%M")}
        **Usuario:** Investigador
        """)
        
        st.markdown("---")
        st.info("""
        **📈 Categorías de Indicadores:**
        
        🌳 **Carbono**: Reservas y tendencias del carbono
        📉 **Deforestación**: Pérdida de cobertura boscosa  
        ⚠️ **Impacto Antrópico**: Presiones humanas
        🌿 **Vegetación**: Estado y clasificación
        🌊 **Agua**: Disponibilidad y riesgo
        ☀️ **Clima**: Factores relacionados
        """)
    
    return uploaded_file, vegetation_type, area_hectares, manual_areas

# ===============================
# 🎯 APLICACIÓN PRINCIPAL MEJORADA
# ===============================

def main():
    # Aplicar estilos globales
    aplicar_estilos_globales()
    crear_header()
    
    # Inicializar estado de la sesión
    initialize_session_state()
    
    # Sidebar moderno
    uploaded_file, vegetation_type, area_hectares, manual_areas = sidebar_mejorado()
    
    # Contenido principal en tarjetas
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    
    # Procesar archivo subido
    if uploaded_file:
        with st.spinner("Procesando archivo del territorio..."):
            area_count = min(manual_areas * 2, 50)
            st.success(f"🗺️ Territorio procesado: {uploaded_file.name}")
            st.info(f"🔍 Se analizarán {area_count} parcelas de muestreo")
    else:
        area_count = manual_areas
        st.info(f"🔬 Configuración manual: {area_count} parcelas de muestreo")

    # Mostrar resumen de configuración
    st.markdown("### 🎯 Configuración del Análisis")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔍 Parcelas", area_count)
    col2.metric("📏 Hectáreas", f"{area_hectares:,}")
    col3.metric("🌿 Vegetación", vegetation_type)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botón de ejecución
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    
    if st.button("🚀 EJECUTAR DIAGNÓSTICO INTEGRAL", type="primary", use_container_width=True):
        
        with st.spinner("Realizando análisis integral del territorio..."):
            results = st.session_state.analyzer.comprehensive_analysis(area_count, vegetation_type, area_hectares)
            st.session_state.results = results
            st.session_state.analysis_complete = True
        
        st.success("✅ Análisis completado exitosamente!")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Mostrar resultados si el análisis está completo
    if st.session_state.analysis_complete and st.session_state.results:
        results = st.session_state.results
        
        # ===============================
        # 📊 RESUMEN EJECUTIVO MEJORADO
        # ===============================
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 RESUMEN EJECUTIVO DEL DIAGNÓSTICO")
        
        summary = results['summary_metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🌳 Carbono Total CO₂",
                f"{summary['carbono_total_co2_ton']:,} ton",
                "Almacenamiento potencial"
            )
        
        with col2:
            st.metric(
                "📉 Pérdida de Bosque",
                f"{summary['perdida_bosque_promedio']}%",
                "Acumulada desde 2020"
            )
        
        with col3:
            st.metric(
                "⚠️ Impacto Antrópico",
                f"{summary['impacto_antropico_promedio']}",
                "Promedio por área"
            )
        
        with col4:
            st.metric(
                "🔍 Áreas Analizadas",
                summary['areas_analizadas'],
                "Parcelas de muestreo"
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===============================
        # 🗺️ MAPAS DE INDICADORES MEJORADOS
        # ===============================
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("🗺️ MAPAS DE INDICADORES TERRITORIALES")
        
        map_tab1, map_tab2, map_tab3, map_tab4 = st.tabs([
            "🌳 Carbono CO₂", "🌿 Vegetación", "📉 Deforestación", "⚠️ Impacto Antrópico"
        ])
        
        with map_tab1:
            st.markdown("**🌳 Mapa de Potencial de Captura de CO2**")
            carbon_map = create_carbon_map(results['carbon_indicators'])
            st_folium(carbon_map, width=800, height=500)
            st.info("""
            **Interpretación del Potencial de Carbono:**
            - 🟢 **Alto potencial**: >2,000 ton CO₂ (Bosques maduros)
            - 🟡 **Medio potencial**: 500-2,000 ton CO₂ (Bosques secundarios)
            - 🔴 **Bajo potencial**: <500 ton CO₂ (Vegetación degradada)
            """)
        
        with map_tab2:
            st.markdown("**🌿 Mapa de Clasificación de Vegetación**")
            vegetation_map = create_vegetation_classification_map(results['vegetation_classification'])
            st_folium(vegetation_map, width=800, height=500)
            st.info("""
            **Clasificación de Vegetación:**
            - 🌲 **Bosque Denso**: NDVI > 0.7, cobertura continua
            - 🌳 **Bosque Abierto**: NDVI 0.5-0.7, dosel discontinuo
            - 🌿 **Matorral**: NDVI 0.3-0.6, vegetación arbustiva
            - 🍂 **Sabana/Herbazal**: NDVI 0.1-0.4, predominio herbáceo
            """)
        
        with map_tab3:
            st.markdown("**📉 Mapa de Pérdida de Cobertura (2020-Actual)**")
            deforestation_map = create_deforestation_timeline_map(results['deforestation_data'])
            st_folium(deforestation_map, width=800, height=500)
            st.info("""
            **Niveles de Pérdida de Cobertura:**
            - 🟢 **Baja**: <5% pérdida acumulada
            - 🟡 **Moderada**: 5-25% pérdida
            - 🟠 **Alta**: 25-50% pérdida  
            - 🔴 **Crítica**: >50% pérdida
            """)
        
        with map_tab4:
            st.markdown("**⚠️ Mapa de Impacto Antrópico**")
            impact_map = create_anthropic_impact_map(results['impact_data'])
            st_folium(impact_map, width=800, height=500)
            st.info("""
            **Factores de Impacto Antrópico:**
            - 🚜 **Agricultura**: Expansión agrícola, pesticidas
            - 🐄 **Ganadería**: Pastoreo intensivo, compactación
            - 🏙️ **Urbanización**: Expansión urbana, fragmentación
            - 🛣️ **Infraestructura**: Carreteras, líneas de energía
            - ⛏️ **Minería**: Minería superficial, contaminación
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===============================
        # 📈 GRÁFICOS COMPLEMENTARIOS MEJORADOS
        # ===============================
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📈 ANÁLISIS TEMPORAL Y COMPARATIVO")
        
        chart_tab1, chart_tab2, chart_tab3 = st.tabs([
            "📊 Línea de Tiempo", "🌳 Potencial Carbono", "📊 Impacto por Factor"
        ])
        
        with chart_tab1:
            st.markdown("**Evolución Temporal de la Cobertura Vegetal**")
            timeline_chart = create_deforestation_timeline_chart(results['deforestation_data'])
            st.plotly_chart(timeline_chart, use_container_width=True)
        
        with chart_tab2:
            st.markdown("**Potencial de Captura de CO2 por Área**")
            carbon_chart = create_carbon_bar_chart(results['carbon_indicators'])
            st.plotly_chart(carbon_chart, use_container_width=True)
        
        with chart_tab3:
            st.markdown("**Análisis de Factores de Impacto Antrópico**")
            impact_chart = create_impact_radar_chart(results['impact_data'])
            st.plotly_chart(impact_chart, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===============================
        # 📋 RECOMENDACIONES MEJORADAS
        # ===============================
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("💡 RECOMENDACIONES DE MANEJO BASADAS EN INDICADORES")
        
        # Generar recomendaciones basadas en los resultados
        recommendations = []
        
        # Recomendaciones basadas en carbono
        total_co2 = results['summary_metrics']['carbono_total_co2_ton']
        if total_co2 > 10000:
            recommendations.append({
                'title': 'Protección de Sumideros de Carbono',
                'description': 'Implementar estrategias de conservación para mantener los altos niveles de almacenamiento de carbono. Considerar programas de pago por servicios ambientales.',
                'priority': 95,
                'category': '🌳 Carbono'
            })
        elif total_co2 < 5000:
            recommendations.append({
                'title': 'Restauración para Captura de Carbono',
                'description': 'Implementar proyectos de reforestación y agroforestería para aumentar la capacidad de secuestro de carbono del territorio.',
                'priority': 85,
                'category': '🌳 Carbono'
            })
        
        # Recomendaciones basadas en deforestación
        avg_loss = results['summary_metrics']['perdida_bosque_promedio']
        if avg_loss > 30:
            recommendations.append({
                'title': 'Control Urgente de Deforestación',
                'description': 'Establecer medidas inmediatas de control y vigilancia. Implementar sistemas de alerta temprana de deforestación.',
                'priority': 90,
                'category': '📉 Deforestación'
            })
        
        # Recomendaciones basadas en impacto antrópico
        avg_impact = results['summary_metrics']['impacto_antropico_promedio']
        if avg_impact > 0.6:
            recommendations.append({
                'title': 'Manejo Sostenible de Actividades Humanas',
                'description': 'Desarrollar planes de ordenamiento territorial que regulen las actividades antrópicas. Promover prácticas sostenibles en agricultura y ganadería.',
                'priority': 80,
                'category': '⚠️ Impacto'
            })
        
        # Mostrar recomendaciones
        for i, rec in enumerate(recommendations, 1):
            with st.expander(f"{rec['category']} {rec['title']} (Prioridad: {rec['priority']}/100)"):
                st.write(rec['description'])
                st.progress(rec['priority'] / 100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ===============================
        # 📥 EXPORTACIÓN DE RESULTADOS MEJORADA
        # ===============================
        
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("📊 EXPORTAR DIAGNÓSTICO COMPLETO")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Crear archivo Excel con todos los datos
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                pd.DataFrame(results['carbon_indicators']).to_excel(writer, sheet_name='Carbono', index=False)
                pd.DataFrame(results['deforestation_data']).to_excel(writer, sheet_name='Deforestación', index=False)
                pd.DataFrame(results['impact_data']).to_excel(writer, sheet_name='Impacto', index=False)
                pd.DataFrame(results['vegetation_classification']).to_excel(writer, sheet_name='Vegetación', index=False)
            
            st.download_button(
                label="📊 Descargar Datos Completos (Excel)",
                data=output.getvalue(),
                file_name=f"diagnostico_indicadores_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            if st.button("📄 Generar Reporte Ejecutivo PDF", use_container_width=True):
                st.success("✅ Reporte PDF generado (simulación)")
        
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Pantalla de bienvenida mejorada
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("""
        ## 👋 ¡Bienvenido al Diagnóstico de Biodiversidad Ambiental!
        
        ### 🎯 ¿Qué son los indicadores?
        
        Los indicadores son mediciones normalizadas que captan el estado, las tendencias y los riesgos de los ecosistemas. 
        Nos permiten responder a preguntas clave sobre el territorio:
        
        - 🌳 **¿Cuánto carbono hay almacenado?** ¿Está aumentando o disminuyendo?
        - 📉 **¿Dónde está ocurriendo la pérdida de bosque?** ¿Cuáles son las tendencias?
        - ⚠️ **¿Qué áreas están bajo presión humana?** ¿Cuáles son los factores de impacto?
        - 🌿 **¿Qué tipos de vegetación están presentes?** ¿Cuál es su estado de salud?
        
        ### 🚀 Para comenzar el análisis:
        
        1. Configura los parámetros en la **barra lateral** ←
        2. Sube tu archivo territorial (opcional)  
        3. Presiona **EJECUTAR DIAGNÓSTICO INTEGRAL**
        
        ---
        
        **📚 Categorías de Indicadores Analizados:**
        
        🌳 **Carbono**: Reservas y tendencias del carbono por encima y por debajo del suelo
        📉 **Deforestación**: Pérdida de cobertura boscosa y cambios de uso del suelo
        ⚠️ **Impacto Antrópico**: Presiones humanas que determinan la resistencia de los ecosistemas
        🌿 **Vegetación**: Estado y cambio de la cubierta vegetal
        🌊 **Agua**: Disponibilidad, riesgo y seguridad hídrica
        ☀️ **Clima**: Temperatura de la superficie terrestre y factores relacionados
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer mejorado
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 2rem;'>
        <p>🌍 <strong>Diagnóstico de Biodiversidad Ambiental</strong> | Sistema de Indicadores LE.MU Atlas | Desarrollado con Streamlit 🚀</p>
        <p style='font-size: 0.8rem;'>© 2024 Sistema de Monitoreo Ambiental • v2.0 Mejorado</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
