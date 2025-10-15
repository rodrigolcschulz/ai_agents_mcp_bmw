"""
Streamlit Web Interface for Natural Language SQL Agent - BMW Sales Analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
import os
from datetime import datetime
import importlib.util

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import Natural Language SQL Agent
spec = importlib.util.spec_from_file_location("mcp_agent", os.path.join(os.path.dirname(__file__), '..', 'agents', 'mcp_agent.py'))
mcp_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_agent_module)
NaturalLanguageSQLAgent = mcp_agent_module.NaturalLanguageSQLAgent

# Import Orchestrator Agent (includes SQL + Visualization)
spec_orch = importlib.util.spec_from_file_location("orchestrator_agent", os.path.join(os.path.dirname(__file__), '..', 'agents', 'orchestrator_agent.py'))
orchestrator_module = importlib.util.module_from_spec(spec_orch)
spec_orch.loader.exec_module(orchestrator_module)
OrchestratorAgent = orchestrator_module.OrchestratorAgent

# Import database config
from config.database import test_connection

# Page configuration
st.set_page_config(
    page_title="BMW Sales Analytics - Natural Language SQL Agent",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .query-result {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_sql_agent():
    """Initialize Natural Language SQL Agent"""
    try:
        # Initialize agent
        agent = NaturalLanguageSQLAgent()
        
        # Test if agent can connect to database
        try:
            result = agent.process_natural_language_query("Mostre o dashboard executivo")
            if not result['success']:
                st.error("❌ Natural Language SQL Agent initialized but database connection failed")
                return None
        except Exception as db_error:
            st.error(f"❌ Database connection test failed: {db_error}")
            return None
        
        return agent
        
    except Exception as e:
        st.error(f"❌ Error initializing Natural Language SQL Agent: {e}")
        return None

@st.cache_resource
def initialize_orchestrator_agent():
    """Initialize Orchestrator Agent (SQL + Visualization)"""
    try:
        # Get AI provider from session state or default to OpenAI
        ai_provider = st.session_state.get('ai_provider', 'openai')
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent(ai_provider=ai_provider)
        
        return orchestrator
        
    except Exception as e:
        st.error(f"❌ Error initializing Orchestrator Agent: {e}")
        return None

def get_confidence_color(confidence):
    """Get color based on confidence score"""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"


def display_query_result(result, query, agent=None):
    """Display query result with formatting and automatic chart generation"""
    if result['success']:
        st.markdown(f'<div class="success-message">✅ Query executed successfully!</div>', unsafe_allow_html=True)
        
        # Display confidence
        confidence = result.get('confidence', 0)
        confidence_class = get_confidence_color(confidence)
        st.markdown(f'<p><strong>Confidence:</strong> <span class="{confidence_class}">{confidence:.2f}</span></p>', unsafe_allow_html=True)
        
        # Display SQL query
        st.subheader("🔍 Generated SQL Query")
        st.code(result['sql_query'], language='sql')
        
        # Display explanation
        if result.get('explanation'):
            st.subheader("💡 Explanation")
            st.info(result['explanation'])
        
        # Display results
        if result.get('results'):
            st.subheader("📊 Results")
            results_df = pd.DataFrame(result['results'])
            
            # Format numeric columns with thousand separators
            formatted_df = results_df.copy()
            for col in formatted_df.columns:
                if formatted_df[col].dtype in ['int64', 'float64']:
                    # Check if column contains large numbers that would benefit from formatting
                    if formatted_df[col].max() > 1000:
                        formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x == int(x) else f"{x:,.2f}" if pd.notna(x) else x)
            
            st.dataframe(formatted_df, use_container_width=True)
            
        
        # Display metadata
        st.subheader("ℹ️ Query Information")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows Returned", result.get('row_count', 0))
        with col2:
            st.metric("Query Type", result.get('query_type', 'Unknown'))
        with col3:
            st.metric("Execution Time", f"{result.get('execution_time', 0):.3f}s")
        with col4:
            st.metric("Status", "Success")
    
    else:
        st.markdown(f'<div class="error-message">❌ Query failed: {result.get("error", "Unknown error")}</div>', unsafe_allow_html=True)
        
        if 'suggestions' in result:
            st.subheader("💡 Suggestions")
            for suggestion in result['suggestions']:
                st.write(f"• {suggestion}")


def format_number_streamlit(value, format_type='auto'):
    """Format numbers with thousand separators for Streamlit"""
    try:
        if pd.isna(value) or value is None:
            return "N/A"
        
        value = float(value)
        
        if format_type == 'currency':
            if abs(value) >= 1e12:
                return f"${value/1e12:.1f}T"
            elif abs(value) >= 1e9:
                return f"${value/1e9:.1f}B"
            elif abs(value) >= 1e6:
                return f"${value/1e6:.1f}M"
            elif abs(value) >= 1e3:
                return f"${value/1e3:.1f}K"
            else:
                return f"${value:,.0f}"
        elif format_type == 'count':
            if abs(value) >= 1e9:
                return f"{value/1e9:.1f}B"
            elif abs(value) >= 1e6:
                return f"{value/1e6:.1f}M"
            elif abs(value) >= 1e3:
                return f"{value/1e3:.1f}K"
            else:
                return f"{value:,.0f}"
        else:  # auto
            if abs(value) >= 1e12:
                return f"{value/1e12:.1f}T"
            elif abs(value) >= 1e9:
                return f"{value/1e9:.1f}B"
            elif abs(value) >= 1e6:
                return f"{value/1e6:.1f}M"
            elif abs(value) >= 1e3:
                return f"{value/1e3:.1f}K"
            else:
                return f"{value:,.0f}"
    except:
        return str(value)

def create_visualizations(df, query_type):
    """Create visualizations based on query type and data"""
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(df) == 0:
            st.info("No data to visualize")
            return
        
        # Dashboard queries
        if query_type == 'dashboard':
            if 'metric_name' in df.columns and 'metric_value' in df.columns:
                # Filter numeric metrics
                numeric_metrics = df[df['metric_value'].str.isnumeric()]
                if len(numeric_metrics) > 0:
                    fig = px.bar(
                        numeric_metrics,
                        x='metric_name',
                        y=pd.to_numeric(numeric_metrics['metric_value']),
                        title="Dashboard Metrics"
                    )
                    fig.update_xaxis(tickangle=45)
                    # Format y-axis with thousand separators
                    fig.update_yaxis(tickformat=',.0f')
                    # Format hover labels
                    fig.update_traces(hovertemplate='%{x}: %{y:,.0f}<extra></extra>')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Top regions/models queries
        elif query_type in ['top_regions', 'top_models']:
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                # Find revenue or sales columns
                revenue_cols = [col for col in numeric_cols if 'revenue' in col.lower() or 'sales' in col.lower()]
                if revenue_cols:
                    fig = px.bar(
                        df,
                        x=categorical_cols[0],
                        y=revenue_cols[0],
                        title=f"{query_type.replace('_', ' ').title()} by {revenue_cols[0].replace('_', ' ').title()}"
                    )
                    fig.update_xaxis(tickangle=45)
                    # Format y-axis with thousand separators
                    if 'revenue' in revenue_cols[0].lower():
                        fig.update_yaxis(tickformat='$,.0f')
                        fig.update_traces(hovertemplate='%{x}: $%{y:,.0f}<extra></extra>')
                    else:
                        fig.update_yaxis(tickformat=',.0f')
                        fig.update_traces(hovertemplate='%{x}: %{y:,.0f}<extra></extra>')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Annual sales queries
        elif query_type == 'annual_sales':
            if 'year' in df.columns:
                year_cols = [col for col in numeric_cols if 'total' in col.lower()]
                if year_cols:
                    fig = px.line(
                        df,
                        x='year',
                        y=year_cols[0],
                        title="Annual Sales Trend"
                    )
                    # Format y-axis with thousand separators
                    if 'revenue' in year_cols[0].lower():
                        fig.update_yaxis(tickformat='$,.0f')
                        fig.update_traces(hovertemplate='%{x}: $%{y:,.0f}<extra></extra>')
                    else:
                        fig.update_yaxis(tickformat=',.0f')
                        fig.update_traces(hovertemplate='%{x}: %{y:,.0f}<extra></extra>')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Fuel/transmission performance
        elif query_type in ['fuel_performance', 'transmission_performance']:
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                # Create pie chart for market share
                share_cols = [col for col in numeric_cols if 'share' in col.lower()]
                if share_cols:
                    fig = px.pie(
                        df,
                        values=share_cols[0],
                        names=categorical_cols[0],
                        title=f"{query_type.replace('_', ' ').title()} Market Share"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Generic visualizations
        else:
            if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                # Bar chart
                fig = px.bar(
                    df,
                    x=categorical_cols[0],
                    y=numeric_cols[0],
                    title=f"{categorical_cols[0].replace('_', ' ').title()} vs {numeric_cols[0].replace('_', ' ').title()}"
                )
                fig.update_xaxis(tickangle=45)
                # Format y-axis with thousand separators
                fig.update_yaxis(tickformat=',.0f')
                fig.update_traces(hovertemplate='%{x}: %{y:,.0f}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)
            
            elif len(numeric_cols) > 1:
                # Scatter plot
                fig = px.scatter(
                    df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()}"
                )
                # Format axes with thousand separators
                fig.update_xaxis(tickformat=',.0f')
                fig.update_yaxis(tickformat=',.0f')
                fig.update_traces(hovertemplate='%{x:,.0f}, %{y:,.0f}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Could not create visualization: {e}")

def display_available_queries(agent):
    """Display available predefined queries"""
    st.subheader("📋 Available Queries")
    
    available_queries = agent.get_available_queries()
    
    # Map query types to natural language queries
    query_mapping = {
        'dashboard': 'Mostre o dashboard executivo',
        'top_regions': 'Quais são as top 5 regiões?',
        'top_models': 'Quais são os top 10 modelos?',
        'annual_sales': 'Mostre as vendas anuais',
        'regional_performance': 'Qual a performance por região?',
        'model_performance': 'Qual a performance por modelo?',
        'fuel_performance': 'Mostre a performance por combustível',
        'transmission_performance': 'Mostre a performance por transmissão',
        'annual_growth': 'Qual o crescimento anual?',
        'year_analysis': 'Qual ano tem mais modelos vendidos?'
    }
    
    # Create columns for better layout
    cols = st.columns(2)
    
    for i, (query_type, description) in enumerate(available_queries.items()):
        with cols[i % 2]:
            natural_query = query_mapping.get(query_type, description)
            if st.button(f"📊 {description}", key=f"available_{query_type}"):
                st.session_state.selected_query = natural_query
                st.rerun()

def display_database_schema(agent):
    """Display database schema information"""
    st.subheader("🗄️ Database Schema")
    
    schema = agent.get_database_schema()
    
    if schema:
        # Tables
        if 'tables' in schema:
            st.write("**Tables:**")
            for table_name, columns in schema['tables'].items():
                with st.expander(f"📋 {table_name}"):
                    if columns:
                        df_columns = pd.DataFrame(columns)
                        st.dataframe(df_columns, use_container_width=True)
                    else:
                        st.info("No column information available")
        
        # Views
        if 'views' in schema:
            st.write("**Views:**")
            for schema_name, views in schema['views'].items():
                with st.expander(f"👁️ {schema_name} schema"):
                    if views:
                        df_views = pd.DataFrame(views)
                        st.dataframe(df_views, use_container_width=True)
                    else:
                        st.info("No views available")

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🚗 BMW Sales Analytics - Natural Language SQL Agent</h1>', unsafe_allow_html=True)
    
    # Initialize Natural Language SQL Agent
    agent = initialize_sql_agent()
    
    if not agent:
        st.stop()
    
    # Initialize Orchestrator Agent
    orchestrator = initialize_orchestrator_agent()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Navigation")
        
        # Navigation
        page = st.selectbox(
            "Select Page",
            ["🏠 Dashboard", "💬 Natural Language Query", "📊 AI Visualization", "📋 Available Queries", "🗄️ Database Schema", "📜 Query History"]
        )
        
        # AI Provider Selection
        st.header("🤖 AI Provider")
        ai_provider = st.selectbox(
            "Select AI Provider",
            ["openai", "anthropic"],
            index=0,
            help="Choose which AI provider to use for query processing"
        )
        if 'ai_provider' not in st.session_state or st.session_state.ai_provider != ai_provider:
            st.session_state.ai_provider = ai_provider
            # Clear cache to reinitialize with new provider
            st.cache_resource.clear()
        
        # Database connection status
        st.header("🔗 Connection Status")
        try:
            # Test connection using agent with a known working query
            result = agent.process_natural_language_query("Mostre o dashboard executivo")
            if result['success']:
                st.success("✅ Database Connected")
            else:
                st.error("❌ Database Disconnected")
        except:
            st.error("❌ Database Disconnected")
        
        # Quick stats
        st.header("📊 Quick Stats")
        try:
            # Get basic stats using dashboard query
            result = agent.process_natural_language_query("Mostre o dashboard executivo")
            if result['success'] and result['results']:
                # Find total records in dashboard results
                for row in result['results']:
                    if row.get('metric_name') == 'Total Records':
                        total_records = row.get('metric_value', 'N/A')
                        st.metric("Total Records", total_records)
                        break
                else:
                    st.metric("Total Records", "N/A")
            else:
                st.metric("Total Records", "N/A")
        except:
            st.metric("Total Records", "N/A")
        
        # Available query types
        st.header("🎯 Query Types")
        available_queries = agent.get_available_queries()
        st.write(f"**{len(available_queries)} predefined queries available**")
        
        
        # Example queries removed from sidebar
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        st.header("📈 Dashboard Overview")
        
        # Quick insights
        st.subheader("🔍 Quick Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("💡 **Tip:** Use natural language to query your BMW sales data. The Natural Language SQL Agent understands Portuguese and English queries.")
        
        with col2:
            st.info("🔧 **Feature:** The agent can understand complex queries and generate optimized SQL automatically with confidence scoring.")
        
        # Recent activity placeholder
        st.subheader("📊 Recent Activity")
        st.info("Query history will be displayed here in future versions.")
        
        # Quick stats
        st.subheader("📊 Quick Statistics")
        
        # Get some quick stats using dashboard query
        try:
            result = agent.process_natural_language_query("Mostre o dashboard executivo")
            if result['success'] and result['results']:
                # Extract metrics from dashboard results
                metrics = {}
                for row in result['results']:
                    metric_name = row.get('metric_name', '')
                    metric_value = row.get('metric_value', 'N/A')
                    metrics[metric_name] = metric_value
                
                # Display key metrics
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Total Records", metrics.get('Total Records', 'N/A'))
                with cols[1]:
                    st.metric("Total Regions", metrics.get('Number of Regions', 'N/A'))
                with cols[2]:
                    st.metric("Total Models", metrics.get('Number of Models', 'N/A'))
            else:
                st.info("Unable to load dashboard metrics")
        except:
            st.info("Unable to load dashboard metrics")
    
    elif page == "💬 Natural Language Query":
        st.header("🤖 Natural Language Query Interface")
        
        # Initialize session state
        if 'last_result' not in st.session_state:
            st.session_state.last_result = None
        if 'last_query' not in st.session_state:
            st.session_state.last_query = None
        
        # Query input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Use text input for better UX with Enter key support
            user_query = st.text_input(
                "Enter your question in natural language:",
                placeholder="e.g., Mostre o dashboard executivo, Quais são as top 5 regiões?, Qual a média de preços?",
                key="main_query_input"
            )
        
        with col2:
            st.write("**Query Options:**")
            show_sql = st.checkbox("Show SQL", value=True)
            show_explanation = st.checkbox("Show Explanation", value=True)
            show_visualization = st.checkbox("Show Visualization", value=True)
        
        # Query buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 Execute Query", type="primary"):
                if user_query and user_query.strip():
                    with st.spinner("Processing your query..."):
                        result = agent.process_natural_language_query(user_query.strip())
                        st.session_state.last_result = result
                        st.session_state.last_query = user_query.strip()
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter a query")
        
        # Auto-execute when Enter is pressed (if query is not empty and different from last)
        if (user_query and user_query.strip() and 
            user_query.strip() != st.session_state.get('last_query', '') and
            user_query.strip() != '' and
            'example_query' not in st.session_state):
            with st.spinner("Processing your query..."):
                result = agent.process_natural_language_query(user_query.strip())
                st.session_state.last_result = result
                st.session_state.last_query = user_query.strip()
                st.rerun()
        
        with col2:
            if st.button("🔄 Clear"):
                st.session_state.last_result = None
                st.session_state.last_query = None
                st.rerun()
        
        # Handle example query selection
        if 'example_query' in st.session_state:
            st.text_area(
                "Selected example:",
                value=st.session_state.example_query,
                height=50,
                disabled=True,
                key="example_display"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use this query"):
                    # Set the query and execute it
                    st.session_state.last_query = st.session_state.example_query
                    with st.spinner("Processing your query..."):
                        result = agent.process_natural_language_query(st.session_state.example_query)
                        st.session_state.last_result = result
                    del st.session_state.example_query
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.example_query
                    st.rerun()
        
        # Display results
        if st.session_state.last_result:
            st.markdown("---")
            display_query_result(st.session_state.last_result, st.session_state.last_query, agent)
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "Mostre o dashboard executivo",
            "Quais são as top 5 regiões?",
            "Quais são os top 10 modelos?",
            "Mostre as vendas anuais",
            "Qual a média de preços?",
            "Soma total de vendas",
            "Qual o crescimento anual?",
            "Conte o total de registros",
            "Qual o preço máximo?"
        ]
        
        # Create columns for example queries
        cols = st.columns(2)
        for i, example in enumerate(example_queries):
            with cols[i % 2]:
                if st.button(f"📝 {example}", key=f"example_{i}"):
                    st.session_state.example_query = example
                    st.rerun()
    
    
    elif page == "📋 Available Queries":
        st.header("📋 Available Predefined Queries")
        
        display_available_queries(agent)
        
        # Handle selected query
        if 'selected_query' in st.session_state:
            st.markdown("---")
            st.subheader(f"Executing: {st.session_state.selected_query}")
            
            with st.spinner("Processing query..."):
                result = agent.process_natural_language_query(st.session_state.selected_query)
                display_query_result(result, st.session_state.selected_query, agent)
    
    elif page == "🗄️ Database Schema":
        st.header("🗄️ Database Schema Information")
        
        display_database_schema(agent)
    
    elif page == "📊 AI Visualization":
        st.header("📊 AI-Powered Visualization")
        
        st.info("💡 **Novo!** Agora você pode criar visualizações personalizadas usando linguagem natural!")
        
        # Initialize session state for visualization
        if 'viz_last_data' not in st.session_state:
            st.session_state.viz_last_data = None
        if 'viz_last_result' not in st.session_state:
            st.session_state.viz_last_result = None
        
        # Two modes: Query + Viz, or Viz from existing data
        mode = st.radio(
            "Modo de Visualização:",
            ["🔄 Consulta + Visualização", "🎨 Visualizar Dados Existentes"],
            help="Escolha se quer buscar dados e visualizar, ou apenas criar visualizações de dados já consultados"
        )
        
        if mode == "🔄 Consulta + Visualização":
            st.subheader("Consulta com Visualização Automática")
            
            # Query input
            viz_query = st.text_input(
                "Digite sua pergunta (pode incluir o tipo de gráfico desejado):",
                placeholder="Ex: Mostre um gráfico de barras das vendas por região",
                key="viz_query_input"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Executar", type="primary", key="execute_viz"):
                    if viz_query and viz_query.strip():
                        with st.spinner("Processando consulta e gerando visualização..."):
                            result = orchestrator.process_query(viz_query.strip())
                            st.session_state.viz_last_result = result
                            
                            # Save data for later reuse
                            if result.get('success') and result.get('data'):
                                st.session_state.viz_last_data = pd.DataFrame(result['data'])
                            
                            st.rerun()
                    else:
                        st.warning("⚠️ Por favor, digite uma consulta")
            
            with col2:
                if st.button("🔄 Limpar", key="clear_viz"):
                    st.session_state.viz_last_result = None
                    st.session_state.viz_last_data = None
                    st.rerun()
            
            # Display results
            if st.session_state.viz_last_result:
                result = st.session_state.viz_last_result
                
                if result['success']:
                    st.success("✅ Consulta executada com sucesso!")
                    
                    # Display SQL results
                    if 'sql_result' in result:
                        st.subheader("📊 Dados")
                        with st.expander("Ver SQL Query"):
                            st.code(result['sql_result'].get('sql_query', ''), language='sql')
                        
                        if result.get('data'):
                            df = pd.DataFrame(result['data'])
                            st.dataframe(df, use_container_width=True)
                    
                    # Display visualization
                    if 'visualization_result' in result:
                        viz_result = result['visualization_result']
                        
                        if viz_result['success']:
                            st.subheader("📈 Visualização")
                            
                            # Display chart
                            import base64
                            img_data = base64.b64decode(viz_result['image_base64'])
                            st.image(img_data, use_column_width=True)
                            
                            # Chart info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Tipo de Gráfico", viz_result['chart_type'].title())
                            with col2:
                                st.metric("Tempo de Execução", f"{viz_result['execution_time']:.3f}s")
                            with col3:
                                st.metric("AI Provider", result['ai_provider'].upper())
                            
                            # Show generated code
                            with st.expander("📝 Ver Código Python"):
                                st.code(viz_result.get('chart_code', ''), language='python')
                        else:
                            st.error(f"❌ Erro ao gerar visualização: {viz_result.get('error', 'Unknown')}")
                else:
                    st.error(f"❌ Erro: {result.get('error', 'Unknown error')}")
            
            # Example queries
            st.subheader("💡 Exemplos de Consultas com Visualização")
            example_viz_queries = [
                "Mostre um gráfico de barras das vendas por região",
                "Crie um gráfico de linha da receita ao longo dos anos",
                "Faça um gráfico de dispersão entre preço e vendas dos modelos",
                "Mostre um gráfico de pizza das vendas por tipo de combustível",
                "Crie um heatmap de correlação entre as variáveis numéricas"
            ]
            
            cols = st.columns(2)
            for i, example in enumerate(example_viz_queries):
                with cols[i % 2]:
                    if st.button(f"📊 {example}", key=f"viz_example_{i}"):
                        st.session_state.viz_query_example = example
                        st.rerun()
        
        else:  # Visualizar Dados Existentes
            st.subheader("Criar Visualização de Dados Existentes")
            
            if st.session_state.viz_last_data is not None and not st.session_state.viz_last_data.empty:
                st.info(f"✅ Dados carregados: {len(st.session_state.viz_last_data)} linhas, {len(st.session_state.viz_last_data.columns)} colunas")
                
                # Show data preview
                with st.expander("👀 Visualizar Dados"):
                    st.dataframe(st.session_state.viz_last_data.head(10), use_container_width=True)
                
                # Get visualization suggestions
                if orchestrator:
                    suggestions = orchestrator.suggest_visualizations(st.session_state.viz_last_data)
                    
                    if suggestions:
                        st.subheader("💡 Visualizações Sugeridas")
                        
                        cols = st.columns(2)
                        for i, suggestion in enumerate(suggestions):
                            with cols[i % 2]:
                                if st.button(
                                    f"📊 {suggestion['type'].upper()}: {suggestion['description']}",
                                    key=f"suggestion_{i}"
                                ):
                                    # Generate visualization
                                    with st.spinner("Gerando visualização..."):
                                        viz_result = orchestrator.process_query_with_data(
                                            query=suggestion['query'],
                                            data=st.session_state.viz_last_data
                                        )
                                        
                                        if viz_result['success']:
                                            viz = viz_result['visualization_result']
                                            
                                            # Display chart
                                            import base64
                                            img_data = base64.b64decode(viz['image_base64'])
                                            st.image(img_data, use_column_width=True)
                                            
                                            st.success(f"✅ {viz['title']}")
                
                # Custom visualization query
                st.subheader("🎨 Criar Visualização Personalizada")
                custom_viz_query = st.text_input(
                    "Descreva o gráfico que você quer criar:",
                    placeholder="Ex: Gráfico de barras empilhadas por região e ano",
                    key="custom_viz_query"
                )
                
                if st.button("🎨 Criar Visualização", type="primary"):
                    if custom_viz_query:
                        with st.spinner("Criando visualização..."):
                            viz_result = orchestrator.process_query_with_data(
                                query=custom_viz_query,
                                data=st.session_state.viz_last_data
                            )
                            
                            if viz_result['success']:
                                viz = viz_result['visualization_result']
                                
                                # Display chart
                                import base64
                                img_data = base64.b64decode(viz['image_base64'])
                                st.image(img_data, use_column_width=True)
                                
                                # Chart info
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Tipo de Gráfico", viz['chart_type'].title())
                                with col2:
                                    st.metric("Título", viz['title'])
                                with col3:
                                    st.metric("Tempo", f"{viz['execution_time']:.3f}s")
                                
                                # Show code
                                with st.expander("📝 Ver Código Python"):
                                    st.code(viz.get('chart_code', ''), language='python')
                            else:
                                st.error(f"❌ Erro: {viz_result.get('error', 'Unknown')}")
                    else:
                        st.warning("⚠️ Descreva a visualização desejada")
            else:
                st.warning("⚠️ Nenhum dado disponível. Execute uma consulta primeiro no modo 'Consulta + Visualização'.")
    
    elif page == "📜 Query History":
        st.header("📜 Query History")
        
        st.info("Query history feature will be implemented in future versions.")
        
        # Placeholder for query history
        st.subheader("📊 Recent Queries")
        
        # Show some example queries
        example_queries = [
            {"query": "Mostre o dashboard executivo", "success": True, "time": "0.071s"},
            {"query": "Quais são as top 5 regiões?", "success": True, "time": "0.050s"},
            {"query": "Qual a média de preços?", "success": False, "time": "0.000s"},
            {"query": "Soma total de vendas", "success": False, "time": "0.000s"}
        ]
        
        for query_info in example_queries:
            status = "✅" if query_info['success'] else "❌"
            st.write(f"{status} **{query_info['query']}** - {query_info['time']}")

if __name__ == "__main__":
    main()
