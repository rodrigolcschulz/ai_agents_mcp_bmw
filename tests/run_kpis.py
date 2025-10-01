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
            'analytics.kpi_annual_growth',
            'analytics.kpi_price_analysis',
            'analytics.kpi_color_performance',
            'analytics.kpi_model_efficiency',
            'analytics.kpi_seasonal_analysis',
            'analytics.kpi_top_performers',
            'analytics.kpi_price_volume_correlation',
            'analytics.kpi_market_penetration',
            'analytics.kpi_temporal_trends'
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
        
        # Análise de Preços
        print("\n--- Análise de Preços por Segmento ---")
        cursor.execute("""
            SELECT price_segment, COUNT(*) as models_count, 
                   AVG(avg_price) as avg_price, SUM(total_units_sold) as total_units
            FROM analytics.kpi_price_analysis 
            GROUP BY price_segment 
            ORDER BY avg_price DESC
        """)
        price_segments = cursor.fetchall()
        
        for segment in price_segments:
            print(f"{segment['price_segment']}: {segment['models_count']} modelos, "
                  f"Preço médio: ${segment['avg_price']:,.0f}, "
                  f"Unidades: {segment['total_units']:,}")
        
        # Top Cores
        print("\n--- Top 5 Cores por Vendas ---")
        cursor.execute("SELECT * FROM analytics.kpi_color_performance LIMIT 5")
        colors = cursor.fetchall()
        
        for i, color in enumerate(colors, 1):
            print(f"{i}. {color['color']}: {color['total_units_sold']:,} unidades "
                  f"({color['market_share_units_pct']}%)")
        
        # Modelos Mais Eficientes
        print("\n--- Top 5 Modelos Mais Eficientes ---")
        cursor.execute("""
            SELECT model, revenue_per_unit, efficiency_rank, total_units_sold
            FROM analytics.kpi_model_efficiency 
            ORDER BY efficiency_rank 
            LIMIT 5
        """)
        efficient_models = cursor.fetchall()
        
        for i, model in enumerate(efficient_models, 1):
            print(f"{i}. {model['model']}: ${model['revenue_per_unit']:,.0f}/unidade "
                  f"(Rank: {model['efficiency_rank']}, Volume: {model['total_units_sold']:,})")
        
        # Market Penetration
        print("\n--- Penetração de Mercado por Região ---")
        cursor.execute("""
            SELECT region, model_penetration_pct, revenue_penetration_pct, 
                   models_available, fuel_types_available
            FROM analytics.kpi_market_penetration 
            ORDER BY revenue_penetration_pct DESC
        """)
        penetration = cursor.fetchall()
        
        for region in penetration:
            print(f"{region['region']}: {region['model_penetration_pct']}% modelos, "
                  f"{region['revenue_penetration_pct']}% receita, "
                  f"{region['models_available']} modelos, {region['fuel_types_available']} combustíveis")
        
        # Tendências Temporais
        print("\n--- Tendências dos Últimos 3 Anos ---")
        cursor.execute("""
            SELECT year, total_units_sold, total_revenue, units_growth_pct, revenue_growth_pct
            FROM analytics.kpi_temporal_trends 
            ORDER BY year DESC 
            LIMIT 3
        """)
        trends = cursor.fetchall()
        
        for trend in trends:
            growth_units = f"{trend['units_growth_pct']:+.1f}%" if trend['units_growth_pct'] else "N/A"
            growth_revenue = f"{trend['revenue_growth_pct']:+.1f}%" if trend['revenue_growth_pct'] else "N/A"
            print(f"{trend['year']}: {trend['total_units_sold']:,} unidades ({growth_units}), "
                  f"${trend['total_revenue']:,.0f} ({growth_revenue})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao mostrar resumo: {e}")

def show_advanced_insights():
    """Mostrar insights avançados e perguntas de negócio"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n=== INSIGHTS AVANÇADOS E PERGUNTAS DE NEGÓCIO ===")
        
        # 1. Qual modelo tem melhor relação preço-eficiência?
        print("\n--- 1. Modelos com Melhor Relação Preço-Eficiência ---")
        cursor.execute("""
            SELECT model, revenue_per_unit, price_per_liter, efficiency_rank
            FROM analytics.kpi_model_efficiency 
            WHERE efficiency_rank <= 3
            ORDER BY efficiency_rank
        """)
        efficiency = cursor.fetchall()
        
        for model in efficiency:
            print(f"• {model['model']}: ${model['revenue_per_unit']:,.0f}/unidade, "
                  f"${model['price_per_liter']:,.0f}/L, Rank: {model['efficiency_rank']}")
        
        # 2. Quais regiões têm maior potencial de crescimento?
        print("\n--- 2. Regiões com Maior Potencial de Crescimento ---")
        cursor.execute("""
            SELECT region, revenue_penetration_pct, model_penetration_pct,
                   (100 - revenue_penetration_pct) as growth_potential
            FROM analytics.kpi_market_penetration 
            ORDER BY growth_potential DESC
        """)
        growth_potential = cursor.fetchall()
        
        for region in growth_potential:
            print(f"• {region['region']}: {region['revenue_penetration_pct']}% penetração atual, "
                  f"Potencial: {region['growth_potential']:.1f}%")
        
        # 3. Qual cor é mais popular por região?
        print("\n--- 3. Cores Mais Populares por Região ---")
        cursor.execute("""
            SELECT region, color, total_units_sold, market_share_units_pct
            FROM (
                SELECT region, color, SUM(sales_volume) as total_units_sold,
                       ROUND((SUM(sales_volume) * 100.0 / SUM(SUM(sales_volume)) OVER (PARTITION BY region))::numeric, 2) as market_share_units_pct,
                       RANK() OVER (PARTITION BY region ORDER BY SUM(sales_volume) DESC) as rn
                FROM bmw_sales 
                WHERE color IS NOT NULL AND color != 'Unknown'
                GROUP BY region, color
            ) ranked
            WHERE rn = 1
            ORDER BY total_units_sold DESC
        """)
        popular_colors = cursor.fetchall()
        
        for color in popular_colors:
            print(f"• {color['region']}: {color['color']} ({color['market_share_units_pct']}% do mercado)")
        
        # 4. Análise de correlação preço-volume
        print("\n--- 4. Análise de Correlação Preço-Volume ---")
        cursor.execute("""
            SELECT price_volume_segment, COUNT(*) as combinations,
                   AVG(price_volume_correlation) as avg_correlation
            FROM analytics.kpi_price_volume_correlation 
            GROUP BY price_volume_segment
            ORDER BY avg_correlation DESC
        """)
        correlations = cursor.fetchall()
        
        for corr in correlations:
            print(f"• {corr['price_volume_segment']}: {corr['combinations']} combinações, "
                  f"Correlação média: {corr['avg_correlation']:.3f}")
        
        # 5. Top performers por múltiplas métricas
        print("\n--- 5. Top Performers por Múltiplas Métricas ---")
        cursor.execute("""
            SELECT model, overall_rank, composite_score, total_units, total_revenue, avg_price
            FROM analytics.kpi_top_performers 
            WHERE overall_rank <= 5
            ORDER BY overall_rank
        """)
        top_performers = cursor.fetchall()
        
        for performer in top_performers:
            print(f"• {performer['model']}: Rank {performer['overall_rank']}, "
                  f"Score: {performer['composite_score']}, "
                  f"${performer['total_revenue']:,.0f} receita, "
                  f"${performer['avg_price']:,.0f} preço médio")
        
        # 6. Tendências de crescimento por região
        print("\n--- 6. Tendências de Crescimento por Região (Últimos 3 Anos) ---")
        cursor.execute("""
            SELECT region, year, revenue_growth_pct, units_growth_pct
            FROM analytics.kpi_seasonal_analysis 
            WHERE year >= (SELECT MAX(year) - 2 FROM bmw_sales)
            ORDER BY region, year DESC
        """)
        regional_trends = cursor.fetchall()
        
        current_region = None
        for trend in regional_trends:
            if trend['region'] != current_region:
                print(f"\n• {trend['region']}:")
                current_region = trend['region']
            
            growth_revenue = f"{trend['revenue_growth_pct']:+.1f}%" if trend['revenue_growth_pct'] else "N/A"
            growth_units = f"{trend['units_growth_pct']:+.1f}%" if trend['units_growth_pct'] else "N/A"
            print(f"  {trend['year']}: Receita {growth_revenue}, Unidades {growth_units}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao mostrar insights avançados: {e}")

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
        
        # 4. Mostrar insights avançados
        print("\n4. Insights Avançados...")
        show_advanced_insights()
        
        print("\nViews de KPIs criadas e testadas com sucesso!")
    else:
        print("\nFalha ao executar views de KPIs")

if __name__ == "__main__":
    main()
