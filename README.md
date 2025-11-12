# Atlas de Biodiversidad (Metodología LE.MU + Shannon Index)

Aplicación interactiva online para el análisis de biodiversidad con métricas estandarizadas e integración geográfica y mapas satelitales.  

## Características

- Mide e interpreta índices clásicos de biodiversidad (Shannon, Simpson, Riqueza, Equitatividad).
- Soporte para archivos geográficos: KML (Google Earth) y Shapefile (en ZIP).
- Visualización en mapa con base satelital ESRI.
- Exportación de resultados en CSV.
- 100% online, sin instalaciones locales. Despliegue directo vía [Streamlit Cloud](https://streamlit.io/cloud).
- Metodología basada en [LE.MU Atlas](https://www.le.mu/atlas/).

## Uso

1. Clona este repositorio o haz el fork en tu cuenta.
2. Conéctalo a Streamlit Cloud para desplegar la app online.
3. Sube tus archivos KML o ZIP con shapefiles en la interfaz para analizar zonas reales.
4. Configura los parámetros y ejecuta el análisis.
5. Visualiza resultados, métricas y mapas. Descarga los CSV para reportes.

## Dependencias

Ver `requirements.txt` para todas las librerías requeridas (Streamlit, pandas, numpy, folium, geopandas).

## Visualización avanzada

Para datos LiDAR y visualización 3D puedes extender usando [PyVista](https://docs.pyvista.org/) y [stpyvista](https://github.com/Marph82/stpyvista), integrable con un bloque adicional.

## Contacto y metodología

Desarrollado siguiendo buenas prácticas de transparencia, trazabilidad de indicadores y usando la metodología LE.MU para gestión de datos de naturaleza.

---
