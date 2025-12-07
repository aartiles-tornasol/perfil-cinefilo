import json
from collections import defaultdict, Counter
import statistics
import random

FILE_PATH = 'pelis_series_vistas.json'
CUTOFF_DATE = "2013-12-07"

def load_data():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [d for d in data if d.get('tipo') == 'pelicula' and d.get('mi_nota') is not None]

def get_favorites(movies, min_rating=7.5):
    # Returns stats for Favorites
    favs = [m for m in movies if m['mi_nota'] >= min_rating]
    
    dirs = defaultdict(int)
    gens = defaultdict(int)
    acts = defaultdict(int)
    
    for m in favs:
        for d in m.get('directores', []): dirs[d] += 1
        for g in m.get('generos', []): gens[g] += 1
        for a in m.get('actores', []): 
            name = a.get('nombre')
            if name: acts[name] += 1
            
    return {
        'directors': sorted(dirs.items(), key=lambda x:x[1], reverse=True)[:10],
        'genres': sorted(gens.items(), key=lambda x:x[1], reverse=True)[:10],
        'actors': sorted(acts.items(), key=lambda x:x[1], reverse=True)[:10],
        'samples': [m['titulo'] for m in favs]
    }

def get_dislikes(movies, max_rating=5.5):
    hated = [m for m in movies if m['mi_nota'] <= max_rating]
    
    gens = defaultdict(int)
    for m in hated:
        for g in m.get('generos', []): gens[g] += 1
        
    return {
        'genres': sorted(gens.items(), key=lambda x:x[1], reverse=True)[:5]
    }

def generate_prompts(dataset, label, count=20):
    fav_stats = get_favorites(dataset)
    hate_stats = get_dislikes(dataset)
    
    prompts = []
    
    # We will procedurally generate prompts based on the stats
    # Mix and match strategy
    
    top_dirs = [d[0] for d in fav_stats['directors']]
    top_gens = [g[0] for g in fav_stats['genres']]
    top_acts = [a[0] for a in fav_stats['actors']]
    avoid_gens = [g[0] for g in hate_stats['genres']]
    
    sample_movies = fav_stats['samples']
    
    for i in range(count):
        # Different templates for variety
        roll = i % 4
        
        p = f"**Perfil {label} #{i+1}**: "
        
        if roll == 0: # Director Focused
            d1 = random.choice(top_dirs) if top_dirs else "Unknown"
            g1 = random.choice(top_gens) if top_gens else "General"
            p += f"Busco películas con el estilo visual y narrativo de **{d1}**. Me gusta el género **{g1}** cuando tiene una dirección fuerte. "
            if avoid_gens:
                p += f"Evita el género **{avoid_gens[0]}** si es genérico. "
            p += "Valoro la originalidad y la puesta en escena."
            
        elif roll == 1: # Actor + Vibe
            a1 = random.choice(top_acts) if top_acts else "Unknown"
            m1 = random.choice(sample_movies) if sample_movies else "Unknown"
            p += f"Soy fan de la filmografía de **{a1}**. He disfrutado mucho películas como **'{m1}'**. "
            p += "Busco interpretaciones sólidas y guiones centrados en personajes, no solo efectos especiales. "
            p += "Quiero algo que me mantenga pegado a la pantalla."
            
        elif roll == 2: # Genre Deep Dive
            g1 = random.choice(top_gens) if top_gens else "Cine"
            g2 = random.choice(top_gens)
            p += f"Tengo debilidad por el **{g1}** y el **{g2}**. "
            p += "Busco joyas ocultas o clásicos que quizás me haya perdido en estos géneros. "
            p += "Prefiero tramas inteligentes a la acción sin sentido. "
            if avoid_gens:
                p += f"Por favor, nada de **{random.choice(avoid_gens)}** aburrido."

        elif roll == 3: # "Trust Me" (Based on high ratings)
            samples = random.sample(sample_movies, min(3, len(sample_movies)))
            samples_str = ", ".join([f"'{s}'" for s in samples])
            p += f"Basado en que amé películas como **{samples_str}**, recomiéndame algo similar. "
            p += "Me gustan las historias que dejan poso. "
            p += "No me importa si es antiguo o moderno, siempre que la calidad sea alta (7.5+)."
            
        prompts.append(p)
        
    return prompts

def main():
    movies = load_data()
    recent_movies = [m for m in movies if m.get('fecha_puntuacion_iso', '') >= CUTOFF_DATE]
    
    md = "# 🤖 Perfiles para Recomendación IA\n"
    md += "Copia y pega estos párrafos en ChatGPT/Claude/Gemini para obtener recomendaciones variadas.\n\n"
    
    md += "## 🏛️ Perfiles Históricos (Basado en TODO tu historial)\n"
    hist_prompts = generate_prompts(movies, "HI", 20)
    for p in hist_prompts:
        md += f"{p}\n\n"
        
    md += "## 🚀 Perfiles Modernos (Basado en los últimos 12 años)\n"
    rec_prompts = generate_prompts(recent_movies, "MO", 20)
    for p in rec_prompts:
        md += f"{p}\n\n"
        
    return md

if __name__ == "__main__":
    content = main()
    with open("Perfiles_IA_Recomendaciones.md", "w", encoding='utf-8') as f:
        f.write(content)
    print("Prompts generated: Perfiles_IA_Recomendaciones.md")
