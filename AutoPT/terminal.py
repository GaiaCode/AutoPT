import subprocess, time
try:
    import paramiko
    HAS_PARAMIKO = True
except Exception:
    HAS_PARAMIKO = False

class InteractiveShell:
    def __init__(self, hostname=None, port=22, username='root', password=None, timeout=30):
        self.timeout = timeout
        self.hostname = hostname
        self.ssh_mode = False
        self.session = None
        self.client = None

        if hostname and HAS_PARAMIKO:
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(hostname, username=username, password=password, port=port, timeout=10)
                self.session = self.client.invoke_shell()
                self.ssh_mode = True
                self.execute_command("pwd")
                return
            except Exception:
                self.ssh_mode = False

    def execute_command(self, command: str):
        command = command.strip()
        if command.startswith("`") and command.endswith("`"):
            command = command[1:-1]
        if 'nano ' in command:
            return "nano is not supported in this environment"
        if 'searchsploit ' in command:
            return "searchsploit is not supported in this environment"

        if "xray" in command and '--poc' in command:
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

        if self.ssh_mode and self.session:
            self.session.send(command + '\n')
            start_time = time.time()
            output = ""
            while True:
                if time.time() - start_time > self.timeout:
                    try:
                        self.session.send('\x03')
                    except Exception:
                        pass
                    return "[TIMEOUT]"
                if self.session.recv_ready():
                    while self.session.recv_ready():
                        output += self.session.recv(4096).decode('utf-8','ignore')
                    time.sleep(0.2)
                    if output.strip():
                        return output.strip()
                else:
                    time.sleep(0.2)
        else:
            try:
                proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=self.timeout)
                return (proc.stdout + proc.stderr).strip()
            except subprocess.TimeoutExpired:
                return "[TIMEOUT]"
            except Exception as e:
                return f"[ERROR executing command: {e}]"

    def close(self):
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
