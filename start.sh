#!/bin/bash
# Şifreyi değiştirmek için:
# export ADMIN_PASSWORD="yenisifre"
# export PORT=5000

export ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
export SECRET_KEY="${SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"
export PORT="${PORT:-5000}"

echo "Admin panel başlatılıyor: http://0.0.0.0:$PORT"
echo "Şifre: $ADMIN_PASSWORD"

python3 app.py
