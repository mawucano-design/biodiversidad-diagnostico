# 🌿 Atlas de Biodiversidad LE.MU

App Streamlit para análisis de biodiversidad basada en la metodología de [LE.MU Atlas](https://www.le.mu/atlas/), incorporando el **Índice de Shannon-Wiener** junto con métricas como riqueza de especies, Simpson y equitatividad. 

## 🎯 Características
- **Carga de datos**: KML o Shapefile (ZIP) para áreas geográficas.
- **Análisis**: Simulación de datos ecológicos + cálculo de indicadores de biodiversidad.
- **Visualizaciones**: 
  - Métricas principales (dashboard).
  - **Mapas interactivos** con base ESRI Satellite, coloreados por Shannon/riqueza.
  - **3D con LiDAR**: Visualización de nubes de puntos superpuesta con áreas de estudio.
- **Export**: CSV de resultados.
- Todo online, sin instalación local.

## 📊 Indicadores (Basados en LE.MU)
- **Índice de Shannon (H')**: Diversidad (-Σ p_i ln p_i). Baja (<1), Moderada (1-3), Alta (>3).
- **Riqueza de Especies (S)**: Número de especies únicas.
- **Equitatividad (J')**: H' / ln(S) (0-1, uniforme=1).
- **Índice de Simpson (λ)**: Probabilidad de misma especie (bajo=alta diversidad).
- Integración con LE.MU: Enfocado en Species Richness y bioraridad, usando datos espaciales para zonificación.

## 🚀 Despliegue
- Desplegada en [Streamlit Cloud](https://share.streamlit.io).
- Para correr local: `streamlit run app.py`.

## 📁 Uso
1. Sube KML/SHP (o usa ejemplo).
2. Configura parámetros en sidebar.
3. Ejecuta análisis.
4. Explora mapas y 3D.

## 🔧 Mejoras Pendientes
- Integración real con APIs LE.MU (si disponible).
- Soporte para datos satelitales (ej. NDVI de ESA).

Desarrollado con ❤️ usando Streamlit. Basado en [LE.MU Docs](https://www.le.mu/docs/indicators/).
