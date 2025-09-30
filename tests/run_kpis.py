#!/usr/bin/env python3
"""
Script para executar as views de KPIs
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Configurações de conexão
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ai_data_engineering',
    'user': 'postgres',
    'password': 'postgres123',
    'client_encoding': 'utf8'
}

def execute_sql_file(file_path):
    """Executar arquivo SQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        cursor.execute(sql_content)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"Arquivo SQL executado com sucesso: {file_path}")
        return True
        
    except Exception as e:
        print(f"Erro ao executar {file_path}: {e}")
        return False

def test_kpi_views():
    """Testar as views de KPIs"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== TESTANDO VIEWS DE KPIs ===")
        
        # Lista de views para testar
        views_to_test = [
            'analytics.kpi_executive_dashboard',
            'analytics.kpi_annual_sales',
            'analytics.kpi_regional_performance',
            'analytics.kpi_model_performance',
            'analytics.kpi_top_10_models',
            'analytics.kpi_top_5_regions',
            'analytics.kpi_annual_growth'
        ]
        
        for view in views_to_test:
            try:
                print(f"\n--- Testando {view} ---")
                cursor.execute(f"SELECT * FROM {view} LIMIT 5")
                results = cursor.fetchall()
                
                if results:
                    print(f"OK {view}: {len(results)} registros encontrados")
                    print("Primeiros registros:")
                    for i, row in enumerate(results[:3]):
                        print(f"  {i+1}: {dict(row)}")
                else:
                    print(f"AVISO {view}: Nenhum registro encontrado")
                    
            except Exception as e:
                print(f"ERRO ao testar {view}: {e}")
        
        cursor.close()
        conn.close()
        
        print("\n=== TESTE CONCLUÍDO ===")
        
    except Exception as e:
        print(f"Erro na conexão: {e}")

def show_kpi_summary():
    """Mostrar resumo dos KPIs"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== RESUMO DOS KPIs ===")
        
        # Dashboard Executivo
        print("\n--- Dashboard Executivo ---")
        cursor.execute("SELECT * FROM analytics.kpi_executive_dashboard")
        dashboard = cursor.fetchall()
        
        for metric in dashboard:
            print(f"{metric['metric_name']}: {metric['metric_value']} {metric['metric_unit']}")
        
        # Top 5 Regiões
        print("\n--- Top 5 Regiões ---")
        cursor.execute("SELECT * FROM analytics.kpi_top_5_regions")
        regions = cursor.fetchall()
        
        for i, region in enumerate(regions, 1):
            print(f"{i}. {region['region']}: ${region['total_revenue']:,.0f} ({region['market_share_revenue_pct']}%)")
        
        # Top 5 Modelos
        print("\n--- Top 5 Modelos ---")
        cursor.execute("SELECT * FROM analytics.kpi_top_10_models LIMIT 5")
        models = cursor.fetchall()
        
        for i, model in enumerate(models, 1):
            print(f"{i}. {model['model']}: ${model['total_revenue']:,.0f} ({model['market_share_revenue_pct']}%)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao mostrar resumo: {e}")

def main():
    """Função principal"""
    print("Executando Views de KPIs")
    
    # 1. Executar arquivo SQL
    print("\n1. Executando arquivo SQL...")
    success = execute_sql_file('sql/kpis_views.sql')
    
    if success:
        # 2. Testar views
        print("\n2. Testando views...")
        test_kpi_views()
        
        # 3. Mostrar resumo
        print("\n3. Resumo dos KPIs...")
        show_kpi_summary()
        
        print("\nViews de KPIs criadas e testadas com sucesso!")
    else:
        print("\nFalha ao executar views de KPIs")

if __name__ == "__main__":
    main()
