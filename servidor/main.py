import subprocess
import os
import requests
import sys
from concurrent.futures import ThreadPoolExecutor  # Para hilos (o usa ProcessPoolExecutor para procesos)

sys.stdout.reconfigure(encoding='utf-8')
def enviar_csv_al_servidor(filepath):
    """Envía un archivo CSV al servidor."""
    if not os.path.exists(filepath):
        print(f"Error: El archivo {filepath} no existe.")
        return

    url = "http://127.0.0.1:5000/subir_csv"
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

def ejecutar_script(script_name, csv_filename):
    """Ejecuta un script en un subproceso y envía su CSV generado al servidor."""
    try:
        if not os.path.exists(script_name):
            print(f"⚠️ Error: El archivo {script_name} no existe.")
            return

        proceso = subprocess.Popen(
            ["python", script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        while True:
            salida = proceso.stdout.readline()
            error = proceso.stderr.readline()

            if salida:
                print(salida.strip())

            if error:
                print(f"⚠️ Error en {script_name}: {error.strip()}", flush=True)

            if salida == "" and error == "" and proceso.poll() is not None:
                break

        proceso.wait()
        print(f"✅ El script {script_name} finalizó con código: {proceso.returncode}")

        if proceso.returncode == 0:
            csv_filepath = os.path.join("./uploads", csv_filename)
            enviar_csv_al_servidor(csv_filepath)
        else:
            print(f"⚠️ El script {script_name} terminó con errores.")

    except subprocess.TimeoutExpired:
        proceso.kill()
        print(f"⚠️ El script {script_name} tardó demasiado y fue terminado.")
    except Exception as e:
        print(f"⚠️ Error al ejecutar {script_name}: {e}")
    finally:
        if proceso.stdout:
            proceso.stdout.close()
        if proceso.stderr:
            proceso.stderr.close()

if __name__ == "__main__":
    print("🔄 Iniciando extracción de comentarios...")

    scripts_info = [
        {"script": "tiktok.py", "csv": "tiktok_comments_preprocessed.csv"},
        {"script": "youtube.py", "csv": "youtube_comments_preprocessed.csv"},
        {"script": "breadsoupautomatico.py", "csv": "comentarios_IA.csv"}  # Script de páginas web
    ]

    # Ejecutar scripts en paralelo usando ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(scripts_info)) as executor:
        futures = []
        for info in scripts_info:
            print(f"🔄 Encolando {info['script']} para ejecución...")
            futures.append(executor.submit(ejecutar_script, info["script"], info["csv"]))

        # Esperar a que todos los scripts terminen
        for future in futures:
            future.result()

    print("✅ Todos los procesos han finalizado. Archivos enviados al servidor.")
