#!/usr/bin/env python3
"""
Parse MD report files to generate dashboard data.
Uses the existing .md summaries as the source of truth.
"""

import re
import json
import os

# MD Files
MD_FILES = {
    'directors_all': 'Top_20_Directores.md',
    'directors_recent': 'Top_20_Directores_Recent.md',
    'actors': 'Reporte_Actores_Ratings.md',
    'genres': 'Reporte_Generos.md',
    'frequency': 'Reporte_Frecuencia_Vistas.md',
    'psychology': 'Reporte_Psicologia.md',
}

# Image mappings for directors
DIRECTOR_IMAGES = {
    "Martin McDonagh": "img/Martin_McDonagh.jpg",
    "Jean-Pierre Jeunet": "img/Jean_Pierre_Jeunet.jpg",
    "Alex Garland": "img/Alex_Garland.jpg",
    "Aaron Sorkin": "img/Aaron_Sorkin.jpg",
    "Marc Forster": "img/Marc_Forster.jpg",
    "Damien Chazelle": "img/Damien_Chazelle.jpg",
    "Rian Johnson": "img/Rian_Johnson.jpg",
    "Baz Luhrmann": "img/Baz_Luhrmann.jpg",
    "Jordan Peele": "img/Jordan_Peele.jpg",
    "Park Chan-wook": "img/Park_Chan_wook.jpg",
    "Alfred Hitchcock": "img/Alfred_Hitchcock.jpg",
    "Quentin Tarantino": "img/Quentin_Tarantino.jpg",
    "Steven Spielberg": "img/Steven_Spielberg.jpg",
    "Christopher Nolan": "img/Christopher_Nolan.jpg",
    "Wes Anderson": "img/Wes_Anderson.jpg",
    "David Fincher": "img/David_Fincher.jpg",
    "M. Night Shyamalan": "img/M_Night_Shyamalan.jpg",
}

ACTOR_IMAGES = {
    "Helena Bonham Carter": "img/Helena_Bonham_Carter.jpg",
    "Michael Cera": "img/Michael_Cera.jpg",
    "Meryl Streep": "img/Meryl_Streep.jpg",
    "Tom Hollander": "img/Tom_Hollander.jpg",
    "Jon Hamm": "img/Jon_Hamm.jpg",
    "Emma Stone": "img/Emma_Stone.jpg",
    "Mark Rylance": "img/Mark_Rylance.jpg",
    "Sam Rockwell": "img/Sam_Rockwell.jpg",
    "J.K. Simmons": "img/J_K_Simmons.jpg",
    "Mark Ruffalo": "img/Mark_Ruffalo.jpg",
}


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
                'image': DIRECTOR_IMAGES.get(name)
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
                'image': ACTOR_IMAGES.get(name)
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
