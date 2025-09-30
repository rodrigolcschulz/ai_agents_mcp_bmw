-- =====================================================
-- BMW SALES KPIs - Views e Métricas de Performance
-- =====================================================

-- 1. VIEW: Resumo Geral de Vendas por Ano
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_annual_sales AS
SELECT 
    year,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    SUM(price_usd * sales_volume) as total_sales_value,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    COUNT(DISTINCT region) as regions_count,
    COUNT(DISTINCT model) as models_count,
    COUNT(DISTINCT region) as regions_count_yearly
FROM bmw_sales
GROUP BY year
ORDER BY year;

-- 2. VIEW: Performance por Região
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_regional_performance AS
SELECT 
    region,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    SUM(price_usd * sales_volume) as total_sales_value,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    COUNT(DISTINCT model) as models_count,
    COUNT(DISTINCT year) as years_active,
    -- KPIs calculados
    ROUND((SUM(sales_volume) * 100.0 / SUM(SUM(sales_volume)) OVER())::numeric, 2) as market_share_units_pct,
    ROUND((SUM(price_usd * sales_volume) * 100.0 / SUM(SUM(price_usd * sales_volume)) OVER())::numeric, 2) as market_share_revenue_pct
FROM bmw_sales
GROUP BY region
ORDER BY total_revenue DESC;

-- 3. VIEW: Top Modelos por Performance
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_model_performance AS
SELECT 
    model,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    SUM(price_usd * sales_volume) as total_sales_value,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    COUNT(DISTINCT region) as regions_count,
    COUNT(DISTINCT year) as years_active,
    -- KPIs calculados
    ROUND((SUM(sales_volume) * 100.0 / SUM(SUM(sales_volume)) OVER())::numeric, 2) as market_share_units_pct,
    ROUND((SUM(price_usd * sales_volume) * 100.0 / SUM(SUM(price_usd * sales_volume)) OVER())::numeric, 2) as market_share_revenue_pct,
    -- Ranking
    RANK() OVER (ORDER BY SUM(sales_volume) DESC) as rank_by_units,
    RANK() OVER (ORDER BY SUM(price_usd * sales_volume) DESC) as rank_by_revenue
FROM bmw_sales
GROUP BY model
ORDER BY total_revenue DESC;

-- 4. VIEW: Tendências Mensais (REMOVED - No monthly data available)
-- =====================================================

-- 5. VIEW: Performance por Tipo de Combustível
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_fuel_type_performance AS
SELECT 
    fuel_type,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    SUM(price_usd * sales_volume) as total_sales_value,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    COUNT(DISTINCT model) as models_count,
    COUNT(DISTINCT region) as regions_count,
    -- KPIs calculados
    ROUND((SUM(sales_volume) * 100.0 / SUM(SUM(sales_volume)) OVER())::numeric, 2) as market_share_units_pct,
    ROUND((SUM(price_usd * sales_volume) * 100.0 / SUM(SUM(price_usd * sales_volume)) OVER())::numeric, 2) as market_share_revenue_pct
FROM bmw_sales
WHERE fuel_type IS NOT NULL AND fuel_type != 'Unknown'
GROUP BY fuel_type
ORDER BY total_revenue DESC;

-- 6. VIEW: Performance por Transmissão
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_transmission_performance AS
SELECT 
    transmission,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    SUM(price_usd * sales_volume) as total_sales_value,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    COUNT(DISTINCT model) as models_count,
    COUNT(DISTINCT region) as regions_count,
    -- KPIs calculados
    ROUND((SUM(sales_volume) * 100.0 / SUM(SUM(sales_volume)) OVER())::numeric, 2) as market_share_units_pct,
    ROUND((SUM(price_usd * sales_volume) * 100.0 / SUM(SUM(price_usd * sales_volume)) OVER())::numeric, 2) as market_share_revenue_pct
FROM bmw_sales
WHERE transmission IS NOT NULL AND transmission != 'Unknown'
GROUP BY transmission
ORDER BY total_revenue DESC;

-- 7. VIEW: Dashboard Executivo - KPIs Principais
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_executive_dashboard AS
SELECT 
    'Total Records' as metric_name,
    COUNT(*)::TEXT as metric_value,
    'count' as metric_unit
FROM bmw_sales
UNION ALL
SELECT 
    'Total Units Sold',
    SUM(sales_volume)::TEXT,
    'units'
FROM bmw_sales
UNION ALL
SELECT 
    'Total Revenue',
    CONCAT('$', ROUND((SUM(price_usd * sales_volume)/1000000000)::numeric, 2), 'B'),
    'USD'
FROM bmw_sales
UNION ALL
SELECT 
    'Total Sales Value',
    CONCAT('$', ROUND((SUM(price_usd * sales_volume)/1000000000)::numeric, 2), 'B'),
    'USD'
FROM bmw_sales
UNION ALL
SELECT 
    'Average Units per Record',
    ROUND(AVG(sales_volume)::numeric, 0)::TEXT,
    'units'
FROM bmw_sales
UNION ALL
SELECT 
    'Average Revenue per Record',
    CONCAT('$', ROUND(AVG(price_usd * sales_volume)::numeric, 0)),
    'USD'
FROM bmw_sales
UNION ALL
SELECT 
    'Number of Regions',
    COUNT(DISTINCT region)::TEXT,
    'count'
FROM bmw_sales
UNION ALL
SELECT 
    'Number of Models',
    COUNT(DISTINCT model)::TEXT,
    'count'
FROM bmw_sales
UNION ALL
SELECT 
    'Number of Regions',
    COUNT(DISTINCT region)::TEXT,
    'count'
FROM bmw_sales
UNION ALL
SELECT 
    'Years Covered',
    CONCAT(MIN(year), ' - ', MAX(year)),
    'period'
FROM bmw_sales;

-- 8. VIEW: Top 10 Modelos por Vendas
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_top_10_models AS
SELECT 
    model,
    total_units_sold,
    total_revenue,
    market_share_units_pct,
    market_share_revenue_pct,
    rank_by_units,
    rank_by_revenue
FROM analytics.kpi_model_performance
ORDER BY total_revenue DESC
LIMIT 10;

-- 9. VIEW: Top 5 Regiões por Performance
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_top_5_regions AS
SELECT 
    region,
    total_units_sold,
    total_revenue,
    market_share_units_pct,
    market_share_revenue_pct,
    models_count,
    years_active
FROM analytics.kpi_regional_performance
ORDER BY total_revenue DESC
LIMIT 5;

-- 10. VIEW: Crescimento Anual
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_annual_growth AS
SELECT 
    year,
    total_units_sold,
    total_revenue,
    LAG(total_units_sold) OVER (ORDER BY year) as prev_year_units,
    LAG(total_revenue) OVER (ORDER BY year) as prev_year_revenue,
    CASE 
        WHEN LAG(total_units_sold) OVER (ORDER BY year) > 0 
        THEN ROUND(((total_units_sold - LAG(total_units_sold) OVER (ORDER BY year)) * 100.0 / LAG(total_units_sold) OVER (ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as units_growth_pct,
    CASE 
        WHEN LAG(total_revenue) OVER (ORDER BY year) > 0 
        THEN ROUND(((total_revenue - LAG(total_revenue) OVER (ORDER BY year)) * 100.0 / LAG(total_revenue) OVER (ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as revenue_growth_pct
FROM analytics.kpi_annual_sales
ORDER BY year;

-- =====================================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- =====================================================

COMMENT ON VIEW analytics.kpi_annual_sales IS 'KPIs de vendas agregados por ano';
COMMENT ON VIEW analytics.kpi_regional_performance IS 'Performance de vendas por região com market share';
COMMENT ON VIEW analytics.kpi_model_performance IS 'Performance de vendas por modelo com rankings';
-- COMMENT ON VIEW analytics.kpi_monthly_trends IS 'Tendências mensais com crescimento período a período' (REMOVED);
COMMENT ON VIEW analytics.kpi_fuel_type_performance IS 'Performance por tipo de combustível';
COMMENT ON VIEW analytics.kpi_transmission_performance IS 'Performance por tipo de transmissão';
COMMENT ON VIEW analytics.kpi_executive_dashboard IS 'Dashboard executivo com KPIs principais';
COMMENT ON VIEW analytics.kpi_top_10_models IS 'Top 10 modelos por performance de vendas';
COMMENT ON VIEW analytics.kpi_top_5_regions IS 'Top 5 regiões por performance de vendas';
COMMENT ON VIEW analytics.kpi_annual_growth IS 'Crescimento anual de vendas e receita';

-- =====================================================
-- GRANTS E PERMISSÕES
-- =====================================================

GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;
