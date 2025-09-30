# 🚗 BMW Sales Analytics - MCP Agent

Um projeto completo de análise de dados de vendas da BMW com agente de IA que permite consultas em linguagem natural através de uma interface web moderna.

## 📋 Visão Geral

Este projeto demonstra uma arquitetura moderna de análise de dados com IA, incluindo:

- **ETL Pipeline**: Extração de dados do Kaggle (BMW Sales Dataset)
- **Banco de Dados**: PostgreSQL com 50.000 registros de vendas
- **Agente MCP**: Consultas em linguagem natural com padrões de reconhecimento aprimorados
- **Interface Web**: Dashboard interativo com Streamlit
- **Visualizações**: Gráficos automáticos baseados nas consultas
- **Containerização**: Docker Compose para orquestração completa

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kaggle API    │───▶│   ETL Pipeline  │───▶│   PostgreSQL    │
│  (BMW Dataset)  │    │  (50k records)  │    │  (Sales Data)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │◀───│   MCP Agent     │◀───│   KPI Views     │
│  (Web Interface)│    │ (Natural Lang)  │    │  (Analytics)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Funcionalidades

### 🔄 ETL Pipeline
- Extração automática do dataset BMW Sales do Kaggle
- Processamento e limpeza de 50.000 registros
- Validação de qualidade dos dados
- Carregamento otimizado no PostgreSQL

### 🤖 Agente MCP (Model Context Protocol)
- Consultas em linguagem natural (português/inglês)
- Padrões de reconhecimento aprimorados
- Sistema de confiança (0.0 - 1.0)
- 10 consultas predefinidas + consultas customizadas
- Geração automática de SQL

### 📊 Interface Web Streamlit
- Dashboard interativo com visualizações automáticas
- Consultas em linguagem natural
- Gráficos dinâmicos (barras, linhas, pizza)
- Score de confiança das consultas
- Schema do banco de dados
- Exemplos de consultas

### 🗄️ Banco de Dados
- PostgreSQL com 50.000 registros de vendas BMW
- 19 colunas: região, modelo, vendas, receita, preço, etc.
- 10 views de KPIs pré-definidas
- Schema analytics para relatórios
- Otimizações de performance

## 📁 Estrutura do Projeto

```
ai_agents/
├── src/
│   ├── agents/           # Agente MCP
│   ├── config/           # Configurações do banco
│   ├── etl/             # Pipeline ETL
│   └── web/             # Interface Streamlit
├── sql/                 # Scripts SQL e views de KPIs
├── tests/               # Testes automatizados
├── logs/                # Logs do sistema
├── notebooks/           # Jupyter notebooks
├── docker-compose.yml   # Orquestração Docker
├── Dockerfile          # Imagem da aplicação
├── requirements.txt    # Dependências Python
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

### 2. Consultas com IA Multi-LLM
- Digite perguntas em linguagem natural
- Escolha entre diferentes provedores de IA:
  - **OpenAI GPT-4**: Para consultas rápidas e precisas
  - **Anthropic Claude**: Para raciocínio complexo
  - **Hugging Face**: Para modelos open source
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
- **etl**: Serviço ETL (opcional, usa o mesmo Dockerfile)
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

# Executar ETL
docker-compose run --rm etl

# Ver logs específicos
docker-compose logs -f postgres
docker-compose logs -f app

# Executar comandos no container
docker-compose exec app bash
docker-compose exec postgres psql -U postgres -d ai_data_engineering
```

## 💬 Exemplos de Consultas

O agente MCP entende consultas em português e inglês. Aqui estão alguns exemplos:

### 📊 Consultas de Dashboard
- "Mostre o dashboard executivo"
- "Quais são as métricas principais?"
- "Exiba um resumo geral"

### 🌍 Consultas Regionais
- "Quais são as top 5 regiões?"
- "Mostre a performance por região"
- "Qual região tem maior faturamento?"

### 🚗 Consultas de Modelos
- "Quais são os top 10 modelos?"
- "Mostre a performance por modelo"
- "Qual modelo é mais vendido?"

### 📈 Consultas Temporais
- "Mostre as vendas anuais"
- "Exiba as tendências mensais"
- "Qual o crescimento anual?"

### 🔢 Consultas Numéricas
- "Conte o total de registros"
- "Qual a média de preços?"
- "Soma total de vendas"
- "Qual o preço máximo/mínimo?"

### ⚡ Consultas de Performance
- "Mostre a performance por combustível"
- "Exiba a performance por transmissão"
- "Qual o ranking de modelos?"

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
- Agente de IA Multi-LLM com MCP
- Suporte para OpenAI, Anthropic e Hugging Face
- Interface web com Streamlit
- Docker Compose
- Documentação completa

---

**Desenvolvido com ❤️ usando Python, Streamlit, PostgreSQL e OpenAI**
