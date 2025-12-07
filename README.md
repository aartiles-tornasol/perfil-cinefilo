# Cinephile DNA Profile

Este repositorio contiene las herramientas y el dashboard interactivo para analizar mi historial de visionado de películas (exportado desde TV Time / Trakt o similar).

## Contenido

- **Dashboard Interactivo:** `infographic.html` (Visualización de datos con Chart.js)
- **Scrips de Análisis:** 
  - `export_dashboard_data.py`: Procesa el JSON de historial y genera `dashboard_data.js`.
  - `generate_psychology_report.py`: Genera insights curiosos sobre mis gustos.
  - `generate_ai_prompts.py`: Crea prompts para pedir recomendaciones a IAs.
- **Reportes Generados:** Varios archivos `.md` con estadísticas detalladas de directores, actores y géneros.

## Uso

1. Coloca tu archivo `pelis_series_vistas.json` en la raíz.
2. Ejecuta `python3 export_dashboard_data.py`.
3. Abre `infographic.html` en tu navegador.
