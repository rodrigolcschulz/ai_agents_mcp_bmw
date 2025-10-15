#!/usr/bin/env python3
"""
Script de inicialização automática do banco de dados
Detecta se o banco está vazio e roda ETL + Views automaticamente
"""
import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5433')),
        database=os.getenv('POSTGRES_DB', 'ai_data_engineering'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres123')
    )

def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready"""
    logger.info("Aguardando banco de dados...")
    
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            conn.close()
            logger.info("✅ Banco de dados disponível!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                logger.info(f"Tentativa {i+1}/{max_retries} - Aguardando {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"❌ Falha ao conectar ao banco: {e}")
                return False
    
    return False

def check_if_database_empty():
    """Check if bmw_sales table exists and has data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if bmw_sales table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'bmw_sales'
            )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.close()
            conn.close()
            return True  # Database is empty
        
        # Check if table has data
        cursor.execute("SELECT COUNT(*) FROM bmw_sales")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return count == 0
        
    except Exception as e:
        logger.error(f"Erro ao verificar banco: {e}")
        return True  # Assume empty on error

def check_if_views_exist():
    """Check if analytics views exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.views 
            WHERE table_schema = 'analytics'
        """)
        
        view_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return view_count > 0
        
    except Exception as e:
        logger.error(f"Erro ao verificar views: {e}")
        return False

def run_etl():
    """Run ETL pipeline"""
    logger.info("🚀 Executando ETL Pipeline...")
    
    try:
        from src.etl.pipeline import ETLPipeline
        
        pipeline = ETLPipeline()
        result = pipeline.run()
        
        if result.get('success'):
            logger.info(f"✅ ETL concluído! {result.get('records_loaded', 0)} registros carregados")
            return True
        else:
            logger.error(f"❌ Erro no ETL: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao executar ETL: {e}")
        return False

def create_kpi_views():
    """Create KPI views from SQL file"""
    logger.info("📊 Criando views de KPI...")
    
    try:
        # Read KPI views SQL file
        sql_file = os.path.join(os.path.dirname(__file__), '..', 'sql', 'kpis_views.sql')
        
        if not os.path.exists(sql_file):
            logger.error(f"❌ Arquivo não encontrado: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(sql_content)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Views de KPI criadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar views: {e}")
        return False

def main():
    """Main initialization function"""
    logger.info("="*60)
    logger.info("🚀 INICIALIZANDO BANCO DE DADOS")
    logger.info("="*60)
    
    # Step 1: Wait for database
    if not wait_for_db():
        logger.error("❌ Falha na inicialização: banco não disponível")
        sys.exit(1)
    
    # Step 2: Check if database is empty
    is_empty = check_if_database_empty()
    
    if is_empty:
        logger.info("📦 Banco de dados vazio detectado - iniciando carga inicial...")
        
        # Step 3: Run ETL
        if not run_etl():
            logger.error("❌ Falha ao executar ETL")
            sys.exit(1)
        
        # Step 4: Create views
        if not create_kpi_views():
            logger.error("❌ Falha ao criar views")
            sys.exit(1)
        
        logger.info("="*60)
        logger.info("✅ INICIALIZAÇÃO COMPLETA!")
        logger.info("="*60)
    else:
        logger.info("✅ Banco de dados já contém dados")
        
        # Check if views exist
        if not check_if_views_exist():
            logger.info("📊 Views não encontradas - criando...")
            if create_kpi_views():
                logger.info("✅ Views criadas!")
            else:
                logger.warning("⚠️ Falha ao criar views")
        else:
            logger.info("✅ Views já existem")
        
        logger.info("="*60)
        logger.info("✅ VERIFICAÇÃO COMPLETA!")
        logger.info("="*60)

if __name__ == "__main__":
    main()

