"""
MCP (Model Context Protocol) handler for AI agent communication
"""
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime

from .sql_agent import SQLAgent

logger = logging.getLogger(__name__)

class MCPHandler:
    def __init__(self, sql_agent: SQLAgent):
        """
        Initialize MCP handler
        
        Args:
            sql_agent: Initialized SQL agent instance
        """
        self.sql_agent = sql_agent
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history = []
        
        logger.info(f"MCP Handler initialized with session ID: {self.session_id}")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP request
        
        Args:
            request: MCP request dictionary
            
        Returns:
            MCP response dictionary
        """
        try:
            request_type = request.get('type', 'unknown')
            request_id = request.get('id', 'unknown')
            
            logger.info(f"Handling MCP request: {request_type} (ID: {request_id})")
            
            # Route request based on type
            if request_type == 'query':
                response = await self._handle_query_request(request)
            elif request_type == 'schema':
                response = await self._handle_schema_request(request)
            elif request_type == 'history':
                response = await self._handle_history_request(request)
            elif request_type == 'stats':
                response = await self._handle_stats_request(request)
            else:
                response = self._create_error_response(
                    request_id, f"Unknown request type: {request_type}"
                )
            
            # Add to conversation history
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'request': request,
                'response': response
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return self._create_error_response(
                request.get('id', 'unknown'), str(e)
            )
    
    async def _handle_query_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database query request"""
        request_id = request.get('id')
        query = request.get('query', '')
        context = request.get('context', '')
        
        if not query:
            return self._create_error_response(request_id, "No query provided")
        
        try:
            # Process query using SQL agent
            result = self.sql_agent.query_database(query, context)
            
            return {
                'id': request_id,
                'type': 'query_response',
                'success': result.get('success', False),
                'data': {
                    'natural_language_query': result.get('natural_language_query'),
                    'sql_query': result.get('sql_query'),
                    'explanation': result.get('explanation'),
                    'results': result.get('results', []),
                    'row_count': result.get('row_count', 0),
                    'timestamp': result.get('timestamp')
                },
                'error': result.get('error') if not result.get('success') else None
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._create_error_response(request_id, str(e))
    
    async def _handle_schema_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database schema request"""
        request_id = request.get('id')
        
        try:
            schema = self.sql_agent.get_database_schema()
            
            return {
                'id': request_id,
                'type': 'schema_response',
                'success': True,
                'data': schema,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return self._create_error_response(request_id, str(e))
    
    async def _handle_history_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle query history request"""
        request_id = request.get('id')
        limit = request.get('limit', 10)
        
        try:
            history = self.sql_agent.get_query_history(limit)
            
            return {
                'id': request_id,
                'type': 'history_response',
                'success': True,
                'data': {
                    'queries': history,
                    'total_count': len(history)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return self._create_error_response(request_id, str(e))
    
    async def _handle_stats_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle database statistics request"""
        request_id = request.get('id')
        
        try:
            stats = self.sql_agent.get_database_stats()
            
            return {
                'id': request_id,
                'type': 'stats_response',
                'success': True,
                'data': stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return self._create_error_response(request_id, str(e))
    
    def _create_error_response(self, request_id: str, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'id': request_id,
            'type': 'error_response',
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def export_conversation(self, file_path: str):
        """Export conversation history to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': self.session_id,
                    'exported_at': datetime.now().isoformat(),
                    'conversation': self.conversation_history
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversation exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting conversation: {e}")
            raise

class MCPClient:
    """MCP Client for testing and interaction"""
    
    def __init__(self, mcp_handler: MCPHandler):
        self.mcp_handler = mcp_handler
    
    async def send_query(self, query: str, context: str = None) -> Dict[str, Any]:
        """Send a query request"""
        request = {
            'id': f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'type': 'query',
            'query': query,
            'context': context
        }
        
        return await self.mcp_handler.handle_request(request)
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema"""
        request = {
            'id': f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'type': 'schema'
        }
        
        return await self.mcp_handler.handle_request(request)
    
    async def get_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get query history"""
        request = {
            'id': f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'type': 'history',
            'limit': limit
        }
        
        return await self.mcp_handler.handle_request(request)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        request = {
            'id': f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'type': 'stats'
        }
        
        return await self.mcp_handler.handle_request(request)

def main():
    """Example usage"""
    async def test_mcp():
        # Initialize SQL agent
        sql_agent = SQLAgent()
        
        # Initialize MCP handler
        mcp_handler = MCPHandler(sql_agent)
        
        # Initialize MCP client
        client = MCPClient(mcp_handler)
        
        # Test schema request
        print("Getting database schema...")
        schema_response = await client.get_schema()
        print(f"Schema response: {json.dumps(schema_response, indent=2)}")
        
        # Test query request
        print("\nSending query...")
        query_response = await client.send_query("Show me the total sales by year")
        print(f"Query response: {json.dumps(query_response, indent=2)}")
        
        # Test stats request
        print("\nGetting database stats...")
        stats_response = await client.get_stats()
        print(f"Stats response: {json.dumps(stats_response, indent=2)}")
    
    # Run the test
    asyncio.run(test_mcp())

if __name__ == "__main__":
    main()
