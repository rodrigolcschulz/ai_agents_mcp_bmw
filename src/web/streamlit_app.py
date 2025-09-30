"""
Streamlit Web Interface for MCP Agent - BMW Sales Analytics
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

# Import MCP Agent
spec = importlib.util.spec_from_file_location("mcp_agent", os.path.join(os.path.dirname(__file__), '..', 'agents', 'mcp_agent.py'))
mcp_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_agent_module)
MCPAgentImproved = mcp_agent_module.MCPAgentImproved

# Import database config
from config.database import test_connection

# Page configuration
st.set_page_config(
    page_title="BMW Sales Analytics - MCP Agent",
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
def initialize_mcp_agent():
    """Initialize MCP Agent"""
    try:
        # Initialize agent
        agent = MCPAgentImproved()
        
        # Test if agent can connect to database
        try:
            result = agent.process_natural_language_query("Mostre o dashboard executivo")
            if not result['success']:
                st.error("❌ MCP Agent initialized but database connection failed")
                return None
        except Exception as db_error:
            st.error(f"❌ Database connection test failed: {db_error}")
            return None
        
        return agent
        
    except Exception as e:
        st.error(f"❌ Error initializing MCP Agent: {e}")
        return None

def get_confidence_color(confidence):
    """Get color based on confidence score"""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def display_query_result(result, query):
    """Display query result with formatting"""
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
            st.dataframe(results_df, use_container_width=True)
            
            # Create visualizations
            if len(results_df) > 0:
                st.subheader("📈 Visualization")
                create_visualizations(results_df, result.get('query_type', 'unknown'))
        
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
                st.plotly_chart(fig, use_container_width=True)
            
            elif len(numeric_cols) > 1:
                # Scatter plot
                fig = px.scatter(
                    df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()}"
                )
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
        'monthly_trends': 'Mostre as tendências mensais',
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
    st.markdown('<h1 class="main-header">🚗 BMW Sales Analytics - MCP Agent</h1>', unsafe_allow_html=True)
    
    # Initialize MCP Agent
    agent = initialize_mcp_agent()
    
    if not agent:
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Navigation")
        
        # Navigation
        page = st.selectbox(
            "Select Page",
            ["🏠 Dashboard", "💬 Natural Language Query", "📋 Available Queries", "🗄️ Database Schema", "📊 Query History"]
        )
        
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
            st.info("💡 **Tip:** Use natural language to query your BMW sales data. The MCP Agent understands Portuguese and English queries.")
        
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
            user_query.strip() != ''):
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
            if st.button("Use this query"):
                # Clear the example query and rerun
                del st.session_state.example_query
                st.rerun()
        
        # Display results
        if st.session_state.last_result:
            st.markdown("---")
            display_query_result(st.session_state.last_result, st.session_state.last_query)
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "Mostre o dashboard executivo",
            "Quais são as top 5 regiões?",
            "Quais são os top 10 modelos?",
            "Mostre as vendas anuais",
            "Qual a média de preços?",
            "Soma total de vendas",
            "Mostre as tendências mensais",
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
                display_query_result(result, st.session_state.selected_query)
    
    elif page == "🗄️ Database Schema":
        st.header("🗄️ Database Schema Information")
        
        display_database_schema(agent)
    
    elif page == "📊 Query History":
        st.header("📊 Query History")
        
        st.info("Query history feature will be implemented in future versions.")
        
        # Placeholder for query history
        st.subheader("📜 Recent Queries")
        
        # Show some example queries
        example_queries = [
            {"query": "Mostre o dashboard executivo", "success": True, "time": "0.071s"},
            {"query": "Quais são as top 5 regiões?", "success": True, "time": "0.050s"},
            {"query": "Qual a média de preços?", "success": False, "time": "0.000s"},
            {"query": "Soma total de vendas", "success": False, "time": "0.000s"},
            {"query": "Mostre as tendências mensais", "success": True, "time": "0.060s"}
        ]
        
        for query_info in example_queries:
            status = "✅" if query_info['success'] else "❌"
            st.write(f"{status} **{query_info['query']}** - {query_info['time']}")

if __name__ == "__main__":
    main()
