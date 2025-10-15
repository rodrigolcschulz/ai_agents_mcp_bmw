"""
Orchestrator Agent - Coordinates the pipeline between SQL and Visualization agents
Intelligently routes queries to appropriate specialized agents
"""
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import re

# Import specialized agents
from agents.ai_sql_agent import AISQLAgent
from agents.visualization_agent import VisualizationAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Orchestrator that coordinates between SQL Agent and Visualization Agent.
    Determines whether a query needs data retrieval, visualization, or both.
    """
    
    def __init__(self, ai_provider: str = "openai"):
        """
        Initialize Orchestrator Agent
        
        Args:
            ai_provider: "openai" or "anthropic" (used for both SQL and Visualization)
        """
        self.ai_provider = ai_provider
        
        # Initialize specialized agents
        self.sql_agent = AISQLAgent(ai_provider=ai_provider)
        self.viz_agent = VisualizationAgent(ai_provider=ai_provider)
        
        # Query intent patterns
        self.visualization_keywords = [
            # Portuguese
            'gráfico', 'grafico', 'chart', 'visualiz', 'plot', 'mostre gráfico',
            'crie gráfico', 'faça gráfico', 'desenhe', 'plote',
            'barra', 'linha', 'pizza', 'dispersão', 'scatter', 'heatmap',
            'boxplot', 'histograma', 'área', 'area',
            # English
            'show chart', 'create chart', 'make chart', 'draw chart',
            'bar chart', 'line chart', 'pie chart', 'scatter plot',
            'visualize', 'plot', 'graph'
        ]
        
        self.data_only_keywords = [
            # Portuguese
            'mostre os dados', 'exiba os dados', 'liste', 'tabela',
            'dados', 'registros', 'linhas', 'valores',
            'qual', 'quais', 'quanto', 'quantos', 'quantas',
            'conte', 'soma', 'média', 'total',
            # English  
            'show data', 'display data', 'list', 'table',
            'what', 'which', 'how many', 'count', 'sum', 'average', 'total'
        ]
        
        logger.info(f"Orchestrator Agent initialized with {ai_provider}")
    
    def process_query(self, query: str, return_chart: bool = True) -> Dict[str, Any]:
        """
        Process a user query by routing to appropriate agents
        
        Args:
            query: Natural language query from user
            return_chart: Whether to generate visualization (default True if query asks for chart)
            
        Returns:
            Dictionary with results from SQL and/or Visualization agents
        """
        try:
            start_time = datetime.now()
            
            # Determine query intent
            intent = self._classify_query_intent(query)
            
            logger.info(f"Query intent: {intent}")
            
            response = {
                'success': True,
                'query': query,
                'intent': intent,
                'ai_provider': self.ai_provider,
                'timestamp': datetime.now().isoformat()
            }
            
            # Route based on intent
            if intent == 'visualization_only':
                # User wants visualization but didn't specify data source
                # This is an error - need data first
                response['success'] = False
                response['error'] = "Por favor, primeiro especifique quais dados você quer visualizar. Exemplo: 'Mostre vendas por região' e depois 'Crie um gráfico de barras'"
                response['execution_time'] = (datetime.now() - start_time).total_seconds()
                return response
                
            elif intent == 'data_then_visualization':
                # Get data first, then create visualization
                sql_result = self.sql_agent.process_query(query)
                
                if not sql_result['success']:
                    response['success'] = False
                    response['sql_result'] = sql_result
                    response['error'] = f"Erro ao buscar dados: {sql_result.get('error', 'Unknown error')}"
                    response['execution_time'] = (datetime.now() - start_time).total_seconds()
                    return response
                
                # Convert results to DataFrame
                if sql_result['results']:
                    df = pd.DataFrame(sql_result['results'])
                    
                    # Generate visualization
                    viz_result = self.viz_agent.generate_chart(
                        data=df,
                        query=query
                    )
                    
                    response['sql_result'] = sql_result
                    response['visualization_result'] = viz_result
                    response['data'] = sql_result['results']
                    response['chart_available'] = viz_result['success']
                else:
                    response['sql_result'] = sql_result
                    response['data'] = []
                    response['message'] = "Consulta executada mas nenhum dado retornado"
                    
            elif intent == 'data_only':
                # Just get data, no visualization
                sql_result = self.sql_agent.process_query(query)
                response['sql_result'] = sql_result
                response['data'] = sql_result.get('results', [])
                response['success'] = sql_result['success']
                
                if not sql_result['success']:
                    response['error'] = sql_result.get('error', 'Unknown error')
            
            else:  # unknown
                response['success'] = False
                response['error'] = "Não foi possível entender a intenção da consulta"
            
            response['execution_time'] = (datetime.now() - start_time).total_seconds()
            return response
            
        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def process_query_with_data(
        self,
        query: str,
        data: pd.DataFrame,
        force_visualization: bool = False
    ) -> Dict[str, Any]:
        """
        Process a query when data is already available
        Useful for creating different visualizations from the same data
        
        Args:
            query: Natural language query (usually visualization request)
            data: DataFrame with data to visualize
            force_visualization: Force visualization even if query doesn't explicitly ask
            
        Returns:
            Dictionary with visualization results
        """
        try:
            start_time = datetime.now()
            
            # Generate visualization
            viz_result = self.viz_agent.generate_chart(
                data=data,
                query=query
            )
            
            response = {
                'success': viz_result['success'],
                'query': query,
                'intent': 'visualization_with_data',
                'visualization_result': viz_result,
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            if not viz_result['success']:
                response['error'] = viz_result.get('error', 'Unknown error')
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query with data: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _classify_query_intent(self, query: str) -> str:
        """
        Classify the intent of a query
        
        Returns:
            'data_only': Just retrieve data
            'data_then_visualization': Get data and create visualization
            'visualization_only': Just create visualization (error if no data provided)
            'unknown': Could not determine intent
        """
        query_lower = query.lower()
        
        # Check if query explicitly asks for visualization
        has_viz_keyword = any(keyword in query_lower for keyword in self.visualization_keywords)
        has_data_keyword = any(keyword in query_lower for keyword in self.data_only_keywords)
        
        if has_viz_keyword and has_data_keyword:
            # Query asks for both data and visualization
            return 'data_then_visualization'
        elif has_viz_keyword:
            # Query only asks for visualization
            # Check if it also mentions data source
            if any(word in query_lower for word in ['vendas', 'sales', 'modelos', 'models', 'região', 'region', 'ano', 'year']):
                return 'data_then_visualization'
            else:
                return 'visualization_only'
        elif has_data_keyword:
            # Query only asks for data
            return 'data_only'
        else:
            # Default: assume data retrieval
            # Most queries without explicit keywords are data queries
            return 'data_only'
    
    def get_available_operations(self) -> Dict[str, List[str]]:
        """Get information about available operations"""
        return {
            'sql_operations': [
                'Consultas em linguagem natural',
                'Geração automática de SQL',
                'Suporte para agregações, filtros, ordenação',
                'Consultas em português e inglês'
            ],
            'visualization_operations': [
                'Gráficos de barras, linhas, dispersão',
                'Gráficos de pizza, heatmaps, boxplots',
                'Histogramas, gráficos de área',
                'Detecção automática de melhor tipo de gráfico',
                'Customização via linguagem natural'
            ],
            'orchestration_features': [
                'Roteamento inteligente de consultas',
                'Pipeline automático: dados → visualização',
                'Suporte para múltiplas visualizações dos mesmos dados',
                'Análise de intenção de consulta'
            ]
        }
    
    def create_visualization_from_sql(
        self,
        sql_query: str,
        visualization_query: str
    ) -> Dict[str, Any]:
        """
        Execute SQL query and create visualization
        Useful when user has specific SQL in mind
        
        Args:
            sql_query: SQL query to execute
            visualization_query: Natural language description of desired chart
            
        Returns:
            Dictionary with SQL and visualization results
        """
        try:
            start_time = datetime.now()
            
            # Execute SQL directly
            import psycopg2
            from psycopg2.extras import RealDictCursor
            import os
            
            DB_CONFIG = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', '5433')),
                'database': os.getenv('POSTGRES_DB', 'ai_data_engineering'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres123'),
                'options': '-c client_encoding=UTF8'
            }
            
            conn = psycopg2.connect(**DB_CONFIG)
            conn.set_client_encoding('UTF8')
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql_query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in results])
            
            # Generate visualization
            viz_result = self.viz_agent.generate_chart(
                data=df,
                query=visualization_query
            )
            
            response = {
                'success': True,
                'sql_query': sql_query,
                'visualization_query': visualization_query,
                'data': df.to_dict('records'),
                'row_count': len(df),
                'visualization_result': viz_result,
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in create_visualization_from_sql: {e}")
            return {
                'success': False,
                'sql_query': sql_query,
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def suggest_visualizations(self, data: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Suggest appropriate visualizations for given data
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            List of visualization suggestions with descriptions
        """
        suggestions = []
        
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Categorical + Numeric → Bar chart
        if categorical_cols and numeric_cols:
            suggestions.append({
                'type': 'bar',
                'description': f"Gráfico de barras: {categorical_cols[0]} vs {numeric_cols[0]}",
                'query': f"Crie um gráfico de barras de {numeric_cols[0]} por {categorical_cols[0]}"
            })
        
        # Time series → Line chart
        time_cols = [col for col in data.columns if any(word in col.lower() for word in ['year', 'ano', 'date', 'data', 'month', 'mes'])]
        if time_cols and numeric_cols:
            suggestions.append({
                'type': 'line',
                'description': f"Gráfico de linha: tendência de {numeric_cols[0]} ao longo do tempo",
                'query': f"Mostre um gráfico de linha de {numeric_cols[0]} por {time_cols[0]}"
            })
        
        # Two numeric → Scatter
        if len(numeric_cols) >= 2:
            suggestions.append({
                'type': 'scatter',
                'description': f"Gráfico de dispersão: correlação entre {numeric_cols[0]} e {numeric_cols[1]}",
                'query': f"Crie um gráfico de dispersão de {numeric_cols[0]} vs {numeric_cols[1]}"
            })
        
        # Categorical + Numeric → Pie chart (for small number of categories)
        if categorical_cols and numeric_cols and len(data[categorical_cols[0]].unique()) <= 10:
            suggestions.append({
                'type': 'pie',
                'description': f"Gráfico de pizza: distribuição de {numeric_cols[0]} por {categorical_cols[0]}",
                'query': f"Faça um gráfico de pizza de {numeric_cols[0]} por {categorical_cols[0]}"
            })
        
        # Multiple numeric → Heatmap (correlation)
        if len(numeric_cols) >= 3:
            suggestions.append({
                'type': 'heatmap',
                'description': f"Heatmap: correlação entre variáveis numéricas",
                'query': f"Mostre um heatmap de correlação das variáveis numéricas"
            })
        
        return suggestions


def main():
    """Test the Orchestrator Agent"""
    print("=== ORCHESTRATOR AGENT TEST ===")
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent("openai")
    
    # Test queries
    test_queries = [
        # Data only queries
        "Quais são as top 5 regiões?",
        "Mostre o total de vendas por modelo",
        "Qual a média de preços por ano?",
        
        # Data + Visualization queries
        "Mostre um gráfico de barras das vendas por região",
        "Crie um gráfico de linha da receita ao longo dos anos",
        "Faça um gráfico de dispersão entre preço e vendas",
        
        # Visualization only (should error)
        "Crie um gráfico de pizza"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        result = orchestrator.process_query(query)
        
        print(f"Intent: {result.get('intent', 'unknown')}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            if 'sql_result' in result:
                print(f"\n[SQL Result]")
                print(f"  - SQL: {result['sql_result'].get('sql_query', 'N/A')}")
                print(f"  - Rows: {result['sql_result'].get('row_count', 0)}")
            
            if 'visualization_result' in result:
                print(f"\n[Visualization Result]")
                viz = result['visualization_result']
                print(f"  - Chart Type: {viz.get('chart_type', 'N/A')}")
                print(f"  - Title: {viz.get('title', 'N/A')}")
                print(f"  - Success: {viz.get('success', False)}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
        
        print(f"\nExecution Time: {result.get('execution_time', 0):.3f}s")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()

