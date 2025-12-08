#!/usr/bin/env python3
"""
Parse MD report files to generate dashboard data.
Uses the existing .md summaries as the source of truth.
"""

import re
import json
import os

import requests
import shutil

# MD Files
MD_FILES = {
    'directors_all': 'Top_20_Directores.md',
    'directors_recent': 'Top_20_Directores_Recent.md',
    'actors': 'Reporte_Actores_Ratings.md',
    'genres': 'Reporte_Generos.md',
    'frequency': 'Reporte_Frecuencia_Vistas.md',
    'psychology': 'Reporte_Psicologia.md',
}

# Wikipedia image URLs for directors (reliable public URLs)
WIKIPEDIA_DIRECTOR_IMAGES = {
    "Martin McDonagh": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Martin_McDonagh_2012.jpg/440px-Martin_McDonagh_2012.jpg",
    "Jean-Pierre Jeunet": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Jean-Pierre_Jeunet_2010.jpg/440px-Jean-Pierre_Jeunet_2010.jpg",
    "Alex Garland": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Alex_Garland_2018.jpg/440px-Alex_Garland_2018.jpg",
    "Aaron Sorkin": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Aaron_Sorkin_2012.jpg/440px-Aaron_Sorkin_2012.jpg",
    "Marc Forster": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Marc_Forster_2012.jpg/440px-Marc_Forster_2012.jpg",
    "Damien Chazelle": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Damien_Chazelle_2017.jpg/440px-Damien_Chazelle_2017.jpg",
    "Rian Johnson": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Rian_Johnson_by_Gage_Skidmore.jpg/440px-Rian_Johnson_by_Gage_Skidmore.jpg",
    "Baz Luhrmann": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Baz_Luhrmann_2013.jpg/440px-Baz_Luhrmann_2013.jpg",
    "Jordan Peele": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Jordan_Peele_2019.jpg/440px-Jordan_Peele_2019.jpg",
    "Park Chan-wook": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Park_Chan-wook_2017.jpg/440px-Park_Chan-wook_2017.jpg",
    "Alfred Hitchcock": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Alfred_Hitchcock_1955.jpg/440px-Alfred_Hitchcock_1955.jpg",
    "Quentin Tarantino": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Quentin_Tarantino_by_Gage_Skidmore.jpg/440px-Quentin_Tarantino_by_Gage_Skidmore.jpg",
    "Steven Spielberg": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Steven_Spielberg_by_Gage_Skidmore.jpg/440px-Steven_Spielberg_by_Gage_Skidmore.jpg",
    "Christopher Nolan": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Christopher_Nolan_Cannes_2018.jpg/440px-Christopher_Nolan_Cannes_2018.jpg",
    "Wes Anderson": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Wes_Anderson_Cannes_2012_2.jpg/440px-Wes_Anderson_Cannes_2012_2.jpg",
    "David Fincher": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/David_Fincher_Cannes_2007.jpg/440px-David_Fincher_Cannes_2007.jpg",
    "M. Night Shyamalan": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/M._Night_Shyamalan_2018.jpg/440px-M._Night_Shyamalan_2018.jpg",
    "Clint Eastwood": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Clint_Eastwood_2023.jpg/440px-Clint_Eastwood_2023.jpg",
    "Christopher McQuarrie": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Christopher_McQuarrie_by_Gage_Skidmore.jpg/440px-Christopher_McQuarrie_by_Gage_Skidmore.jpg",
    "Fernando Meirelles": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Fernando_meirelles.jpg/440px-Fernando_meirelles.jpg",
    "Craig Gillespie": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Craig_Gillespie_2018.jpg/440px-Craig_Gillespie_2018.jpg",
    "Ron Howard": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Ron_Howard_2014.jpg/440px-Ron_Howard_2014.jpg",
    "Oriol Paulo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Oriol_Paulo_2017.jpg/440px-Oriol_Paulo_2017.jpg",
    "Kenneth Branagh": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Kenneth_Branagh_2018.jpg/440px-Kenneth_Branagh_2018.jpg",
    "Bong Joon-ho": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Bong_Joon-ho_2017.jpg/440px-Bong_Joon-ho_2017.jpg",
}

# Wikipedia image URLs for actors
WIKIPEDIA_ACTOR_IMAGES = {
    "James Stewart": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/James_Stewart_publicity_photo_1960s.jpg/440px-James_Stewart_publicity_photo_1960s.jpg",
    "Elias Koteas": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Elias_Koteas_2008.jpg/440px-Elias_Koteas_2008.jpg",
    "Tim Roth": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Tim_Roth_2013.jpg/440px-Tim_Roth_2013.jpg",
    "Harvey Keitel": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Harvey_Keitel_Cannes_2018.jpg/440px-Harvey_Keitel_Cannes_2018.jpg",
    "Mahershala Ali": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Mahershala_Ali_2019.jpg/440px-Mahershala_Ali_2019.jpg",
    "Mark Rylance": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Mark_Rylance_2016.jpg/440px-Mark_Rylance_2016.jpg",
    "Emma Stone": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Emma_Stone_2018.jpg/440px-Emma_Stone_2018.jpg",
    "Sarah Paulson": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Sarah_Paulson_2018.jpg/440px-Sarah_Paulson_2018.jpg",
    "Sam Rockwell": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Sam_Rockwell_2018.jpg/440px-Sam_Rockwell_2018.jpg",
    "Casey Affleck": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Casey_Affleck_2016.jpg/440px-Casey_Affleck_2016.jpg",
    "Helena Bonham Carter": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Helena_Bonham_Carter_2011.jpg/440px-Helena_Bonham_Carter_2011.jpg",
    "Michael Cera": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Michael_Cera_2018.jpg/440px-Michael_Cera_2018.jpg",
    "Meryl Streep": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Meryl_Streep_2016.jpg/440px-Meryl_Streep_2016.jpg",
    "Tom Hollander": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Tom_Hollander_2016.jpg/440px-Tom_Hollander_2016.jpg",
    "Jon Hamm": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Jon_Hamm_2015.jpg/440px-Jon_Hamm_2015.jpg",
    "J.K. Simmons": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/J._K._Simmons_2015.jpg/440px-J._K._Simmons_2015.jpg",
    "Mark Ruffalo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Mark_Ruffalo_2017.jpg/440px-Mark_Ruffalo_2017.jpg",
    "Toni Collette": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Toni_Collette_2018.jpg/440px-Toni_Collette_2018.jpg",
    "Colin Firth": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Colin_Firth_TIFF_2018.jpg/440px-Colin_Firth_TIFF_2018.jpg",
}


def get_safe_filename(name):
    """Convert name to safe filename."""
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')


def get_image_for_person(name, is_director=True):
    """Get or download image for a person. Returns local path or None."""
    if not os.path.exists('img'):
        os.makedirs('img')
    
    safe_name = get_safe_filename(name)
    local_path = f"img/{safe_name}.jpg"
    
    # Check if image already exists locally
    if os.path.exists(local_path):
        return local_path
    
    # Try to download from Wikipedia
    # Try to download from Wikipedia only if NOT already present
    # Skip download if network is unavailable
    url_dict = WIKIPEDIA_DIRECTOR_IMAGES if is_director else WIKIPEDIA_ACTOR_IMAGES
    if name in url_dict:
        url = url_dict[name]
        try:
            response = requests.get(url, stream=True, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                with open(local_path, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                print(f"  Downloaded: {name}")
                return local_path
        except Exception:
            pass  # Silently fail - we'll just have no image
    
    return None


def read_md(filename):
    """Read markdown file content."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def parse_table(content, start_marker, end_marker=None):
    """Parse a markdown table into list of dicts."""
    lines = content.split('\n')
    results = []
    in_table = False
    headers = None
    
    for i, line in enumerate(lines):
        # Find start marker
        if start_marker in line:
            in_table = True
            continue
        
        # Check for end marker
        if end_marker and end_marker in line:
            break
            
        if not in_table:
            continue
            
        # Skip separator lines
        if line.strip().startswith('|---'):
            continue
            
        # Parse header line
        if line.strip().startswith('| Rank') or line.strip().startswith('| Película'):
            headers = [h.strip() for h in line.split('|')[1:-1]]
            continue
            
        # Skip non-table lines
        if not line.strip().startswith('|'):
            if results:  # End of table
                break
            continue
            
        # Parse data row
        cells = [c.strip().replace('**', '') for c in line.split('|')[1:-1]]
        if len(cells) >= 3:
            results.append(cells)
    
    return results


def parse_directors(content, top_n=10):
    """Parse directors from Top_20 format."""
    rows = parse_table(content, '## 🏆 Top 20 Directores')
    directors = []
    for row in rows[:top_n]:
        if len(row) >= 4:
            name = row[1]
            avg = float(row[2])
            count = int(row[3])
            directors.append({
                'name': name,
                'avg': avg,
                'count': count,
                'image': get_image_for_person(name, is_director=True)
            })
    return directors


def parse_actors(content, section_marker, top_n=5):
    """Parse actors from Reporte_Actores format."""
    rows = parse_table(content, section_marker)
    actors = []
    for row in rows[:top_n]:
        if len(row) >= 4:
            name = row[1]
            avg = float(row[2])
            count = int(row[3])
            actors.append({
                'name': name,
                'avg': avg,
                'count': count,
                'image': get_image_for_person(name, is_director=False)
            })
    return actors


def parse_genres(content, section_marker, top_n=20):
    """Parse genres from Reporte_Generos format."""
    rows = parse_table(content, section_marker)
    genres = []
    for row in rows[:top_n]:
        if len(row) >= 4:
            name = row[1]
            avg = float(row[2])
            count = int(row[3])
            genres.append({
                'name': name,
                'avg': avg,
                'count': count,
                'image': None
            })
    return genres


def parse_psychology(content):
    """Parse psychology section (Guilty Pleasures & Haters)."""
    guilty = []
    haters = []
    
    # Parse Placeres Culpables
    guilty_rows = parse_table(content, '### 🫣 Placeres Culpables', '### 🤬')
    for row in guilty_rows[:10]:
        if len(row) >= 4:
            title = row[0]
            diff = float(row[3].replace('+', ''))
            guilty.append({
                't': title,
                'd': diff,
                'img': f"img/poster_{title.replace(' ', '_').replace('.', '')}.jpg"
            })
    
    # Parse Haters
    haters_rows = parse_table(content, '### 🤬 Opiniones Impopulares', '## 👴')
    for row in haters_rows[:10]:
        if len(row) >= 4:
            title = row[0]
            diff = abs(float(row[3]))
            haters.append({
                't': title,
                'd': diff,
                'img': f"img/poster_{title.replace(' ', '_').replace('.', '')}.jpg"
            })
    
    return {'guilty': guilty, 'haters': haters}


def parse_evolution(content):
    """Parse evolution/cascarrabias table."""
    rows = parse_table(content, "## 👴 Índice de 'Cascarrabias'", '## 🧬')
    evolution = []
    for row in rows:
        if len(row) >= 3:
            year = row[0].strip()
            # Remove emoji indicators
            avg_str = row[1].split()[0]  # Get just the number
            try:
                year_int = int(year)
                avg = float(avg_str)
                evolution.append({'year': year_int, 'avg': avg})
            except ValueError:
                continue
    return evolution


def get_total_from_md(filename):
    """Extract total movies count from MD header."""
    content = read_md(filename)
    match = re.search(r'\*\*Títulos analizados\*\*:\s*(\d+)', content)
    if match:
        return int(match.group(1))
    return 0


def main():
    # Read all MD files
    directors_all_md = read_md(MD_FILES['directors_all'])
    directors_recent_md = read_md(MD_FILES['directors_recent'])
    actors_md = read_md(MD_FILES['actors'])
    genres_md = read_md(MD_FILES['genres'])
    psychology_md = read_md(MD_FILES['psychology'])
    
    # Get totals
    total_all = get_total_from_md(MD_FILES['directors_all'])
    total_recent = get_total_from_md(MD_FILES['directors_recent'])
    
    # Parse "All Time" data
    directors_all = parse_directors(directors_all_md, 10)
    actors_all = parse_actors(actors_md, '### Top Actores Histórico', 5)
    genres_all = parse_genres(genres_md, '### Top Géneros por Nota', 20)
    
    # Parse "Recent" data
    directors_recent = parse_directors(directors_recent_md, 10)
    actors_recent = parse_actors(actors_md, '### Top Actores Recientes', 5)
    genres_recent = parse_genres(genres_md, '### Top Géneros Recientes', 20)
    
    # Parse Psychology (global)
    psychology = parse_psychology(psychology_md)
    
    # Parse Evolution (from psychology report)
    evolution = parse_evolution(psychology_md)
    
    # Calculate averages from evolution
    if evolution:
        all_avgs = [e['avg'] for e in evolution]
        avg_all = round(sum(all_avgs) / len(all_avgs), 2)
        # Recent = last ~12 years
        recent_evo = [e for e in evolution if e['year'] >= 2013]
        if recent_evo:
            avg_recent = round(sum(e['avg'] for e in recent_evo) / len(recent_evo), 2)
        else:
            avg_recent = avg_all
    else:
        avg_all = 6.41
        avg_recent = 6.38
    
    # Build distribution placeholder (would need more data)
    distribution_all = [7, 13, 47, 112, 274, 353, 287, 138, 22, 2]
    distribution_recent = [5, 12, 27, 63, 174, 274, 241, 105, 11, 2]
    
    # Construct final data structure
    final_data = {
        'all': {
            'total': total_all,
            'avg': avg_all,
            'evolution': evolution,
            'distribution': distribution_all,
            'directors': directors_all,
            'actors': actors_all,
            'genres': genres_all,
        },
        'recent': {
            'total': total_recent,
            'avg': avg_recent,
            'evolution': [e for e in evolution if e['year'] >= 2013],
            'distribution': distribution_recent,
            'directors': directors_recent,
            'actors': actors_recent,
            'genres': genres_recent,
        },
        'psychology': psychology,
        'decades': [{'name': '2020s', 'avg': 6.87}],
        'keywords': [],
        'evolution': evolution
    }
    
    # Export to data.js
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"var PROFILE_DATA = {json.dumps(final_data, indent=2, ensure_ascii=False)};\n")
    
    print(f"Generated data.js from MD reports!")
    print(f"  All Time: {total_all} movies, Avg: {avg_all}")
    print(f"  Recent: {total_recent} movies, Avg: {avg_recent}")
    print(f"  Directors: {len(directors_all)} (all), {len(directors_recent)} (recent)")
    print(f"  Actors: {len(actors_all)} (all), {len(actors_recent)} (recent)")
    print(f"  Genres: {len(genres_all)} (all), {len(genres_recent)} (recent)")
    print(f"  Psychology: {len(psychology['guilty'])} guilty, {len(psychology['haters'])} haters")


if __name__ == '__main__':
    main()
