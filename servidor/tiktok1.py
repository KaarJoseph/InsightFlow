import csv
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Configuración del navegador Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ejecutar en segundo plano
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Inicialización del driver
driver = webdriver.Chrome(options=chrome_options)

# Función para buscar y extraer comentarios
def extraer_comentarios(busqueda):
    driver.get("https://www.tiktok.com")
    comentarios = []
    try:
        # Esperar hasta que la barra de búsqueda esté disponible
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Buscar"]'))
        )
        search_bar.send_keys(busqueda)
        search_bar.send_keys(Keys.ENTER)
        time.sleep(5)  # Esperar a que se carguen los resultados

        # Extraer comentarios (ajusta el XPath si es necesario)
        elementos_comentarios = driver.find_elements(By.XPATH, '//p[contains(@class, "comment-text-class")]')
        for elemento in elementos_comentarios:
            comentario = elemento.text
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comentarios.append({"id": "t", "comentario": comentario, "fecha": fecha})

    except Exception as e:
        print(f"Error durante la extracción: {e}")
    finally:
        driver.quit()  # Asegurarse de cerrar el navegador
    return comentarios

# Función para guardar los comentarios en un archivo CSV
def guardar_comentarios_csv(comentarios, nombre_archivo="comentarios_tiktok.csv"):
    try:
        with open(nombre_archivo, mode="w", encoding="utf-8", newline="") as archivo_csv:
            campos = ["id", "comentario", "fecha"]
            writer = csv.DictWriter(archivo_csv, fieldnames=campos)
            writer.writeheader()
            writer.writerows(comentarios)
        print(f"Archivo CSV guardado exitosamente: {nombre_archivo}")
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")

# Función para enviar el archivo CSV al servidor
def enviar_csv_al_servidor(filepath):
    if not os.path.exists(filepath):
        print(f"Error: El archivo {filepath} no existe.")
        return

    url = "http://127.0.0.1:5000/subir_csv"  # URL del servidor
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

# Main: Configuración de búsqueda y ejecución
if __name__ == "__main__":
    try:
        busqueda = "IA"  # Define aquí el texto que quieres buscar
        comentarios_extraidos = extraer_comentarios(busqueda)
        if comentarios_extraidos:
            guardar_comentarios_csv(comentarios_extraidos)
            enviar_csv_al_servidor("comentarios_tiktok.csv")
        else:
            print("No se encontraron comentarios.")
    except Exception as e:
        print(f"Error general: {e}")
