# agent/src/auto_cycle.py
import os
import glob
import time
import subprocess
from datetime import datetime

LOG_DIR = "logs"
PLANNER_PATH = "planner_prompt_psm.md"
BASE_URL = "http://juiceshop:3000/#/"
ITERATIONS = 3   #  Numero di cicli AutoPT da eseguire
SEED = 42

def get_latest_log():
    """Trova l'ultimo file JSONL generato nei log."""
    files = sorted(glob.glob(os.path.join(LOG_DIR, "run_*.jsonl")))
    return files[-1] if files else None

def run_agent():
    """Esegue un ciclo ReAct e ritorna il percorso del file di log generato."""
    print("\n[+] Avvio nuovo ciclo ReAct...")
    cmd = [
        "python", "react_agent.py",
        "--base-url", BASE_URL,
        "--seed", str(SEED)
    ]
    subprocess.run(cmd, check=False)
    latest = get_latest_log()
    if latest:
        print(f"[OK] Log generato: {latest}")
    else:
        print("[WARN] Nessun log trovato.")
    return latest

def run_optimizer(log_path):
    """Esegue il self-optimizer sul log specificato."""
    print(f"\n[+] Ottimizzazione AutoPT su {log_path}...")
    cmd = ["python", "self_optimizer.py", "--log", log_path]
    subprocess.run(cmd, check=False)

def backup_planner():
    """Salva una copia del planner attuale prima della modifica."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{PLANNER_PATH}.bak_{ts}"
    if os.path.exists(PLANNER_PATH):
        os.rename(PLANNER_PATH, backup_path)
        print(f"[+] Backup planner salvato → {backup_path}")

def main():
    print(f"[*] Avvio AutoPT auto-cycle | Base URL: {BASE_URL} | Iterazioni: {ITERATIONS}")
    os.makedirs(LOG_DIR, exist_ok=True)

    for i in range(1, ITERATIONS + 1):
        print(f"\n===  Iterazione {i}/{ITERATIONS} ===")
        backup_planner()
        log_path = run_agent()
        if not log_path:
            print("[!] Nessun log trovato, salto ottimizzazione.")
            continue
        run_optimizer(log_path)
        print("[✔] Iterazione completata, attesa 10s prima del prossimo ciclo...")
        time.sleep(10)

    print("\n Tutti i cicli AutoPT completati con successo.")

if __name__ == "__main__":
    main()
