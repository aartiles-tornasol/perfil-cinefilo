import json
from collections import defaultdict
import statistics
from datetime import datetime

def get_stats(data, date_cutoff=None):
    directors_ratings = defaultdict(list)
    count_analyzed = 0
    
    for item in data:
        # Filter: ONLY MOVIES
        if item.get('tipo') != 'pelicula':
            continue
            
        if item.get('mi_nota') is None:
            continue

        # Date filter if applicable
        if date_cutoff:
            date_str = item.get('fecha_puntuacion_iso')
            if not date_str or date_str < date_cutoff:
                continue
        
        count_analyzed += 1
        
        if 'directores' in item and item['directores']:
            for director in item['directores']:
                directors_ratings[director].append(item['mi_nota'])

    return directors_ratings, count_analyzed

def generate_report(directors_ratings, title, total_count):
    director_stats = []
    for director, ratings in directors_ratings.items():
        if len(ratings) >= 3:
            director_stats.append({
                'name': director,
                'avg': statistics.mean(ratings),
                'count': len(ratings),
                'ratings': ratings
            })

    director_stats.sort(key=lambda x: x['avg'], reverse=True)

    md = f"# {title}\n"
    md += f"**Filtro**: Solo Películas\n"
    md += f"**Títulos analizados**: {total_count}\n\n"
    
    # Wes Anderson check
    wes = next((d for d in director_stats if "Wes Anderson" in d['name']), None)
    if wes:
        md += "## 🕵️‍♂️ Análisis: Wes Anderson\n"
        md += f"- **Nota Media**: {wes['avg']:.2f}\n"
        md += f"- **Películas Vistas**: {wes['count']}\n"
        rank = director_stats.index(wes) + 1
        md += f"- **Ranking actual**: #{rank}\n\n"
    else:
        md += "## 🕵️‍♂️ Análisis: Wes Anderson\n❌ No aparece en el Top (mínimo 3 pelis) en este periodo/filtro.\n\n"

    md += "## 🏆 Top 20 Directores (Mínimo 3 pelis)\n"
    md += "| Rank | Director | Nota Media | Vistas |\n|---|---|---|---|\n"
    for i, d in enumerate(director_stats[:20], 1):
        md += f"| {i} | **{d['name']}** | {d['avg']:.2f} | {d['count']} |\n"
        
    return md

def main():
    with open('pelis_series_vistas.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Report 1: All Time
    stats_all, count_all = get_stats(data)
    report_all = generate_report(stats_all, "Top 20 Directores (Histórico)", count_all)
    with open("Top_20_Directores.md", "w", encoding='utf-8') as f:
        f.write(report_all)

    # Report 2: Recent (Last 12 years)
    cutoff = "2013-12-07"
    stats_recent, count_recent = get_stats(data, date_cutoff=cutoff)
    report_recent = generate_report(stats_recent, "Top 20 Directores (Últimos 12 años)", count_recent)
    with open("Top_20_Directores_Recent.md", "w", encoding='utf-8') as f:
        f.write(report_recent)
        
    print("Reports generated successfully.")

if __name__ == "__main__":
    main()
