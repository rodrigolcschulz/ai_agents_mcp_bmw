"""
Data processing and transformation utilities
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        """Initialize data processor"""
        self.processed_data = {}
    
    def clean_data(self, df: pd.DataFrame, 
                   drop_duplicates: bool = True,
                   handle_missing: str = 'drop',
                   numeric_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Clean and preprocess data
        
        Args:
            df: Input DataFrame
            drop_duplicates: Whether to drop duplicate rows
            handle_missing: How to handle missing values ('drop', 'fill', 'interpolate')
            numeric_columns: List of columns to convert to numeric
            
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Starting data cleaning. Original shape: {df.shape}")
        
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Drop duplicates
        if drop_duplicates:
            before_drop = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            after_drop = len(cleaned_df)
            logger.info(f"Dropped {before_drop - after_drop} duplicate rows")
        
        # Handle missing values
        if handle_missing == 'drop':
            before_drop = len(cleaned_df)
            cleaned_df = cleaned_df.dropna()
            after_drop = len(cleaned_df)
            logger.info(f"Dropped {before_drop - after_drop} rows with missing values")
        elif handle_missing == 'fill':
            # Fill numeric columns with median, categorical with mode
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype in ['int64', 'float64']:
                    cleaned_df[col].fillna(cleaned_df[col].median(), inplace=True)
                else:
                    cleaned_df[col].fillna(cleaned_df[col].mode()[0] if not cleaned_df[col].mode().empty else 'Unknown', inplace=True)
        elif handle_missing == 'interpolate':
            # Only interpolate numeric columns
            numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
            cleaned_df[numeric_cols] = cleaned_df[numeric_cols].interpolate()
        
        # Convert specified columns to numeric
        if numeric_columns:
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        logger.info(f"Data cleaning completed. Final shape: {cleaned_df.shape}")
        return cleaned_df
    
    def transform_bmw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform BMW sales data with specific business logic
        
        Args:
            df: BMW sales DataFrame
            
        Returns:
            Transformed DataFrame
        """
        logger.info("Starting BMW data transformation")
        
        transformed_df = df.copy()
        
        # Standardize column names
        transformed_df.columns = transformed_df.columns.str.lower().str.replace(' ', '_')
        
        # Convert date columns if they exist
        date_columns = ['date', 'year', 'month', 'sales_date']
        for col in date_columns:
            if col in transformed_df.columns:
                try:
                    transformed_df[col] = pd.to_datetime(transformed_df[col], errors='coerce')
                except:
                    pass
        
        # Create derived features
        if 'year' in transformed_df.columns:
            # Create year_month from year only (since month column doesn't exist)
            transformed_df['year_month'] = transformed_df['year'].astype(str) + '-01'
        
        # Add sales metrics if sales data exists
        sales_columns = [col for col in transformed_df.columns if 'sales' in col.lower() or 'units' in col.lower()]
        if sales_columns:
            # Convert to numeric and handle non-numeric values
            numeric_sales = transformed_df[sales_columns].apply(pd.to_numeric, errors='coerce')
            transformed_df['total_sales'] = numeric_sales.sum(axis=1)
        
        logger.info("BMW data transformation completed")
        return transformed_df
    
    def create_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create summary statistics for the dataset
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_summary': {},
            'categorical_summary': {}
        }
        
        # Numeric columns summary
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary['numeric_summary'] = df[numeric_cols].describe().to_dict()
        
        # Categorical columns summary
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            summary['categorical_summary'][col] = {
                'unique_values': df[col].nunique(),
                'top_values': df[col].value_counts().head().to_dict()
            }
        
        return summary
    
    def validate_data(self, df: pd.DataFrame, 
                     required_columns: Optional[List[str]] = None,
                     min_rows: int = 1) -> bool:
        """
        Validate data quality
        
        Args:
            df: Input DataFrame
            required_columns: List of required column names
            min_rows: Minimum number of rows required
            
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Starting data validation")
        
        # Check minimum rows
        if len(df) < min_rows:
            logger.error(f"Data validation failed: Only {len(df)} rows, minimum required: {min_rows}")
            return False
        
        # Check required columns
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                logger.error(f"Data validation failed: Missing columns: {missing_columns}")
                return False
        
        # Check for completely empty columns
        empty_columns = df.columns[df.isnull().all()].tolist()
        if empty_columns:
            logger.warning(f"Found completely empty columns: {empty_columns}")
        
        logger.info("Data validation passed")
        return True

def main():
    """Example usage"""
    # Create sample data for testing
    sample_data = {
        'year': [2020, 2021, 2022, 2023, 2024],
        'month': [1, 2, 3, 4, 5],
        'sales': [100, 150, 200, 180, 220],
        'region': ['North', 'South', 'East', 'West', 'North']
    }
    
    df = pd.DataFrame(sample_data)
    processor = DataProcessor()
    
    # Clean data
    cleaned_df = processor.clean_data(df)
    
    # Transform data
    transformed_df = processor.transform_bmw_data(cleaned_df)
    
    # Create summary
    summary = processor.create_summary_stats(transformed_df)
    
    # Validate data
    is_valid = processor.validate_data(transformed_df, required_columns=['year', 'sales'])
    
    print("Processing completed successfully!" if is_valid else "Processing failed validation!")

if __name__ == "__main__":
    main()
