# Base image con Python + Playwright
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Directory di lavoro
WORKDIR /app

# Copia il codice sorgente
COPY ./src /app

# Aggiorna pip e strumenti base
RUN pip install --upgrade pip setuptools wheel

# Installa solo le dipendenze necessarie per il mock agent
RUN pip install --no-cache-dir \
    playwright==1.55.0 \
    beautifulsoup4 \
    requests

# (Facoltativo) Se in futuro vorrai attivare OpenAI, abilita questa riga
# ARG ENABLE_OPENAI=false
# RUN if [ "$ENABLE_OPENAI" = "true" ]; then pip install openai; fi

# Installa i browser necessari a Playwright (Chromium in questo caso)
RUN playwright install --with-deps chromium

# Comando di default
CMD ["bash"]
