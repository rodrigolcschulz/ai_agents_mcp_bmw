"""
AI Agent for SQL query generation and database interaction using MCP
"""
import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

import openai
from langchain.agents import create_sql_agent, AgentExecutor
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..config.database import engine
from ..database.loader import DatabaseLoader
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLAgent:
    def __init__(self, openai_api_key: str = None):
        """
        Initialize SQL Agent with OpenAI and database connection
        
        Args:
            openai_api_key: OpenAI API key (if not provided, will use env var)
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI
        openai.api_key = self.openai_api_key
        
        # Initialize database connection
        self.db = SQLDatabase(engine)
        self.db_loader = DatabaseLoader()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model_name="gpt-4",
            temperature=0.1
        )
        
        # Initialize SQL toolkit
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # Create SQL agent
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            verbose=True,
            handle_parsing_errors=True
        )
        
        logger.info("SQL Agent initialized successfully")
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get database schema information
        
        Returns:
            Dictionary containing schema information
        """
        try:
            # Get table information
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
    
    def generate_sql_query(self, natural_language_query: str, 
                          context: str = None) -> Tuple[str, str]:
        """
        Generate SQL query from natural language
        
        Args:
            natural_language_query: Query in natural language
            context: Additional context for the query
            
        Returns:
            Tuple of (SQL query, explanation)
        """
        try:
            start_time = time.time()
            
            # Prepare the prompt with schema context
            schema_info = self.get_database_schema()
            schema_context = self._format_schema_context(schema_info)
            
            # Create system message with context
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
            
            # Generate SQL query using the agent
            response = self.agent.run(
                f"{system_message}\n\nUser Query: {natural_language_query}"
            )
            
            execution_time = time.time() - start_time
            
            # Extract SQL query and explanation from response
            sql_query, explanation = self._parse_agent_response(response)
            
            # Log the query
            self.db_loader.log_query(
                user_query=natural_language_query,
                sql_query=sql_query,
                response=explanation,
                execution_time=execution_time,
                success=True
            )
            
            return sql_query, explanation
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            
            # Log the error
            self.db_loader.log_query(
                user_query=natural_language_query,
                response=str(e),
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            
            raise
    
    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            List of dictionaries containing query results
        """
        try:
            start_time = time.time()
            
            # Execute query using database loader
            results = self.db_loader.execute_query(sql_query)
            
            execution_time = time.time() - start_time
            
            # Log the execution
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
            
            # Log the error
            self.db_loader.log_query(
                user_query=f"Execute SQL: {sql_query}",
                sql_query=sql_query,
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            
            raise
    
    def query_database(self, natural_language_query: str, 
                      context: str = None) -> Dict[str, Any]:
        """
        Complete workflow: generate SQL and execute query
        
        Args:
            natural_language_query: Query in natural language
            context: Additional context
            
        Returns:
            Dictionary containing SQL query, results, and metadata
        """
        try:
            # Generate SQL query
            sql_query, explanation = self.generate_sql_query(
                natural_language_query, context
            )
            
            # Execute query
            results = self.execute_query(sql_query)
            
            return {
                'natural_language_query': natural_language_query,
                'sql_query': sql_query,
                'explanation': explanation,
                'results': results,
                'row_count': len(results),
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
        # This is a simplified parser - in practice, you might need more sophisticated parsing
        lines = response.split('\n')
        sql_query = ""
        explanation = response
        
        # Look for SQL query markers
        for i, line in enumerate(lines):
            if 'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper() or 'DELETE' in line.upper():
                # Found SQL query
                sql_query = line.strip()
                # Remove the SQL from explanation
                explanation = '\n'.join(lines[:i] + lines[i+1:]).strip()
                break
        
        return sql_query, explanation
    
    def get_query_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent query history"""
        try:
            # This would query the QueryLog table
            query = f"""
            SELECT user_query, sql_query, response, execution_time, success, created_at
            FROM query_logs
            ORDER BY created_at DESC
            LIMIT {limit}
            """
            
            results = self.db_loader.execute_query(query)
            return results
            
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = self.db_loader.get_database_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

def main():
    """Example usage"""
    try:
        # Initialize agent
        agent = SQLAgent()
        
        # Get database schema
        schema = agent.get_database_schema()
        print("Database Schema:")
        print(json.dumps(schema, indent=2))
        
        # Example query
        result = agent.query_database("Show me the total sales by year")
        print("\nQuery Result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
