"""
Database loader for inserting processed data into PostgreSQL
"""
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..config.database import engine, Base
from ..models.database_models import BMWSales, DataSource, QueryLog, SystemMetrics

logger = logging.getLogger(__name__)

class DatabaseLoader:
    def __init__(self):
        """Initialize database loader"""
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
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
        session = self.SessionLocal()
        try:
            data_source = DataSource(
                name=name,
                source_type=source_type,
                record_count=record_count,
                last_updated=datetime.now()
            )
            session.add(data_source)
            session.commit()
            session.refresh(data_source)
            return data_source.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording data source: {e}")
            raise
        finally:
            session.close()
    
    def _insert_bmw_batch(self, batch_df: pd.DataFrame, source_id: int) -> int:
        """Insert a batch of BMW sales records"""
        session = self.SessionLocal()
        try:
            records = []
            for _, row in batch_df.iterrows():
                # Map DataFrame columns to model fields
                record = BMWSales(
                    year=row.get('year'),
                    month=row.get('month'),
                    year_month=row.get('year_month'),
                    region=row.get('region'),
                    country=row.get('country'),
                    model=row.get('model'),
                    sales_units=row.get('sales_units'),
                    revenue=row.get('revenue'),
                    total_sales=row.get('total_sales')
                )
                records.append(record)
            
            session.add_all(records)
            session.commit()
            return len(records)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting BMW batch: {e}")
            raise
        finally:
            session.close()
    
    def log_query(self, user_query: str, sql_query: str = None, 
                  response: str = None, execution_time: float = None,
                  success: bool = True, error_message: str = None,
                  user_id: str = None, session_id: str = None):
        """Log AI agent query interactions"""
        session = self.SessionLocal()
        try:
            query_log = QueryLog(
                user_query=user_query,
                sql_query=sql_query,
                response=response,
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                user_id=user_id,
                session_id=session_id
            )
            session.add(query_log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging query: {e}")
        finally:
            session.close()
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a database table"""
        session = self.SessionLocal()
        try:
            # Get table schema
            result = session.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3]
                })
            
            # Get row count
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()
            
            return {
                'table_name': table_name,
                'columns': columns,
                'row_count': row_count
            }
            
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {}
        finally:
            session.close()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results"""
        session = self.SessionLocal()
        try:
            result = session.execute(text(query))
            
            # Convert result to list of dictionaries
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        stats = {}
        
        # Get table information
        tables = ['bmw_sales', 'data_sources', 'query_logs', 'system_metrics']
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
