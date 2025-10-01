"""
Natural Language SQL Agent - Versão Melhorada com Padrões de Reconhecimento Aprimorados
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

# Chart Agent removed - focusing on SQL functionality only

logger = logging.getLogger(__name__)

class NaturalLanguageSQLAgent:
    def __init__(self):
        """Initialize Natural Language SQL Agent"""
        # Database configuration
        import os
        self.DB_CONFIG = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'ai_data_engineering'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres123'),
            'client_encoding': 'utf8'
        }
        
        # Enhanced query patterns with better recognition
        self.query_patterns = {
            # Dashboard queries - Multiple variations
            'dashboard': [
                r'(dashboard|resumo|overview|visão geral|painel|painel executivo)',
                r'(mostre|exiba|apresente).*(dashboard|resumo|overview)',
                r'(kpis|indicadores|métricas).*(principais|gerais)'
            ],
            
            # Regional queries - Enhanced patterns
            'top_regions': [
                r'(top|melhores|principais).*(regiões|região|regions)',
                r'(quais|mostre|exiba).*(top|melhores).*(regiões|região)',
                r'(regiões|região).*(com mais|com maior).*(vendas|performance)',
                r'(ranking|classificação).*(regiões|região)',
                r'(top 5|top5|cinco melhores).*(regiões|região)',
                r'(quais).*(são|sao).*(as).*(top).*5.*(regiões|região)',
                r'(quais).*(são|sao).*(as).*(top 5).*(regiões|região)',
                r'(quais).*(são|sao).*(top 5).*(regiões|região)'
            ],
            
            'regional_performance': [
                r'(performance|desempenho).*(por|da|das).*(regi[aã]o|regi[oõ]es)',
                r'(vendas|resultados).*(por|da|das).*(regi[aã]o|regi[oõ]es)',
                r'(an[aá]lise|comparativo).*(regi[oõ]es|regi[aã]o)',
                r'(regi[aã]o|regi[oõ]es).*(performance|desempenho|vendas)',
                r'(qual|quais).*(performance|desempenho).*(por|da|das).*(regi[aã]o|regi[oõ]es)',
                r'(mostre|exiba).*(performance|desempenho).*(por|da|das).*(regi[aã]o|regi[oõ]es)'
            ],
            
            # Model queries - Enhanced patterns
            'top_models': [
                r'(top|melhores|principais).*(modelos|modelo|models)',
                r'(quais|mostre|exiba).*(top|melhores).*(modelos|modelo)',
                r'(modelos|modelo).*(com mais|com maior).*(vendas|performance)',
                r'(ranking|classificação).*(modelos|modelo)',
                r'(top 10|top10|dez melhores).*(modelos|modelo)',
                r'(quais).*(são|sao).*(os).*(top|melhores).*(modelos|modelo)'
            ],
            
            'model_performance': [
                r'(performance|desempenho).*(por|do|dos).*(modelo|modelos)',
                r'(vendas|resultados).*(por|do|dos).*(modelo|modelos)',
                r'(análise|comparativo).*(modelos|modelo)',
                r'(modelo|modelos).*(performance|desempenho|vendas)',
                r'(total|soma).*(vendas|receita).*(por|do|dos).*(modelo|modelos)',
                r'(modelo|modelos).*(total|soma).*(vendas|receita)',
                r'(mostre|exiba).*(total|soma).*(vendas|receita).*(por|do|dos).*(modelo|modelos)',
                r'(receita|faturamento).*(por|do|dos).*(modelo|modelos)'
            ],
            
            # Time-based queries - Enhanced patterns
            'annual_sales': [
                r'(vendas|sales).*(anuais|anual|por ano|by year)',
                r'(mostre|exiba|apresente).*(vendas|sales).*(anuais|anual)',
                r'(resumo|agregado).*(anual|por ano)',
                r'(evolução|histórico).*(anual|por ano)'
            ],
            
            
            'annual_growth': [
                r'(crescimento|growth|evolução).*(anual|por ano)',
                r'(mostre|exiba).*(crescimento|growth).*(anual|por ano)',
                r'(taxa|percentual).*(crescimento|growth)',
                r'(aumento|redução).*(anual|por ano)'
            ],
            
            # New advanced analysis patterns
            'price_analysis': [
                r'(análise|analise).*(preços|precos|preço|preco)',
                r'(segmentação|segmentacao).*(preços|precos|preço|preco)',
                r'(distribuição|distribuicao).*(preços|precos|preço|preco)',
                r'(faixas|ranges).*(preços|precos|preço|preco)',
                r'(preços|precos|preço|preco).*(por|por).*(modelo|região|regiao)',
                r'(entry level|mid range|premium|luxury).*(modelos|modelo)'
            ],
            
            'color_performance': [
                r'(cores|cor).*(mais|top|melhores).*(vendidas|populares)',
                r'(performance|desempenho).*(por|da|das).*(cores|cor)',
                r'(análise|analise).*(cores|cor)',
                r'(cores|cor).*(preferidas|favoritas|populares)',
                r'(qual|quais).*(cores|cor).*(são|sao).*(mais).*(vendidas|populares)'
            ],
            
            'model_efficiency': [
                r'(eficiência|eficiencia).*(modelos|modelo)',
                r'(relação|relacao).*(preço|preco).*(eficiência|eficiencia)',
                r'(modelos|modelo).*(mais|melhor).*(eficientes|eficiente)',
                r'(revenue per unit|receita por unidade)',
                r'(price per liter|preço por litro)',
                r'(análise|analise).*(eficiência|eficiencia)'
            ],
            
            'seasonal_analysis': [
                r'(sazonalidade|sazonal).*(por|da|das).*(região|regiao)',
                r'(tendências|trends).*(sazonais|sazonal)',
                r'(crescimento|growth).*(por|da|das).*(região|regiao)',
                r'(análise|analise).*(sazonal|sazonalidade)',
                r'(performance|desempenho).*(sazonal|sazonalidade)'
            ],
            
            'top_performers': [
                r'(top performers|melhores performers)',
                r'(modelos|modelo).*(completos|completo)',
                r'(ranking|classificação|classificacao).*(composto|completo)',
                r'(múltiplas|multiplas).*(métricas|metricas)',
                r'(score|pontuação|pontuacao).*(composto|completo)'
            ],
            
            'price_volume_correlation': [
                r'(correlação|correlacao).*(preço|preco).*(volume)',
                r'(relação|relacao).*(preço|preco).*(vendas|volume)',
                r'(análise|analise).*(correlação|correlacao)',
                r'(preço|preco).*(vs|versus).*(volume|vendas)',
                r'(high price high volume|low price high volume)'
            ],
            
            'market_penetration': [
                r'(penetração|penetracao).*(mercado|market)',
                r'(cobertura|coverage).*(mercado|market)',
                r'(diversidade|diversidade).*(produtos|produto)',
                r'(modelos|modelo).*(disponíveis|disponiveis).*(por|da|das).*(região|regiao)',
                r'(market share|participação|participacao).*(mercado|market)'
            ],
            
            'temporal_trends': [
                r'(tendências|trends).*(temporais|temporal)',
                r'(evolução|evolucao).*(temporal|tempo)',
                r'(histórico|historico).*(completo|completo)',
                r'(análise|analise).*(temporal|tempo)',
                r'(crescimento|growth).*(temporal|tempo)'
            ],
            
            # Year-based queries
            'year_analysis': [
                r'(qual|quais).*(ano|anos).*(tem|tem mais|tem maior|tem melhor)',
                r'(ano|anos).*(com mais|com maior|com melhor|melhor)',
                r'(melhor|maior|mais).*(ano|anos)',
                r'(vendas|modelos|performance).*(por|do|da).*(ano|anos)',
                r'(ano|anos).*(vendas|modelos|performance)',
                r'(qual|quais).*(ano|anos).*(vendas|modelos)',
                r'(ano|anos).*(mais|maior|melhor).*(vendas|modelos)'
            ],
            
            # Fuel and transmission - Enhanced patterns
            'fuel_performance': [
                r'(tipo|tipos).*(combustível|combustivel|fuel)',
                r'(performance|desempenho).*(combustível|combustivel|fuel)',
                r'(vendas|sales).*(por|do).*(combustível|combustivel|fuel)',
                r'(análise|comparativo).*(combustível|combustivel|fuel)'
            ],
            
            'transmission_performance': [
                r'(transmissão|transmissao|transmission|câmbio|cambio)',
                r'(performance|desempenho).*(transmissão|transmissao|transmission)',
                r'(vendas|sales).*(por|do).*(transmissão|transmissao|transmission)',
                r'(análise|comparativo).*(transmissão|transmissao|transmission)'
            ],
            
            # Market share queries
            'market_share': [
                r'(market share|participação|participacao).*(mercado|market)',
                r'(quota|share).*(mercado|market)',
                r'(percentual|porcentagem).*(mercado|market)'
            ],
            
            # Count queries - Enhanced patterns
            'count_total': [
                r'(conte|count|total|quantos|quantas).*(registros|records)',
                r'(quantos|quantas).*(registros|records|linhas)',
                r'(total|soma).*(registros|records)',
                r'(número|numero|n).*(registros|records)'
            ],
            
            'count_regions': [
                r'(conte|count|quantos|quantas).*(regiões|região|regions)',
                r'(quantos|quantas).*(regiões|região|regions)',
                r'(total|soma).*(regiões|região|regions)'
            ],
            
            'count_models': [
                r'(conte|count|quantos|quantas).*(modelos|modelo|models)',
                r'(quantos|quantas).*(modelos|modelo|models)',
                r'(total|soma).*(modelos|modelo|models)'
            ],
            
            # Average queries - Enhanced patterns
            'average_price': [
                r'(média|media|average|avg).*(preço|preco|price)',
                r'(preço|preco|price).*(médio|medio|average)',
                r'(valor|value).*(médio|medio|average)',
                r'(custo|cost).*(médio|medio|average)',
                r'(média|media|average|avg).*(preço|preco|price).*(por|do|da|dos).*(ano|anos)',
                r'(preço|preco|price).*(médio|medio|average).*(por|do|da|dos).*(ano|anos)',
                r'(qual|quais).*(média|media|average|avg).*(preço|preco|price).*(por|do|da|dos).*(ano|anos)'
            ],
            
            'average_sales': [
                r'(média|media|average|avg).*(vendas|sales|unidades)',
                r'(vendas|sales|unidades).*(média|media|average)',
                r'(quantidade|quantity).*(média|media|average)'
            ],
            
            # Sum queries - Enhanced patterns
            'sum_sales': [
                r'(soma|sum|total).*(vendas|sales|unidades)',
                r'(total|soma|sum).*(unidades|units)',
                r'(quantidade|quantity).*(total|soma|sum)'
            ],
            
            'sum_revenue': [
                r'(soma|sum|total).*(receita|revenue|faturamento)',
                r'(total|soma|sum).*(receita|revenue)',
                r'(faturamento|billing).*(total|soma|sum)'
            ],
            
            # Specific region queries
            'asia_sales': [
                r'(vendas|sales).*(ásia|asia|asiático|asiatico)',
                r'(ásia|asia|asiático|asiatico).*(vendas|sales)',
                r'(mercado|market).*(asiático|asiatico|ásia|asia)'
            ],
            
            'europe_sales': [
                r'(vendas|sales).*(europa|europeu|europe)',
                r'(europa|europeu|europe).*(vendas|sales)',
                r'(mercado|market).*(europeu|europe|europa)'
            ],
            
            'america_sales': [
                r'(vendas|sales).*(américa|america|americano|america)',
                r'(américa|america|americano|america).*(vendas|sales)',
                r'(mercado|market).*(americano|america|américa)'
            ],
            
            # Specific model queries
            'series_7': [
                r'(série|serie|series).*7',
                r'7.*(série|serie|series)',
                r'(modelo|model).*7',
                r'7.*(modelo|model)'
            ],
            
            'series_3': [
                r'(série|serie|series).*3',
                r'3.*(série|serie|series)',
                r'(modelo|model).*3',
                r'3.*(modelo|model)'
            ],
            
            'i8_sales': [
                r'(i8|i-8)',
                r'(modelo|model).*(i8|i-8)',
                r'(vendas|sales).*(i8|i-8)'
            ]
        }
        
        # Predefined queries for common requests
        self.predefined_queries = {
            'dashboard': "SELECT * FROM analytics.kpi_executive_dashboard",
            'top_regions': "SELECT * FROM analytics.kpi_top_5_regions",
            'top_models': "SELECT * FROM analytics.kpi_top_10_models LIMIT 10",
            'annual_sales': "SELECT * FROM analytics.kpi_annual_sales",
            'regional_performance': "SELECT * FROM analytics.kpi_regional_performance",
            'model_performance': "SELECT model, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue, SUM(sales_volume) as total_units_sold FROM bmw_sales GROUP BY model ORDER BY SUM(price_usd * sales_volume) DESC",
            'fuel_performance': "SELECT * FROM analytics.kpi_fuel_type_performance",
            'transmission_performance': "SELECT * FROM analytics.kpi_transmission_performance",
            'annual_growth': "SELECT * FROM analytics.kpi_annual_growth",
            'year_analysis': "SELECT year, COUNT(DISTINCT model) as total_models, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY year ORDER BY total_sales DESC",
            
            # New advanced KPI queries
            'price_analysis': "SELECT * FROM analytics.kpi_price_analysis",
            'color_performance': "SELECT * FROM analytics.kpi_color_performance",
            'model_efficiency': "SELECT * FROM analytics.kpi_model_efficiency",
            'seasonal_analysis': "SELECT * FROM analytics.kpi_seasonal_analysis",
            'top_performers': "SELECT * FROM analytics.kpi_top_performers",
            'price_volume_correlation': "SELECT * FROM analytics.kpi_price_volume_correlation",
            'market_penetration': "SELECT * FROM analytics.kpi_market_penetration",
            'temporal_trends': "SELECT * FROM analytics.kpi_temporal_trends",
            
            # Count queries
            'count_total': "SELECT COUNT(*) as total_records FROM bmw_sales",
            'count_regions': "SELECT COUNT(DISTINCT region) as total_regions FROM bmw_sales",
            'count_models': "SELECT COUNT(DISTINCT model) as total_models FROM bmw_sales",
            'count_countries': "SELECT COUNT(DISTINCT country) as total_countries FROM bmw_sales",
            
            # Average queries
            'average_price': "SELECT year, AVG(price_usd) as average_price FROM bmw_sales GROUP BY year ORDER BY year",
            'average_sales': "SELECT AVG(sales_volume) as average_sales FROM bmw_sales",
            'average_revenue': "SELECT AVG(price_usd * sales_volume) as average_revenue FROM bmw_sales",
            'average_mileage': "SELECT AVG(mileage_km) as average_mileage FROM bmw_sales",
            
            # Sum queries
            'sum_sales': "SELECT SUM(sales_volume) as total_sales FROM bmw_sales",
            'sum_revenue': "SELECT TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales",
            'sum_sales_value': "SELECT TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_sales_value FROM bmw_sales",
            
            # Min/Max queries
            'min_price': "SELECT MIN(price_usd) as min_price FROM bmw_sales",
            'max_price': "SELECT MAX(price_usd) as max_price FROM bmw_sales",
            'min_sales': "SELECT MIN(sales_volume) as min_sales FROM bmw_sales",
            'max_sales': "SELECT MAX(sales_volume) as max_sales FROM bmw_sales",
            
            # Top performance queries
            'top_region_revenue': "SELECT region, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY region ORDER BY SUM(price_usd * sales_volume) DESC LIMIT 1",
            'top_model_revenue': "SELECT model, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY model ORDER BY SUM(price_usd * sales_volume) DESC LIMIT 1",
            
            # Specific model queries
            'series_7': "SELECT * FROM bmw_sales WHERE model = '7 Series' ORDER BY sales_volume DESC LIMIT 10",
            'series_3': "SELECT * FROM bmw_sales WHERE model = '3 Series' ORDER BY sales_volume DESC LIMIT 10",
            'i8_sales': "SELECT * FROM bmw_sales WHERE model = 'i8' ORDER BY sales_volume DESC LIMIT 10"
        }
        
        # Chart Agent removed - focusing on SQL functionality only
        
        logger.info("Natural Language SQL Agent initialized")
    
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
            
            # Find matching pattern with improved scoring
            matched_query = self._find_matching_query_improved(normalized_query)
            
            if matched_query:
                # Execute predefined query
                results = self._execute_query(matched_query['sql'])
                
                response = {
                    'success': True,
                    'natural_language_query': query,
                    'sql_query': matched_query['sql'],
                    'query_type': matched_query['type'],
                    'explanation': matched_query['explanation'],
                    'confidence': matched_query['confidence'],
                    'results': results,
                    'row_count': len(results),
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                    'timestamp': datetime.now().isoformat()
                }
                
            else:
                # Try to generate custom query
                custom_sql = self._generate_custom_query_improved(normalized_query)
                if custom_sql:
                    results = self._execute_query(custom_sql)
                    response = {
                        'success': True,
                        'natural_language_query': query,
                        'sql_query': custom_sql,
                        'query_type': 'custom',
                        'explanation': 'Query customizada gerada automaticamente',
                        'confidence': 0.7,
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
                        'suggestions': self._get_suggestions_improved(),
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
    
    def _find_matching_query_improved(self, query: str) -> Optional[Dict[str, Any]]:
        """Find matching predefined query with improved scoring"""
        best_match = None
        best_score = 0
        
        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    # Calculate confidence score based on match length and position
                    match_length = len(match.group())
                    query_length = len(query)
                    position_score = 1.0 - (match.start() / max(query_length, 1))
                    length_score = match_length / max(query_length, 1)
                    confidence = (position_score + length_score) / 2
                    
                    if confidence > best_score:
                        best_score = confidence
                        best_match = {
                            'type': query_type,
                            'sql': self.predefined_queries.get(query_type),
                            'explanation': f"Consulta de {query_type.replace('_', ' ')}",
                            'confidence': confidence,
                            'pattern': pattern,
                            'match': match.group()
                        }
        
        return best_match if best_score > 0.3 else None  # Minimum confidence threshold
    
    def _generate_custom_query_improved(self, query: str) -> Optional[str]:
        """Generate custom SQL query with improved logic"""
        # Enhanced keyword-based query generation
        
        # Count queries - but check if it's actually a sum query first
        if any(word in query for word in ['conte', 'count', 'quantos', 'quantas']) and not any(word in query for word in ['soma', 'sum', 'total']):
            if any(word in query for word in ['regiões', 'região', 'regions']):
                return "SELECT COUNT(DISTINCT region) as total_regions FROM bmw_sales"
            elif any(word in query for word in ['modelos', 'modelo', 'models']):
                return "SELECT COUNT(DISTINCT model) as total_models FROM bmw_sales"
            elif any(word in query for word in ['países', 'país', 'countries']):
                return "SELECT COUNT(DISTINCT country) as total_countries FROM bmw_sales"
            elif any(word in query for word in ['registros', 'records', 'linhas']):
                return "SELECT COUNT(*) as total_records FROM bmw_sales"
            else:
                return "SELECT COUNT(*) as total_records FROM bmw_sales"
        
        # Average queries
        elif any(word in query for word in ['média', 'media', 'average', 'avg']):
            if any(word in query for word in ['preço', 'preco', 'price']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, AVG(price_usd) as average_price FROM bmw_sales GROUP BY model ORDER BY average_price DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, AVG(price_usd) as average_price FROM bmw_sales GROUP BY region ORDER BY average_price DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, AVG(price_usd) as average_price FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT AVG(price_usd) as average_price FROM bmw_sales"
                else:
                    return "SELECT AVG(price_usd) as average_price FROM bmw_sales"
            elif any(word in query for word in ['vendas', 'sales', 'unidades']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, AVG(sales_volume) as average_sales FROM bmw_sales GROUP BY model ORDER BY average_sales DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, AVG(sales_volume) as average_sales FROM bmw_sales GROUP BY region ORDER BY average_sales DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, AVG(sales_volume) as average_sales FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT AVG(sales_volume) as average_sales FROM bmw_sales"
                else:
                    return "SELECT AVG(sales_volume) as average_sales FROM bmw_sales"
            elif any(word in query for word in ['receita', 'revenue']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, AVG(price_usd * sales_volume) as average_revenue FROM bmw_sales GROUP BY model ORDER BY average_revenue DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, AVG(price_usd * sales_volume) as average_revenue FROM bmw_sales GROUP BY region ORDER BY average_revenue DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, AVG(price_usd * sales_volume) as average_revenue FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT AVG(price_usd * sales_volume) as average_revenue FROM bmw_sales"
                else:
                    return "SELECT AVG(price_usd * sales_volume) as average_revenue FROM bmw_sales"
            elif any(word in query for word in ['quilometragem', 'mileage']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, AVG(mileage_km) as average_mileage FROM bmw_sales GROUP BY model ORDER BY average_mileage DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, AVG(mileage_km) as average_mileage FROM bmw_sales GROUP BY region ORDER BY average_mileage DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, AVG(mileage_km) as average_mileage FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT AVG(mileage_km) as average_mileage FROM bmw_sales"
                else:
                    return "SELECT AVG(mileage_km) as average_mileage FROM bmw_sales"
        
        # Sum queries - prioritize sum/total over count
        elif any(word in query for word in ['soma', 'sum']) or (any(word in query for word in ['total']) and any(word in query for word in ['vendas', 'sales', 'unidades', 'receita', 'revenue'])):
            if any(word in query for word in ['vendas', 'sales', 'unidades']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY model ORDER BY total_sales DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY region ORDER BY total_sales DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT SUM(sales_volume) as total_sales FROM bmw_sales"
                else:
                    return "SELECT SUM(sales_volume) as total_sales FROM bmw_sales"
            elif any(word in query for word in ['receita', 'revenue', 'faturamento']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY model ORDER BY SUM(price_usd * sales_volume) DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY region ORDER BY SUM(price_usd * sales_volume) DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales"
                else:
                    return "SELECT TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales"
            elif any(word in query for word in ['valor', 'value', 'total_sales']):
                # Check if grouping is requested
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_sales_value FROM bmw_sales GROUP BY model ORDER BY SUM(price_usd * sales_volume) DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_sales_value FROM bmw_sales GROUP BY region ORDER BY SUM(price_usd * sales_volume) DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_sales_value FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_sales_value FROM bmw_sales"
                else:
                    return "SELECT TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_sales_value FROM bmw_sales"
            else:
                # Check if grouping is requested for generic sum
                if any(word in query for word in ['por', 'por cada', 'por modelo', 'por modelos', 'por região', 'por regiões', 'por ano', 'por anos']):
                    if any(word in query for word in ['modelo', 'modelos']):
                        return "SELECT model, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY model ORDER BY total_sales DESC"
                    elif any(word in query for word in ['região', 'regiões']):
                        return "SELECT region, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY region ORDER BY total_sales DESC"
                    elif any(word in query for word in ['ano', 'anos']):
                        return "SELECT year, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY year ORDER BY year"
                    else:
                        return "SELECT SUM(sales_volume) as total_sales FROM bmw_sales"
                else:
                    return "SELECT SUM(sales_volume) as total_sales FROM bmw_sales"
        
        # Min/Max queries
        elif any(word in query for word in ['mínimo', 'minimo', 'min', 'menor']):
            if any(word in query for word in ['preço', 'preco', 'price']):
                return "SELECT MIN(price_usd) as min_price FROM bmw_sales"
            elif any(word in query for word in ['vendas', 'sales']):
                return "SELECT MIN(sales_volume) as min_sales FROM bmw_sales"
        
        elif any(word in query for word in ['máximo', 'maximo', 'max', 'maior']):
            if any(word in query for word in ['preço', 'preco', 'price']):
                return "SELECT MAX(price_usd) as max_price FROM bmw_sales"
            elif any(word in query for word in ['vendas', 'sales']):
                return "SELECT MAX(sales_volume) as max_sales FROM bmw_sales"
        
        # Specific value queries
        elif any(word in query for word in ['maior', 'melhor', 'top 1']):
            if any(word in query for word in ['região', 'regiões']):
                return "SELECT region, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY region ORDER BY SUM(price_usd * sales_volume) DESC LIMIT 1"
            elif any(word in query for word in ['modelo', 'modelos']):
                return "SELECT model, TO_CHAR(SUM(price_usd * sales_volume), 'FM999,999,999,999,999') as total_revenue FROM bmw_sales GROUP BY model ORDER BY SUM(price_usd * sales_volume) DESC LIMIT 1"
        
        # Performance queries
        elif any(word in query for word in ['performance', 'desempenho']):
            if any(word in query for word in ['regiao', 'regioes', 'região', 'regiões']):
                return "SELECT * FROM analytics.kpi_regional_performance"
            elif any(word in query for word in ['modelo', 'modelos']):
                return "SELECT * FROM analytics.kpi_model_performance"
            elif any(word in query for word in ['cor', 'cores']):
                return "SELECT * FROM analytics.kpi_color_performance"
            elif any(word in query for word in ['eficiência', 'eficiencia']):
                return "SELECT * FROM analytics.kpi_model_efficiency"
            elif any(word in query for word in ['sazonal', 'sazonalidade']):
                return "SELECT * FROM analytics.kpi_seasonal_analysis"
        
        # Ranking queries
        elif any(word in query for word in ['ranking', 'classificação', 'top']):
            if any(word in query for word in ['modelo', 'modelos']):
                # Check if specific number is mentioned
                if any(word in query for word in ['10', 'dez']):
                    return "SELECT * FROM analytics.kpi_top_10_models LIMIT 10"
                elif any(word in query for word in ['5', 'cinco']):
                    return "SELECT * FROM analytics.kpi_top_10_models LIMIT 5"
                else:
                    return "SELECT * FROM analytics.kpi_top_10_models LIMIT 10"
            elif any(word in query for word in ['região', 'regiões']):
                # Check if specific number is mentioned for regions
                if any(word in query for word in ['5', 'cinco']):
                    return "SELECT * FROM analytics.kpi_top_5_regions"
                elif any(word in query for word in ['10', 'dez']):
                    return "SELECT * FROM analytics.kpi_top_5_regions LIMIT 10"
                else:
                    return "SELECT * FROM analytics.kpi_top_5_regions"
        
        # Year-based queries
        elif any(word in query for word in ['ano', 'anos', 'year']):
            if any(word in query for word in ['modelos', 'modelo', 'vendas', 'sales']):
                if any(word in query for word in ['mais', 'maior', 'melhor', 'top']):
                    return "SELECT year, COUNT(DISTINCT model) as total_models, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY year ORDER BY total_sales DESC LIMIT 5"
                else:
                    return "SELECT year, COUNT(DISTINCT model) as total_models, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY year ORDER BY year"
            elif any(word in query for word in ['qual', 'quais']):
                return "SELECT year, COUNT(DISTINCT model) as total_models, SUM(sales_volume) as total_sales FROM bmw_sales GROUP BY year ORDER BY total_sales DESC LIMIT 1"
            elif any(word in query for word in ['crescimento', 'growth']):
                return "SELECT * FROM analytics.kpi_annual_growth"
            elif any(word in query for word in ['vendas', 'sales']):
                return "SELECT * FROM analytics.kpi_annual_sales"
            else:
                return "SELECT * FROM analytics.kpi_annual_sales"
        
        # Advanced analysis queries
        elif any(word in query for word in ['preços', 'precos', 'preço', 'preco']):
            if any(word in query for word in ['análise', 'analise', 'segmentação', 'segmentacao']):
                return "SELECT * FROM analytics.kpi_price_analysis"
            elif any(word in query for word in ['correlação', 'correlacao', 'volume']):
                return "SELECT * FROM analytics.kpi_price_volume_correlation"
            else:
                return "SELECT * FROM analytics.kpi_price_analysis"
        
        elif any(word in query for word in ['cor', 'cores']):
            return "SELECT * FROM analytics.kpi_color_performance"
        
        elif any(word in query for word in ['eficiência', 'eficiencia']):
            return "SELECT * FROM analytics.kpi_model_efficiency"
        
        elif any(word in query for word in ['sazonal', 'sazonalidade']):
            return "SELECT * FROM analytics.kpi_seasonal_analysis"
        
        elif any(word in query for word in ['top performers', 'melhores performers', 'múltiplas', 'multiplas']):
            return "SELECT * FROM analytics.kpi_top_performers"
        
        elif any(word in query for word in ['penetração', 'penetracao', 'mercado', 'market']):
            return "SELECT * FROM analytics.kpi_market_penetration"
        
        elif any(word in query for word in ['temporal', 'tempo', 'histórico', 'historico']):
            return "SELECT * FROM analytics.kpi_temporal_trends"
        
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
    
    def _get_suggestions_improved(self) -> List[str]:
        """Get improved query suggestions"""
        return [
            "Mostre o dashboard executivo",
            "Quais são as top 5 regiões?",
            "Quais são os top 10 modelos?",
            "Mostre as vendas anuais",
            "Qual a performance por região?",
            "Qual o crescimento anual?",
            "Conte o total de registros",
            "Qual a média de preços?",
            "Soma total de vendas",
            "Qual a região com maior faturamento?",
            "Total de vendas por modelo",
            "Mostre a performance por combustível",
            "Qual o modelo mais vendido?",
            "Conte quantas regiões temos",
            "Qual o preço máximo?",
            "Qual ano tem mais modelos vendidos?",
            "Quais são os anos com mais vendas?",
            "Mostre vendas por ano",
            "Qual o melhor ano em vendas?",
            
            # New advanced suggestions
            "Análise de preços por segmento",
            "Quais cores são mais vendidas?",
            "Modelos mais eficientes",
            "Análise sazonal por região",
            "Top performers por múltiplas métricas",
            "Correlação preço-volume",
            "Penetração de mercado por região",
            "Tendências temporais completas",
            "Performance por cor",
            "Eficiência dos modelos",
            "Crescimento por região",
            "Diversidade de produtos por região"
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
            'year_analysis': 'Análise de vendas e modelos por ano'
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
    """Test the Natural Language SQL Agent"""
    agent = NaturalLanguageSQLAgent()
    
    # Test queries
    test_queries = [
        "Mostre o dashboard executivo",
        "Quais são as top 5 regiões?",
        "Quais são os top 10 modelos?",
        "Mostre as vendas anuais",
        "Conte o total de registros",
        "Qual a média de preços?",
        "Soma total de vendas",
        "Qual a região com maior faturamento?",
        "Conte quantas regiões temos",
        "Qual o preço máximo?"
    ]
    
    print("=== TESTANDO NATURAL LANGUAGE SQL AGENT ===")
    
    for query in test_queries:
        print(f"\n--- Consulta: {query} ---")
        result = agent.process_natural_language_query(query)
        
        if result['success']:
            print(f"SQL: {result['sql_query']}")
            print(f"Confiança: {result.get('confidence', 'N/A')}")
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
