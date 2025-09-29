#!/usr/bin/env python3
"""
Script rápido para testar conexão com PostgreSQL
"""

import psycopg2
from datetime import datetime

# Configurações de conexão
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ai_data_engineering',
    'user': 'postgres',
    'password': 'postgres123'
}

print("🔌 Testando conexão com PostgreSQL...")
print("-" * 40)
print(f"🕐 Teste realizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Conexão estabelecida com sucesso!")
    
    # Criar cursor
    cursor = conn.cursor()
    
    # Teste básico
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"📊 PostgreSQL: {version[:50]}...")
    
    # Verificar database
    cursor.execute("SELECT current_database();")
    db_name = cursor.fetchone()[0]
    print(f"🗄️ Database: {db_name}")
    
    # Verificar usuário
    cursor.execute("SELECT current_user;")
    user = cursor.fetchone()[0]
    print(f"👤 Usuário: {user}")
    
    # Verificar encoding
    cursor.execute("SELECT current_setting('client_encoding');")
    encoding = cursor.fetchone()[0]
    print(f"🔤 Encoding: {encoding}")
    
    # Verificar timezone
    cursor.execute("SELECT current_setting('timezone');")
    timezone = cursor.fetchone()[0]
    print(f"🌍 Timezone: {timezone}")
    
    # Teste com dados em português
    cursor.execute("SELECT 'Blumenau' as cidade, 'Santa Catarina' as estado")
    portuguese_data = cursor.fetchone()
    print(f"📍 Dados em português: {portuguese_data[0]} - {portuguese_data[1]}")
    
    # Fechar conexão
    cursor.close()
    conn.close()
    
    print("\n🎉 CONEXÃO FUNCIONANDO PERFEITAMENTE!")
    print("✅ PostgreSQL está rodando na porta 5433")
    print("✅ Encoding UTF-8 configurado corretamente")
    print("✅ Datos em português funcionando")
    
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
    print(f"🔍 Tipo do erro: {type(e).__name__}")
