import time
import csv
import requests
import re
import nltk
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Descargar los recursos de nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Configurar el driver de Selenium
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")  # Ejecutar en segundo plano

    # Ruta del archivo msedgedriver.exe
    edge_driver_path = "C:/Users/bryam/Desktop/Driver_Notes/msedgedriver.exe"
    service = Service(edge_driver_path)
    
    return webdriver.Edge(service=service, options=options)


# Limpiar y normalizar el texto
def clean_text(text):
    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'http\S+', '', text)  # Eliminar URLs
    text = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚüÜ\s]', '', text)  # Eliminar signos de puntuación y números
    text = re.sub(r'\s+', ' ', text)  # Eliminar espacios extra
    text = text.strip()  # Eliminar espacios al principio y al final
    return text

# Tokenizar el texto
def tokenize_text(text):
    return word_tokenize(text)

# Remover stopwords
def remove_stopwords(tokens):
    stop_words = set(stopwords.words('spanish'))  # Usar 'spanish' si los comentarios están en español
    return [word for word in tokens if word not in stop_words]

# Lematizar las palabras
def lemmatize_tokens(tokens):
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(token) for token in tokens]

# Extraer los comentarios con BeautifulSoup desde la URL del video
def extract_comments_from_html(html, video_url):
    soup = BeautifulSoup(html, 'html.parser')
    all_comments = set()
    
    # Encontrar los comentarios en el HTML
    comments_elements = soup.find_all('yt-attributed-string', {'id': 'content-text'})
    print(f"Comentarios encontrados: {len(comments_elements)}")  # Depuración

    for comment in comments_elements:
        comment_text = comment.get_text().strip()
        if comment_text:
            all_comments.add(comment_text)
    
    return [{"video_url": video_url, "comment": comment} for comment in all_comments]

# Extraer los comentarios de los primeros 5 videos usando Selenium
def extract_comments(driver, search_query):
    # Automatizar la búsqueda en YouTube
    driver.get("https://www.youtube.com")
    time.sleep(3)
    
    # Realizar la búsqueda
    search_box = driver.find_element(By.NAME, "search_query")
    search_box.clear()
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)  # Esperar resultados de búsqueda

    # Obtener los primeros 5 videos de los resultados
    video_elements = driver.find_elements(By.XPATH, '//a[@id="video-title"]')[:10]  # Cambio clave: primeros 5
    video_urls = [video.get_attribute('href') for video in video_elements]

    all_comments = []
    for video_url in video_urls:
        print(f"🎬 Navegando al video: {video_url}")
        driver.get(video_url)
        print("Esperando que se carguen los comentarios...")

        # Desplazar para cargar comentarios
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)

        # Esperar comentarios
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content-text')))
        except:
            print("⚠️ No se cargaron los comentarios. Pasando al siguiente video.")
            continue

        # Extraer comentarios del HTML
        html = driver.page_source
        comments = extract_comments_from_html(html, video_url)
        all_comments.extend(comments)
        print(f"✅ Comentarios extraídos: {len(comments)}")

    return all_comments

def generate_wordcloud(comments, dataset_folder):
    all_comments_text = ' '.join([comment['comment'] for comment in comments])
    if all_comments_text.strip() == "":
        print("No hay comentarios para generar la nube de palabras.")
        return

    cleaned_text = clean_text(all_comments_text)
    tokens = tokenize_text(cleaned_text)
    filtered_tokens = remove_stopwords(tokens)
    lemmatized_tokens = lemmatize_tokens(filtered_tokens)
    
    # Palabras clave relevantes relacionadas con el caso de estudio
    relevant_words = ['bueno', 'malo', 'útil', 'tecnología', 'avance', 'inteligente', 'futuro', 'aceptación', 'IA', 'innovación']

    # Extender con palabras clave adicionales y limitar el número de palabras
    lemmatized_tokens.extend(relevant_words)
    
    # Contar las palabras y seleccionar las 10 más frecuentes
    from collections import Counter
    word_counts = Counter(lemmatized_tokens)
    common_words = word_counts.most_common(10)  # Obtener las 10 más comunes

    # Crear la nube de palabras con solo las 10 palabras más frecuentes
    wordcloud = WordCloud(width=800, height=400).generate_from_frequencies(dict(common_words))

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')

    # Guardar la imagen de la nube de palabras
    wordcloud_image_path = os.path.join(crear_directorio_youtube(), "wordcloud.png")
    plt.savefig(wordcloud_image_path)
    print(f"🎨 La nube de palabras ha sido guardada en {wordcloud_image_path}")
    plt.show()
    return wordcloud_image_path

# Función para crear la carpeta y obtener el nombre de la carpeta más reciente
def create_dataset_folder():
    base_folder = "Datasets"
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)  # Crear la carpeta base si no existe
    
    # Obtener el número más alto de carpeta existente
    existing_folders = [f for f in os.listdir(base_folder) if f.startswith("Dataset")]
    dataset_numbers = [int(f.replace('Dataset', '')) for f in existing_folders]
    
    next_folder_number = max(dataset_numbers, default=0) + 1
    new_folder = os.path.join(base_folder, f"Dataset{next_folder_number}")
    os.makedirs(new_folder)
    
    return new_folder

# Guardar comentarios en un archivo CSV (original)
def save_comments_to_csv(all_comments, output_file):
    with open(output_file, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["video_url", "comment"])
        writer.writeheader()
        writer.writerows(all_comments)

# Guardar comentarios preprocesados en un archivo CSV (limpiados y normalizados)
def save_preprocessed_comments(all_comments, output_file):
    with open(output_file, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["video_url", "comment"])
        writer.writeheader()
        for comment in all_comments:
            # Preprocesar el comentario
            cleaned_comment = clean_text(comment['comment'])
            tokens = tokenize_text(cleaned_comment)
            filtered_tokens = remove_stopwords(tokens)
            lemmatized_tokens = lemmatize_tokens(filtered_tokens)
            processed_comment = ' '.join(lemmatized_tokens)
            writer.writerow({"video_url": comment['video_url'], "comment": processed_comment})

def crear_directorio_youtube():
    folder_path = "./uploads/youtube"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path
def enviar_archivo_al_servidor(filepath, endpoint):
    url = f"http://127.0.0.1:5000/{endpoint}"

    if not os.path.exists(filepath):
        print(f"⚠️ Error: El archivo {filepath} no existe.")
        return

    try:
        with open(filepath, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                print(f"✅ Archivo {filepath} enviado con éxito:", response.json())
            else:
                print(f"⚠️ Error al enviar el archivo: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Error al conectarse al servidor: {e}")

# Función principal
def main():
    search_query = "inteligencia artificial"  # La búsqueda que deseas realizar
    all_comments = []
    driver = setup_driver()

    try:
        print(f"🔍 Buscando videos sobre: {search_query}")
        comments = extract_comments(driver, search_query)
        all_comments.extend(comments)
        print(f"✅ Comentarios extraídos de {len(comments)} videos")

    finally:
        driver.quit()

    # Crear la carpeta para guardar los resultados
    dataset_folder = crear_directorio_youtube()

    # Guardar comentarios originales
    original_output_file = os.path.join(dataset_folder, "youtube_comments_original.csv")
    save_comments_to_csv(all_comments, original_output_file)
    print(f"🎉 Extracción completada. Los comentarios originales han sido guardados en {original_output_file}")

    # Guardar comentarios preprocesados
    preprocessed_output_file = os.path.join(dataset_folder, "youtube_comments_preprocessed.csv")
    save_preprocessed_comments(all_comments, preprocessed_output_file)
    print(f"🎉 Los comentarios preprocesados han sido guardados en {preprocessed_output_file}")

    # Generar y guardar la nube de palabras
    wordcloud_image_path = generate_wordcloud(all_comments, dataset_folder)

    # Enviar los archivos al servidor
    enviar_archivo_al_servidor(preprocessed_output_file, "subir_csv")
    if wordcloud_image_path:
        enviar_archivo_al_servidor(wordcloud_image_path, "subir_csv")


if __name__ == "__main__":
    main()