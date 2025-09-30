"""
Database loader for BMW sales data
"""
import os
import sys
import psycopg2
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.database import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseLoader:
    def __init__(self):
        """Initialize database loader"""
        self.config = DATABASE_CONFIG
        self.connection = None
        
    def get_connection(self):
        """Get database connection"""
        if not self.connection:
            self.connection = psycopg2.connect(**self.config)
        return self.connection
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_tables(self) -> bool:
        """Create BMW sales table"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create schema if not exists
            cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
            
            # Drop table if exists
            cursor.execute("DROP TABLE IF EXISTS bmw_sales CASCADE;")
            
            # Create BMW sales table
            create_table_sql = """
            CREATE TABLE bmw_sales (
                id SERIAL PRIMARY KEY,
                model VARCHAR(100),
                year INTEGER,
                region VARCHAR(100),
                color VARCHAR(50),
                fuel_type VARCHAR(50),
                transmission VARCHAR(50),
                engine_size_l DECIMAL(5,2),
                mileage_km INTEGER,
                price_usd DECIMAL(12,2),
                sales_volume INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("BMW sales table created successfully")
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def clear_existing_data(self) -> bool:
        """Clear existing data from tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("TRUNCATE TABLE bmw_sales RESTART IDENTITY CASCADE;")
            conn.commit()
            
            logger.info("Existing data cleared successfully")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error clearing existing data: {e}")
            return False
    
    def load_bmw_sales(self, df: pd.DataFrame, source_name: str) -> bool:
        """Load BMW sales data into database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Prepare data for insertion
            records = []
            for _, row in df.iterrows():
                record = (
                    str(row.get('model', '')),
                    int(row.get('year', 0)) if pd.notna(row.get('year')) else None,
                    str(row.get('region', '')),
                    str(row.get('color', '')),
                    str(row.get('fuel_type', '')),
                    str(row.get('transmission', '')),
                    float(row.get('engine_size_l', 0)) if pd.notna(row.get('engine_size_l')) else None,
                    int(row.get('mileage_km', 0)) if pd.notna(row.get('mileage_km')) else None,
                    float(row.get('price_usd', 0)) if pd.notna(row.get('price_usd')) else None,
                    int(row.get('sales_volume', 0)) if pd.notna(row.get('sales_volume')) else None
                )
                records.append(record)
            
            # Insert data
            insert_sql = """
            INSERT INTO bmw_sales 
            (model, year, region, color, fuel_type, transmission, engine_size_l, mileage_km, price_usd, sales_volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_sql, records)
            conn.commit()
            
            logger.info(f"Successfully loaded {len(records)} records from {source_name}")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error loading BMW sales data: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Get table row counts
            cursor.execute("SELECT COUNT(*) FROM bmw_sales;")
            stats['bmw_sales'] = {'row_count': cursor.fetchone()[0]}
            
            cursor.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

def main():
    """Test database loader"""
    loader = DatabaseLoader()
    
    # Test connection
    if loader.test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return
    
    # Create tables
    if loader.create_tables():
        print("✅ Tables created successfully")
    else:
        print("❌ Failed to create tables")
        return
    
    # Get stats
    stats = loader.get_database_stats()
    print(f"📊 Database stats: {stats}")
    
    loader.close_connection()

if __name__ == "__main__":
    main()
