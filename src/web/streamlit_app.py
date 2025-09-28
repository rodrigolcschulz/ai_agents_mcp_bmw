"""
Streamlit web interface for AI Data Engineering project
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import asyncio
from datetime import datetime, timedelta
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.sql_agent import SQLAgent
from agents.multi_llm_agent import MultiLLMAgent
from agents.mcp_handler import MCPHandler, MCPClient
from database.loader import DatabaseLoader
from config.database import test_connection

# Page configuration
st.set_page_config(
    page_title="AI Data Engineering Dashboard",
    page_icon="🤖",
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
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_components():
    """Initialize SQL agent and MCP handler"""
    try:
        # Check database connection
        if not test_connection():
            st.error("❌ Database connection failed. Please check your configuration.")
            return None, None, None, None
        
        # Initialize components
        sql_agent = SQLAgent()
        multi_llm_agent = MultiLLMAgent()
        mcp_handler = MCPHandler(sql_agent)
        mcp_client = MCPClient(mcp_handler)
        db_loader = DatabaseLoader()
        
        return sql_agent, multi_llm_agent, mcp_client, db_loader
        
    except Exception as e:
        st.error(f"❌ Error initializing components: {e}")
        return None, None, None, None

def display_database_stats(db_loader):
    """Display database statistics"""
    try:
        stats = db_loader.get_database_stats()
        
        st.subheader("📊 Database Statistics")
        
        # Create columns for metrics
        cols = st.columns(len(stats))
        
        for i, (table_name, table_info) in enumerate(stats.items()):
            with cols[i]:
                st.metric(
                    label=table_name.replace('_', ' ').title(),
                    value=table_info.get('row_count', 0),
                    help=f"Columns: {len(table_info.get('columns', []))}"
                )
        
        # Display table details
        with st.expander("📋 Table Details"):
            for table_name, table_info in stats.items():
                st.write(f"**{table_name}**")
                st.write(f"Rows: {table_info.get('row_count', 0)}")
                st.write(f"Columns: {len(table_info.get('columns', []))}")
                
                # Display column information
                if table_info.get('columns'):
                    df_columns = pd.DataFrame(table_info['columns'])
                    st.dataframe(df_columns, use_container_width=True)
                
                st.write("---")
                
    except Exception as e:
        st.error(f"Error displaying database stats: {e}")

def display_query_history(sql_agent):
    """Display query history"""
    try:
        history = sql_agent.get_query_history(limit=20)
        
        if not history:
            st.info("No query history available")
            return
        
        st.subheader("📜 Query History")
        
        # Convert to DataFrame for better display
        df_history = pd.DataFrame(history)
        df_history['created_at'] = pd.to_datetime(df_history['created_at'])
        
        # Filter by date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=df_history['created_at'].min().date(),
                min_value=df_history['created_at'].min().date(),
                max_value=df_history['created_at'].max().date()
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=df_history['created_at'].max().date(),
                min_value=df_history['created_at'].min().date(),
                max_value=df_history['created_at'].max().date()
            )
        
        # Filter data
        filtered_history = df_history[
            (df_history['created_at'].dt.date >= start_date) &
            (df_history['created_at'].dt.date <= end_date)
        ]
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Queries", len(filtered_history))
        with col2:
            successful_queries = len(filtered_history[filtered_history['success'] == True])
            st.metric("Successful", successful_queries)
        with col3:
            avg_time = filtered_history['execution_time'].mean()
            st.metric("Avg Execution Time", f"{avg_time:.2f}s" if pd.notna(avg_time) else "N/A")
        
        # Display history table
        st.dataframe(
            filtered_history[['user_query', 'success', 'execution_time', 'created_at']],
            use_container_width=True
        )
        
        # Display detailed view
        with st.expander("🔍 Detailed Query View"):
            for idx, row in filtered_history.iterrows():
                st.write(f"**Query:** {row['user_query']}")
                st.write(f"**SQL:** ```sql\n{row['sql_query']}\n```")
                st.write(f"**Success:** {'✅' if row['success'] else '❌'}")
                st.write(f"**Execution Time:** {row['execution_time']:.2f}s")
                st.write(f"**Timestamp:** {row['created_at']}")
                st.write("---")
                
    except Exception as e:
        st.error(f"Error displaying query history: {e}")

async def process_query(mcp_client, query, context):
    """Process query using MCP client"""
    try:
        response = await mcp_client.send_query(query, context)
        return response
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Data Engineering Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize components
    sql_agent, multi_llm_agent, mcp_client, db_loader = initialize_components()
    
    if not all([sql_agent, multi_llm_agent, mcp_client, db_loader]):
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Navigation")
        
        # Navigation
        page = st.selectbox(
            "Select Page",
            ["🏠 Dashboard", "💬 AI Query", "📊 Database Stats", "📜 Query History", "⚙️ Settings"]
        )
        
        # Database connection status
        st.header("🔗 Connection Status")
        if test_connection():
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Disconnected")
        
        # Quick stats
        try:
            stats = db_loader.get_database_stats()
            total_rows = sum(table_info.get('row_count', 0) for table_info in stats.values())
            st.metric("Total Records", total_rows)
        except:
            st.metric("Total Records", "N/A")
        
        # Available AI providers
        st.header("🤖 AI Providers")
        try:
            providers = multi_llm_agent.get_available_providers()
            for provider in providers:
                st.success(f"✅ {provider.title()}")
        except:
            st.info("No AI providers available")
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        st.header("📈 Dashboard Overview")
        
        # Display database stats
        display_database_stats(db_loader)
        
        # Quick insights
        st.subheader("🔍 Quick Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("💡 **Tip:** Use natural language to query your data. For example: 'Show me sales by region' or 'What are the top 10 models by sales?'")
        
        with col2:
            st.info("🔧 **Feature:** The AI agent can understand complex queries and generate optimized SQL automatically.")
        
        # Recent activity
        st.subheader("📊 Recent Activity")
        try:
            recent_queries = sql_agent.get_query_history(limit=5)
            if recent_queries:
                for query in recent_queries:
                    status = "✅" if query['success'] else "❌"
                    st.write(f"{status} {query['user_query'][:50]}...")
            else:
                st.info("No recent queries found")
        except:
            st.info("Unable to load recent queries")
    
    elif page == "💬 AI Query":
        st.header("🤖 AI-Powered Database Query")
        
        # AI Provider selection
        col1, col2 = st.columns([1, 1])
        
        with col1:
            available_providers = multi_llm_agent.get_available_providers()
            selected_provider = st.selectbox(
                "Select AI Provider:",
                available_providers,
                index=0 if available_providers else None
            )
        
        with col2:
            st.write("**Provider Info:**")
            if selected_provider == "openai":
                st.info("🚀 OpenAI GPT-4 - Fast and accurate")
            elif selected_provider == "anthropic":
                st.info("🧠 Anthropic Claude - Advanced reasoning")
            elif selected_provider == "huggingface":
                st.info("🤗 Hugging Face - Open source models")
        
        # Query input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_query = st.text_area(
                "Enter your question in natural language:",
                placeholder="e.g., Show me the total sales by year and region",
                height=100
            )
        
        with col2:
            st.write("**Context (Optional):**")
            context = st.text_area(
                "Additional context:",
                placeholder="e.g., Focus on BMW sales data",
                height=100
            )
        
        # Query buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 Execute Query", type="primary"):
                if user_query:
                    with st.spinner(f"Processing your query with {selected_provider}..."):
                        # Use multi-LLM agent with selected provider
                        result = multi_llm_agent.query_database(
                            user_query, 
                            provider=selected_provider, 
                            context=context
                        )
                        
                        # Display results
                        if result.get('success'):
                            st.success(f"✅ Query executed successfully with {result.get('provider_used', 'unknown')}!")
                            
                            # Display SQL query
                            if result.get('sql_query'):
                                st.subheader("🔍 Generated SQL Query")
                                st.code(result['sql_query'], language='sql')
                            
                            # Display explanation
                            if result.get('explanation'):
                                st.subheader("💡 Explanation")
                                st.write(result['explanation'])
                            
                            # Display results
                            if result.get('results'):
                                st.subheader("📊 Results")
                                results_df = pd.DataFrame(result['results'])
                                st.dataframe(results_df, use_container_width=True)
                                
                                # Create visualizations if possible
                                if len(results_df) > 0:
                                    st.subheader("📈 Visualization")
                                    
                                    # Auto-generate charts based on data
                                    numeric_cols = results_df.select_dtypes(include=['number']).columns
                                    categorical_cols = results_df.select_dtypes(include=['object']).columns
                                    
                                    if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                                        # Bar chart
                                        fig = px.bar(
                                            results_df,
                                            x=categorical_cols[0],
                                            y=numeric_cols[0],
                                            title=f"{categorical_cols[0]} vs {numeric_cols[0]}"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    
                                    elif len(numeric_cols) > 1:
                                        # Scatter plot
                                        fig = px.scatter(
                                            results_df,
                                            x=numeric_cols[0],
                                            y=numeric_cols[1],
                                            title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                            
                            # Display metadata
                            st.subheader("ℹ️ Query Information")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Rows Returned", result.get('row_count', 0))
                            with col2:
                                st.metric("Provider Used", result.get('provider_used', 'Unknown'))
                            with col3:
                                st.metric("Status", "Success" if result['success'] else "Failed")
                        
                        else:
                            st.error(f"❌ Query failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("⚠️ Please enter a query")
        
        with col2:
            if st.button("🔄 Clear"):
                st.rerun()
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "Show me the total sales by year",
            "What are the top 5 regions by sales?",
            "Display sales trends over time",
            "Compare sales between different models",
            "Show me the average sales per month"
        ]
        
        for i, example in enumerate(example_queries):
            if st.button(f"📝 {example}", key=f"example_{i}"):
                st.session_state.example_query = example
                st.rerun()
        
        # Handle example query selection
        if 'example_query' in st.session_state:
            st.text_area(
                "Selected example:",
                value=st.session_state.example_query,
                height=50,
                disabled=True
            )
            if st.button("Use this query"):
                user_query = st.session_state.example_query
                del st.session_state.example_query
                st.rerun()
    
    elif page == "📊 Database Stats":
        st.header("📊 Database Statistics")
        display_database_stats(db_loader)
    
    elif page == "📜 Query History":
        st.header("📜 Query History")
        display_query_history(sql_agent)
    
    elif page == "⚙️ Settings":
        st.header("⚙️ Settings")
        
        # Database configuration
        st.subheader("🗄️ Database Configuration")
        st.info("Database configuration is managed through environment variables. Please check your .env file.")
        
        # AI configuration
        st.subheader("🤖 AI Configuration")
        st.info("AI configuration is managed through environment variables. Please check your .env file.")
        
        # Export options
        st.subheader("📤 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Database Stats"):
                try:
                    stats = db_loader.get_database_stats()
                    stats_json = json.dumps(stats, indent=2)
                    st.download_button(
                        label="Download Stats JSON",
                        data=stats_json,
                        file_name=f"database_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error exporting stats: {e}")
        
        with col2:
            if st.button("📜 Export Query History"):
                try:
                    history = sql_agent.get_query_history(limit=1000)
                    history_json = json.dumps(history, indent=2, default=str)
                    st.download_button(
                        label="Download History JSON",
                        data=history_json,
                        file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error exporting history: {e}")

if __name__ == "__main__":
    main()
