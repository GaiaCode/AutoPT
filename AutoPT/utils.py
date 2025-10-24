import re
import requests
from bs4 import BeautifulSoup
import functools
import time
from termcolor import colored
import yaml

# ---------------------------------------------------------------------
# Decoratore di retry con gestione degli errori di rete
# ---------------------------------------------------------------------
def retry(max_retries=3, retry_delay=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"[WARN] Eccezione: {e}")
                    if i < max_retries - 1:
                        print(f"[INFO] Riprovo tra {retry_delay} secondi...")
                        time.sleep(retry_delay)
                    else:
                        print("[ERROR] Tutti i tentativi falliti.")
                        raise
        return wrapper
    return decorator


# ---------------------------------------------------------------------
# Funzione sicura per scaricare e parsare HTML
# ---------------------------------------------------------------------
@retry(max_retries=3, retry_delay=2)
def cat_html(url: str) -> str:
    """Scarica e ritorna il testo da una pagina HTML in modo sicuro."""
    if not url or not isinstance(url, str):
        return "Invalid URL (empty or None)."

    # Rimuove eventuali virgolette e spazi
    url = re.sub(r'^["\']|["\']$', '', url.strip())

    # Gestisce segnaposto tipo {link_url} o placeholder da xray
    if "{" in url or "}" in url or "link_url" in url or url.strip().lower().startswith("placeholder"):
        return f"Placeholder URL ignorato: {url}"

    # Aggiunge schema se manca (assume http)
    if not re.match(r'^https?://', url):
        url = f"http://{url}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Errore nella richiesta HTTP: {e}"

    # Parse HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    body = soup.find("body")
    if not body:
        return "No body content found"

    text_content = body.get_text(separator="\n", strip=True)
    return text_content or "Empty body content"


# ---------------------------------------------------------------------
# Config Loader
# ---------------------------------------------------------------------
def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as config_stream:
        return yaml.safe_load(config_stream)


# ---------------------------------------------------------------------
# Logo AutoRT
# ---------------------------------------------------------------------
def print_AutoRT():
    ascii_art = r"""
     _              _             ____    _____ 
    / \     _   _  | |_    ___   |  _ \  |_   _|
   / _ \   | | | | | __|  / _ \  | |_) |   | |  
  / ___ \  | |_| | | |_  | (_) | |  __/    | |  
 /_/   \_\  \__,_|  \__|  \___/  |_|       |_|  
    """
    color = "red"
    for line in ascii_art.splitlines():
        print(colored(line, color))
