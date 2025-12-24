# projetoSeleniumPython/Dockerfile
FROM python:3.11

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONIOENCODING=UTF-8

# ---- pacotes do sistema necessários ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    ca-certificates \
    wget \
    curl \
    gnupg \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia requirements primeiro para aproveitar cache
COPY requirements.txt /app/requirements.txt

# Instala dependências Python (incluindo debugpy)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir debugpy==1.8.0

# Copia toda a aplicação
COPY . /app

# Ajusta permissões corretas para que appuser possa ler tudo
RUN useradd -ms /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod 644 backend/.env

USER appuser

# Expõe porta da aplicação e porta do debugger
EXPOSE 8000 5678

# Script de entrada para modo debug ou normal
COPY docker-entrypoint.sh /docker-entrypoint.sh
USER root
RUN chmod +x /docker-entrypoint.sh
USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]