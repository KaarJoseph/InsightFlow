import http.client
import json
import csv
import os
import time
import requests
import nltk
nltk.data.path.append(r'C:\Users\bryam\AppData\Roaming\nltk_data')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

import re

from selenium.webdriver.edge.options import Options

options = Options()
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-gpu')
driver = webdriver.Edge(options=options)


# Función para agregar datos al archivo CSV
def append_to_csv_file(filename, data):
    fieldnames = ["Comentario", "Fecha", "ID"]  # Campos actualizados
    try:
        with open(filename, "a", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for item in data:
                writer.writerow(item)
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")

# Función para limpiar y normalizar el texto
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9áéíóúüñ ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    stop_words = set(stopwords.words("spanish"))
    tokens = word_tokenize(text)
    cleaned_tokens = [word for word in tokens if word not in stop_words]
    return " ".join(cleaned_tokens)

# Función para obtener IDs de videos relacionados
def get_video_ids(search_term):
    driver = webdriver.Edge()
    video_ids = []

    try:
        driver.get("https://www.tiktok.com/")

        # Espera a que el campo de búsqueda sea clickeable
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Search')]"))
        )
        search_box = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Search')]")

        # Asegúrate de que sea visible e interactuable
        driver.execute_script("arguments[0].scrollIntoView();", search_box)
        time.sleep(1)  # Pequeño retraso para asegurar que el scroll se realice
        search_box.click()
        search_box.send_keys(search_term)
        search_box.send_keys(Keys.RETURN)

        # Esperar a los videos relacionados (usa un tiempo mayor si es necesario)
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/video/')]"))
        )
        video_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
        video_ids = [video.get_attribute("href").split("/")[-1] for video in video_elements]
    except Exception as e:
        print(f"Error al buscar videos: {e}")
    finally:
        driver.quit()

    return video_ids

# Función para extraer comentarios de un video
def extract_comments(video_id):
    conn = http.client.HTTPSConnection("tiktok-api23.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': "a804f1756fmsh533187fa19c7d06p126490jsncd9a259b938b",
        'x-rapidapi-host': "tiktok-api23.p.rapidapi.com"
    }

    cursor = 0
    comments = []
    fecha_actual = time.strftime("%Y-%m-%d")

    while True:
        conn.request("GET", f"/api/post/comments?videoId={video_id}&count=50&cursor={cursor}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))

        if "comments" in response_json and response_json["comments"]:
            for comment in response_json["comments"]:
                text = comment.get("text", "Sin texto")
                cleaned_text = clean_text(text)
                comments.append({
                    "Comentario": cleaned_text,
                    "Fecha": fecha_actual,
                    "ID": "tiktok"
                })

            cursor = response_json.get("cursor", 0)
            if not response_json.get("has_more", False):
                break
        else:
            break

    return comments

# Obtener IDs de videos relacionados
search_term = "Ventajas y desventajas de la IA?"
video_ids = get_video_ids(search_term)

# Verifica si hay videos antes de procesar
if not video_ids:
    print("No se encontraron videos relacionados con el término de búsqueda.")
else:
    for video_id in video_ids:
        comments = extract_comments(video_id)
        if comments:
            append_to_csv_file("comentarios_tiktok.csv", comments)
            print(f"Comentarios agregados para el video {video_id}")

# Función para enviar el archivo al servidor
def enviar_csv_al_servidor(filepath):
    if not os.path.exists(filepath):
        print(f"Error: El archivo {filepath} no existe.")
        return

    url = "http://127.0.0.1:5000/subir_csv"
    try:
        with open(filepath, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                print("Archivo enviado con éxito:", response.json())
            else:
                print("Error al enviar el archivo:", response.json())
    except Exception as e:
        print(f"Error al conectarse al servidor: {e}")

# Ruta del archivo CSV generado
csv_filepath = "comentarios_tiktok.csv"

# Enviar el archivo al servidor
enviar_csv_al_servidor(csv_filepath)