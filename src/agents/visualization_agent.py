"""
Visualization Agent - AI-powered chart generation using Seaborn and Matplotlib
Translates natural language requests into beautiful, customized visualizations
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
from dotenv import load_dotenv
import openai
from anthropic import Anthropic
import re

load_dotenv()

logger = logging.getLogger(__name__)

# Set default style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

class VisualizationAgent:
    """
    AI-powered visualization agent that generates charts from natural language queries.
    Supports seaborn and matplotlib for creating beautiful, customized visualizations.
    """
    
    def __init__(self, ai_provider: str = "openai"):
        """
        Initialize Visualization Agent
        
        Args:
            ai_provider: "openai" or "anthropic"
        """
        self.ai_provider = ai_provider
        
        # Initialize AI clients
        if ai_provider == "openai":
            self.openai_client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
        elif ai_provider == "anthropic":
            self.anthropic_client = Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
        
        # Chart type mappings
        self.chart_patterns = {
            'bar': ['barra', 'bar', 'barras', 'bars', 'coluna', 'column'],
            'line': ['linha', 'line', 'linhas', 'lines', 'tendência', 'trend', 'série temporal', 'time series'],
            'scatter': ['dispersão', 'scatter', 'pontos', 'points', 'correlação', 'correlation'],
            'pie': ['pizza', 'pie', 'torta', 'circular'],
            'heatmap': ['heatmap', 'mapa de calor', 'heat map', 'matriz'],
            'box': ['box', 'boxplot', 'caixa', 'distribuição', 'distribution'],
            'violin': ['violin', 'violino', 'violão'],
            'histogram': ['histograma', 'histogram', 'frequência', 'frequency'],
            'area': ['área', 'area', 'preenchida', 'filled'],
            'stacked_bar': ['empilhada', 'stacked', 'empilhado'],
            'grouped_bar': ['agrupada', 'grouped', 'agrupado', 'lado a lado'],
            'pair': ['pair', 'pairplot', 'relações', 'relationships', 'múltiplas variáveis']
        }
        
        logger.info(f"Visualization Agent initialized with {ai_provider}")
    
    def generate_chart(
        self,
        data: pd.DataFrame,
        query: str,
        chart_type: Optional[str] = None,
        title: Optional[str] = None,
        style: str = "whitegrid"
    ) -> Dict[str, Any]:
        """
        Generate a chart based on natural language query
        
        Args:
            data: DataFrame with the data to visualize
            query: Natural language description of desired chart
            chart_type: Optional explicit chart type (auto-detected if not provided)
            title: Optional chart title
            style: Seaborn style (whitegrid, darkgrid, white, dark, ticks)
            
        Returns:
            Dictionary with chart information and base64 encoded image
        """
        try:
            start_time = datetime.now()
            
            # Set style
            sns.set_theme(style=style)
            
            # Detect chart type if not provided
            if not chart_type:
                chart_type = self._detect_chart_type(query, data)
            
            # Generate chart title if not provided
            if not title:
                title = self._generate_title(query, data)
            
            # Analyze data to determine best columns to use
            chart_config = self._analyze_data_for_chart(data, query, chart_type)
            
            # Generate the chart
            fig, chart_code = self._create_chart(
                data=data,
                chart_type=chart_type,
                config=chart_config,
                title=title,
                query=query
            )
            
            # Convert to base64 for web display
            img_base64 = self._fig_to_base64(fig)
            
            # Close figure to free memory
            plt.close(fig)
            
            response = {
                'success': True,
                'query': query,
                'chart_type': chart_type,
                'title': title,
                'image_base64': img_base64,
                'chart_code': chart_code,
                'config': chart_config,
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'ai_provider': self.ai_provider,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _detect_chart_type(self, query: str, data: pd.DataFrame) -> str:
        """Detect the best chart type based on query and data"""
        query_lower = query.lower()
        
        # Check for explicit chart type mentions
        for chart_type, keywords in self.chart_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return chart_type
        
        # Use AI to suggest chart type
        return self._ai_suggest_chart_type(query, data)
    
    def _ai_suggest_chart_type(self, query: str, data: pd.DataFrame) -> str:
        """Use AI to suggest the best chart type"""
        try:
            # Prepare data summary
            data_summary = self._get_data_summary(data)
            
            prompt = f"""Based on this data and user query, suggest the SINGLE BEST chart type.

DATA SUMMARY:
{data_summary}

USER QUERY: {query}

AVAILABLE CHART TYPES:
- bar: For comparing categories or showing rankings
- line: For trends over time or continuous data
- scatter: For correlations between two numeric variables
- pie: For part-to-whole relationships (use sparingly)
- heatmap: For matrix data or correlations
- box: For distribution comparisons
- histogram: For frequency distributions
- area: For cumulative trends over time

Respond with ONLY the chart type name (e.g., "bar" or "line" or "scatter").
No explanations, just the chart type."""

            if self.ai_provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a data visualization expert. Respond with only the chart type name."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=20
                )
                chart_type = response.choices[0].message.content.strip().lower()
            else:  # anthropic
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=20,
                    temperature=0.1,
                    system="You are a data visualization expert. Respond with only the chart type name.",
                    messages=[{"role": "user", "content": prompt}]
                )
                chart_type = response.content[0].text.strip().lower()
            
            # Validate chart type
            valid_types = ['bar', 'line', 'scatter', 'pie', 'heatmap', 'box', 'histogram', 'area']
            if chart_type not in valid_types:
                # Default to bar chart if AI suggests invalid type
                return 'bar'
            
            return chart_type
            
        except Exception as e:
            logger.error(f"Error in AI chart type suggestion: {e}")
            # Default to bar chart
            return 'bar'
    
    def _generate_title(self, query: str, data: pd.DataFrame) -> str:
        """Generate appropriate chart title"""
        try:
            data_summary = self._get_data_summary(data)
            
            prompt = f"""Generate a clear, concise chart title for this visualization.

USER QUERY: {query}
DATA SUMMARY: {data_summary}

Respond with ONLY the title text, maximum 10 words.
Make it descriptive and professional."""

            if self.ai_provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a data visualization expert. Create concise chart titles."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=50
                )
                return response.choices[0].message.content.strip()
            else:  # anthropic
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=50,
                    temperature=0.3,
                    system="You are a data visualization expert. Create concise chart titles.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Data Visualization"
    
    def _analyze_data_for_chart(
        self,
        data: pd.DataFrame,
        query: str,
        chart_type: str
    ) -> Dict[str, Any]:
        """Analyze data and determine best columns and configuration for chart"""
        try:
            data_info = self._get_detailed_data_info(data)
            
            prompt = f"""Analyze this data and determine the best configuration for a {chart_type} chart.

DATA INFO:
{data_info}

USER QUERY: {query}

CHART TYPE: {chart_type}

Provide a JSON response with:
{{
    "x_column": "column name for x-axis",
    "y_column": "column name for y-axis",
    "hue_column": "column for color grouping (optional)",
    "aggregation": "sum/mean/count/none",
    "sort_by": "x/y/none",
    "sort_order": "asc/desc",
    "limit": 10-20 for top N results,
    "explanation": "brief explanation of choices"
}}

Respond with ONLY valid JSON, no additional text."""

            if self.ai_provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a data analyst. Respond with only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=300
                )
                config_text = response.choices[0].message.content.strip()
            else:  # anthropic
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=300,
                    temperature=0.1,
                    system="You are a data analyst. Respond with only valid JSON.",
                    messages=[{"role": "user", "content": prompt}]
                )
                config_text = response.content[0].text.strip()
            
            # Clean and parse JSON
            config_text = config_text.strip()
            if config_text.startswith('```json'):
                config_text = config_text[7:]
            if config_text.startswith('```'):
                config_text = config_text[3:]
            if config_text.endswith('```'):
                config_text = config_text[:-3]
            config_text = config_text.strip()
            
            import json
            config = json.loads(config_text)
            
            return config
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            # Return default configuration
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
            
            return {
                'x_column': categorical_cols[0] if categorical_cols else numeric_cols[0],
                'y_column': numeric_cols[0] if numeric_cols else categorical_cols[0],
                'hue_column': None,
                'aggregation': 'sum',
                'sort_by': 'y',
                'sort_order': 'desc',
                'limit': 10,
                'explanation': 'Default configuration'
            }
    
    def _create_chart(
        self,
        data: pd.DataFrame,
        chart_type: str,
        config: Dict[str, Any],
        title: str,
        query: str
    ) -> Tuple[plt.Figure, str]:
        """Create the actual chart using seaborn/matplotlib"""
        
        # Prepare data based on configuration
        plot_data = self._prepare_data_for_plot(data, config)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        chart_code = f"# Generated chart code\nimport seaborn as sns\nimport matplotlib.pyplot as plt\n\n"
        
        try:
            if chart_type == 'bar':
                if config.get('hue_column'):
                    sns.barplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        hue=config.get('hue_column'),
                        ax=ax,
                        palette='viridis'
                    )
                    chart_code += f"sns.barplot(data=df, x='{config['x_column']}', y='{config['y_column']}', hue='{config['hue_column']}', palette='viridis')\n"
                else:
                    sns.barplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        ax=ax,
                        palette='viridis'
                    )
                    chart_code += f"sns.barplot(data=df, x='{config['x_column']}', y='{config['y_column']}', palette='viridis')\n"
                ax.tick_params(axis='x', rotation=45)
                
            elif chart_type == 'line':
                if config.get('hue_column'):
                    sns.lineplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        hue=config.get('hue_column'),
                        marker='o',
                        ax=ax
                    )
                    chart_code += f"sns.lineplot(data=df, x='{config['x_column']}', y='{config['y_column']}', hue='{config['hue_column']}', marker='o')\n"
                else:
                    sns.lineplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        marker='o',
                        ax=ax,
                        linewidth=2.5
                    )
                    chart_code += f"sns.lineplot(data=df, x='{config['x_column']}', y='{config['y_column']}', marker='o', linewidth=2.5)\n"
                
            elif chart_type == 'scatter':
                if config.get('hue_column'):
                    sns.scatterplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        hue=config.get('hue_column'),
                        s=100,
                        alpha=0.6,
                        ax=ax
                    )
                    chart_code += f"sns.scatterplot(data=df, x='{config['x_column']}', y='{config['y_column']}', hue='{config['hue_column']}', s=100, alpha=0.6)\n"
                else:
                    sns.scatterplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        s=100,
                        alpha=0.6,
                        ax=ax
                    )
                    chart_code += f"sns.scatterplot(data=df, x='{config['x_column']}', y='{config['y_column']}', s=100, alpha=0.6)\n"
                
            elif chart_type == 'pie':
                # Pie charts use matplotlib, not seaborn
                values = plot_data[config['y_column']].values
                labels = plot_data[config['x_column']].values
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                chart_code += f"plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)\n"
                
            elif chart_type == 'heatmap':
                # Prepare data for heatmap (pivot if needed)
                if len(plot_data.select_dtypes(include=['number']).columns) > 1:
                    corr_data = plot_data.select_dtypes(include=['number']).corr()
                    sns.heatmap(corr_data, annot=True, fmt='.2f', cmap='coolwarm', ax=ax)
                    chart_code += "sns.heatmap(df.corr(), annot=True, fmt='.2f', cmap='coolwarm')\n"
                else:
                    st_warning = "Insufficient numeric data for heatmap"
                    ax.text(0.5, 0.5, st_warning, ha='center', va='center')
                    
            elif chart_type == 'box':
                if config.get('hue_column'):
                    sns.boxplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        hue=config.get('hue_column'),
                        ax=ax,
                        palette='Set2'
                    )
                    chart_code += f"sns.boxplot(data=df, x='{config['x_column']}', y='{config['y_column']}', hue='{config['hue_column']}', palette='Set2')\n"
                else:
                    sns.boxplot(
                        data=plot_data,
                        x=config['x_column'],
                        y=config['y_column'],
                        ax=ax,
                        palette='Set2'
                    )
                    chart_code += f"sns.boxplot(data=df, x='{config['x_column']}', y='{config['y_column']}', palette='Set2')\n"
                ax.tick_params(axis='x', rotation=45)
                
            elif chart_type == 'histogram':
                sns.histplot(
                    data=plot_data,
                    x=config['x_column'],
                    bins=20,
                    kde=True,
                    ax=ax
                )
                chart_code += f"sns.histplot(data=df, x='{config['x_column']}', bins=20, kde=True)\n"
                
            elif chart_type == 'area':
                plot_data_sorted = plot_data.sort_values(config['x_column'])
                ax.fill_between(
                    plot_data_sorted[config['x_column']],
                    plot_data_sorted[config['y_column']],
                    alpha=0.5
                )
                ax.plot(
                    plot_data_sorted[config['x_column']],
                    plot_data_sorted[config['y_column']],
                    linewidth=2
                )
                chart_code += f"plt.fill_between(x=df['{config['x_column']}'], y=df['{config['y_column']}'], alpha=0.5)\n"
                ax.tick_params(axis='x', rotation=45)
            
            else:  # Default to bar chart
                sns.barplot(
                    data=plot_data,
                    x=config['x_column'],
                    y=config['y_column'],
                    ax=ax,
                    palette='viridis'
                )
                ax.tick_params(axis='x', rotation=45)
                chart_code += f"sns.barplot(data=df, x='{config['x_column']}', y='{config['y_column']}', palette='viridis')\n"
            
            # Set title and labels
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(config['x_column'].replace('_', ' ').title(), fontsize=11)
            ax.set_ylabel(config['y_column'].replace('_', ' ').title(), fontsize=11)
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3)
            
            # Tight layout
            plt.tight_layout()
            
            chart_code += f"plt.title('{title}')\nplt.xlabel('{config['x_column']}')\nplt.ylabel('{config['y_column']}')\nplt.tight_layout()\nplt.show()"
            
            return fig, chart_code
            
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            # Create error message chart
            ax.text(0.5, 0.5, f"Error creating chart:\n{str(e)}", ha='center', va='center')
            return fig, f"# Error: {e}"
    
    def _prepare_data_for_plot(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Prepare data according to configuration (aggregation, sorting, limiting)"""
        plot_data = data.copy()
        
        try:
            # Apply aggregation if specified
            if config.get('aggregation') and config['aggregation'] != 'none':
                x_col = config['x_column']
                y_col = config['y_column']
                hue_col = config.get('hue_column')
                
                if hue_col and hue_col in plot_data.columns:
                    group_cols = [x_col, hue_col]
                else:
                    group_cols = [x_col]
                
                if config['aggregation'] == 'sum':
                    plot_data = plot_data.groupby(group_cols)[y_col].sum().reset_index()
                elif config['aggregation'] == 'mean':
                    plot_data = plot_data.groupby(group_cols)[y_col].mean().reset_index()
                elif config['aggregation'] == 'count':
                    plot_data = plot_data.groupby(group_cols)[y_col].count().reset_index()
            
            # Apply sorting
            if config.get('sort_by') and config['sort_by'] != 'none':
                sort_col = config[f"{config['sort_by']}_column"]
                ascending = config.get('sort_order', 'desc') == 'asc'
                plot_data = plot_data.sort_values(sort_col, ascending=ascending)
            
            # Apply limit
            if config.get('limit'):
                plot_data = plot_data.head(config['limit'])
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            return plot_data
    
    def _get_data_summary(self, data: pd.DataFrame) -> str:
        """Get a concise summary of the data"""
        summary = f"Rows: {len(data)}, Columns: {len(data.columns)}\n"
        summary += f"Columns: {', '.join(data.columns.tolist()[:5])}"
        if len(data.columns) > 5:
            summary += f"... (+{len(data.columns) - 5} more)"
        return summary
    
    def _get_detailed_data_info(self, data: pd.DataFrame) -> str:
        """Get detailed information about the data structure"""
        info = f"Shape: {data.shape}\n\n"
        
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if numeric_cols:
            info += f"Numeric columns: {', '.join(numeric_cols)}\n"
        if categorical_cols:
            info += f"Categorical columns: {', '.join(categorical_cols)}\n"
        
        info += f"\nFirst few rows:\n{data.head(3).to_string()}"
        
        return info
    
    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        return img_base64
    
    def get_supported_chart_types(self) -> List[str]:
        """Get list of supported chart types"""
        return list(self.chart_patterns.keys())
    
    def explain_chart_choice(self, query: str, data: pd.DataFrame, chart_type: str) -> str:
        """Get AI explanation of why a particular chart type was chosen"""
        try:
            data_summary = self._get_data_summary(data)
            
            prompt = f"""Explain in 2-3 sentences why a {chart_type} chart is appropriate for this data and query.

DATA: {data_summary}
QUERY: {query}
CHART TYPE: {chart_type}

Make it concise and educational."""

            if self.ai_provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a data visualization teacher. Explain chart choices clearly."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=150
                )
                return response.choices[0].message.content.strip()
            else:  # anthropic
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=150,
                    temperature=0.3,
                    system="You are a data visualization teacher. Explain chart choices clearly.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
        except Exception as e:
            return f"Error generating explanation: {e}"


def main():
    """Test the Visualization Agent"""
    print("=== VISUALIZATION AGENT TEST ===")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'region': ['North America', 'Europe', 'Asia', 'South America', 'Africa'],
        'sales': [15000, 22000, 18000, 9000, 6000],
        'revenue': [750000, 1100000, 900000, 450000, 300000],
        'year': [2020, 2020, 2020, 2020, 2020]
    })
    
    # Initialize agent
    agent = VisualizationAgent("openai")
    
    # Test queries
    test_queries = [
        "Crie um gráfico de barras das vendas por região",
        "Mostre um gráfico de linha da receita",
        "Faça um gráfico de dispersão entre vendas e receita",
        "Crie um gráfico de pizza das vendas por região"
    ]
    
    for query in test_queries:
        print(f"\n--- Query: {query} ---")
        result = agent.generate_chart(sample_data, query)
        
        if result['success']:
            print(f"✅ Chart Type: {result['chart_type']}")
            print(f"   Title: {result['title']}")
            print(f"   Execution Time: {result['execution_time']:.3f}s")
            print(f"   Config: {result['config']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    main()

