# Atlas de Biodiversidad - Streamlit

Esta aplicación permite analizar y visualizar métricas básicas de biodiversidad usando simulaciones y archivos geográficos (KML o Shapefile).

## Cómo usar

- Subir archivo KML o ZIP con shapefile a la app.
- O ajustar número de áreas simuladas para análisis.
- Hacer click en "Ejecutar análisis".
- Ver métricas, tabla y mapas satelitales de Esri integrados.

## Requisitos

- Python 3.11 recomendado.
- Streamlit Cloud para despliegue online.
- Dependencias en requirements.txt.

## Dependencias principales

- Streamlit 1.28
- Pandas compatible 2.x
- Numpy <=1.25.1 para evitar errores en build
- Folium + streamlit-folium para mapas
- Geopandas para manejo GIS

## Despliegue

Para desplegar, conecta tu repositorio a Streamlit Cloud y asegúrate de incluir:

- `requirements.txt` con versiones compatibles
- `runtime.txt` con `python-3.11.16` para evitar problemas de versión

---

Este proyecto está basado en experiencias reales de despliegue que aseguran compatibilidad y buen rendimiento en Streamlit Cloud.
