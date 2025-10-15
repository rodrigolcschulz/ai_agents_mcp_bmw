# 🚗 BMW Sales Analytics - AI Multi-Agent System

Sistema de análise de dados de vendas BMW com agentes de IA especializados que permitem consultas e visualizações em linguagem natural.

## 🎯 Features Principais

- 🤖 **SQL Agent**: Converte linguagem natural em SQL (OpenAI/Anthropic)
- 📊 **Visualization Agent**: Cria gráficos personalizados via texto (8+ tipos)
- 🔄 **Orchestrator Agent**: Pipeline inteligente que coordena SQL + Visualização
- 📈 **Dashboard Interativo**: Interface Streamlit moderna
- ⚡ **ETL Pipeline**: Extração automática do Kaggle e processamento
- 🗄️ **Analytics Views**: 18 KPIs pré-calculados

---

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kaggle API    │───▶│   ETL Pipeline  │───▶│   PostgreSQL    │
│  (BMW Dataset)  │    │  (50k records)  │    │  (Sales Data)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │◀───│  Orchestrator   │◀───│   SQL Agent     │
│  (Web Interface)│    │     Agent       │    │ (Text to SQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Visualization  │
                       │     Agent       │
                       │ (Text to Chart) │
                       └─────────────────┘
```

**Pipeline Multi-Agent:**
1. Usuário faz pergunta em linguagem natural
2. Orchestrator analisa intenção
3. SQL Agent gera query e busca dados
4. Visualization Agent cria gráfico apropriado
5. Interface exibe resultados

---

## 🚀 Quick Start

### 1. Pré-requisitos
```bash
- Docker & Docker Compose
- API Keys: OpenAI ou Anthropic
- Kaggle API Key
```

### 2. Configurar Ambiente
```bash
# Clone o repositório
git clone <repo>
cd ai_agents_mcp_bmw

# Configure .env com suas API keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
KAGGLE_USERNAME=seu_usuario
KAGGLE_KEY=sua_key
POSTGRES_PASSWORD=postgres123
```

### 3. Iniciar Aplicação
```bash
# Subir containers
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f app
```

### 4. Acessar
- **Interface Web**: http://localhost:8501
- **PostgreSQL**: localhost:5433
- **Database**: ai_data_engineering

---

## 💬 Exemplos de Uso

### Consultas SQL em Linguagem Natural
```
"Mostre as top 5 regiões por vendas"
"Qual a média de preços por modelo?"
"Compare vendas entre 2018 e 2020"
"Conte o total de registros"
```

### Visualizações Automáticas (Novo!)
```
"Mostre um gráfico de barras por região"
"Crie um gráfico de linha das vendas anuais"
"Faça um gráfico de pizza por tipo de combustível"
"Mostre um heatmap de correlação"
```

### Pipeline Completo
```
"Mostre um gráfico de barras das top 5 regiões por vendas"
→ Busca dados + Cria gráfico automaticamente! 🎉
```

---

## 📁 Estrutura do Projeto

```
ai_agents_mcp_bmw/
├── src/
│   ├── agents/           # AI Agents (SQL, Visualization, Orchestrator)
│   ├── etl/             # Pipeline ETL
│   ├── web/             # Interface Streamlit
│   ├── config/          # Configurações
│   └── database/        # Utilitários de banco
├── sql/                 # Scripts SQL e KPIs views
├── data/               # Dados (raw, processed)
├── logs/               # Logs da aplicação
└── docker-compose.yml  # Orquestração Docker
```

---

## 🛠️ Desenvolvimento Local

### Instalar Dependências
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Executar ETL
```bash
python src/etl/pipeline.py
```

### Criar KPI Views
```bash
python src/database/run_kpis.py
```

### Rodar Streamlit
```bash
streamlit run src/web/streamlit_app.py
```

---

## 🐳 Docker - Comandos Úteis

```bash
# Iniciar
docker-compose up -d

# Parar (MANTÉM dados)
docker-compose down

# Rebuild
docker-compose up --build -d

# Ver logs
docker-compose logs -f postgres
docker-compose logs -f app

# Executar comandos no container
docker-compose exec postgres psql -U postgres -d ai_data_engineering
```

### ⚠️ Preservar Dados do Banco

**❌ EVITE** (remove dados):
```bash
docker-compose down -v  # O -v remove volumes!
```

**✅ USE** (preserva dados):
```bash
docker-compose down     # Sem -v
docker-compose restart
```

### 🔄 Reinicializar Banco Vazio

Se você perdeu os dados:
```bash
# Rodar ETL
python src/etl/pipeline.py

# Criar views
python src/database/run_kpis.py

# Ou usar script de inicialização
python src/database/init_database.py
```

---

## 📊 KPIs e Analytics Views

O banco possui 18 views pré-calculadas no schema `analytics`:

| View | Descrição |
|------|-----------|
| `kpi_annual_sales` | Vendas por ano |
| `kpi_regional_performance` | Performance por região |
| `kpi_model_performance` | Performance por modelo |
| `kpi_top_10_models` | Top 10 modelos |
| `kpi_top_5_regions` | Top 5 regiões |
| `kpi_annual_growth` | Crescimento anual |
| `kpi_fuel_type_performance` | Performance por combustível |
| `kpi_transmission_performance` | Performance por transmissão |
| E mais 10 views... | Ver `sql/kpis_views.sql` |

**Uso:**
```sql
-- Consulta direta via SQL
SELECT * FROM analytics.kpi_regional_performance;

-- Ou via linguagem natural
"Mostre a performance por região"
```

---

## 🎨 AI Visualization Agent

### Tipos de Gráficos Suportados
- 📊 **Barras** (bar, stacked, grouped)
- 📈 **Linha** (line, area)
- 🥧 **Pizza** (pie)
- 🔵 **Dispersão** (scatter)
- 🔥 **Heatmap** (correlation)
- 📦 **Boxplot** (distribution)
- 📊 **Histograma** (histogram)
- 🎻 **Violino** (violin)

### Uso Programático
```python
from src.agents.orchestrator_agent import OrchestratorAgent

# Inicializar
orchestrator = OrchestratorAgent(ai_provider="openai")

# Pipeline completo
result = orchestrator.process_query(
    "Mostre um gráfico de barras das vendas por região"
)

if result['success']:
    sql_query = result['sql_result']['sql_query']
    chart_type = result['visualization_result']['chart_type']
    image = result['visualization_result']['image_base64']
```

---

## 🆘 Troubleshooting

### Problema: Banco vazio após rebuild
**Causa:** Você usou `docker-compose down -v`  
**Solução:**
```bash
python src/etl/pipeline.py
python src/database/run_kpis.py
```

### Problema: Views não encontradas
**Solução:**
```bash
python src/database/run_kpis.py
```

### Problema: Erro de conexão PostgreSQL
**Verificações:**
```bash
# 1. PostgreSQL está rodando?
docker ps | grep postgres

# 2. Porta 5433 livre?
netstat -an | grep 5433

# 3. Ver logs
docker-compose logs postgres
```

### Problema: Erro na API OpenAI/Anthropic
- Verificar se a chave API está correta no `.env`
- Verificar saldo/limites da conta
- Testar conexão de rede

### Problema: Erro no ETL (Kaggle)
- Verificar `KAGGLE_USERNAME` e `KAGGLE_KEY` no `.env`
- Verificar se tem acesso ao dataset BMW Sales
- Ver logs: `cat logs/etl.log`

---

## 🔐 Segurança

- ✅ Use `.env` para credenciais (nunca commite!)
- ✅ `.gitignore` já configurado para proteger dados sensíveis
- ✅ Passwords fortes em produção
- ✅ Restrinja acesso à porta 5433

---

## 📝 Tecnologias

| Categoria | Stack |
|-----------|-------|
| **Backend** | Python 3.11, FastAPI |
| **Database** | PostgreSQL 15 |
| **AI/ML** | OpenAI GPT-4, Anthropic Claude |
| **Visualization** | Seaborn, Matplotlib, Plotly |
| **Frontend** | Streamlit |
| **ETL** | Pandas, Kaggle API |
| **Infra** | Docker, Docker Compose, Nginx |

---

## 🔄 Workflow Recomendado

### Desenvolvimento Diário
1. `docker-compose up -d` - Iniciar ambiente
2. Editar código (hot reload automático)
3. `docker-compose logs -f app` - Ver logs
4. `docker-compose stop` - Parar (mantém dados)

### Atualizar Dados
1. `python src/etl/pipeline.py` - Rodar ETL
2. Verificar interface web

### Deploy/Rebuild
1. **SEMPRE** parar sem `-v`: `docker-compose down`
2. Rebuild: `docker-compose up --build -d`
3. Se perdeu dados: rodar ETL + criar views

---

## 📚 Documentação Adicional

- **Scripts SQL**: `sql/kpis_views.sql` - Todas as views de KPI
- **ETL**: `src/etl/pipeline.py` - Pipeline completo
- **Agents**: `src/agents/` - Código dos agentes especializados

---

## 📄 Licença

Apache 2.0 - Ver `LICENSE`

---

## 🎉 Próximos Passos

1. ✅ Acesse http://localhost:8501
2. 🔍 Explore o Dashboard
3. 💬 Teste consultas em linguagem natural
4. 📊 Crie visualizações personalizadas
5. 🚀 Customize para seu caso de uso!

---

**Desenvolvido com ❤️ usando AI Multi-Agent Architecture**

---
