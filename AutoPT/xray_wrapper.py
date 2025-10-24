#!/usr/bin/env python3
import subprocess
import os
import sys
import time
from termcolor import colored
from utils import extract_xray_links

XRAY_BIN = "/usr/local/bin/xray"
XRAY_OUTPUT = "/tmp/xray_run.txt"


def run_xray_scan(target_url: str):
    """
    Esegue una scansione con Xray sul target specificato.
    Produce il file /tmp/xray_run.txt in formato JSON.
    """
    print(colored(f"[INFO] Avvio scansione Xray su: {target_url}", "cyan"))

    # Cancella eventuali residui precedenti
    if os.path.exists(XRAY_OUTPUT):
        try:
            os.remove(XRAY_OUTPUT)
            print(f"[DEBUG] Rimosso file precedente: {XRAY_OUTPUT}")
        except Exception as e:
            print(colored(f"[WARN] Impossibile rimuovere {XRAY_OUTPUT}: {e}", "yellow"))

    # Comando Xray corretto
    cmd = [
        XRAY_BIN,
        "webscan",
        "--url", target_url,
        "--json-output", XRAY_OUTPUT
    ]

    print(colored("[CMD] ", "blue") + " ".join(cmd))

    try:
        subprocess.run(cmd, check=True, timeout=600)
    except FileNotFoundError:
        print(colored("[ERROR] xray non trovato nel PATH. Installa o modifica XRAY_BIN.", "red"))
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(colored("[ERROR] Timeout durante la scansione Xray.", "red"))
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(colored(f"[ERROR] Xray ha restituito errore: {e}", "red"))
        sys.exit(1)

    # Controlla il file di output
    if not os.path.exists(XRAY_OUTPUT):
        print(colored(f"[ERROR] File di output {XRAY_OUTPUT} non trovato!", "red"))
        sys.exit(2)

    if os.path.getsize(XRAY_OUTPUT) == 0:
        print(colored(f"[ERROR] File di output {XRAY_OUTPUT} vuoto!", "red"))
        sys.exit(2)

    print(colored(f"[OK] Scansione completata. Risultati salvati in {XRAY_OUTPUT}", "green"))

    # Estrai link per verifica
    links = extract_xray_links(XRAY_OUTPUT)
    print(colored(f"[INFO] Trovati {len(links)} link totali.", "cyan"))
    for i, l in enumerate(links[:10], 1):
        print(f"  {i}. {l}")

    if links:
        os.environ["XRAY_LINK"] = links[0]
        print(colored(f"[INFO] Primo link salvato in variabile XRAY_LINK -> {links[0]}", "magenta"))
    else:
        print(colored("[WARN] Nessun link trovato nel risultato di Xray.", "yellow"))

    return links


if __name__ == "__main__":
    # Uso diretto da terminale
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <target_url>")
        print("Esempio: ./xray_wrapper.py http://127.0.0.1:8080")
        sys.exit(1)

    target = sys.argv[1]
    start = time.time()
    run_xray_scan(target)
    elapsed = time.time() - start
    print(colored(f"[INFO] Durata scansione: {elapsed:.1f}s", "cyan"))
