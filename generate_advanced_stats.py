import json
from collections import defaultdict
import statistics
from datetime import datetime

# CONFIGURATION
FILE_PATH = 'pelis_series_vistas.json'
CUTOFF_DATE = "2013-12-07" # 12 years back from Dec 2025
MIN_MOVIES_GENRE = 5
MIN_MOVIES_ACTOR_RATING = 5
MIN_MOVIES_DIRECTOR_FREQ = 3
MIN_MOVIES_ACTOR_FREQ = 5

def load_and_filter_data():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter 1: Only movies with rating
    movies = [d for d in data if d.get('tipo') == 'pelicula' and d.get('mi_nota') is not None]
    
    # Dataset 1: All Time
    all_time = movies
    
    # Dataset 2: Recent (Last 12 years)
    recent = []
    for m in movies:
        date_str = m.get('fecha_puntuacion_iso')
        if date_str and date_str >= CUTOFF_DATE:
            recent.append(m)
            
    return all_time, recent

def analyze_group(dataset, key_field, is_list=True):
    # Aggregates ratings and counts for a specific field (e.g., 'generos', 'actores', 'directores')
    # Returns dictionary: { name: [ratings] }
    grouped = defaultdict(list)
    
    for item in dataset:
        rating = item['mi_nota']
        values = item.get(key_field)
        
        if not values:
            continue
            
        if is_list:
            # Handle list of strings (generos, directores) or list of dicts (actores)
            for val in values:
                name = None
                if isinstance(val, dict):
                    name = val.get('nombre')
                else:
                    name = val
                
                if name:
                    grouped[name].append(rating)
    return grouped

def calculate_stats(grouped_data, min_count=1):
    # Returns list of dicts {name, count, avg}
    stats = []
    for name, ratings in grouped_data.items():
        if len(ratings) >= min_count:
            stats.append({
                'name': name,
                'count': len(ratings),
                'avg': statistics.mean(ratings)
            })
    return stats

def format_table(stats, title, sort_by='avg', limit=None):
    # Sort
    if sort_by == 'avg':
        stats.sort(key=lambda x: x['avg'], reverse=True)
        col_focus = "Nota Media"
    else: # sort by count
        stats.sort(key=lambda x: x['count'], reverse=True)
        col_focus = "Vistas"

    if limit:
        stats = stats[:limit]

    md = f"### {title}\n"
    if sort_by == 'avg':
        md += "| Rank | Nombre | Nota Media | Vistas |\n|---|---|---|---|\n"
        for i, s in enumerate(stats, 1):
            md += f"| {i} | **{s['name']}** | {s['avg']:.2f} | {s['count']} |\n"
    else:
        md += "| Rank | Nombre | Vistas | Nota Media |\n|---|---|---|---|\n"
        for i, s in enumerate(stats, 1):
            md += f"| {i} | **{s['name']}** | **{s['count']}** | {s['avg']:.2f} |\n"
    md += "\n"
    return md

def generate_genre_report(all_time, recent):
    # Process
    g_all = calculate_stats(analyze_group(all_time, 'generos'), MIN_MOVIES_GENRE)
    g_rec = calculate_stats(analyze_group(recent, 'generos'), MIN_MOVIES_GENRE)
    
    md = "# 🎭 Reporte de Géneros (Solo Películas)\n\n"
    
    md += "## Histórico Completo\n"
    md += format_table(g_all, f"Top Géneros por Nota (Min {MIN_MOVIES_GENRE} v)", sort_by='avg')
    
    md += "## Últimos 12 Años\n"
    md += format_table(g_rec, f"Top Géneros Recientes por Nota (Min {MIN_MOVIES_GENRE} v)", sort_by='avg')
    
    return md

def generate_actor_rating_report(all_time, recent):
    a_all = calculate_stats(analyze_group(all_time, 'actores'), MIN_MOVIES_ACTOR_RATING)
    a_rec = calculate_stats(analyze_group(recent, 'actores'), MIN_MOVIES_ACTOR_RATING)
    
    md = "# 🌟 Reporte de Actores por Calidad (Solo Películas)\n"
    md += "*Ordenados por Nota Media. Mínimo 5 películas.*\n\n"
    
    md += "## Histórico Completo\n"
    md += format_table(a_all, "Top Actores Histórico", sort_by='avg', limit=50)
    
    md += "## Últimos 12 Años\n"
    md += format_table(a_rec, "Top Actores Recientes", sort_by='avg', limit=50)
    
    return md

def generate_frequency_report(all_time, recent):
    # Directors
    d_all = calculate_stats(analyze_group(all_time, 'directores'), MIN_MOVIES_DIRECTOR_FREQ)
    d_rec = calculate_stats(analyze_group(recent, 'directores'), MIN_MOVIES_DIRECTOR_FREQ)
    
    # Actors
    a_all = calculate_stats(analyze_group(all_time, 'actores'), MIN_MOVIES_ACTOR_FREQ)
    a_rec = calculate_stats(analyze_group(recent, 'actores'), MIN_MOVIES_ACTOR_FREQ)
    
    md = "# 📊 Reporte de Frecuencia (Obsesiones)\n"
    md += "*Ordenados por CANTIDAD de visualizaciones, independiente de la nota.*\n\n"
    
    md += "## 🎬 Directores Más Vistos\n"
    md += format_table(d_all, "Histórico (Min 3)", sort_by='count', limit=20)
    md += format_table(d_rec, "Últimos 12 Años (Min 3)", sort_by='count', limit=20)
    
    md += "## 🌟 Actores Más Vistos\n"
    md += format_table(a_all, "Histórico (Min 5)", sort_by='count', limit=20)
    md += format_table(a_rec, "Últimos 12 Años (Min 5)", sort_by='count', limit=20)
    
    return md

def main():
    print("Loading data...")
    all_time, recent = load_and_filter_data()
    print(f"Loaded {len(all_time)} movies (Total) and {len(recent)} movies (Recent).")
    
    # 1. Genres
    print("Generating Genre Report...")
    with open('Reporte_Generos.md', 'w', encoding='utf-8') as f:
        f.write(generate_genre_report(all_time, recent))
        
    # 2. Actors by Rating
    print("Generating Actor Quality Report...")
    with open('Reporte_Actores_Ratings.md', 'w', encoding='utf-8') as f:
        f.write(generate_actor_rating_report(all_time, recent))
        
    # 3. Frequency
    print("Generating Frequency Report...")
    with open('Reporte_Frecuencia_Vistas.md', 'w', encoding='utf-8') as f:
        f.write(generate_frequency_report(all_time, recent))
        
    print("Done! Files created: Reporte_Generos.md, Reporte_Actores_Ratings.md, Reporte_Frecuencia_Vistas.md")

if __name__ == "__main__":
    main()
