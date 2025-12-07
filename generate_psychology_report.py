import json
from collections import defaultdict, Counter
import statistics
from datetime import datetime

FILE_PATH = 'pelis_series_vistas.json'
STOP_WORDS = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'y', 'o', 'en', 'a', 'al', 'the', 'of', 'and', 'in', 'to', 'for', 'on', 'at', 'by', 'is', 'it', 'that', 'with', 'from', 'as', 'part'}

def load_movies():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Filter: Only rated movies
    return [d for d in data if d.get('tipo') == 'pelicula' and d.get('mi_nota') is not None]

def get_year_watched(item):
    # Try multiple date fields if needed, but primary is fecha_puntuacion_iso
    d = item.get('fecha_puntuacion_iso')
    if d:
        return d[:4] # YYYY
    return None

def analyze_against_world(movies):
    guilty_pleasures = []
    haters = []
    hidden_gems = [] # High rating, low popularity/public rating but not trashy

    for m in movies:
        my_rating = m.get('mi_nota')
        public_rating = m.get('vote_average_publico', 0)
        
        if not public_rating:
            continue
            
        diff = my_rating - public_rating
        
        # Placeres Culpables: I like it (>=7), world hates it (<=5.8 to be generous)
        if my_rating >= 7.0 and public_rating <= 5.8:
            guilty_pleasures.append({
                'title': m['titulo'],
                'mine': my_rating,
                'public': public_rating,
                'diff': diff
            })
            
        # Hater / Unpopular Opinion: I hate it (<=5), world loves it (>=7.5)
        if my_rating <= 5.0 and public_rating >= 7.3:
            haters.append({
                'title': m['titulo'],
                'mine': my_rating,
                'public': public_rating,
                'diff': diff
            })

    # Sort by magnitude of difference
    guilty_pleasures.sort(key=lambda x: x['diff'], reverse=True)
    haters.sort(key=lambda x: x['diff']) # most negative first

    return guilty_pleasures, haters

def analyze_curmudgeon_index(movies):
    years = defaultdict(list)
    for m in movies:
        y = get_year_watched(m)
        if y:
            years[y].append(m['mi_nota'])
            
    stats = []
    for y, ratings in years.items():
        stats.append({
            'year': y,
            'avg': statistics.mean(ratings),
            'count': len(ratings)
        })
    
    stats.sort(key=lambda x: x['year'])
    return stats

def analyze_keywords(movies):
    # Only movies I liked (>= 8)
    liked_movies = [m for m in movies if m['mi_nota'] >= 8]
    cnt = Counter()
    
    for m in liked_movies:
        kws = m.get('titulo_keywords', [])
        for k in kws:
            k_lower = k.lower()
            if k_lower not in STOP_WORDS and len(k_lower) > 2:
                cnt[k_lower] += 1
                
    return cnt.most_common(30)

def analyze_dynamic_duos(movies):
    duos = defaultdict(list)
    
    for m in movies:
        rating = m['mi_nota']
        directors = m.get('directores', [])
        actors = m.get('actores', []) # list of dicts
        
        # Extract actor names, top 5 only to be relevant
        actor_names = [a['nombre'] for a in actors[:5] if 'nombre' in a]
        
        for d in directors:
            for a in actor_names:
                if d == a: continue # Director acting in own movie
                duos[(d, a)].append(rating)
                
    stats = []
    for (d, a), ratings in duos.items():
        if len(ratings) >= 3:
            stats.append({
                'director': d,
                'actor': a,
                'count': len(ratings),
                'avg': statistics.mean(ratings)
            })
            
    stats.sort(key=lambda x: x['avg'], reverse=True)
    return stats

def generate_report():
    movies = load_movies()
    
    # 1. World Analysis
    guilty, haters = analyze_against_world(movies)
    
    # 2. Curmudgeon
    curmudgeon = analyze_curmudgeon_index(movies)
    
    # 3. Keywords
    keywords = analyze_keywords(movies)
    
    # 4. Duos
    duos = analyze_dynamic_duos(movies)
    
    # --- WRITE MARKDOWN ---
    md = "# 🧠 Reporte Psicología Cinéfila\n\n"
    
    md += "## 🌍 Tú contra el Mundo\n"
    
    md += "### 🫣 Placeres Culpables\n"
    md += "*(Te gustaron mucho, pero el mundo las odia)*\n\n"
    md += "| Película | Tu Nota | Nota Público | Diferencia |\n|---|---|---|---|\n"
    for item in guilty[:10]:
        md += f"| **{item['title']}** | {item['mine']} | {item['public']} | +{item['diff']:.1f} |\n"
    if not guilty:
        md += "_No tienes placeres culpables detectados (¿tienes un gusto muy normativo?)_\n"
    md += "\n"
        
    md += "### 🤬 Opiniones Impopulares (Modo Hater)\n"
    md += "*(Obras maestras para todos... menos para ti)*\n\n"
    md += "| Película | Tu Nota | Nota Público | Diferencia |\n|---|---|---|---|\n"
    for item in haters[:10]:
        md += f"| **{item['title']}** | {item['mine']} | {item['public']} | {item['diff']:.1f} |\n"
    if not haters:
        md += "_Parece que no odias nada popular._\n"
    md += "\n"
    
    md += "## 👴 Índice de 'Cascarrabias' (Evolución)\n"
    md += "¿Te estás volviendo más exigente con los años?\n\n| Año | Nota Media | Vistas |\n|---|---|---|\n"
    for s in curmudgeon:
        trend = ""
        # Simple trend indicator visual
        if s['avg'] >= 7.5: trend = "💖"
        elif s['avg'] <= 6.0: trend = "💀"
        md += f"| {s['year']} | {s['avg']:.2f} {trend} | {s['count']} |\n"
    md += "\n"
    
    md += "## 🧬 ADN de tus Favoritas (Keywords)\n"
    md += "Palabras más repetidas en títulos que puntúas con 9 o 10:\n\n"
    kw_strings = [f"**{w}** ({c})" for w, c in keywords]
    md += ", ".join(kw_strings)
    md += "\n\n"
    
    md += "## 🤝 Dúos Dinámicos (Director + Actor)\n"
    md += "Colaboraciones que siempre (o casi siempre) te funcionan (Min 3 pelis).\n\n"
    md += "| Director | Actor | Nota Media | Vistas |\n|---|---|---|---|\n"
    for d in duos[:15]:
        md += f"| {d['director']} | {d['actor']} | **{d['avg']:.2f}** | {d['count']} |\n"
        
    return md

if __name__ == "__main__":
    report = generate_report()
    with open("Reporte_Psicologia.md", "w", encoding='utf-8') as f:
        f.write(report)
    print("Report generated: Reporte_Psicologia.md")
