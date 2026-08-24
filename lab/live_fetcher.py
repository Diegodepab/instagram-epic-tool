import json
import zipfile
import time
import os
import random
import logging

try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired
    from dotenv import load_dotenv
except ImportError:
    print("Error: Faltan dependencias. Ejecuta: pip install instagrapi python-dotenv")
    exit(1)

# Configurar logging básico para la prueba de laboratorio
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

def create_export_zip(target_username, followers, following, filename):
    followers_data = {
        "relationships_followers": [
            {
                "string_list_data": [
                    {
                        "href": f"https://www.instagram.com/{user}",
                        "value": user,
                        "timestamp": int(time.time())
                    }
                ]
            }
            for user in followers
        ]
    }

    following_data = {
        "relationships_following": [
            {
                "string_list_data": [
                    {
                        "href": f"https://www.instagram.com/{user}",
                        "value": user,
                        "timestamp": int(time.time())
                    }
                ]
            }
            for user in following
        ]
    }

    with zipfile.ZipFile(filename, 'w') as zf:
        zf.writestr('followers_1.json', json.dumps(followers_data, indent=2))
        zf.writestr('following.json', json.dumps(following_data, indent=2))
        
    logger.info(f"Archivo generado con éxito: {filename}")

def safe_delay(min_seconds=3, max_seconds=7):
    """
    Introduce un retraso aleatorio para simular comportamiento humano
    y evitar ser detectado por los sistemas anti-bot de Instagram.
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"Esperando {delay:.2f} segundos por seguridad...")
    time.sleep(delay)

def fetch_and_generate_export(temp_username, temp_password, target_username, proxy_url=None):
    cl = Client()
    
    # [Mejor práctica de seguridad] Configurar Proxy si está disponible
    if proxy_url:
        logger.info("Configurando conexión a través del proxy...")
        try:
            cl.set_proxy(proxy_url)
        except Exception as e:
            logger.error(f"Error al configurar el proxy: {e}")
            return
    
    # [Mejor práctica de seguridad] 
    # Configurar retrasos internos en instagrapi
    cl.delay_range = [2, 5]
    
    # Intentar cargar sesión guardada para evitar logins constantes (más seguro)
    session_file = f"lab/{temp_username}_session.json"
    if os.path.exists(session_file):
        logger.info("Cargando sesión previamente guardada...")
        cl.load_settings(session_file)
    
    logger.info(f"Iniciando sesión con la cuenta temporal: {temp_username}...")
    try:
        # Iniciar sesión
        cl.login(temp_username, temp_password)
        cl.dump_settings(session_file) # Guardar sesión para el futuro
        logger.info("Sesión iniciada/verificada correctamente.")
    except Exception as e:
        logger.error(f"Error al iniciar sesión: {e}")
        return

    safe_delay(2, 4)

    logger.info(f"Obteniendo el ID de usuario para el objetivo: @{target_username}...")
    try:
        target_user_id = cl.user_id_from_username(target_username)
    except Exception as e:
        logger.error(f"No se pudo encontrar el usuario {target_username}: {e}")
        return

    safe_delay(3, 6)

    logger.info("Descargando lista de seguidores...")
    try:
        followers_dict = cl.user_followers(target_user_id)
        followers_list = [user.username for user in followers_dict.values()]
        logger.info(f"Se obtuvieron {len(followers_list)} seguidores.")
    except Exception as e:
        logger.error(f"Error al obtener seguidores: {e}")
        return

    safe_delay(5, 10) # Retraso mayor entre peticiones pesadas

    logger.info("Descargando lista de seguidos...")
    try:
        following_dict = cl.user_following(target_user_id)
        following_list = [user.username for user in following_dict.values()]
        logger.info(f"Se obtuvieron {len(following_list)} seguidos.")
    except Exception as e:
        logger.error(f"Error al obtener seguidos: {e}")
        return

    # Generar el ZIP
    filename = f"lab/{target_username}_live_export.zip"
    logger.info("Empaquetando datos en formato compatible con CircleScope...")
    create_export_zip(target_username, followers_list, following_list, filename)


if __name__ == "__main__":
    # Obtener credenciales de variables de entorno (.env)
    TEMP_ACCOUNT_USER = os.getenv("IG_TEMP_USERNAME")
    TEMP_ACCOUNT_PASS = os.getenv("IG_TEMP_PASSWORD")
    TARGET_ACCOUNT = os.getenv("IG_TARGET_ACCOUNT", "diegodepab")
    PROXY_URL = os.getenv("IG_PROXY") # Opcional: http://user:pass@ip:port
    
    if not TEMP_ACCOUNT_USER or not TEMP_ACCOUNT_PASS:
        logger.error("Credenciales no encontradas. Por favor, crea un archivo .env basándote en .env.example")
    else:
        fetch_and_generate_export(TEMP_ACCOUNT_USER, TEMP_ACCOUNT_PASS, TARGET_ACCOUNT, PROXY_URL)
