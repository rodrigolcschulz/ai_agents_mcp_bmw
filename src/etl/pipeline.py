"""
ETL Pipeline Runner - Versão Organizada e Limpa
"""
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from etl.kaggle_extractor import KaggleExtractor
from etl.data_processor import DataProcessor
from database.loader import DatabaseLoader

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
        # Initialize components
        extractor = KaggleExtractor()
        processor = DataProcessor()
        loader = DatabaseLoader()
        
        # Step 1: Create tables
        logger.info("Step 1: Creating database tables")
        if not loader.create_tables():
            logger.error("Failed to create tables")
            return False
        
        # Step 2: Clear existing data
        logger.info("Step 2: Clearing existing data")
        loader.clear_existing_data()
        
        # Step 3: Extract data from Kaggle
        logger.info("Step 3: Extracting data from Kaggle")
        dataset_path = extractor.download_dataset("sidraaazam/bmw-global-sales-analysis")
        
        # List downloaded files
        files = extractor.list_files(dataset_path)
        logger.info(f"Downloaded {len(files)} files")
        
        # Step 4: Process data
        logger.info("Step 4: Processing data")
        total_records = 0
        
        for file_path in files:
            if file_path.endswith('.csv'):
                try:
                    logger.info(f"Processing file: {file_path}")
                    
                    # Load CSV
                    df = extractor.load_csv(file_path)
                    logger.info(f"Loaded CSV with shape: {df.shape}")
                    logger.info(f"Columns: {list(df.columns)}")
                    
                    # Clean data
                    cleaned_df = processor.clean_data(df)
                    
                    # Transform data (BMW specific)
                    transformed_df = processor.transform_bmw_data(cleaned_df)
                    
                    # Validate data
                    if processor.validate_data(transformed_df):
                        # Load into database using DatabaseLoader
                        filename = os.path.basename(file_path)
                        success = loader.load_bmw_sales(transformed_df, f"BMW Sales - {filename}")
                        if success:
                            total_records += len(transformed_df)
                            logger.info(f"Successfully processed {filename}: {len(transformed_df)} records")
                        else:
                            logger.error(f"Failed to load {filename}")
                    else:
                        logger.warning(f"Data validation failed for {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        # Step 5: Generate summary
        logger.info("Step 5: Generating ETL summary")
        
        logger.info(f"ETL Pipeline completed successfully!")
        logger.info(f"Total records processed: {total_records}")
        
        # Get database stats
        stats = loader.get_database_stats()
        for table_name, table_info in stats.items():
            logger.info(f"{table_name}: {table_info.get('row_count', 0)} rows")
        
        return True
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run ETL pipeline
    success = main()
    
    if success:
        print("ETL pipeline completed successfully!")
        sys.exit(0)
    else:
        print("ETL pipeline failed!")
        sys.exit(1)
