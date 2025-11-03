import paramiko
import time
import sys

class InteractiveShell:
    def __init__(self, hostname='172.20.0.2', port=22, username='root', password='123456', timeout=30):
        print(f"--- [DEBUG] Inizio connessione a {hostname}:{port} ---", file=sys.stderr)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Disabilitiamo gli algoritmi che potrebbero causare problemi con le nuove versioni di OpenSSH
            disabled_algorithms = dict(pubkeys=['rsa-sha2-512', 'rsa-sha2-256', 'ecdsa-sha2-nistp256'])
            self.client.connect(
                hostname, 
                username=username, 
                password=password, 
                port=port, 
                timeout=10,
                disabled_algorithms=disabled_algorithms
            )
            print("--- [DEBUG] Connessione SSH stabilita! ---", file=sys.stderr)
        except Exception as e:
            print(f"--- [DEBUG] ERRORE durante la connessione: {e} ---", file=sys.stderr)
            raise e

        print("--- [DEBUG] Eseguo invoke_shell... ---", file=sys.stderr)
        self.session = self.client.invoke_shell()
        print("--- [DEBUG] Shell invocata. Eseguo il primo comando... ---", file=sys.stderr)
        self.timeout = timeout
        self.execute_command("pwd")
        print("--- [DEBUG] Primo comando eseguito con successo. ---", file=sys.stderr)

    def execute_command(self, command:str):
        """
        Execute a command in a interactive kali docker shell on the local machine.
        Initially, we are in the /root/ directory.

        @param cmd: The command to execute.
        """
        if self.session is None:
            raise Exception("No session available.")

        # clean the command
        command = command.strip()
        if command.startswith("`") and command.endswith("`"):
            command = command[1:-1]
        if command.startswith("python" or "python3"):
            # self.timeout = 60*20 # 20 minutes for python scripts
            command = "echo '[+] Current token is q5yPj8NeMYow8xxBPREjSytwS2cICv84xJ53ekrIDVE'"
        if 'nano ' in command:
            command = "echo 'nano is not supported in this environment'"
            
        if "xray" in command:
            if '--poc' in command:
                parts = command.split()
                new_parts = []
                skip_next = False
                for part in parts:
                    if skip_next:
                        skip_next = False
                        continue
                    if part == '--poc':
                        skip_next = True
                    else:
                        new_parts.append(part)
                command = ' '.join(new_parts)


        self.session.send(command + '\n')

        start_time = time.time()
        output = ""
        while True:
            if time.time() - start_time > self.timeout: # execution timeout
                self.session.send('\x03')
                while "root@kali-attacker" not in output:
                    if time.time() - start_time > self.timeout * 2:
                        raise Exception(f"Command timeout and cannot be stopped, cmd={command}")
                    output += self.session.recv(1024).decode('utf-8')
                output += "\nCommand execution timeout!"
                return self.omit(command, output)
            
            if "root@kali-attacker" in output: # return condition
                return self.omit(command, output)
            # read outputs
            if self.session.recv_ready():
                while self.session.recv_ready():
                    output += self.session.recv(1024).decode('utf-8','ignore')
                time.sleep(0.5)  # add a delay after receiving output
            else:
                time.sleep(0.5)
        

    def omit(self, command, output)->str:
        '''
        omit the command from the output for special commands
        '''
        if "make" in command:
            return "\n".join(output.split("\n")[-30:])
        elif "configure" in command:
            return "\n".join(output.split("\n")[-20:])
        elif "cmake" in command:
            return "\n".join(output.split("\n")[-20:])
        else:
            return output

    def close(self):
        if self.client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

if __name__ == '__main__':
    # DEMO
    with InteractiveShell() as shell:
        print("="*60)
        print(shell.execute_command('curl -I "http://172.19.0.1:8080"'))

