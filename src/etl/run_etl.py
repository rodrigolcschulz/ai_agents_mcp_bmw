"""
Main ETL pipeline runner
"""
import os
import sys
import logging
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from etl.kaggle_extractor import KaggleExtractor
from etl.data_processor import DataProcessor
from database.loader import DatabaseLoader
from config.database import test_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main ETL pipeline execution"""
    logger.info("Starting ETL pipeline execution")
    
    try:
        # Test database connection
        if not test_connection():
            logger.error("Database connection failed. Exiting.")
            return False
        
        # Initialize components
        extractor = KaggleExtractor()
        processor = DataProcessor()
        loader = DatabaseLoader()
        
        # Step 1: Extract data from Kaggle
        logger.info("Step 1: Extracting data from Kaggle")
        dataset_path = extractor.download_dataset("sidraaazam/bmw-global-sales-analysis")
        
        # List downloaded files
        files = extractor.list_files(dataset_path)
        logger.info(f"Downloaded {len(files)} files")
        
        # Step 2: Process data
        logger.info("Step 2: Processing data")
        processed_data = {}
        
        for file_path in files:
            if file_path.endswith('.csv'):
                try:
                    # Load CSV
                    df = extractor.load_csv(file_path)
                    
                    # Clean data
                    cleaned_df = processor.clean_data(df)
                    
                    # Transform data (BMW specific)
                    transformed_df = processor.transform_bmw_data(cleaned_df)
                    
                    # Validate data
                    if processor.validate_data(transformed_df):
                        processed_data[os.path.basename(file_path)] = transformed_df
                        logger.info(f"Successfully processed {file_path}")
                    else:
                        logger.warning(f"Data validation failed for {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        # Step 3: Load data into database
        logger.info("Step 3: Loading data into database")
        
        for filename, df in processed_data.items():
            try:
                success = loader.load_bmw_sales(df, f"BMW Sales - {filename}")
                if success:
                    logger.info(f"Successfully loaded {filename} into database")
                else:
                    logger.error(f"Failed to load {filename} into database")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        
        # Step 4: Generate summary
        logger.info("Step 4: Generating ETL summary")
        
        total_records = sum(len(df) for df in processed_data.values())
        logger.info(f"ETL Pipeline completed successfully!")
        logger.info(f"Total records processed: {total_records}")
        logger.info(f"Files processed: {len(processed_data)}")
        
        # Get database stats
        stats = loader.get_database_stats()
        for table_name, table_info in stats.items():
            logger.info(f"{table_name}: {table_info.get('row_count', 0)} rows")
        
        return True
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        return False

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run ETL pipeline
    success = main()
    
    if success:
        print("✅ ETL pipeline completed successfully!")
        sys.exit(0)
    else:
        print("❌ ETL pipeline failed!")
        sys.exit(1)
