"""
AI-Powered SQL Agent - Usa IA para gerar queries SQL baseadas em linguagem natural
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from dotenv import load_dotenv
import openai
from anthropic import Anthropic

load_dotenv()

logger = logging.getLogger(__name__)

class AISQLAgent:
    def __init__(self, ai_provider: str = "openai"):
        """
        Initialize AI SQL Agent
        
        Args:
            ai_provider: "openai" or "anthropic"
        """
        self.ai_provider = ai_provider
        
        # Database configuration
        self.DB_CONFIG = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'ai_data_engineering'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres123'),
            'options': '-c client_encoding=utf8'
        }
        
        # Initialize AI clients
        if ai_provider == "openai":
            self.openai_client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
        elif ai_provider == "anthropic":
            self.anthropic_client = Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
        
        # Get database schema
        self.schema = self._get_database_schema()
        
        logger.info(f"AI SQL Agent initialized with {ai_provider}")
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """Get comprehensive database schema information"""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            schema_info = {
                'tables': {},
                'views': {},
                'sample_data': {}
            }
            
            # Get all tables in public schema
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            
            tables = cursor.fetchall()
            for table in tables:
                table_name = table['table_name']
                if table_name not in schema_info['tables']:
                    schema_info['tables'][table_name] = []
                
                schema_info['tables'][table_name].append({
                    'column': table['column_name'],
                    'type': table['data_type'],
                    'nullable': table['is_nullable'] == 'YES',
                    'default': table['column_default']
                })
            
            # Get all views in analytics schema
            cursor.execute("""
                SELECT table_name as view_name
                FROM information_schema.views
                WHERE table_schema = 'analytics'
                ORDER BY table_name
            """)
            
            views = cursor.fetchall()
            for view in views:
                schema_info['views'][view['view_name']] = 'analytics view'
            
            # Get sample data from main table
            if 'bmw_sales' in schema_info['tables']:
                cursor.execute("SELECT * FROM bmw_sales LIMIT 5")
                sample_data = cursor.fetchall()
                schema_info['sample_data']['bmw_sales'] = [dict(row) for row in sample_data]
            
            cursor.close()
            conn.close()
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return {}
    
    def _generate_sql_with_ai(self, natural_query: str) -> str:
        """Generate SQL query using AI"""
        
        # Create schema context
        schema_context = self._format_schema_for_ai()
        
        if self.ai_provider == "openai":
            return self._generate_sql_openai(natural_query, schema_context)
        elif self.ai_provider == "anthropic":
            return self._generate_sql_anthropic(natural_query, schema_context)
        else:
            raise ValueError(f"Unsupported AI provider: {self.ai_provider}")
    
    def _format_schema_for_ai(self) -> str:
        """Format database schema for AI context"""
        schema_text = "DATABASE SCHEMA:\n\n"
        
        # Add tables
        schema_text += "TABLES:\n"
        for table_name, columns in self.schema.get('tables', {}).items():
            schema_text += f"\n{table_name}:\n"
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                schema_text += f"  - {col['column']}: {col['type']} {nullable}{default}\n"
        
        # Add views
        if self.schema.get('views'):
            schema_text += "\nVIEWS (analytics schema):\n"
            for view_name in self.schema['views'].keys():
                schema_text += f"  - {view_name}\n"
        
        # Add sample data
        if self.schema.get('sample_data', {}).get('bmw_sales'):
            schema_text += "\nSAMPLE DATA (bmw_sales):\n"
            sample = self.schema['sample_data']['bmw_sales'][0]
            for key, value in sample.items():
                schema_text += f"  - {key}: {value}\n"
        
        return schema_text
    
    def _generate_sql_openai(self, natural_query: str, schema_context: str) -> str:
        """Generate SQL using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert SQL developer. Generate PostgreSQL queries based on natural language requests.

{schema_context}

IMPORTANT RULES:
1. Always use proper PostgreSQL syntax
2. Use the exact table and column names from the schema
3. For analytics queries, prefer using views from the analytics schema when available
4. Format numbers with TO_CHAR for better readability when appropriate
5. Always include ORDER BY for ranking queries
6. Use LIMIT for top N queries
7. Return ONLY the SQL query, no explanations or markdown formatting
8. If the query is ambiguous, make reasonable assumptions based on the schema
9. For Portuguese queries, translate the intent to appropriate SQL operations
10. Use proper JOINs when needed
11. Handle NULL values appropriately
12. Use proper date/time functions for temporal queries

Common patterns:
- "top X" or "melhores X" → ORDER BY ... DESC LIMIT X
- "média" or "average" → AVG()
- "soma" or "total" → SUM()
- "contar" or "count" → COUNT()
- "por região" → GROUP BY region
- "por ano" → GROUP BY year
- "por modelo" → GROUP BY model
"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a PostgreSQL query for: {natural_query}"
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.startswith('```'):
                sql_query = sql_query[3:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            logger.error(f"Error generating SQL with OpenAI: {e}")
            raise
    
    def _generate_sql_anthropic(self, natural_query: str, schema_context: str) -> str:
        """Generate SQL using Anthropic Claude"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0.1,
                system=f"""You are an expert SQL developer. Generate PostgreSQL queries based on natural language requests.

{schema_context}

IMPORTANT RULES:
1. Always use proper PostgreSQL syntax
2. Use the exact table and column names from the schema
3. For analytics queries, prefer using views from the analytics schema when available
4. Format numbers with TO_CHAR for better readability when appropriate
5. Always include ORDER BY for ranking queries
6. Use LIMIT for top N queries
7. Return ONLY the SQL query, no explanations or markdown formatting
8. If the query is ambiguous, make reasonable assumptions based on the schema
9. For Portuguese queries, translate the intent to appropriate SQL operations
10. Use proper JOINs when needed
11. Handle NULL values appropriately
12. Use proper date/time functions for temporal queries

Common patterns:
- "top X" or "melhores X" → ORDER BY ... DESC LIMIT X
- "média" or "average" → AVG()
- "soma" or "total" → SUM()
- "contar" or "count" → COUNT()
- "por região" → GROUP BY region
- "por ano" → GROUP BY year
- "por modelo" → GROUP BY model
""",
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate a PostgreSQL query for: {natural_query}"
                    }
                ]
            )
            
            sql_query = response.content[0].text.strip()
            
            # Clean up the response (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.startswith('```'):
                sql_query = sql_query[3:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            logger.error(f"Error generating SQL with Anthropic: {e}")
            raise
    
    def _execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def process_query(self, natural_query: str) -> Dict[str, Any]:
        """
        Process natural language query and return results
        
        Args:
            natural_query: Natural language query
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            start_time = datetime.now()
            
            # Generate SQL using AI
            sql_query = self._generate_sql_with_ai(natural_query)
            
            # Execute the query
            results = self._execute_query(sql_query)
            
            response = {
                'success': True,
                'natural_language_query': natural_query,
                'sql_query': sql_query,
                'ai_provider': self.ai_provider,
                'results': results,
                'row_count': len(results),
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'natural_language_query': natural_query,
                'error': str(e),
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        return self.schema
    
    def explain_query(self, natural_query: str) -> str:
        """Get explanation of what the AI would do for a query"""
        try:
            sql_query = self._generate_sql_with_ai(natural_query)
            
            if self.ai_provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "Explain what this SQL query does in simple terms. Focus on the business logic and what insights it provides."
                        },
                        {
                            "role": "user",
                            "content": f"Explain this SQL query: {sql_query}"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()
            
            elif self.ai_provider == "anthropic":
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=200,
                    temperature=0.3,
                    system="Explain what this SQL query does in simple terms. Focus on the business logic and what insights it provides.",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Explain this SQL query: {sql_query}"
                        }
                    ]
                )
                return response.content[0].text.strip()
            
        except Exception as e:
            return f"Error generating explanation: {e}"

def main():
    """Test the AI SQL Agent"""
    print("=== AI SQL AGENT TEST ===")
    
    # Test with OpenAI
    print("\n--- Testing with OpenAI ---")
    agent_openai = AISQLAgent("openai")
    
    test_queries = [
        "Quais são os top 5 modelos mais vendidos?",
        "Qual a média de preços por região?",
        "Mostre o total de vendas por ano",
        "Quantos registros temos no total?",
        "Qual região tem maior faturamento?",
        "Mostre a performance dos modelos da série 3",
        "Quais cores são mais populares?",
        "Qual o crescimento de vendas entre 2018 e 2020?"
    ]
    
    for query in test_queries:
        print(f"\n--- Query: {query} ---")
        result = agent_openai.process_query(query)
        
        if result['success']:
            print(f"SQL: {result['sql_query']}")
            print(f"Results: {result['row_count']} rows")
            if result['results']:
                print("First few results:")
                for i, row in enumerate(result['results'][:3]):
                    print(f"  {i+1}: {row}")
        else:
            print(f"Error: {result['error']}")
    
    # Test with Anthropic
    print("\n--- Testing with Anthropic ---")
    agent_anthropic = AISQLAgent("anthropic")
    
    for query in test_queries[:3]:  # Test first 3 queries
        print(f"\n--- Query: {query} ---")
        result = agent_anthropic.process_query(query)
        
        if result['success']:
            print(f"SQL: {result['sql_query']}")
            print(f"Results: {result['row_count']} rows")
        else:
            print(f"Error: {result['error']}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    main()
