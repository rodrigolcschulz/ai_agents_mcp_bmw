"""
Kaggle data extractor with improved functionality
"""
import os
import pandas as pd
import kagglehub
from kaggle.api.kaggle_api_extended import KaggleApi
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KaggleExtractor:
    def __init__(self):
        """Initialize Kaggle API"""
        self.api = KaggleApi()
        self.api.authenticate()
        
    def download_dataset(self, dataset_name, download_path="data/raw"):
        """
        Download dataset from Kaggle
        
        Args:
            dataset_name (str): Kaggle dataset name (e.g., 'sidraaazam/bmw-global-sales-analysis')
            download_path (str): Local path to save the dataset
            
        Returns:
            str: Path to downloaded dataset
        """
        try:
            # Create download directory if it doesn't exist
            os.makedirs(download_path, exist_ok=True)
            
            # Download dataset using kagglehub
            path = kagglehub.dataset_download(dataset_name)
            logger.info(f"Dataset downloaded to: {path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Error downloading dataset {dataset_name}: {e}")
            raise
    
    def list_files(self, dataset_path):
        """List all files in the downloaded dataset"""
        files = []
        for root, dirs, filenames in os.walk(dataset_path):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        return files
    
    def load_csv(self, file_path, **kwargs):
        """
        Load CSV file into pandas DataFrame
        
        Args:
            file_path (str): Path to CSV file
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            pd.DataFrame: Loaded data
        """
        try:
            df = pd.read_csv(file_path, **kwargs)
            logger.info(f"Loaded CSV with shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
            raise
    
    def get_dataset_info(self, dataset_name):
        """Get information about a dataset"""
        try:
            # This would require additional Kaggle API calls
            # For now, return basic info
            return {
                "name": dataset_name,
                "status": "downloaded"
            }
        except Exception as e:
            logger.error(f"Error getting dataset info: {e}")
            return None

def main():
    """Example usage"""
    extractor = KaggleExtractor()
    
    # Download BMW dataset
    dataset_path = extractor.download_dataset("sidraaazam/bmw-global-sales-analysis")
    
    # List files
    files = extractor.list_files(dataset_path)
    print("Downloaded files:")
    for file in files:
        print(f"  - {file}")
    
    # Load CSV files
    for file in files:
        if file.endswith('.csv'):
            try:
                df = extractor.load_csv(file)
                print(f"\n{os.path.basename(file)}:")
                print(f"  Shape: {df.shape}")
                print(f"  Columns: {list(df.columns)}")
                print(f"  First few rows:")
                print(df.head())
            except Exception as e:
                print(f"Error loading {file}: {e}")

if __name__ == "__main__":
    main()
