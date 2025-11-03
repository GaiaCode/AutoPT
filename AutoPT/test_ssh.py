import paramiko
import logging
import sys
import time

# --- FASE 1: ATTIVAZIONE DEL DEBUGGING (come prima) ---
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
paramiko_log = logging.getLogger("paramiko")
paramiko_log.setLevel(logging.DEBUG)


# --- FASE 2: DEFINIZIONE DEI PARAMETRI (come prima) ---
HOSTNAME = '172.20.0.2'
PORT = 22
USERNAME = 'root'
PASSWORD = '123456'
PROMPT = 'root@kali-attacker' # Il prompt che ci aspettiamo


# --- FASE 3: TENTATIVO DI CONNESSIONE E INVOKE_SHELL ---
client = None
try:
    print("\n" + "="*50)
    print(f"[*] Tentativo di connessione a {HOSTNAME}:{PORT}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=HOSTNAME, port=PORT, username=USERNAME, password=PASSWORD, timeout=10)
    print("[+] SUCCESSO! Connessione stabilita.")

    print("\n[*] Tentativo di invocare una shell interattiva (invoke_shell)...")
    channel = client.invoke_shell()
    print("[+] SUCCESSO! Shell interattiva creata.")

    # --- FASE 4: LETTURA DEL BANNER INIZIALE ---
    # Leggiamo tutto quello che il server ci manda appena apriamo la shell
    # (messaggio di benvenuto, login, ecc.)
    print("\n[*] Lettura del banner di benvenuto...")
    
    # Attendiamo che ci siano dati da leggere
    time.sleep(2) # Diamo tempo al server di inviare tutto
    
    if channel.recv_ready():
        initial_banner = channel.recv(4096).decode('utf-8', 'ignore')
        print("\n--- BANNER RICEVUTO ---")
        print(initial_banner)
        print("-----------------------")
        
        if PROMPT in initial_banner:
            print("[+] Il prompt è stato trovato nel banner iniziale.")
        else:
            print("[-] ATTENZIONE: Il prompt NON è stato trovato nel banner iniziale.")
            print(f"    Sto cercando '{PROMPT}'")
    else:
        print("[-] ATTENZIONE: Nessun dato ricevuto dopo invoke_shell.")

    # --- FASE 5: ESECUZIONE DI UN COMANDO ---
    print("\n[*] Invio del comando 'pwd'...")
    channel.send('pwd\n')

    print("[*] Lettura dell'output del comando 'pwd'...")
    time.sleep(2) # Diamo tempo al server di rispondere

    if channel.recv_ready():
        command_output = channel.recv(4096).decode('utf-8', 'ignore')
        print("\n--- OUTPUT DEL COMANDO RICEVUTO ---")
        print(command_output)
        print("---------------------------------")
        
        if PROMPT in command_output:
            print("[+] Il prompt è stato trovato nell'output del comando.")
        else:
            print("[-] ATTENZIONE: Il prompt NON è stato trovato nell'output del comando.")

    else:
        print("[-] ATTENZIONE: Nessun dato ricevuto dopo aver inviato il comando.")

        
except Exception as e:
    print(f"\n[-] FALLIMENTO! Errore: {type(e).__name__}: {e}")
    
finally:
    # --- FASE 6: CHIUSURA ---
    if client:
        client.close()
        print("\n[*] Connessione chiusa.")
    print("="*50 + "\n")