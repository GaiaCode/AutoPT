import paramiko
import time
import sys
import re

class InteractiveShell:
    def __init__(self, hostname='172.20.0.2', port=22, username='root', password='123456', timeout=30):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname, username=username, password=password, port=port)
        self.session = self.client.invoke_shell()
        self.timeout = timeout
        self.execute_command("pwd")

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
        if command.count('\n') > 0:
            command = command.splitlines()
            command = ''.join(command[1:-1])
        if 'nano ' in command:
            return "nano is not supported in this environment"
            command = "echo 'nano is not supported in this environment'"
        if 'searchsploit ' in command:
            return "searchsploit is not supported in this environment"
            command = "echo 'searchsploit is not supported in this environment'"
        if 'man ' in command:
            return "man is not supported in this environment"


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
            # command += " --poc ~/poc_info/pocs/*"

        self.session.send(command + '\n')
        print(f"--- [DEBUG] Comando inviato: {command.strip()} ---", file=sys.stderr)

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
                print("--- [DEBUG] Prompt trovato! Uscita dal loop. ---", file=sys.stderr)
                return self.omit(command, output)
            # read outputs
            if self.session.recv_ready():
                print("--- [DEBUG] Dati pronti da leggere... ---", file=sys.stderr)
                chunk = ""
                while self.session.recv_ready():
                    data_chunk = self.session.recv(1024).decode('utf-8','ignore')
                    chunk += data_chunk
                    output += data_chunk
                    print(f"--- [DEBUG] Letto un pezzo:\n---\n{chunk[:200]}...\n---", file=sys.stderr) # Stampiamo solo i primi 200 caratteri del pezzo
                    #output += self.session.recv(1024).decode('utf-8','ignore')
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

import re

def parse_vuln(text):
    vulns = []
    color_codes = r'\x1b\[([0-?]*[ -/]*[@-~])'
    raw_text = re.sub(color_codes, '', text)
    lines = raw_text.splitlines()
    # lines = text.splitlines()
    vuln_info = None
    for line in lines:
        if line.startswith('[Vuln: '):
            vuln_info = {}
            vuln_match = re.search(r'\[Vuln: (.*?)\]', line)
            if vuln_match:
                vuln_info['vuln'] = vuln_match.group(1)
        elif vuln_info:
            match = re.search(r'(\w+)\s+"(.*?)"', line)
            if match:
                vuln_info[match.group(1).lower()] = match.group(2)
            elif line.startswith('Payload'):
                match = re.search(r'Payload\s+"(.*?)"', line)
                if match:
                    vuln_info['payload'] = match.group(1)
            elif line.startswith('Links'):
                match = re.search(r'Links\s+\[(.*?)\]', line)
                if match:
                    links = match.group(1).split(', ')
                    vuln_info['links'] = [link.strip('"') for link in links]
            elif line.startswith('level'):
                match = re.search(r'level\s+"(.*?)"\s*', line)
                if match:
                    vuln_info['level'] = match.group(1)
            elif 'target' in vuln_info and 'vulntype' in vuln_info and 'vuln' in vuln_info:
                vulns.append(vuln_info)
                vuln_info = None
    return vulns

if __name__ == '__main__':
    # DEMO
    with InteractiveShell() as shell:
        print("="*60)
        print(shell.execute_command("pwd"))

        scan_res = shell.execute_command('xray ws --url 192.168.160.1:8081')
        print(scan_res)
        # color_codes = r'\x1b\[([0-?]*[ -/]*[@-~])'
        # scan_res = re.sub(color_codes, '', scan_res)
        vuln_dict = parse_vuln(scan_res)

        print(vuln_dict)
        result = [item for item in vuln_dict if 'level' in item]

        print(result)
