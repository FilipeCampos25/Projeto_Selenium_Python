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

# -------------------------------------------------------------------------
# (NOVO) Instala Google Chrome Stable
# -------------------------------------------------------------------------
RUN mkdir -p /etc/apt/keyrings && \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------------------
# (NOVO) Instala ChromeDriver compatível com a versão do Chrome (linux64)
# -------------------------------------------------------------------------
RUN set -eux; \
    CHROME_VERSION="$(google-chrome --version | awk '{print $3}')"; \
    CHROME_MAJOR="$(echo "$CHROME_VERSION" | cut -d. -f1)"; \
    echo "Chrome version: $CHROME_VERSION (major=$CHROME_MAJOR)"; \
    curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json" -o /tmp/cft.json; \
    python - <<'PY' \
import json,os,sys \
data=json.load(open("/tmp/cft.json","r")) \
major=os.environ.get("CHROME_MAJOR") \
m=data["milestones"].get(major) \
if not m: \
    print("No milestone found for major", major) \
    sys.exit(1) \
dl=[d for d in m["downloads"]["chromedriver"] if d["platform"]=="linux64"][0]["url"] \
print(dl) \
open("/tmp/chromedriver_url.txt","w").write(dl) \
PY; \
    CD_URL="$(cat /tmp/chromedriver_url.txt)"; \
    echo "ChromeDriver URL: $CD_URL"; \
    curl -fsSL "$CD_URL" -o /tmp/chromedriver.zip; \
    unzip /tmp/chromedriver.zip -d /tmp/cd; \
    install -m 0755 /tmp/cd/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
    rm -rf /tmp/chromedriver.zip /tmp/cd /tmp/cft.json /tmp/chromedriver_url.txt

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
    chmod 644 .env

USER appuser

EXPOSE 8000 5678

COPY docker-entrypoint.sh /docker-entrypoint.sh
USER root
RUN chmod +x /docker-entrypoint.sh
USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]
