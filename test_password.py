#!/usr/bin/env python3
"""
Teste simples para verificar senha do PostgreSQL
"""

import psycopg2

# Testar diferentes senhas
passwords = ["postgres123", "postgres", "password", ""]

for pwd in passwords:
    print(f"\n🔑 Testando senha: '{pwd}'...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            database='ai_data_engineering',
            user='postgres',
            password=pwd
        )
        print(f"✅ SUCCESS! Senha correta é: '{pwd}'")
        conn.close()
        break
    except Exception as e:
        print(f"❌ Erro: {e}")

print("\n🔍 Se nenhuma senha funcionou, pode ser que a variável POSTGRES_PASSWORD esteja definida diferente.")
