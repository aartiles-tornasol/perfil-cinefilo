import json
from collections import defaultdict, Counter
import statistics

FILE_PATH = 'pelis_series_vistas.json'
STOP_WORDS = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'y', 'o', 'en', 'a', 'al', 'the', 'of', 'and', 'in', 'to', 'for', 'on', 'at', 'by', 'is', 'it', 'that', 'with', 'from', 'as', 'part'}
NEGATIVE_THRESHOLD = 5.5 # Ratings <= this are considered "dislikes"

def load_data():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Only Movies with ratings
    return [d for d in data if d.get('tipo') == 'pelicula' and d.get('mi_nota') is not None]

def analyze_worst(dataset, key, min_count=2):
    grouped = defaultdict(list)
    for m in dataset:
        vals = m.get(key, [])
        for v in vals:
            name = v.get('nombre') if isinstance(v, dict) else v
            if name:
                grouped[name].append(m['mi_nota'])
                
    stats = []
    for name, ratings in grouped.items():
        if len(ratings) >= min_count:
            stats.append({
                'name': name,
                'avg': statistics.mean(ratings),
                'count': len(ratings)
            })
            
    # Sort by avg ASCENDING (Worst first)
    stats.sort(key=lambda x: x['avg'])
    return stats[:20]

def analyze_negative_keywords(dataset):
    bad_movies = [m for m in dataset if m['mi_nota'] <= NEGATIVE_THRESHOLD]
    cnt = Counter()
    for m in bad_movies:
        for k in m.get('titulo_keywords', []):
            if k.lower() not in STOP_WORDS and len(k) > 2:
                cnt[k.lower()] += 1
    return cnt.most_common(20)

def generate_report():
    movies = load_data()
    
    worst_genres = analyze_worst(movies, 'generos', min_count=5)
    worst_directors = analyze_worst(movies, 'directores', min_count=2) # 2 is enough for "worst"
    worst_actors = analyze_worst(movies, 'actores', min_count=4)
    bad_keywords = analyze_negative_keywords(movies)
    
    md = "# ⛔ El Anti-Perfil (Lo que NO te gusta)\n"
    md += f"*Análisis de películas con nota <= {NEGATIVE_THRESHOLD}*\n\n"
    
    md += "## 📉 Géneros Kriptonita\n"
    md += "| Género | Nota Media | Vistas |\n|---|---|---|\n"
    for i in worst_genres:
        md += f"| {i['name']} | {i['avg']:.2f} | {i['count']} |\n"
    md += "\n"
    
    md += "## 🎬 Directores 'Non-Gratis'\n"
    md += "*(O aquellos que te han decepcionado reiteradamente)*\n\n"
    md += "| Director | Nota Media | Vistas |\n|---|---|---|\n"
    for i in worst_directors:
        md += f"| {i['name']} | {i['avg']:.2f} | {i['count']} |\n"
    md += "\n"
    
    md += "## 🎭 Actores que Bajan la Nota\n"
    md += "| Actor | Nota Media | Vistas |\n|---|---|---|\n"
    for i in worst_actors:
        md += f"| {i['name']} | {i['avg']:.2f} | {i['count']} |\n"
    md += "\n"
    
    md += "## 🚩 Keywords de Alerta\n"
    md += "Palabras frecuentes en títulos que suspendes:\n\n"
    md += ", ".join([f"{w} ({c})" for w, c in bad_keywords])
    
    return md

if __name__ == "__main__":
    rep = generate_report()
    with open("Reporte_Negativo.md", "w", encoding='utf-8') as f:
        f.write(rep)
    print("Report generated: Reporte_Negativo.md")
