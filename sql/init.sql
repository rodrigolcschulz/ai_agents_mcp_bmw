-- Database initialization script for AI Data Engineering project

-- Create database if it doesn't exist
-- (This is handled by the POSTGRES_DB environment variable in docker-compose)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS staging;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO postgres;

-- Create indexes for better performance
-- (These will be created after tables are created by the application)

-- Create views for common queries
CREATE OR REPLACE VIEW analytics.sales_summary AS
SELECT 
    year,
    month,
    region,
    country,
    model,
    SUM(sales_units) as total_units,
    SUM(revenue) as total_revenue,
    AVG(sales_units) as avg_units,
    COUNT(*) as record_count
FROM bmw_sales
GROUP BY year, month, region, country, model;

CREATE OR REPLACE VIEW analytics.monthly_trends AS
SELECT 
    year,
    month,
    SUM(sales_units) as total_units,
    SUM(revenue) as total_revenue,
    COUNT(DISTINCT region) as regions_count,
    COUNT(DISTINCT model) as models_count
FROM bmw_sales
GROUP BY year, month
ORDER BY year, month;

CREATE OR REPLACE VIEW analytics.regional_performance AS
SELECT 
    region,
    country,
    SUM(sales_units) as total_units,
    SUM(revenue) as total_revenue,
    AVG(sales_units) as avg_units_per_record,
    COUNT(*) as record_count
FROM bmw_sales
GROUP BY region, country
ORDER BY total_revenue DESC;

-- Create function for data validation
CREATE OR REPLACE FUNCTION validate_sales_data()
RETURNS TABLE(
    validation_type TEXT,
    record_count BIGINT,
    status TEXT
) AS $$
BEGIN
    -- Check for negative sales
    RETURN QUERY
    SELECT 
        'Negative Sales'::TEXT,
        COUNT(*)::BIGINT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END::TEXT
    FROM bmw_sales 
    WHERE sales_units < 0 OR revenue < 0;
    
    -- Check for missing required fields
    RETURN QUERY
    SELECT 
        'Missing Required Fields'::TEXT,
        COUNT(*)::BIGINT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END::TEXT
    FROM bmw_sales 
    WHERE year IS NULL OR month IS NULL;
    
    -- Check for future dates
    RETURN QUERY
    SELECT 
        'Future Dates'::TEXT,
        COUNT(*)::BIGINT,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END::TEXT
    FROM bmw_sales 
    WHERE year > EXTRACT(YEAR FROM CURRENT_DATE) 
       OR (year = EXTRACT(YEAR FROM CURRENT_DATE) AND month > EXTRACT(MONTH FROM CURRENT_DATE));
END;
$$ LANGUAGE plpgsql;

-- Create function for data cleanup
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete query logs older than 90 days
    DELETE FROM query_logs 
    WHERE created_at < CURRENT_DATE - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete system metrics older than 30 days
    DELETE FROM system_metrics 
    WHERE recorded_at < CURRENT_DATE - INTERVAL '30 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT USAGE ON SCHEMA analytics TO postgres;
GRANT USAGE ON SCHEMA staging TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA staging TO postgres;

-- Insert initial system metrics
INSERT INTO system_metrics (metric_name, metric_value, metric_unit, tags) VALUES
('database_initialized', 1, 'boolean', '{"timestamp": "' || CURRENT_TIMESTAMP || '"}'),
('tables_created', 4, 'count', '{"tables": ["bmw_sales", "data_sources", "query_logs", "system_metrics"]}'),
('views_created', 3, 'count', '{"views": ["sales_summary", "monthly_trends", "regional_performance"]}');

-- Create comments for documentation
COMMENT ON SCHEMA analytics IS 'Analytics views and aggregated data';
COMMENT ON SCHEMA staging IS 'Staging area for data processing';
COMMENT ON FUNCTION validate_sales_data() IS 'Validates data quality in bmw_sales table';
COMMENT ON FUNCTION cleanup_old_logs() IS 'Cleans up old log entries to maintain performance';
COMMENT ON VIEW analytics.sales_summary IS 'Aggregated sales data by various dimensions';
COMMENT ON VIEW analytics.monthly_trends IS 'Monthly sales trends and metrics';
COMMENT ON VIEW analytics.regional_performance IS 'Regional performance analysis';
