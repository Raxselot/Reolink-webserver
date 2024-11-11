import os
import requests
import time
import threading
import logging
from datetime import datetime
from flask import Flask, send_file, jsonify
from dotenv import load_dotenv
import urllib3
from PIL import Image
 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
 
load_dotenv()
 
CAMERA_IP = os.getenv('CAMERA_IP')
USERNAME =  '' # Username kann nicht in os.getenv gehohlt werden kp wieso
PASSWORD = os.getenv('PASSWORD')
SAVE_DIR = os.getenv('SAVE_DIR', './images')
PORT = int(os.getenv('PORT', 8000))  
TIMETOLOAD = int(os.getenv('TIMETOLOAD', 5000))
 
CROP_LEFT = int(os.getenv('CROP_LEFT', 0))
CROP_RIGHT = int(os.getenv('CROP_RIGHT', 0))
CROP_TOP = int(os.getenv('CROP_TOP', 0))
CROP_BOTTOM = int(os.getenv('CROP_BOTTOM', 0))
 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
 
logging.info("Geladene Konfigurationen:")
logging.info(f"CAMERA_IP: {CAMERA_IP}")
logging.info(f"USERNAME: {USERNAME}")
logging.info(f"SAVE_DIR: {SAVE_DIR}")
logging.info(f"PORT: {PORT}")
logging.info(f"TIMETOLOAD: {TIMETOLOAD} ms")
logging.info(f"CROP_LEFT: {CROP_LEFT}")
logging.info(f"CROP_RIGHT: {CROP_RIGHT}")
logging.info(f"CROP_TOP: {CROP_TOP}")
logging.info(f"CROP_BOTTOM: {CROP_BOTTOM}")
 
os.makedirs(SAVE_DIR, exist_ok=True)
 
app = Flask(__name__)
 
class CameraClient:
    """Client zur Kommunikation mit der Kamera."""
   
    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.session.verify = False  # Ist Unsicher gibt aber keinen anderne Weg sich zu Verifizieren!
        self.session.timeout = 5
 
    def login(self) -> bool:
        """Anmeldung per Token"""
        logging.info(f"Versuch, bei der Kamera {self.ip} anzumelden.")
        url = f'https://{self.ip}/api.cgi?cmd=Login'
 
        payload = [
            {
                "cmd": "Login",
                "param": {
                    "User": {
                        "Version": "0",
                        "userName": self.username,
                        "password": self.password
                    }
                }
            }
        ]
       
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            response_data = response.json()
           
            if response_data[0]["code"] == 0:
                self.token = response_data[0]["value"]["Token"]["name"]
                logging.info("Login erfolgreich. Token erhalten.")
                return True
           
            else:
                logging.error(f"Fehler beim Login: Code {response_data[0]['code']}")
                self.token = None
                return False
               
        except requests.exceptions.RequestException as e:
            logging.error(f"Login fehlgeschlagen: {e}")
            self.token = None
            return False
 
    def get_image(self) -> str:
        """Aktuelles Bild Hohlen/Speichern"""
       
        if not self.token:
            logging.info("Kein gültiger Token. Versuche einzuloggen...")
           
            if not self.login():
                logging.error("Login fehlgeschlagen.Bildaufruf übersprungen.")
                return ""
       
        url = f'https://{self.ip}/cgi-bin/api.cgi?cmd=Snap&channel=0&token={self.token}'
       
        try:
            response = self.session.get(url, stream=True)
           
            if response.status_code == 200:
                filename = os.path.join(SAVE_DIR, 'latest.jpg')
               
                with open(filename, 'wb') as f:
                   
                    for chunk in response.iter_content(4096):
                        f.write(chunk)
                       
                logging.info(f"Bild gespeichert: {filename}")
                self.crop_image(filename)
               
                return filename
           
            elif response.status_code == 401:
                logging.warning("Token abgelaufen. Neuer Login benötigt.")
               
                if self.login():
                    return self.get_image()
               
            else:
                logging.error(f"Unerwarteter Code (Bild Abruf) : {response.status_code}")
               
        except requests.exceptions.RequestException as e:
            logging.error(f"Fehler beim Abruf des Bilds {e}")
           
            if self.login():
                return self.get_image()
           
        return ""
 
    def crop_image(self, filepath: str) -> None:
        """ZUschneiden Des Bildes."""
       
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                left = CROP_LEFT
                top = CROP_TOP
                right = width - CROP_RIGHT
                bottom = height - CROP_BOTTOM
 
                if any([
                    left < 0, top < 0,
                    right > width, bottom > height,
                    left >= right, top >= bottom
                ]):
                    logging.warning("Bitte Crop Werte überprüfen, Bild kann nicht zu geschnitten werden")
                    return
 
                cropped_img = img.crop((left, top, right, bottom))
                cropped_img.save(filepath)
                logging.info(f"Bild zugeschnitten: {filepath} (Links: {left}, Oben: {top}, Rechts: {right}, Unten: {bottom})")
               
        except Exception as e:
            logging.error(f"Fehler beim Zuschneiden des Bildes: {e}")
 
def capture_images(client: CameraClient, interval: int = 5) -> None:
    """Hohlt alle X Sec ein Bild """
   
    while True:
        try:
            client.get_image()
            time.sleep(interval)
           
        except Exception as e:
            logging.error(f"Ein Fehler ist aufgetreten: {e}")
            logging.info("Warte 10 Sekunden bis neugestartet wird")
            time.sleep(10)
 
@app.route('/')
def index():
    """Hauptseite mit Bild Erstellen"""
    return f'''
    <html>
    <head>
    <title>Schießstand</title>
    <script>
        function reloadImage() {{
            const img = document.getElementById("cameraImage");
            img.src = "/latest?" + new Date().getTime();
        }}
        setInterval(reloadImage, {TIMETOLOAD});
    </script>
    </head>
    <body>
    <img src="/latest" id="cameraImage" alt="Kamera Bild" width="1920" height="1080">
    </body>
    </html>
    '''
 
@app.route('/latest')
def latest_image():
    """neustes Kamera bild hohlen"""
   
    filepath = os.path.join(SAVE_DIR, 'latest.jpg')
   
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/jpeg')
   
    else:
        return jsonify({"error": "Bild nicht verfügbar"}), 404
 
def start_flask():
    """Flask Webserver starten."""
    app.run(host='0.0.0.0', port=PORT)
 
def main():
    """Start des Programms"""
    camera_client = CameraClient(CAMERA_IP, USERNAME, PASSWORD)
   
    if not camera_client.login():
        logging.error("Initialer Login fehlgeschlagen. Beende Programm.")
        return
   
    capture_thread = threading.Thread(target=capture_images, args=(camera_client,), daemon=True)
    capture_thread.start()
    logging.info("Bildaufnahme-Thread gestartet.")
    start_flask()
 
if __name__ == "__main__":
    main()
