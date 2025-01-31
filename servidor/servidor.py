from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import csv
import requests
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/ejecutar_extraccion', methods=['POST'])
def ejecutar_extraccion():
    """
    Ejecuta el script main.py para realizar la extracción de datos.
    """
    try:
        proceso = subprocess.Popen(
            ["python", "main.py"],  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proceso.communicate()  # Esperar a que termine

        if proceso.returncode != 0:
            raise RuntimeError(f"Error al ejecutar el script: {stderr}")

        # Después de ejecutar main.py, enviar los archivos generados a la página web
        enviar_archivos_a_pagina_web()

        return jsonify({"mensaje": "Extracción completada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al ejecutar la extracción: {e}"}), 500

@app.route('/subir_csv', methods=['POST'])
def subir_csv():
    """
    Recibe un archivo CSV desde el cliente y lo guarda en el servidor.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "El nombre del archivo está vacío"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Formato de archivo no permitido, solo se permite CSV"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    return jsonify({"mensaje": f"Archivo {filename} recibido y guardado con éxito"}), 200

@app.route('/obtener_datos_youtube', methods=['GET'])
def obtener_datos_youtube():
    """
    Lee el archivo CSV de YouTube y devuelve los datos en formato JSON.
    """
    csv_path = './uploads/youtube/youtube_comments_preprocessed.csv'

    if not os.path.exists(csv_path):
        return jsonify({"error": "El archivo CSV de YouTube no existe"}), 404

    data = []
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return jsonify(data[:15]), 200
    except Exception as e:
        return jsonify({"error": f"Error al leer el archivo CSV: {e}"}), 500

    return jsonify(data), 200

@app.route('/ejecutar_extraccion_web', methods=['POST'])
def ejecutar_extraccion_web():
    """
    Ejecuta la extracción de datos de páginas web relacionadas con IA.
    """
    try:
        # Ejecuta el script para extraer información de las páginas web
        proceso = subprocess.Popen(
            ["python", "breadsoupautomatico.py"],  # Cambia el nombre si tu script tiene otro nombre
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = proceso.communicate()  # Esperar a que termine

        if proceso.returncode != 0:
            raise RuntimeError(f"Error al ejecutar el script: {stderr}")

        return jsonify({"mensaje": "Extracción web completada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": f"Error al ejecutar la extracción web: {e}"}), 500


@app.route('/obtener_datos_web', methods=['GET'])
def obtener_datos_web():
    """
    Devuelve los datos extraídos de las páginas web en formato JSON.
    """
    csv_path = './comentarios_IA.csv'  # Archivo generado por el script

    if not os.path.exists(csv_path):
        return jsonify({"error": "El archivo CSV de páginas web no existe"}), 404

    data = []
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return jsonify(data[:15]), 200
    except Exception as e:
        return jsonify({"error": f"Error al leer el archivo CSV: {e}"}), 500

    return jsonify(data), 200




@app.route('/obtener_datos_tiktok', methods=['GET'])
def obtener_datos_tiktok():
    """
    Lee el archivo CSV de TikTok y devuelve los datos en formato JSON.
    """
    csv_path = './uploads/tiktok_comments_preprocessed.csv'

    if not os.path.exists(csv_path):
        return jsonify({"error": "El archivo CSV de TikTok no existe"}), 404

    data = []
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
    except Exception as e:
        return jsonify({"error": f"Error al leer el archivo CSV: {e}"}), 500

    return jsonify(data), 200

@app.route('/recibir_archivos', methods=['POST'])
def recibir_archivos():
    """
    Recibe y guarda los archivos enviados desde el cliente.
    """
    try:
        # Verifica si se enviaron los archivos necesarios
        if 'csv' not in request.files or 'wordcloud' not in request.files:
            return jsonify({"error": "No se enviaron los archivos necesarios"}), 400

        # Procesar archivo CSV
        csv_file = request.files['csv']
        if csv_file.filename == '':
            return jsonify({"error": "El archivo CSV no tiene un nombre válido"}), 400
        csv_filename = secure_filename(csv_file.filename)
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
        csv_file.save(csv_path)

        # Procesar archivo de la nube de palabras
        wordcloud_file = request.files['wordcloud']
        if wordcloud_file.filename == '':
            return jsonify({"error": "El archivo de la nube de palabras no tiene un nombre válido"}), 400
        wordcloud_filename = secure_filename(wordcloud_file.filename)
        wordcloud_path = os.path.join(app.config['UPLOAD_FOLDER'], wordcloud_filename)
        wordcloud_file.save(wordcloud_path)

        return jsonify({
            "mensaje": "Archivos recibidos y guardados con éxito",
            "csv_path": csv_path,
            "wordcloud_path": wordcloud_path
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error al procesar los archivos: {e}"}), 500


@app.route('/uploads/youtube/<path:filename>', methods=['GET'])
def obtener_imagen_youtube(filename):
    """
    Devuelve la imagen almacenada en la carpeta de YouTube.
    """
    uploads_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'youtube')
    return send_from_directory(uploads_dir, filename)

@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_file(filename):
    """
    Sirve archivos estáticos de la carpeta 'uploads', como wordcloud.png.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def enviar_archivos_a_pagina_web():
    """
    Envía el CSV y la imagen de la nube de palabras generados a la página web.
    """
    url_pagina_web = "http://127.0.0.1:5000/recibir_archivos"  # Cambia esto al endpoint de tu página web
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], "youtube/youtube_comments_preprocessed.csv")
    wordcloud_path = os.path.join(app.config['UPLOAD_FOLDER'], "youtube/wordcloud.png")

    if not os.path.exists(csv_path) or not os.path.exists(wordcloud_path):
        print("⚠️ Los archivos generados no se encuentran en el servidor.")
        return

    try:
        with open(csv_path, 'rb') as csv_file, open(wordcloud_path, 'rb') as img_file:
            files = {
                'csv': csv_file,
                'wordcloud': img_file
            }
            response = requests.post(url_pagina_web, files=files)

            if response.status_code == 200:
                print("✅ Archivos enviados correctamente a la página web.")
            else:
                print(f"⚠️ Error al enviar los archivos: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ No se pudo enviar los archivos a la página web: {e}")

@app.route('/ping', methods=['GET'])
def ping():
    """
    Verifica que el servidor esté funcionando.
    """
    return jsonify({"mensaje": "Servidor funcionando"}), 200

if __name__ == "__main__":
    app.run(debug=True)
