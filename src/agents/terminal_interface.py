1"""
Terminal Interface for AI SQL Agent
"""
import os
import sys
from typing import Optional
from ai_sql_agent import AISQLAgent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerminalInterface:
    def __init__(self, ai_provider: str = "openai"):
        """Initialize terminal interface"""
        self.agent = AISQLAgent(ai_provider)
        self.ai_provider = ai_provider
        
    def print_banner(self):
        """Print welcome banner"""
        print("=" * 60)
        print("🤖 AI SQL AGENT - Terminal Interface")
        print("=" * 60)
        print(f"Provider: {self.ai_provider.upper()}")
        print("Digite suas consultas em linguagem natural!")
        print("Comandos especiais:")
        print("  /help     - Mostrar ajuda")
        print("  /schema   - Mostrar schema do banco")
        print("  /explain  - Explicar última consulta")
        print("  /switch   - Trocar provider (openai/anthropic)")
        print("  /quit     - Sair")
        print("=" * 60)
    
    def print_help(self):
        """Print help information"""
        print("\n📚 AJUDA - AI SQL AGENT")
        print("-" * 40)
        print("Exemplos de consultas:")
        print("• Quais são os top 5 modelos mais vendidos?")
        print("• Qual a média de preços por região?")
        print("• Mostre o total de vendas por ano")
        print("• Quantos registros temos no total?")
        print("• Qual região tem maior faturamento?")
        print("• Mostre a performance dos modelos da série 3")
        print("• Quais cores são mais populares?")
        print("• Qual o crescimento de vendas entre 2018 e 2020?")
        print("• Análise de preços por segmento")
        print("• Modelos mais eficientes")
        print("• Tendências temporais")
        print("\nComandos especiais:")
        print("• /help     - Mostrar esta ajuda")
        print("• /schema   - Mostrar schema do banco")
        print("• /explain  - Explicar última consulta")
        print("• /switch   - Trocar provider")
        print("• /quit     - Sair")
        print("-" * 40)
    
    def print_schema(self):
        """Print database schema"""
        print("\n🗄️  SCHEMA DO BANCO DE DADOS")
        print("-" * 40)
        
        schema = self.agent.get_schema_info()
        
        # Print tables
        if schema.get('tables'):
            print("TABELAS:")
            for table_name, columns in schema['tables'].items():
                print(f"\n📋 {table_name}:")
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"  • {col['column']}: {col['type']} {nullable}")
        
        # Print views
        if schema.get('views'):
            print(f"\n📊 VIEWS (analytics):")
            for view_name in schema['views'].keys():
                print(f"  • {view_name}")
        
        # Print sample data
        if schema.get('sample_data', {}).get('bmw_sales'):
            print(f"\n📝 DADOS DE EXEMPLO (bmw_sales):")
            sample = schema['sample_data']['bmw_sales'][0]
            for key, value in sample.items():
                print(f"  • {key}: {value}")
        
        print("-" * 40)
    
    def print_results(self, result: dict):
        """Print query results in a formatted way"""
        if result['success']:
            print(f"\n✅ SUCESSO ({result['execution_time']:.2f}s)")
            print(f"🔍 SQL: {result['sql_query']}")
            print(f"📊 Resultados: {result['row_count']} registros")
            
            if result['results']:
                print("\n📋 DADOS:")
                for i, row in enumerate(result['results'][:10]):  # Show max 10 rows
                    print(f"  {i+1:2d}: {row}")
                
                if result['row_count'] > 10:
                    print(f"  ... e mais {result['row_count'] - 10} registros")
            else:
                print("  (Nenhum resultado encontrado)")
        else:
            print(f"\n❌ ERRO ({result['execution_time']:.2f}s)")
            print(f"💥 {result['error']}")
    
    def switch_provider(self):
        """Switch AI provider"""
        print("\n🔄 TROCAR PROVIDER")
        print("-" * 20)
        print("Providers disponíveis:")
        print("1. openai (GPT-4)")
        print("2. anthropic (Claude)")
        
        while True:
            choice = input("\nEscolha (1-2): ").strip()
            if choice == "1":
                self.ai_provider = "openai"
                break
            elif choice == "2":
                self.ai_provider = "anthropic"
                break
            else:
                print("Opção inválida. Digite 1 ou 2.")
        
        self.agent = AISQLAgent(self.ai_provider)
        print(f"✅ Provider alterado para: {self.ai_provider.upper()}")
    
    def explain_last_query(self, last_query: Optional[str]):
        """Explain the last query"""
        if not last_query:
            print("\n❌ Nenhuma consulta anterior para explicar.")
            return
        
        print(f"\n🧠 EXPLICANDO: {last_query}")
        print("-" * 40)
        
        try:
            explanation = self.agent.explain_query(last_query)
            print(explanation)
        except Exception as e:
            print(f"❌ Erro ao explicar: {e}")
        
        print("-" * 40)
    
    def run(self):
        """Run the terminal interface"""
        self.print_banner()
        
        last_query = None
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n[{self.ai_provider.upper()}] > ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command == '/quit':
                        print("\n👋 Até logo!")
                        break
                    elif command == '/help':
                        self.print_help()
                    elif command == '/schema':
                        self.print_schema()
                    elif command == '/explain':
                        self.explain_last_query(last_query)
                    elif command == '/switch':
                        self.switch_provider()
                    else:
                        print(f"❌ Comando desconhecido: {command}")
                        print("Digite /help para ver os comandos disponíveis.")
                    
                    continue
                
                # Process natural language query
                print(f"\n🔄 Processando: {user_input}")
                result = self.agent.process_query(user_input)
                
                # Print results
                self.print_results(result)
                
                # Store for explanation
                if result['success']:
                    last_query = user_input
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrompido pelo usuário. Até logo!")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                logger.error(f"Unexpected error: {e}")

def main():
    """Main function"""
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado!")
        print("Crie um arquivo .env com as chaves de API necessárias.")
        sys.exit(1)
    
    # Choose AI provider
    print("🤖 AI SQL AGENT - Terminal Interface")
    print("=" * 40)
    print("Escolha o provider de IA:")
    print("1. OpenAI (GPT-4)")
    print("2. Anthropic (Claude)")
    
    while True:
        choice = input("\nEscolha (1-2): ").strip()
        if choice == "1":
            provider = "openai"
            break
        elif choice == "2":
            provider = "anthropic"
            break
        else:
            print("Opção inválida. Digite 1 ou 2.")
    
    # Start interface
    interface = TerminalInterface(provider)
    interface.run()

if __name__ == "__main__":
    main()
