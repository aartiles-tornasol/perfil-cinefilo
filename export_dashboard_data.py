
import json
import collections
from collections import defaultdict, Counter
import statistics
from datetime import datetime
import os
import requests
import shutil

FILE_PATH = 'pelis_series_vistas.json'
CUTOFF_DATE = "2013-12-07"

# Hardcoded images for top directors using Wikipedia/Commons (Reliable public URLs)
# Falls back to TMDB relative paths if not in this list
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
    "Christopher Nolan": "/xuAIuYSmsUzKlUMBFhtV7sHCmFB.jpg",
    "Steven Spielberg": "/tZxcg19YQ3e8fJ0pOs7xjGYlxsw.jpg",
    "Quentin Tarantino": "/1gjcpAa99FAOWGnrUvHEXXsRs7o.jpg"
}

def download_image(name, url_or_path):
    """Downloads image to img/ folder and returns local path."""
    if not url_or_path: return None
    
    if not os.path.exists('img'):
        os.makedirs('img')

    # Create safe filename
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ','-','_')]).strip().replace(' ', '_')
    filename = f"img/{safe_name}.jpg"
    
    # If already exists, return local path
    if os.path.exists(filename):
        return filename

    url = url_or_path
    if not url.startswith('http'):
        url = f"https://image.tmdb.org/t/p/w200{url_or_path}"
    
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            print(f"Downloaded: {name}")
            return filename
    except Exception as e:
        print(f"Error downloading {name}: {e}")
        return None
    return None

def get_stats_block(dataset, recent_only=False):
    def get_top(key, min_limit, count_limit, include_images=True):
        grouped = defaultdict(list)
        images = {}
        
        # 1. Gather all ratings and potential images
        for m in dataset:
            vals = m.get(key, [])
            rating = m['mi_nota']
            for v in vals:
                name = v.get('nombre') if isinstance(v, dict) else v
                if name:
                    grouped[name].append(rating)
                    if include_images and isinstance(v, dict) and 'profile_path' in v and v['profile_path']:
                        if name not in images: images[name] = v['profile_path']
        
        # 2. Filter and Stats
        stats = []
        for name, ratings in grouped.items():
            if len(ratings) >= min_limit:
                
                # Determine image source
                img_src = None
                if key == 'directors' and name in MANUAL_IMAGES:
                    img_src = MANUAL_IMAGES[name]
                elif name in images:
                    img_src = images[name]
                
                # Download local copy if we have a source
                local_path = None
                if include_images and img_src:
                     # Download!
                     local_path = download_image(name, img_src)

                stats.append({
                    'name': name,
                    'avg': statistics.mean(ratings),
                    'count': len(ratings),
                    'image': local_path 
                })
        
        stats.sort(key=lambda x: x['avg'], reverse=True)
        return stats[:count_limit]

    # Filter dataset if needed
    if recent_only:
        filtered = []
        cutoff = datetime.strptime(CUTOFF_DATE, "%Y-%m-%d")
        for m in dataset:
            if m.get('fecha_puntuacion_iso'):
                try:
                    d = datetime.strptime(m['fecha_puntuacion_iso'][:10], "%Y-%m-%d")
                    if d >= cutoff:
                        filtered.append(m)
                except:
                    pass
        dataset = filtered

    # Yearly stats for evolution
    years = defaultdict(list)
    for m in dataset:
        if m['fecha_puntuacion_iso']:
            y = int(m['fecha_puntuacion_iso'][:4])
            years[y].append(m['mi_nota'])
    evolution = [{'year': y, 'avg': statistics.mean(rs)} for y, rs in sorted(years.items())]

    # Distribution
    dist = [0]*10
    total_movies = 0
    for m in dataset:
        r = int(m['mi_nota'])
        if 1 <= r <= 10:
            dist[r-1] += 1
            total_movies += 1
            
    return {
        'total': total_movies,
        'avg': round(statistics.mean([m['mi_nota'] for m in dataset]), 2),
        'evolution': evolution,
        'distribution': dist,
        'directors': get_top('directors', 3, 10),
        'actors': get_top('actores', 5, 10),
        'genres': get_top('generos', 5, 20, include_images=False)
    }

def analyze_decades(dataset):
    """Analyze average rating by decade of movie release."""
    decades = defaultdict(list)
    for m in dataset:
        if m.get('fecha_estreno'):
            try:
                year = int(m['fecha_estreno'][:4])
                decade = (year // 10) * 10
                decades[decade].append(m['mi_nota'])
            except: pass
    
    stats = []
    for d, ratings in decades.items():
        if len(ratings) >= 5: # Min 5 movies to count
            stats.append({'name': str(d)+'s', 'avg': statistics.mean(ratings)})
    
    stats.sort(key=lambda x: x['name']) # Sort chronological
    return stats

def analyze_keyword_dna(dataset):
    """Extract most distinctive keywords from highly rated movies."""
    good_movie_keywords = []
    for m in dataset:
        if m['mi_nota'] >= 8 and m.get('titulo_keywords'):
            good_movie_keywords.extend(m['titulo_keywords'])
            
    counts = Counter(good_movie_keywords)
    # Simple word cloud data
    return [{'text': k, 'weight': c} for k, c in counts.most_common(30)]

def get_psychology(dataset):
    guilty = []
    haters = []
    
    for m in dataset:
        my_rating = m.get('mi_nota', 0)
        public_rating = m.get('vote_average_publico', 0)
        
        if my_rating >= 7 and public_rating > 0 and (my_rating - public_rating) >= 1.5:
            # Download Poster
            local_poster = download_image(f"poster_{m['titulo']}", m['poster_path']) if m.get('poster_path') else None
            guilty.append({
                't': m['titulo'],
                'd': my_rating - public_rating,
                'img': local_poster
            })
            
        if my_rating <= 5 and public_rating >= 7 and (public_rating - my_rating) >= 1.5:
            # Download Poster
            local_poster = download_image(f"poster_{m['titulo']}", m['poster_path']) if m.get('poster_path') else None
            haters.append({
                't': m['titulo'],
                'd': public_rating - my_rating,
                'img': local_poster
            })

    guilty.sort(key=lambda x: x['d'], reverse=True)
    haters.sort(key=lambda x: x['d'], reverse=True)

    return {
        'guilty': guilty[:10],
        'haters': haters[:10]
    }

def main():
    with open(FILE_PATH, 'r') as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} items.")
    
    # Filter Movies Only
    movies = [x for x in data if x.get('tipo') == 'pelicula']
    print(f"Filtered to {len(movies)} movies.")
    
    # Generate Blocks
    all_time = get_stats_block(movies, recent_only=False)
    recent = get_stats_block(movies, recent_only=True)
    psych = get_psychology(movies)
    
    # Global metrics (all time)
    decade_stats = analyze_decades(movies)
    keyword_stats = analyze_keyword_dna(movies)
    evolution_stats = all_time['evolution']

    final_data = {
        'all': all_time,
        'recent': recent,
        'psychology': psych,
        'decades': decade_stats,
        'keywords': keyword_stats,
        'evolution': evolution_stats
    }
    
    js_content = f"const PROFILE_DATA = {json.dumps(final_data, indent=2)};"
    # Export to JS file
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"var PROFILE_DATA = {json.dumps(final_data, indent=2)};\n")

    print("Expanded JS Data File generated.")

if __name__ == '__main__':
    main()
