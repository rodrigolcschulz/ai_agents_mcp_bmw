#!/usr/bin/env python3
"""
Teste do MCP Agent - Consultas em Linguagem Natural
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import directly to avoid langchain dependencies
import importlib.util
spec = importlib.util.spec_from_file_location("mcp_agent_simple", os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'mcp_agent_simple.py'))
mcp_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_agent_module)
MCPAgent = mcp_agent_module.MCPAgent

import json

def test_mcp_agent():
    """Testar o MCP Agent"""
    print("=== TESTE DO MCP AGENT ===")
    
    # Inicializar agente
    agent = MCPAgent()
    
    # Lista de consultas de teste
    test_queries = [
        "Mostre o dashboard executivo",
        "Quais são as top 5 regiões?",
        "Quais são os top 10 modelos?",
        "Mostre as vendas anuais",
        "Qual a performance por região?",
        "Conte o total de registros",
        "Qual a média de preços?",
        "Soma total de vendas",
        "Mostre as tendências mensais",
        "Qual o crescimento anual?"
    ]
    
    print(f"\nTestando {len(test_queries)} consultas...")
    
    successful_queries = 0
    failed_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Teste {i}: {query} ---")
        
        try:
            result = agent.process_natural_language_query(query)
            
            if result['success']:
                successful_queries += 1
                print(f"SUCESSO")
                print(f"   SQL: {result['sql_query']}")
                print(f"   Tipo: {result['query_type']}")
                print(f"   Resultados: {result['row_count']} registros")
                print(f"   Tempo: {result['execution_time']:.3f}s")
                
                # Mostrar primeiros resultados
                if result['results']:
                    print("   Primeiros resultados:")
                    for j, row in enumerate(result['results'][:2]):
                        print(f"     {j+1}: {row}")
            else:
                failed_queries += 1
                print(f"FALHOU")
                print(f"   Erro: {result['error']}")
                if 'suggestions' in result:
                    print("   Sugestões:")
                    for suggestion in result['suggestions'][:2]:
                        print(f"     - {suggestion}")
                        
        except Exception as e:
            failed_queries += 1
            print(f"ERRO: {e}")
    
    # Resumo dos testes
    print(f"\n=== RESUMO DOS TESTES ===")
    print(f"Total de consultas: {len(test_queries)}")
    print(f"Sucessos: {successful_queries}")
    print(f"Falhas: {failed_queries}")
    print(f"Taxa de sucesso: {(successful_queries/len(test_queries)*100):.1f}%")
    
    # Mostrar consultas disponíveis
    print(f"\n=== CONSULTAS DISPONÍVEIS ===")
    available_queries = agent.get_available_queries()
    for query_type, description in available_queries.items():
        print(f"  {query_type}: {description}")
    
    # Mostrar schema
    print(f"\n=== SCHEMA DO BANCO ===")
    schema = agent.get_database_schema()
    if schema:
        print("Tabelas:")
        for table_name, columns in schema.get('tables', {}).items():
            print(f"  {table_name}: {len(columns)} colunas")
        
        print("Views:")
        for schema_name, views in schema.get('views', {}).items():
            print(f"  {schema_name}: {len(views)} views")

def interactive_mode():
    """Modo interativo para testar consultas"""
    print("\n=== MODO INTERATIVO ===")
    print("Digite suas consultas em linguagem natural (ou 'sair' para encerrar)")
    
    agent = MCPAgent()
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print("Encerrando...")
                break
            
            if not query:
                continue
            
            result = agent.process_natural_language_query(query)
            
            if result['success']:
                print(f"OK {result['query_type']}")
                print(f"SQL: {result['sql_query']}")
                print(f"Resultados: {result['row_count']} registros")
                
                if result['results']:
                    print("Resultados:")
                    for i, row in enumerate(result['results'][:5]):
                        print(f"  {i+1}: {row}")
            else:
                print(f"ERRO {result['error']}")
                if 'suggestions' in result:
                    print("Sugestões:")
                    for suggestion in result['suggestions'][:3]:
                        print(f"  - {suggestion}")
                        
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"Erro: {e}")

def main():
    """Função principal"""
    print("MCP Agent - Teste de Consultas em Linguagem Natural")
    
    # Teste automático
    test_mcp_agent()
    
    # Perguntar se quer modo interativo
    try:
        response = input("\nDeseja entrar no modo interativo? (s/n): ").strip().lower()
        if response in ['s', 'sim', 'y', 'yes']:
            interactive_mode()
    except KeyboardInterrupt:
        print("\nEncerrando...")

if __name__ == "__main__":
    main()
