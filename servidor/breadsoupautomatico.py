from googlesearch import search
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unidecode

# -------------------------
# CONFIGURACIÓN
# -------------------------

# Ampliamos palabras clave para buscar páginas sobre la ACEPTACIÓN de la IA en la vida cotidiana
keywords = [
    "inteligencia artificial", "IA", "tecnología", "ChatGPT", "automatización",
    "machine learning", "aprendizaje automático", "ética", "opinión",
    "IA en la vida cotidiana", "IA en el trabajo", "IA en educación", "IA en medicina",
    "IA y sociedad", "IA y empleo", "IA y creatividad", "aceptación de la inteligencia artificial",
    "futuro de la inteligencia artificial", "percepción de la IA", "IA en la economía",
    "IA en la industria", "beneficios de la IA", "impacto social de la IA"
]

# Definir el término de búsqueda para Google
search_query = "aceptación de la inteligencia artificial en la vida cotidiana"

# Número de resultados a obtener de Google
num_results = 30  # Puedes aumentarlo si quieres más datos


# -------------------------
# FUNCIONES DE EXTRACCIÓN
# -------------------------

# Función para dividir el texto en fragmentos más pequeños
def split_into_fragments(text, max_length=300):
    sentences = text.split('. ')
    fragments = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 50 and len(sentence) <= max_length:
            fragments.append(sentence)
    return fragments

# Función para extraer fragmentos relevantes (SIN URLs)
def extract_fragments(url, keywords):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar contenido principal
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if not main_content:
            main_content = soup

        # Extraer párrafos del contenido principal
        paragraphs = main_content.find_all(['p', 'div'])
        fragments = []

        for paragraph in paragraphs:
            text = paragraph.get_text(strip=True)

            # Extraer texto con palabras clave
            if any(keyword.lower() in text.lower() for keyword in keywords):
                fragments.extend(split_into_fragments(text))

        return list(set(fragments))  # Eliminar duplicados

    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return []


# -------------------------
# BÚSQUEDA AUTOMÁTICA DE URLs EN GOOGLE
# -------------------------

print("Buscando URLs relevantes en Google...")
urls = list(search(search_query, num_results=num_results, lang="es"))  # Búsqueda automática de Google

# -------------------------
# EXTRACCIÓN AUTOMÁTICA DE FRAGMENTOS
# -------------------------

print("Extrayendo información de las páginas...")
all_comments = []
for url in urls:
    print(f"Procesando: {url}")
    fragments = extract_fragments(url, keywords)
    all_comments.extend(fragments)

# Convertir a DataFrame con solo los comentarios
dataset = pd.DataFrame({'Comentario': all_comments})

# -------------------------
# LIMPIEZA DE DATOS
# -------------------------

def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.lower()  # Convertir a minúsculas
    text = unidecode.unidecode(text)  # Eliminar acentos
    text = re.sub(r'\s+', ' ', text)  # Eliminar espacios extra
    text = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ,.!? ]', '', text)  # Eliminar caracteres especiales
    text = text.strip()  # Eliminar espacios en los extremos
    return text

print("Limpiando el dataset...")

# Aplicar limpieza
dataset['Comentario'] = dataset['Comentario'].apply(clean_text)
dataset.drop_duplicates(inplace=True)  # Eliminar duplicados

# -------------------------
# GUARDAR RESULTADOS
# -------------------------

dataset.to_csv('comentarios_IA.csv', index=False, encoding='utf-8')

print(f"Se han guardado {len(dataset)} comentarios limpios en 'comentarios_IA.csv'.")
