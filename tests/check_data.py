#!/usr/bin/env python3
"""
Script para verificar dados específicos das tabelas
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Configurações de conexão
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ai_data_engineering',
    'user': 'postgres',
    'password': 'postgres123',
    'client_encoding': 'utf8'
}

def check_data():
    """Verificar dados específicos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== DADOS DAS TABELAS ===")
        
        # Verificar bmw_sales
        print("\n--- BMW SALES ---")
        cursor.execute("SELECT COUNT(*) as total FROM bmw_sales")
        total = cursor.fetchone()['total']
        print(f"Total de registros: {total}")
        
        # Estatísticas por região
        cursor.execute("""
            SELECT region, COUNT(*) as count, 
                   AVG(sales_units) as avg_sales,
                   SUM(total_sales) as total_revenue
            FROM bmw_sales 
            GROUP BY region 
            ORDER BY total_revenue DESC
        """)
        
        regions = cursor.fetchall()
        print("\nVendas por região:")
        for region in regions:
            print(f"  {region['region']}: {region['count']} registros, "
                  f"Média vendas: {region['avg_sales']:.0f}, "
                  f"Receita total: ${region['total_revenue']:,.2f}")
        
        # Estatísticas por modelo
        cursor.execute("""
            SELECT model, COUNT(*) as count,
                   AVG(sales_units) as avg_sales
            FROM bmw_sales 
            GROUP BY model 
            ORDER BY avg_sales DESC
            LIMIT 5
        """)
        
        models = cursor.fetchall()
        print("\nTop 5 modelos por vendas médias:")
        for model in models:
            print(f"  {model['model']}: {model['count']} registros, "
                  f"Média vendas: {model['avg_sales']:.0f}")
        
        # Verificar data_sources
        print("\n--- DATA SOURCES ---")
        cursor.execute("SELECT * FROM data_sources")
        sources = cursor.fetchall()
        for source in sources:
            print(f"  {source['name']}: {source['record_count']} registros, "
                  f"Tipo: {source['source_type']}")
        
        cursor.close()
        conn.close()
        
        print("\n=== VERIFICAÇÃO CONCLUÍDA ===")
        
    except Exception as e:
        print(f"Erro na verificação: {e}")

if __name__ == "__main__":
    check_data()
