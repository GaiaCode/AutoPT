# Usiamo un'immagine ufficiale di Kali Linux come base
FROM kalilinux/kali-rolling

# Evitiamo domande interattive durante l'installazione
ENV DEBIAN_FRONTEND=noninteractive

# Aggiorniamo il sistema e installiamo SSH e gli strumenti base
#RUN apt-get update && apt-get install -y openssh-server sudo curl unzip libpcap-dev python3-pip
# Installiamo tutto quello che serve PRIMA DI PERDERE l'accesso a internet
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    curl \
    wget \
    unzip \
    libpcap-dev \
    python3 \
    python3-pip \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    python3-requests \
    iputils-ping \
    iproute2 \
    net-tools \
    dnsutils \
    && apt-get clean

# Impostiamo la password per l'utente root (quella che il codice si aspetta)
RUN echo 'root:123456' | chpasswd

# Configuriamo il server SSH per permettere il login di root
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Scarichiamo e installiamo lo scanner XRay (che abbiamo visto nel codice)

# --- INSTALLAZIONE CORRETTA DI XRAY ---
# 1. Imposta la cartella di lavoro a /root. 
#    Tutti i comandi successivi verranno eseguiti da qui.
WORKDIR /root

# 2. Scarica e decomprimi. Tutti i file verranno estratti in /root.
RUN curl -L https://github.com/chaitin/xray/releases/download/1.9.11/xray_linux_amd64.zip -o xray.zip && \
    unzip xray.zip && \
    rm xray.zip

# 3. Rinomina l'eseguibile per comodità (da xray_linux_amd64 a xray)
RUN mv xray_linux_amd64 xray

# 4. Rendi l'eseguibile eseguibile da chiunque.
RUN chmod +x xray

# 5. ESEGUI xray UNA VOLTA per forzare la generazione dei file .yml in /root.
RUN ./xray version

# 3. CREA MANUALMENTE un file config.yaml già configurato per ignorare i certificati SSL.
#    Usiamo 'echo -e' per scrivere più righe nel file.
RUN echo -e "version: 2\nhttp:\n  insecure: true" > /root/config.yaml

# 4. Rendi l'eseguibile utilizzabile da qualsiasi punto del sistema
#    creando un collegamento simbolico in /usr/local/bin che punta al file in /root.
RUN ln -s /root/xray /usr/local/bin/xray

# Aggiungiamo configurazioni di crittografia compatibili con Paramiko
RUN echo "KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1" >> /etc/ssh/sshd_config
RUN echo "Ciphers +aes128-cbc,3des-cbc" >> /etc/ssh/sshd_config

# Esponiamo la porta 22 (per SSH)
EXPOSE 22

# Comando per avviare il server SSH quando il container parte
CMD ["/usr/sbin/sshd", "-D"]
