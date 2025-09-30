"""
MCP Agent - Versão Simplificada para Consultas em Linguagem Natural
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import re
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPAgent:
    def __init__(self):
        """Initialize MCP Agent"""
        # Database configuration
        self.DB_CONFIG = {
            'host': 'localhost',
            'port': 5433,
            'database': 'ai_data_engineering',
            'user': 'postgres',
            'password': 'postgres123',
            'client_encoding': 'utf8'
        }
        
        # Query patterns for natural language processing
        self.query_patterns = {
            # Dashboard queries
            'dashboard': r'(dashboard|resumo|overview|visão geral)',
            'total_sales': r'(total de vendas|total sales|vendas totais)',
            'total_revenue': r'(receita total|total revenue|faturamento)',
            
            # Regional queries
            'top_regions': r'(top regiões|melhores regiões|regiões com mais vendas)',
            'region_performance': r'(performance por região|vendas por região)',
            'asia_sales': r'(vendas na ásia|asia|asiático)',
            'europe_sales': r'(vendas na europa|europa|europeu)',
            'america_sales': r'(vendas na américa|américa|americano)',
            
            # Model queries
            'top_models': r'(top modelos|melhores modelos|modelos com mais vendas)',
            'model_performance': r'(performance por modelo|vendas por modelo)',
            'series_7': r'(série 7|7 series|modelo 7)',
            'series_3': r'(série 3|3 series|modelo 3)',
            'i8_sales': r'(i8|modelo i8)',
            
            # Time-based queries
            'annual_sales': r'(vendas anuais|sales by year|por ano)',
            'monthly_trends': r'(tendências mensais|monthly trends|por mês)',
            'growth': r'(crescimento|growth|evolução)',
            
            # Fuel and transmission
            'fuel_type': r'(tipo de combustível|fuel type|combustível)',
            'transmission': r'(transmissão|transmission|câmbio)',
            
            # Market share
            'market_share': r'(market share|participação de mercado|quota)',
            
            # Specific numbers
            'numbers': r'(\d+)',
        }
        
        # Predefined queries for common requests
        self.predefined_queries = {
            'dashboard': "SELECT * FROM analytics.kpi_executive_dashboard",
            'top_regions': "SELECT * FROM analytics.kpi_top_5_regions",
            'top_models': "SELECT * FROM analytics.kpi_top_10_models LIMIT 5",
            'annual_sales': "SELECT * FROM analytics.kpi_annual_sales",
            'regional_performance': "SELECT * FROM analytics.kpi_regional_performance",
            'model_performance': "SELECT * FROM analytics.kpi_model_performance",
            'fuel_performance': "SELECT * FROM analytics.kpi_fuel_type_performance",
            'transmission_performance': "SELECT * FROM analytics.kpi_transmission_performance",
            'annual_growth': "SELECT * FROM analytics.kpi_annual_growth",
            'monthly_trends': "SELECT * FROM analytics.kpi_monthly_trends"
        }
        
        logger.info("MCP Agent initialized")
    
    def process_natural_language_query(self, query: str) -> Dict[str, Any]:
        """
        Process natural language query and return results
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            start_time = datetime.now()
            
            # Normalize query
            normalized_query = query.lower().strip()
            
            # Find matching pattern
            matched_query = self._find_matching_query(normalized_query)
            
            if matched_query:
                # Execute predefined query
                results = self._execute_query(matched_query['sql'])
                
                response = {
                    'success': True,
                    'natural_language_query': query,
                    'sql_query': matched_query['sql'],
                    'query_type': matched_query['type'],
                    'explanation': matched_query['explanation'],
                    'results': results,
                    'row_count': len(results),
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Try to generate custom query
                custom_sql = self._generate_custom_query(normalized_query)
                if custom_sql:
                    results = self._execute_query(custom_sql)
                    response = {
                        'success': True,
                        'natural_language_query': query,
                        'sql_query': custom_sql,
                        'query_type': 'custom',
                        'explanation': 'Query customizada gerada automaticamente',
                        'results': results,
                        'row_count': len(results),
                        'execution_time': (datetime.now() - start_time).total_seconds(),
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    response = {
                        'success': False,
                        'natural_language_query': query,
                        'error': 'Não foi possível interpretar a consulta. Tente reformular.',
                        'suggestions': self._get_suggestions(),
                        'execution_time': (datetime.now() - start_time).total_seconds(),
                        'timestamp': datetime.now().isoformat()
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'natural_language_query': query,
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _find_matching_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Find matching predefined query"""
        for query_type, pattern in self.query_patterns.items():
            if re.search(pattern, query):
                if query_type in self.predefined_queries:
                    return {
                        'type': query_type,
                        'sql': self.predefined_queries[query_type],
                        'explanation': f"Consulta de {query_type.replace('_', ' ')}"
                    }
        
        return None
    
    def _generate_custom_query(self, query: str) -> Optional[str]:
        """Generate custom SQL query based on natural language"""
        # Simple keyword-based query generation
        if 'contar' in query or 'count' in query:
            if 'região' in query or 'region' in query:
                return "SELECT COUNT(DISTINCT region) as total_regions FROM bmw_sales"
            elif 'modelo' in query or 'model' in query:
                return "SELECT COUNT(DISTINCT model) as total_models FROM bmw_sales"
            else:
                return "SELECT COUNT(*) as total_records FROM bmw_sales"
        
        elif 'média' in query or 'average' in query or 'avg' in query:
            if 'preço' in query or 'price' in query:
                return "SELECT AVG(price_usd) as average_price FROM bmw_sales"
            elif 'vendas' in query or 'sales' in query:
                return "SELECT AVG(sales_units) as average_sales FROM bmw_sales"
        
        elif 'soma' in query or 'sum' in query or 'total' in query:
            if 'vendas' in query or 'sales' in query:
                return "SELECT SUM(sales_units) as total_sales FROM bmw_sales"
            elif 'receita' in query or 'revenue' in query:
                return "SELECT SUM(revenue) as total_revenue FROM bmw_sales"
        
        return None
    
    def _execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            conn.set_client_encoding('UTF8')
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def _get_suggestions(self) -> List[str]:
        """Get query suggestions"""
        return [
            "Mostre o dashboard executivo",
            "Quais são as top 5 regiões?",
            "Quais são os top 10 modelos?",
            "Mostre as vendas anuais",
            "Qual a performance por região?",
            "Mostre as tendências mensais",
            "Qual o crescimento anual?",
            "Conte o total de registros",
            "Qual a média de preços?",
            "Soma total de vendas"
        ]
    
    def get_available_queries(self) -> Dict[str, str]:
        """Get list of available predefined queries"""
        return {
            'dashboard': 'Dashboard executivo com KPIs principais',
            'top_regions': 'Top 5 regiões por performance',
            'top_models': 'Top 10 modelos por vendas',
            'annual_sales': 'Vendas agregadas por ano',
            'regional_performance': 'Performance detalhada por região',
            'model_performance': 'Performance detalhada por modelo',
            'fuel_performance': 'Performance por tipo de combustível',
            'transmission_performance': 'Performance por transmissão',
            'annual_growth': 'Crescimento anual de vendas',
            'monthly_trends': 'Tendências mensais de vendas'
        }
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            conn.set_client_encoding('UTF8')
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get table information
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'bmw_sales'
                ORDER BY table_name, ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            # Get view information
            cursor.execute("""
                SELECT table_name as view_name
                FROM information_schema.views
                WHERE table_schema = 'analytics'
                ORDER BY table_name
            """)
            
            views = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'tables': {
                    'bmw_sales': [dict(col) for col in columns]
                },
                'views': {
                    'analytics': [dict(view) for view in views]
                },
                'available_queries': self.get_available_queries()
            }
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return {}

def main():
    """Test the MCP Agent"""
    agent = MCPAgent()
    
    # Test queries
    test_queries = [
        "Mostre o dashboard executivo",
        "Quais são as top 5 regiões?",
        "Quais são os top 10 modelos?",
        "Mostre as vendas anuais",
        "Conte o total de registros",
        "Qual a média de preços?",
        "Soma total de vendas"
    ]
    
    print("=== TESTANDO MCP AGENT ===")
    
    for query in test_queries:
        print(f"\n--- Consulta: {query} ---")
        result = agent.process_natural_language_query(query)
        
        if result['success']:
            print(f"SQL: {result['sql_query']}")
            print(f"Resultados: {result['row_count']} registros")
            if result['results']:
                print("Primeiros resultados:")
                for i, row in enumerate(result['results'][:3]):
                    print(f"  {i+1}: {row}")
        else:
            print(f"Erro: {result['error']}")
            if 'suggestions' in result:
                print("Sugestões:")
                for suggestion in result['suggestions'][:3]:
                    print(f"  - {suggestion}")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    main()
