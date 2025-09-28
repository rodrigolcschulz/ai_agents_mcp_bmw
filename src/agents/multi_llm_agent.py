"""
Multi-LLM Agent supporting OpenAI, Anthropic Claude, and Hugging Face models
"""
import os
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import time

import openai
from langchain.agents import create_sql_agent, AgentExecutor
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from anthropic import Anthropic
from huggingface_hub import InferenceClient

from ..config.database import engine
from ..database.loader import DatabaseLoader
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiLLMAgent:
    def __init__(self, 
                 openai_api_key: str = None,
                 anthropic_api_key: str = None,
                 huggingface_token: str = None,
                 default_provider: str = "openai"):
        """
        Initialize Multi-LLM Agent with support for multiple providers
        
        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            huggingface_token: Hugging Face token
            default_provider: Default provider to use ("openai", "anthropic", "huggingface")
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.huggingface_token = huggingface_token or os.getenv('HUGGINGFACE_API_TOKEN')
        self.default_provider = default_provider
        
        # Initialize database connection
        self.db = SQLDatabase(engine)
        self.db_loader = DatabaseLoader()
        
        # Initialize providers
        self._initialize_providers()
        
        # Initialize LLM based on default provider
        self.llm = self._get_llm(default_provider)
        
        # Initialize SQL toolkit
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # Create SQL agent
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            handle_parsing_errors=True
        )
        
        logger.info(f"Multi-LLM Agent initialized with default provider: {default_provider}")
    
    def _initialize_providers(self):
        """Initialize all available providers"""
        # OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.openai_available = True
        else:
            self.openai_available = False
        
        # Anthropic
        if self.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
            self.anthropic_available = True
        else:
            self.anthropic_available = False
        
        # Hugging Face
        if self.huggingface_token:
            self.hf_client = InferenceClient(token=self.huggingface_token)
            self.huggingface_available = True
        else:
            self.huggingface_available = False
    
    def _get_llm(self, provider: str):
        """Get LLM instance for the specified provider"""
        if provider == "openai" and self.openai_available:
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model_name="gpt-4",
                temperature=0.1
            )
        elif provider == "anthropic" and self.anthropic_available:
            # For now, use OpenAI as fallback since LangChain doesn't have direct Anthropic support
            # In a real implementation, you'd create a custom LLM wrapper
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model_name="gpt-4",
                temperature=0.1
            )
        else:
            # Fallback to OpenAI
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model_name="gpt-4",
                temperature=0.1
            )
    
    def switch_provider(self, provider: str):
        """Switch to a different LLM provider"""
        if provider in ["openai", "anthropic", "huggingface"]:
            self.default_provider = provider
            self.llm = self._get_llm(provider)
            self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            self.agent = create_sql_agent(
                llm=self.llm,
                toolkit=self.toolkit,
                verbose=True,
                handle_parsing_errors=True
            )
            logger.info(f"Switched to provider: {provider}")
        else:
            logger.error(f"Invalid provider: {provider}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        providers = []
        if self.openai_available:
            providers.append("openai")
        if self.anthropic_available:
            providers.append("anthropic")
        if self.huggingface_available:
            providers.append("huggingface")
        return providers
    
    def generate_sql_with_provider(self, 
                                 natural_language_query: str,
                                 provider: str = None,
                                 context: str = None) -> Tuple[str, str, str]:
        """
        Generate SQL query using specified provider
        
        Args:
            natural_language_query: Query in natural language
            provider: Provider to use (if None, uses default)
            context: Additional context
            
        Returns:
            Tuple of (SQL query, explanation, provider_used)
        """
        provider = provider or self.default_provider
        
        try:
            start_time = time.time()
            
            if provider == "openai" and self.openai_available:
                sql_query, explanation = self._generate_with_openai(natural_language_query, context)
            elif provider == "anthropic" and self.anthropic_available:
                sql_query, explanation = self._generate_with_anthropic(natural_language_query, context)
            elif provider == "huggingface" and self.huggingface_available:
                sql_query, explanation = self._generate_with_huggingface(natural_language_query, context)
            else:
                # Fallback to OpenAI
                sql_query, explanation = self._generate_with_openai(natural_language_query, context)
                provider = "openai"
            
            execution_time = time.time() - start_time
            
            # Log the query
            self.db_loader.log_query(
                user_query=natural_language_query,
                sql_query=sql_query,
                response=explanation,
                execution_time=execution_time,
                success=True
            )
            
            return sql_query, explanation, provider
            
        except Exception as e:
            logger.error(f"Error generating SQL with {provider}: {e}")
            
            # Log the error
            self.db_loader.log_query(
                user_query=natural_language_query,
                response=str(e),
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            
            raise
    
    def _generate_with_openai(self, query: str, context: str = None) -> Tuple[str, str]:
        """Generate SQL using OpenAI"""
        schema_info = self.get_database_schema()
        schema_context = self._format_schema_context(schema_info)
        
        system_message = f"""
        You are an expert SQL query generator. You have access to a PostgreSQL database with the following schema:
        
        {schema_context}
        
        Generate accurate SQL queries based on natural language requests. Always:
        1. Use proper SQL syntax for PostgreSQL
        2. Include appropriate WHERE clauses for filtering
        3. Use proper JOINs when needed
        4. Include LIMIT clauses for large result sets
        5. Provide clear explanations of your queries
        
        Context: {context or 'No additional context provided'}
        """
        
        response = self.agent.run(f"{system_message}\n\nUser Query: {query}")
        sql_query, explanation = self._parse_agent_response(response)
        
        return sql_query, explanation
    
    def _generate_with_anthropic(self, query: str, context: str = None) -> Tuple[str, str]:
        """Generate SQL using Anthropic Claude"""
        schema_info = self.get_database_schema()
        schema_context = self._format_schema_context(schema_info)
        
        prompt = f"""
        You are an expert SQL query generator. You have access to a PostgreSQL database with the following schema:
        
        {schema_context}
        
        Generate accurate SQL queries based on natural language requests. Always:
        1. Use proper SQL syntax for PostgreSQL
        2. Include appropriate WHERE clauses for filtering
        3. Use proper JOINs when needed
        4. Include LIMIT clauses for large result sets
        5. Provide clear explanations of your queries
        
        Context: {context or 'No additional context provided'}
        
        User Query: {query}
        
        Please provide:
        1. The SQL query
        2. A clear explanation of what the query does
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            sql_query, explanation = self._parse_anthropic_response(content)
            
            return sql_query, explanation
            
        except Exception as e:
            logger.error(f"Error with Anthropic: {e}")
            # Fallback to OpenAI
            return self._generate_with_openai(query, context)
    
    def _generate_with_huggingface(self, query: str, context: str = None) -> Tuple[str, str]:
        """Generate SQL using Hugging Face models"""
        # For now, fallback to OpenAI since HF models need more setup
        # In a real implementation, you'd use a fine-tuned model for SQL generation
        logger.info("Hugging Face SQL generation not yet implemented, falling back to OpenAI")
        return self._generate_with_openai(query, context)
    
    def _parse_anthropic_response(self, response: str) -> Tuple[str, str]:
        """Parse Anthropic response to extract SQL and explanation"""
        lines = response.split('\n')
        sql_query = ""
        explanation = response
        
        # Look for SQL query markers
        for i, line in enumerate(lines):
            if 'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper() or 'DELETE' in line.upper():
                sql_query = line.strip()
                explanation = '\n'.join(lines[:i] + lines[i+1:]).strip()
                break
        
        return sql_query, explanation
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            tables_info = {}
            tables = self.db.get_usable_table_names()
            
            for table in tables:
                table_info = self.db_loader.get_table_info(table)
                if table_info:
                    tables_info[table] = table_info
            
            return {
                'tables': tables_info,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return {}
    
    def _format_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for the AI agent"""
        context = "Database Schema:\n\n"
        
        for table_name, table_info in schema_info.get('tables', {}).items():
            context += f"Table: {table_name}\n"
            context += f"  Rows: {table_info.get('row_count', 0)}\n"
            context += "  Columns:\n"
            
            for column in table_info.get('columns', []):
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                default = f" DEFAULT {column['default']}" if column['default'] else ""
                context += f"    - {column['name']} ({column['type']}) {nullable}{default}\n"
            
            context += "\n"
        
        return context
    
    def _parse_agent_response(self, response: str) -> Tuple[str, str]:
        """Parse agent response to extract SQL query and explanation"""
        lines = response.split('\n')
        sql_query = ""
        explanation = response
        
        for i, line in enumerate(lines):
            if 'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper() or 'DELETE' in line.upper():
                sql_query = line.strip()
                explanation = '\n'.join(lines[:i] + lines[i+1:]).strip()
                break
        
        return sql_query, explanation
    
    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            start_time = time.time()
            results = self.db_loader.execute_query(sql_query)
            execution_time = time.time() - start_time
            
            self.db_loader.log_query(
                user_query=f"Execute SQL: {sql_query}",
                sql_query=sql_query,
                response=f"Returned {len(results)} rows",
                execution_time=execution_time,
                success=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            
            self.db_loader.log_query(
                user_query=f"Execute SQL: {sql_query}",
                sql_query=sql_query,
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            
            raise
    
    def query_database(self, 
                      natural_language_query: str,
                      provider: str = None,
                      context: str = None) -> Dict[str, Any]:
        """Complete workflow: generate SQL and execute query"""
        try:
            # Generate SQL query
            sql_query, explanation, provider_used = self.generate_sql_with_provider(
                natural_language_query, provider, context
            )
            
            # Execute query
            results = self.execute_query(sql_query)
            
            return {
                'natural_language_query': natural_language_query,
                'sql_query': sql_query,
                'explanation': explanation,
                'results': results,
                'row_count': len(results),
                'provider_used': provider_used,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in query_database: {e}")
            return {
                'natural_language_query': natural_language_query,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Example usage"""
    try:
        # Initialize multi-LLM agent
        agent = MultiLLMAgent()
        
        # Get available providers
        providers = agent.get_available_providers()
        print(f"Available providers: {providers}")
        
        # Test with different providers
        for provider in providers:
            print(f"\nTesting with {provider}...")
            result = agent.query_database("Show me the total sales by year", provider=provider)
            print(f"Provider: {result.get('provider_used')}")
            print(f"Success: {result.get('success')}")
            if result.get('success'):
                print(f"SQL: {result.get('sql_query')}")
                print(f"Rows: {result.get('row_count')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
