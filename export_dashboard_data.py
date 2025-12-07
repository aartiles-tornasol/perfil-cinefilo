import json
from collections import defaultdict, Counter
import statistics
from datetime import datetime

FILE_PATH = 'pelis_series_vistas.json'
CUTOFF_DATE = "2013-12-07"

# Hardcoded images for top directors using Wikipedia/Commons (Reliable public URLs)
MANUAL_IMAGES = {
    "Martin McDonagh": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Martin_McDonagh_2012.jpg/440px-Martin_McDonagh_2012.jpg",
    "Jean-Pierre Jeunet": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Jean-Pierre_Jeunet_2010.jpg/440px-Jean-Pierre_Jeunet_2010.jpg",
    "Alex Garland": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Alex_Garland_2018.jpg/440px-Alex_Garland_2018.jpg",
    "Aaron Sorkin": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Aaron_Sorkin_2012.jpg/440px-Aaron_Sorkin_2012.jpg",
    "Marc Forster": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Marc_Forster_2013.jpg/440px-Marc_Forster_2013.jpg",
    "Damien Chazelle": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Damien_Chazelle_2014.jpg/440px-Damien_Chazelle_2014.jpg",
    "Rian Johnson": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Rian_Johnson_by_Gage_Skidmore.jpg/440px-Rian_Johnson_by_Gage_Skidmore.jpg",
    "Baz Luhrmann": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Baz_Luhrmann_2013.jpg/440px-Baz_Luhrmann_2013.jpg",
    "Jordan Peele": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Jordan_Peele_2019.jpg/440px-Jordan_Peele_2019.jpg",
    "Park Chan-wook": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Park_Chan-wook_2017.jpg/440px-Park_Chan-wook_2017.jpg",
    "Denis Villeneuve": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Denis_Villeneuve_2017_crop.jpg/440px-Denis_Villeneuve_2017_crop.jpg",
    "Pete Docter": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Pete_Docter_Deauville_2009.jpg/440px-Pete_Docter_Deauville_2009.jpg",
    "Tim Burton": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Tim_Burton_Cannes_2010.jpg/440px-Tim_Burton_Cannes_2010.jpg",
    "Christopher McQuarrie": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Christopher_McQuarrie_by_Gage_Skidmore.jpg/440px-Christopher_McQuarrie_by_Gage_Skidmore.jpg",
    "James Cameron": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/James_Cameron_DeepSea_Challenge_2012.jpg/440px-James_Cameron_DeepSea_Challenge_2012.jpg",
    "Fernando Meirelles": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Fernando_meirelles.jpg/440px-Fernando_meirelles.jpg", 
    "David Fincher": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/David_Fincher_Cannes_2007.jpg/440px-David_Fincher_Cannes_2007.jpg",
    "Wes Anderson": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Wes_Anderson_Cannes_2012_2.jpg/440px-Wes_Anderson_Cannes_2012_2.jpg",
    # Keep known TMDB ones for others if wanted, or use these.
    "Christopher Nolan": "/xuAIuYSmsUzKlUMBFhtV7sHCmFB.jpg",
    "Steven Spielberg": "/tZxcg19YQ3e8fJ0pOs7xjGYlxsw.jpg",
    "Quentin Tarantino": "/1gjcpAa99FAOWGnrUvHEXXsRs7o.jpg"
}

def load_data():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [d for d in data if d.get('tipo') == 'pelicula' and d.get('mi_nota') is not None]

def get_year_watched(item):
    d = item.get('fecha_puntuacion_iso')
    if d: return d[:4]
    return None

def get_stats_block(dataset, include_images=True):
    # Helper to calculate stats for a specific subset of movies
    # Returns Directors, Actors, Genres, RatingsDst, KPIS
    
    total = len(dataset)
    if total == 0: return None
    avg = statistics.mean([m['mi_nota'] for m in dataset])
    
    # Global manual map for fallbacks (defined at module level or passed in likely better, but for quick fix:)
    # Actually, let's just use the global variable 'MANUAL_IMAGES' if defined.
    
    # Build global image map from actors
    global_images = {}
    for m in dataset:
        for a in m.get('actores', []):
            if isinstance(a, dict) and a.get('nombre') and a.get('profile_path'):
                global_images[a['nombre']] = a['profile_path']
    
    # Directors & Actors & Genres
    def get_top(key, min_limit, count_limit, include_images=True):
        grouped = defaultdict(list)
        # We don't need a local images map if we use global, but let's keep it for specific matches
        
        for m in dataset:
            vals = m.get(key, [])
            rating = m['mi_nota']
            for v in vals:
                name = v.get('nombre') if isinstance(v, dict) else v
                if name:
                    grouped[name].append(rating)
        
        stats = []
        for name, ratings in grouped.items():
            if len(ratings) >= min_limit:
                # Try to find an image
                img = None
                if include_images:
                    img = global_images.get(name)
                    # Fallback to manual hardcoded map
                    if not img and name in MANUAL_IMAGES:
                         img = MANUAL_IMAGES[name]
                
                stats.append({
                    'name': name,
                    'avg': statistics.mean(ratings),
                    'count': len(ratings),
                    'image': img
                })
        stats.sort(key=lambda x: x['avg'], reverse=True)
        return stats[:count_limit]

    directors = get_top('directores', 3, 10, include_images=True)
    actors = get_top('actores', 5, 12, include_images=True)
    genres = get_top('generos', 5, 10, include_images=False)
    
    # Rating Distribution
    ratings = [round(m['mi_nota']) for m in dataset]
    dist = Counter(ratings)
    # Ensure all 1-10 keys exist
    dist_arr = [dist.get(i, 0) for i in range(1, 11)]

    return {
        'total': total,
        'avg': round(avg, 2),
        'directors': directors,
        'actors': actors,
        'genres': genres,
        'distribution': dist_arr
    }

def get_evolution(movies):
    years = defaultdict(list)
    for m in movies:
        y = get_year_watched(m)
        if y and int(y) >= 2010: # Focus on reliable recent history + some past
            years[y].append(m['mi_nota'])
            
    stats = []
    for y in sorted(years.keys()):
        stats.append({
            'year': y,
            'avg': statistics.mean(years[y]),
            'count': len(years[y])
        })
    return stats

def get_psychology(movies):
    # Guilty Pleasures & Haters
    guilty = []
    haters = []
    
    for m in movies:
        my_rading = m['mi_nota']
        pub_rating = m.get('vote_average_publico', 0)
        if not pub_rating: continue
        
        diff = my_rading - pub_rating
        
        if my_rading >= 7.0 and pub_rating <= 5.8:
            guilty.append({'t': m['titulo'], 'm': my_rading, 'p': pub_rating, 'd': diff, 'img': m.get('poster_path')})
            
        if my_rading <= 5.0 and pub_rating >= 7.3:
            haters.append({'t': m['titulo'], 'm': my_rading, 'p': pub_rating, 'd': diff, 'img': m.get('poster_path')})
            
    guilty.sort(key=lambda x: x['d'], reverse=True)
    haters.sort(key=lambda x: x['d']) # most negative first

    return {'guilty': guilty[:6], 'haters': haters[:6]}, None # Retaining tuple return for compatibility with call site

def analyze_decades(movies):
    decades = defaultdict(list)
    for m in movies:
        d = m.get('fecha_estreno_iso')
        rating = m['mi_nota']
        if d and len(d) >= 4:
            year = int(d[:4])
            decade = f"{(year // 10) * 10}s"
            decades[decade].append(rating)
            
    stats = []
    for dec, ratings in decades.items():
        stats.append({
            'name': dec,
            'avg': statistics.mean(ratings),
            'count': len(ratings)
        })
    stats.sort(key=lambda x: x['name'])
    return stats

def analyze_keyword_dna(movies):
    # Top keywords from highly rated movies (>=8)
    cnt = Counter()
    STOP = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'y', 'o', 'en', 'a', 'al', 'the', 'of', 'and', 'in'}
    for m in movies:
        if m['mi_nota'] >= 8:
            for k in m.get('titulo_keywords', []):
                if k.lower() not in STOP and len(k) > 2:
                    cnt[k] += 1
    return [{"text": k, "weight": v} for k, v in cnt.most_common(20)]

def main():
    movies = load_data()
    
    # Split Data
    recent_movies = [m for m in movies if (m.get('fecha_puntuacion_iso') or "") >= CUTOFF_DATE]
    
    # Stats Blocks
    stats_all = get_stats_block(movies)
    stats_recent = get_stats_block(recent_movies)
    
    # Complex Analysis
    evolution = get_evolution(movies)
    psychology, _ = get_psychology(movies)
    
    # Re-calc stats (images will pick up global MANUAL_IMAGES automatically)
    stats_all = get_stats_block(movies)
    stats_recent = get_stats_block(recent_movies)
    
    # New Metrics
    decades = analyze_decades(movies)
    keywords = analyze_keyword_dna(movies)
    
    export_data = {
        'all': stats_all,
        'recent': stats_recent,
        'evolution': evolution,
        'psychology': psychology,
        'decades': decades,
        'keywords': keywords
    }
    
    js_content = f"const PROFILE_DATA = {json.dumps(export_data, indent=2)};"
    
    with open("dashboard_data.js", "w", encoding='utf-8') as f:
        f.write(js_content)
    print("Expanded JS Data File generated.")

if __name__ == "__main__":
    main()
