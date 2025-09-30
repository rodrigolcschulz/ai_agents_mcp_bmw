"""
Database loader for inserting processed data into PostgreSQL
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseLoader:
    def __init__(self):
        """Initialize database loader"""
        # Database configuration
        self.DB_CONFIG = {
            'host': 'localhost',
            'port': 5433,
            'database': 'ai_data_engineering',
            'user': 'postgres',
            'password': 'postgres123',
            'client_encoding': 'utf8'
        }
    
    def create_tables(self):
        """Create all database tables"""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            conn.set_client_encoding('UTF8')
            cursor = conn.cursor()
            
            # Create BMW sales table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bmw_sales (
                    id SERIAL PRIMARY KEY,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    year_month VARCHAR(7),
                    region VARCHAR(100),
                    country VARCHAR(100),
                    model VARCHAR(100),
                    sales_units INTEGER,
                    revenue FLOAT,
                    total_sales FLOAT,
                    color VARCHAR(50),
                    fuel_type VARCHAR(50),
                    transmission VARCHAR(50),
                    engine_size FLOAT,
                    mileage_km INTEGER,
                    price_usd FLOAT,
                    sales_classification VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create data sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    source_type VARCHAR(50) NOT NULL,
                    source_url VARCHAR(500),
                    dataset_name VARCHAR(200),
                    file_path VARCHAR(500),
                    record_count INTEGER,
                    last_updated TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create query logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id SERIAL PRIMARY KEY,
                    user_query TEXT NOT NULL,
                    sql_query TEXT,
                    response TEXT,
                    execution_time FLOAT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    user_id VARCHAR(100),
                    session_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def clear_existing_data(self):
        """Clear existing BMW sales data"""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            conn.set_client_encoding('UTF8')
            cursor = conn.cursor()
            
            # Clear BMW sales data
            cursor.execute("DELETE FROM bmw_sales")
            
            # Clear data sources
            cursor.execute("DELETE FROM data_sources")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Cleared existing data")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False
    
    def safe_int(self, value, default=0):
        """Safely convert value to int"""
        try:
            if pd.isna(value):
                return default
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                return int(float(value))
            if hasattr(value, 'year'):  # datetime object
                return value.year
            return int(value)
        except:
            return default

    def safe_float(self, value, default=0.0):
        """Safely convert value to float"""
        try:
            if pd.isna(value):
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return float(value)
            return float(value)
        except:
            return default
    
    def load_bmw_sales(self, df: pd.DataFrame, 
                      source_name: str = "BMW Global Sales Analysis",
                      batch_size: int = 1000) -> bool:
        """
        Load BMW sales data into database
        
        Args:
            df: BMW sales DataFrame
            source_name: Name of the data source
            batch_size: Number of records to insert per batch
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting to load {len(df)} BMW sales records")
        
        try:
            # Create tables if they don't exist
            self.create_tables()
            
            # Record data source
            source_id = self._record_data_source(source_name, "kaggle", len(df))
            
            # Process data in batches
            total_inserted = 0
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                inserted_count = self._insert_bmw_batch(batch_df, source_id)
                total_inserted += inserted_count
                logger.info(f"Inserted batch {i//batch_size + 1}: {inserted_count} records")
            
            logger.info(f"Successfully loaded {total_inserted} BMW sales records")
            return True
            
        except Exception as e:
            logger.error(f"Error loading BMW sales data: {e}")
            return False
    
    def _record_data_source(self, name: str, source_type: str, record_count: int) -> int:
        """Record data source information"""
        conn = psycopg2.connect(**self.DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO data_sources (name, source_type, record_count, last_updated)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (name, source_type, record_count, datetime.now()))
            
            source_id = cursor.fetchone()[0]
            conn.commit()
            return source_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error recording data source: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _insert_bmw_batch(self, batch_df: pd.DataFrame, source_id: int) -> int:
        """Insert a batch of BMW sales records"""
        conn = psycopg2.connect(**self.DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        try:
            # Prepare data for insertion
            data_tuples = []
            for _, row in batch_df.iterrows():
                # Map DataFrame columns to database fields with proper type conversion
                year = self.safe_int(row.get('year', 2024), 2024)
                month = 1  # Default month since CSV doesn't have month data
                
                sales_volume = self.safe_int(row.get('sales_volume', 0), 0)
                price_usd = self.safe_float(row.get('price_usd', 0), 0)
                engine_size = self.safe_float(row.get('engine_size_l', 0), 0)
                mileage_km = self.safe_int(row.get('mileage_km', 0), 0)
                
                data_tuples.append((
                    year,  # year
                    month,  # month
                    f"{year}-01",  # year_month
                    str(row.get('region', 'Unknown'))[:100],  # region
                    str(row.get('region', 'Unknown'))[:100],  # country (use region)
                    str(row.get('model', 'Unknown'))[:100],  # model
                    sales_volume,  # sales_units
                    price_usd,  # revenue
                    price_usd * sales_volume,  # total_sales
                    str(row.get('color', 'Unknown'))[:50],  # color
                    str(row.get('fuel_type', 'Unknown'))[:50],  # fuel_type
                    str(row.get('transmission', 'Unknown'))[:50],  # transmission
                    engine_size,  # engine_size
                    mileage_km,  # mileage_km
                    price_usd,  # price_usd
                    str(row.get('sales_classification', 'Unknown'))[:50]  # sales_classification
                ))
            
            # Insert data
            insert_query = """
                INSERT INTO bmw_sales (year, month, year_month, region, country, model, sales_units, revenue, total_sales,
                                      color, fuel_type, transmission, engine_size, mileage_km, price_usd, sales_classification)
                VALUES %s
            """
            
            execute_values(cursor, insert_query, data_tuples)
            conn.commit()
            
            return len(data_tuples)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting BMW batch: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def log_query(self, user_query: str, sql_query: str = None, 
                  response: str = None, execution_time: float = None,
                  success: bool = True, error_message: str = None,
                  user_id: str = None, session_id: str = None):
        """Log AI agent query interactions"""
        conn = psycopg2.connect(**self.DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO query_logs (user_query, sql_query, response, execution_time, success, error_message, user_id, session_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_query, sql_query, response, execution_time, success, error_message, user_id, session_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error logging query: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a database table"""
        conn = psycopg2.connect(**self.DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        try:
            # Get table schema
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3]
                })
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            return {
                'table_name': table_name,
                'columns': columns,
                'row_count': row_count
            }
            
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results"""
        conn = psycopg2.connect(**self.DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            
            # Convert result to list of dictionaries
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        stats = {}
        
        # Get table information
        tables = ['bmw_sales', 'data_sources', 'query_logs']
        for table in tables:
            try:
                table_info = self.get_table_info(table)
                if table_info:
                    stats[table] = table_info
            except:
                pass
        
        return stats

def main():
    """Example usage"""
    loader = DatabaseLoader()
    
    # Create tables
    loader.create_tables()
    
    # Get database stats
    stats = loader.get_database_stats()
    print("Database Statistics:")
    for table, info in stats.items():
        print(f"  {table}: {info.get('row_count', 0)} rows")

if __name__ == "__main__":
    main()
