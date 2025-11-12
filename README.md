# 🌿 Atlas de Biodiversidad (LE.MU + Shannon)

Aplicación interactiva en Streamlit basada en la metodología [LE.MU Atlas](https://www.le.mu/atlas/)  
e incorporando el **Índice de Shannon-Wiener** para evaluar la diversidad biológica por áreas.

## 🚀 Características

- Carga de archivos **KML** o **Shapefile (ZIP)**
- Cálculo de:
  - Índice de Shannon
  - Riqueza de especies
  - Equitatividad (Pielou)
  - Índice de Simpson
- Visualización:
  - Mapa base **ESRI Satellite**
  - Gráficos de abundancia y riqueza
  - Capa **LiDAR 3D (Pydeck)**
- 100 % en línea, sin instalación local.

## 📦 Instalación local (opcional)
```bash
pip install -r requirements.txt
streamlit run app.py
