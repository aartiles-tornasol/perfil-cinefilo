import json
from collections import defaultdict, Counter
from datetime import datetime
import statistics

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_metrics(data):
    # filtered data (only items with a rating)
    rated_items = [item for item in data if item.get('mi_nota') is not None]
    
    if not rated_items:
        return None

    # 1. General DNA
    total_watched = len(rated_items)
    ratings = [item['mi_nota'] for item in rated_items]
    avg_rating = statistics.mean(ratings)
    
    # Rating Distribution (rounded to nearest integer for grouping)
    rating_counts = Counter([round(r) for r in ratings])
    
    # 2. Taste Clusters
    genres_ratings = defaultdict(list)
    genres_counts = Counter()
    
    # 3. Creators
    directors_ratings = defaultdict(list)
    actors_ratings = defaultdict(list)
    
    # 4. Eras (Decades)
    decades_ratings = defaultdict(list)

    for item in rated_items:
        rating = item['mi_nota']
        
        # Genres
        if 'generos' in item and item['generos']:
            for genre in item['generos']:
                genres_ratings[genre].append(rating)
                genres_counts[genre] += 1
        
        # Directors
        if 'directores' in item and item['directores']:
            for director in item['directores']:
                directors_ratings[director].append(rating)
                
        # Actors
        if 'actores' in item and item['actores']:
            # Limit to top 5 billed actors to avoid noise from extras? 
            # Or just take all. Let's take all for now but filtering by significance might be good later using 'order' if available, 
            # but list is just a list. We'll take top 5 if list is long.
            actors = item['actores'][:5] 
            for actor in actors:
                # actor is a dict
                actor_name = actor.get('nombre')
                if actor_name:
                    actors_ratings[actor_name].append(rating)

        # Decades
        if 'fecha_estreno' in item and item['fecha_estreno']:
            try:
                # Format is DD/MM/YYYY
                year = int(item['fecha_estreno'].split('/')[-1])
                decade = (year // 10) * 10
                decades_ratings[decade].append(rating)
            except:
                pass

    # Process Aggregates
    def get_top_items(rating_dict, min_count=1):
        # Returns list of (item, avg_rating, count) sorted by avg_rating desc
        items = []
        for key, scores in rating_dict.items():
            if len(scores) >= min_count:
                items.append({
                    'name': key,
                    'avg': statistics.mean(scores),
                    'count': len(scores)
                })
        return sorted(items, key=lambda x: x['avg'], reverse=True)

    # Top Genres (min 5 watched)
    top_genres = get_top_items(genres_ratings, min_count=5)
    
    # Top Directors (min 3 watched)
    top_directors = get_top_items(directors_ratings, min_count=3)
    
    # Top Actors (min 5 watched)
    top_actors = get_top_items(actors_ratings, min_count=5)
    
    # Decades
    decade_stats = get_top_items(decades_ratings, min_count=1)
    # Sort decades chronologically for display
    decade_stats.sort(key=lambda x: x['name'])

    return {
        'general': {
            'total': total_watched,
            'avg_rating': avg_rating,
            'distribution': dict(sorted(rating_counts.items(), reverse=True))
        },
        'genres': top_genres,
        'directors': top_directors,
        'actors': top_actors,
        'decades': decade_stats
    }

def generate_markdown(metrics):
    if not metrics:
        return "No data found."

    gen = metrics['general']
    
    md = "# Perfil de Cinéfilo\n\n"
    
    md += "## 🧬 ADN General\n"
    md += f"- **Total Visto**: {gen['total']} títulos\n"
    md += f"- **Nota Media**: {gen['avg_rating']:.2f} / 10\n"
    
    # Determine 'Vibe' based on average
    if gen['avg_rating'] < 6:
        vibe = "Crítico Feroz 🦖"
    elif gen['avg_rating'] > 8:
        vibe = "Entusiasta Generoso 💖"
    else:
        vibe = "Espectador Equilibrado ⚖️"
    md += f"- **Vibe**: {vibe}\n\n"
    
    md += "### Distribución de Notas\n"
    md += "| Nota | Cantidad |\n|---|---|\n"
    for note, count in gen['distribution'].items():
        bar = "█" * int(count / 10) # 1 char per 10 items approx for visual
        if not bar: bar = "▏"
        md += f"| {note} | {count} |\n"
    md += "\n"

    md += "## 🎭 Géneros Favoritos\n"
    md += "*(Mínimo 5 vistos, ordenado por nota media)*\n\n"
    md += "| Género | Nota Media | Vistos |\n|---|---|---|\n"
    for g in metrics['genres'][:10]: # Top 10
        md += f"| **{g['name']}** | {g['avg']:.2f} | {g['count']} |\n"
    md += "\n"

    md += "## 🎬 Directores Top\n"
    md += "*(Mínimo 3 vistos)*\n\n"
    for d in metrics['directors'][:10]:
        md += f"- **{d['name']}**: {d['avg']:.2f} (en {d['count']} películas)\n"
    md += "\n"
    
    md += "## 🌟 Actores Preferidos\n"
    md += "*(Mínimo 5 vistos)*\n\n"
    for a in metrics['actors'][:10]:
        md += f"- **{a['name']}**: {a['avg']:.2f} (en {a['count']} películas)\n"
    md += "\n"

    md += "## 🕰️ Por Décadas\n\n"
    md += "| Década | Nota Media | Vistos |\n|---|---|---|\n"
    for d in metrics['decades']:
        md += f"| {d['name']}s | {d['avg']:.2f} | {d['count']} |\n"

    return md

if __name__ == "__main__":
    file_path = "pelis_series_vistas.json"
    try:
        data = load_data(file_path)
        metrics = calculate_metrics(data)
        profile_md = generate_markdown(metrics)
        
        # Save to file
        with open("Cinephile_Profile.md", "w", encoding='utf-8') as f:
            f.write(profile_md)
            
        print("Profile generated successfully: Cinephile_Profile.md")
        print("-" * 20)
        print(profile_md)
        
    except Exception as e:
        print(f"Error: {e}")
