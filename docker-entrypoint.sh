#!/bin/bash
set -e

# Ativa debugpy quando DEBUG_MODE=true
if [ "$DEBUG_MODE" = "true" ]; then
    echo "Iniciando em modo DEBUG (debugpy na porta 5678)"

    WAIT_FLAG=()
    if [ "$DEBUG_WAIT_FOR_CLIENT" = "true" ]; then
        echo "Aguardando conexão do debugger..."
        WAIT_FLAG=(--wait-for-client)
    fi

    exec python -Xfrozen_modules=off -m debugpy \
        --listen 0.0.0.0:5678 \
        "${WAIT_FLAG[@]}" \
        -m uvicorn \
        backend.app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload

else
    echo "Iniciando em modo NORMAL"
    exec uvicorn \
        backend.app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1
fi
