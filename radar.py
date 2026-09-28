import os
import threading
import time
import requests
from flask import Flask

# --- CONFIGURACIONES ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1516983367386533990/2T4iF4jJyxpVI0GP7sPlhTr7GevUpTX_GpF1ICbwWx-ZC-N6WXR8oA3CkI2w3TCXkj-Z"
API_URL = "https://agendadora-endpoint.parqueestadionacional.cl/api/unified-apis/enclosures/EncEventsStoken/1/20?xruta=parqueestadionacional&tipoProgramacion=entrenamiento"

HEADERS = {
    'accept': '*/*',
    'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
    'content-type': 'application/json',
    'origin': 'https://entrenamientos.parqueestadionacional.cl',
    'referer': 'https://entrenamientos.parqueestadionacional.cl/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36'
}

QUINCE_MINUTOS = 15 * 60
SEIS_DIAS = 6 * 24 * 60 * 60

# --- SERVIDOR WEB PARA MANTENER ACTIVA LA INSTANCIA ---
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Radar de canchas funcionando 24/7!", 200

def mantener_vivo():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- LÓGICA DEL RADAR ---
def enviar_discord(cancha_nombre):
    data = {
        "content": f"@DONATELO canchas disponibles! 🟢\n*(Detectada disponibilidad en: {cancha_nombre})*",
        "username": "Radar de Canchas"
    }
    try:
        # timeout=15 evita bloqueos si Discord demora en responder
        requests.post(WEBHOOK_URL, json=data, timeout=15)
        print(f"[{time.strftime('%H:%M:%S')}] ¡Notificación enviada a Discord!")
    except Exception as e:
        print(f"Error enviando a Discord: {e}")

def monitorear_canchas():
    print("Iniciando Radar de Canchas en segundo plano...")
    while True:
        try:
            # timeout=15 para evitar que el script se quede colgado si la API no responde
            response = requests.get(API_URL, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                datos = response.json()
                canchas = datos.get('recordsNew', [])
                encontrada_disponibilidad = False
                cancha_detectada = ""

                for cancha in canchas:
                    nombre = cancha.get('nombre', 'Cancha')
                    esta_disponible = cancha.get('disponible', False)
                    
                    if esta_disponible:
                        encontrada_disponibilidad = True
                        cancha_detectada = nombre
                        break

                if encontrada_disponibilidad:
                    enviar_discord(cancha_detectada)
                    print(f"[{time.strftime('%H:%M:%S')}] Cancha libre. Pausa de 6 días...")
                    time.sleep(SEIS_DIAS)
                    continue

                print(f"[{time.strftime('%H:%M:%S')}] Escaneo completado. Todo agotado.")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Error en la API ({response.status_code}).")
                
        except requests.exceptions.RequestException as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error de red en el escaneo: {e}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error imprevisto: {e}")

        time.sleep(QUINCE_MINUTOS)

if __name__ == "__main__":
    # daemon=True garantiza que el hilo se gestione adecuadamente con el proceso principal
    hilo_radar = threading.Thread(target=monitorear_canchas, daemon=True)
    hilo_radar.start()
    
    mantener_vivo()