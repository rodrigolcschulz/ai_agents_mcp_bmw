# 🤖 AI Data Engineering Project

Um projeto completo de engenharia de dados com IA que inclui ETL, banco de dados PostgreSQL, agente de IA com MCP (Model Context Protocol) e interface web com Streamlit.

## 📋 Visão Geral

Este projeto demonstra uma arquitetura moderna de engenharia de dados com IA, incluindo:

- **ETL Pipeline**: Extração de dados do Kaggle
- **Banco de Dados**: PostgreSQL com modelos otimizados
- **Agente de IA**: Geração de consultas SQL usando OpenAI e LangChain
- **MCP**: Protocolo de comunicação para o agente de IA
- **Interface Web**: Dashboard interativo com Streamlit
- **Containerização**: Docker Compose para orquestração completa

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kaggle API    │───▶│   ETL Pipeline  │───▶│   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │◀───│   AI Agent      │◀───│   MCP Handler   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Funcionalidades

### 🔄 ETL Pipeline
- Extração automática de datasets do Kaggle
- Processamento e limpeza de dados
- Validação de qualidade dos dados
- Carregamento otimizado no PostgreSQL

### 🤖 Agente de IA
- Geração de consultas SQL a partir de linguagem natural
- Integração com OpenAI GPT-3.5/4
- Protocolo MCP para comunicação
- Histórico de consultas e métricas

### 📊 Interface Web
- Dashboard interativo com Streamlit
- Visualizações automáticas de dados
- Histórico de consultas
- Estatísticas do banco de dados
- Exportação de dados e relatórios

### 🗄️ Banco de Dados
- PostgreSQL com otimizações
- Modelos de dados estruturados
- Views analíticas pré-definidas
- Funções de validação e limpeza
- Logs de consultas e métricas

## 📁 Estrutura do Projeto

```
ai_data_engineering/
├── src/
│   ├── agents/           # Agentes de IA e MCP
│   ├── config/           # Configurações do banco
│   ├── database/         # Carregamento de dados
│   ├── etl/             # Pipeline ETL
│   ├── models/          # Modelos do banco
│   └── web/             # Interface Streamlit
├── sql/                 # Scripts SQL
├── nginx/               # Configuração Nginx
├── data/                # Dados processados
├── logs/                # Logs da aplicação
├── docker-compose.yml   # Orquestração Docker
├── Dockerfile           # Imagem da aplicação
├── requirements.txt     # Dependências Python
└── README.md           # Este arquivo
```

## 🛠️ Instalação e Configuração

### Pré-requisitos

- Docker e Docker Compose
- Python 3.9+ (para desenvolvimento local)
- Conta no Kaggle com API key
- Chave da API OpenAI

### 1. Clone o repositório

```bash
git clone <repository-url>
cd ai_data_engineering
```

### 2. Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
cp env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_data_engineering
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

# Kaggle Configuration
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key

# Application Configuration
STREAMLIT_PORT=8501
DEBUG=True
```

### 3. Execute com Docker Compose

```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar status dos serviços
docker-compose ps

# Ver logs
docker-compose logs -f app
```

### 4. Acesse a aplicação

- **Interface Web**: http://localhost:8501
- **Banco de Dados**: localhost:5432
- **Nginx (opcional)**: http://localhost:80

## 🔧 Desenvolvimento Local

### Instalação das dependências

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Executar ETL

```bash
# Executar pipeline ETL
python src/etl/run_etl.py

# Ou executar componentes individuais
python src/etl/kaggle_extractor.py
python src/etl/data_processor.py
```

### Executar aplicação web

```bash
# Iniciar interface Streamlit
streamlit run src/web/streamlit_app.py
```

## 📊 Uso da Aplicação

### 1. Dashboard Principal
- Visão geral das estatísticas do banco
- Métricas de performance
- Atividade recente

### 2. Consultas com IA
- Digite perguntas em linguagem natural
- Exemplo: "Mostre as vendas totais por ano"
- O agente gera SQL automaticamente
- Visualizações automáticas dos resultados

### 3. Histórico de Consultas
- Visualize consultas anteriores
- Métricas de performance
- Exportação de dados

### 4. Estatísticas do Banco
- Informações detalhadas das tabelas
- Contagem de registros
- Estrutura dos dados

## 🔍 Exemplos de Consultas

### Consultas Básicas
```
"Mostre as vendas totais por ano"
"Quais são os top 5 modelos por vendas?"
"Compare as vendas entre diferentes regiões"
```

### Consultas Avançadas
```
"Mostre a tendência de vendas mensais para o último ano"
"Quais regiões tiveram crescimento acima de 20%?"
"Compare o desempenho dos modelos BMW vs outros"
```

## 🐳 Docker Compose

### Serviços Incluídos

- **postgres**: Banco de dados PostgreSQL
- **app**: Aplicação principal (Streamlit)
- **etl**: Serviço ETL (opcional)
- **redis**: Cache Redis (opcional)
- **nginx**: Proxy reverso (opcional)

### Comandos Úteis

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Rebuild e iniciar
docker-compose up --build -d

# Ver logs específicos
docker-compose logs -f postgres
docker-compose logs -f app

# Executar comandos no container
docker-compose exec app bash
docker-compose exec postgres psql -U postgres -d ai_data_engineering
```

## 📈 Monitoramento e Logs

### Logs da Aplicação
```bash
# Ver logs em tempo real
docker-compose logs -f app

# Logs específicos
tail -f logs/app.log
```

### Métricas do Banco
- Consultas executadas
- Tempo de execução
- Taxa de sucesso
- Uso de recursos

### Health Checks
- Banco de dados: `pg_isready`
- Aplicação: endpoint `/health`
- Nginx: endpoint `/health`

## 🔒 Segurança

### Configurações de Segurança
- Variáveis de ambiente para credenciais
- Conexões SSL/TLS (configurável)
- Validação de entrada de dados
- Logs de auditoria

### Boas Práticas
- Nunca commitar credenciais
- Usar secrets do Docker em produção
- Configurar firewall adequadamente
- Monitorar logs de segurança

## 🚀 Deploy em Produção

### 1. Configuração de Produção

```bash
# Criar arquivo de produção
cp docker-compose.yml docker-compose.prod.yml

# Configurar variáveis de ambiente
cp .env .env.prod
```

### 2. SSL/TLS
- Configurar certificados SSL
- Ativar HTTPS no Nginx
- Redirecionar HTTP para HTTPS

### 3. Monitoramento
- Configurar alertas
- Monitorar recursos
- Backup automático

## 🧪 Testes

### Testes Unitários
```bash
# Executar testes
python -m pytest tests/

# Com cobertura
python -m pytest --cov=src tests/
```

### Testes de Integração
```bash
# Testar ETL
python tests/test_etl.py

# Testar agente de IA
python tests/test_agent.py
```

## 📚 Documentação da API

### Endpoints MCP

#### Query Request
```json
{
  "id": "req_123",
  "type": "query",
  "query": "Show me sales by year",
  "context": "Focus on BMW data"
}
```

#### Schema Request
```json
{
  "id": "req_124",
  "type": "schema"
}
```

#### History Request
```json
{
  "id": "req_125",
  "type": "history",
  "limit": 10
}
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

### Problemas Comuns

#### Erro de Conexão com o Banco
```bash
# Verificar se o PostgreSQL está rodando
docker-compose ps postgres

# Verificar logs
docker-compose logs postgres
```

#### Erro da API OpenAI
- Verificar se a chave da API está correta
- Verificar limites de uso
- Verificar conectividade de rede

#### Problemas com Kaggle
- Verificar credenciais do Kaggle
- Verificar se o dataset existe
- Verificar limites de download

### Contato
- Email: [seu-email@exemplo.com]
- GitHub: [seu-usuario]
- LinkedIn: [seu-perfil]

## 🔄 Changelog

### v1.0.0
- Implementação inicial
- ETL pipeline completo
- Agente de IA com MCP
- Interface web com Streamlit
- Docker Compose
- Documentação completa

---

**Desenvolvido com ❤️ usando Python, Streamlit, PostgreSQL e OpenAI**
