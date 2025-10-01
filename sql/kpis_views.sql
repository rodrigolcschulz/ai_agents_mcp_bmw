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

-- 11. VIEW: Análise de Preços por Segmento
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_price_analysis AS
SELECT 
    model,
    region,
    COUNT(*) as total_records,
    AVG(price_usd) as avg_price,
    MIN(price_usd) as min_price,
    MAX(price_usd) as max_price,
    STDDEV(price_usd) as price_stddev,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_usd) as median_price,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_usd) as price_q1,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_usd) as price_q3,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    -- Segmentação de preços
    CASE 
        WHEN AVG(price_usd) < 50000 THEN 'Entry Level'
        WHEN AVG(price_usd) < 80000 THEN 'Mid Range'
        WHEN AVG(price_usd) < 120000 THEN 'Premium'
        ELSE 'Luxury'
    END as price_segment
FROM bmw_sales
WHERE price_usd IS NOT NULL
GROUP BY model, region
ORDER BY avg_price DESC;

-- 12. VIEW: Performance por Cor
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_color_performance AS
SELECT 
    color,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    COUNT(DISTINCT model) as models_count,
    COUNT(DISTINCT region) as regions_count,
    -- KPIs calculados
    ROUND((SUM(sales_volume) * 100.0 / SUM(SUM(sales_volume)) OVER())::numeric, 2) as market_share_units_pct,
    ROUND((SUM(price_usd * sales_volume) * 100.0 / SUM(SUM(price_usd * sales_volume)) OVER())::numeric, 2) as market_share_revenue_pct,
    -- Ranking
    RANK() OVER (ORDER BY SUM(sales_volume) DESC) as rank_by_units,
    RANK() OVER (ORDER BY SUM(price_usd * sales_volume) DESC) as rank_by_revenue
FROM bmw_sales
WHERE color IS NOT NULL AND color != 'Unknown'
GROUP BY color
ORDER BY total_revenue DESC;

-- 13. VIEW: Análise de Eficiência por Modelo
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_model_efficiency AS
SELECT 
    model,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    AVG(price_usd) as avg_price,
    AVG(engine_size_l) as avg_engine_size,
    AVG(mileage_km) as avg_mileage,
    -- Métricas de eficiência
    ROUND((SUM(price_usd * sales_volume) / NULLIF(SUM(sales_volume), 0))::numeric, 2) as revenue_per_unit,
    ROUND((AVG(price_usd) / NULLIF(AVG(engine_size_l), 0))::numeric, 2) as price_per_liter,
    ROUND((SUM(sales_volume) / NULLIF(COUNT(*), 0))::numeric, 2) as units_per_record,
    -- Performance relativa
    RANK() OVER (ORDER BY (SUM(price_usd * sales_volume) / NULLIF(SUM(sales_volume), 0)) DESC) as efficiency_rank,
    RANK() OVER (ORDER BY SUM(sales_volume) DESC) as volume_rank
FROM bmw_sales
WHERE price_usd IS NOT NULL AND sales_volume IS NOT NULL
GROUP BY model
ORDER BY revenue_per_unit DESC;

-- 14. VIEW: Análise de Sazonalidade por Região
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_seasonal_analysis AS
SELECT 
    region,
    year,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    AVG(sales_volume) as avg_units_per_record,
    AVG(price_usd * sales_volume) as avg_revenue_per_record,
    -- Comparação com ano anterior
    LAG(SUM(sales_volume)) OVER (PARTITION BY region ORDER BY year) as prev_year_units,
    LAG(SUM(price_usd * sales_volume)) OVER (PARTITION BY region ORDER BY year) as prev_year_revenue,
    -- Crescimento
    CASE 
        WHEN LAG(SUM(sales_volume)) OVER (PARTITION BY region ORDER BY year) > 0 
        THEN ROUND(((SUM(sales_volume) - LAG(SUM(sales_volume)) OVER (PARTITION BY region ORDER BY year)) * 100.0 / LAG(SUM(sales_volume)) OVER (PARTITION BY region ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as units_growth_pct,
    CASE 
        WHEN LAG(SUM(price_usd * sales_volume)) OVER (PARTITION BY region ORDER BY year) > 0 
        THEN ROUND(((SUM(price_usd * sales_volume) - LAG(SUM(price_usd * sales_volume)) OVER (PARTITION BY region ORDER BY year)) * 100.0 / LAG(SUM(price_usd * sales_volume)) OVER (PARTITION BY region ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as revenue_growth_pct
FROM bmw_sales
GROUP BY region, year
ORDER BY region, year;

-- 15. VIEW: Top Performers por Múltiplas Métricas
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_top_performers AS
WITH model_metrics AS (
    SELECT 
        model,
        SUM(sales_volume) as total_units,
        SUM(price_usd * sales_volume) as total_revenue,
        AVG(price_usd) as avg_price,
        COUNT(DISTINCT region) as regions_count,
        COUNT(DISTINCT year) as years_active
    FROM bmw_sales
    GROUP BY model
),
ranked_models AS (
    SELECT 
        *,
        RANK() OVER (ORDER BY total_units DESC) as units_rank,
        RANK() OVER (ORDER BY total_revenue DESC) as revenue_rank,
        RANK() OVER (ORDER BY avg_price DESC) as price_rank,
        RANK() OVER (ORDER BY regions_count DESC) as coverage_rank
    FROM model_metrics
)
SELECT 
    model,
    total_units,
    total_revenue,
    avg_price,
    regions_count,
    years_active,
    units_rank,
    revenue_rank,
    price_rank,
    coverage_rank,
    -- Score composto (menor é melhor)
    (units_rank + revenue_rank + price_rank + coverage_rank) as composite_score,
    RANK() OVER (ORDER BY (units_rank + revenue_rank + price_rank + coverage_rank)) as overall_rank
FROM ranked_models
ORDER BY composite_score;

-- 16. VIEW: Análise de Correlação Preço-Volume
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_price_volume_correlation AS
SELECT 
    model,
    region,
    COUNT(*) as total_records,
    AVG(price_usd) as avg_price,
    SUM(sales_volume) as total_volume,
    AVG(sales_volume) as avg_volume_per_record,
    -- Correlação preço-volume
    CORR(price_usd, sales_volume) as price_volume_correlation,
    -- Segmentação
    CASE 
        WHEN AVG(price_usd) > 100000 AND SUM(sales_volume) > 2000000 THEN 'High Price, High Volume'
        WHEN AVG(price_usd) > 100000 AND SUM(sales_volume) <= 2000000 THEN 'High Price, Low Volume'
        WHEN AVG(price_usd) <= 100000 AND SUM(sales_volume) > 2000000 THEN 'Low Price, High Volume'
        ELSE 'Low Price, Low Volume'
    END as price_volume_segment
FROM bmw_sales
WHERE price_usd IS NOT NULL AND sales_volume IS NOT NULL
GROUP BY model, region
HAVING COUNT(*) > 1  -- Precisa de pelo menos 2 pontos para correlação
ORDER BY ABS(CORR(price_usd, sales_volume)) DESC;

-- 17. VIEW: Market Penetration por Região
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_market_penetration AS
SELECT 
    region,
    COUNT(DISTINCT model) as models_available,
    COUNT(DISTINCT year) as years_active,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    -- Penetração de mercado
    ROUND((COUNT(DISTINCT model) * 100.0 / (SELECT COUNT(DISTINCT model) FROM bmw_sales))::numeric, 2) as model_penetration_pct,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bmw_sales))::numeric, 2) as record_penetration_pct,
    ROUND((SUM(sales_volume) * 100.0 / (SELECT SUM(sales_volume) FROM bmw_sales))::numeric, 2) as volume_penetration_pct,
    ROUND((SUM(price_usd * sales_volume) * 100.0 / (SELECT SUM(price_usd * sales_volume) FROM bmw_sales))::numeric, 2) as revenue_penetration_pct,
    -- Diversidade de produtos
    COUNT(DISTINCT fuel_type) as fuel_types_available,
    COUNT(DISTINCT transmission) as transmission_types_available,
    COUNT(DISTINCT color) as colors_available
FROM bmw_sales
GROUP BY region
ORDER BY revenue_penetration_pct DESC;

-- 18. VIEW: Análise de Tendências Temporais
-- =====================================================
CREATE OR REPLACE VIEW analytics.kpi_temporal_trends AS
SELECT 
    year,
    COUNT(*) as total_records,
    SUM(sales_volume) as total_units_sold,
    SUM(price_usd * sales_volume) as total_revenue,
    AVG(price_usd) as avg_price,
    COUNT(DISTINCT model) as models_count,
    COUNT(DISTINCT region) as regions_count,
    -- Tendências
    LAG(SUM(sales_volume)) OVER (ORDER BY year) as prev_year_units,
    LAG(SUM(price_usd * sales_volume)) OVER (ORDER BY year) as prev_year_revenue,
    LAG(AVG(price_usd)) OVER (ORDER BY year) as prev_year_avg_price,
    -- Crescimento
    CASE 
        WHEN LAG(SUM(sales_volume)) OVER (ORDER BY year) > 0 
        THEN ROUND(((SUM(sales_volume) - LAG(SUM(sales_volume)) OVER (ORDER BY year)) * 100.0 / LAG(SUM(sales_volume)) OVER (ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as units_growth_pct,
    CASE 
        WHEN LAG(SUM(price_usd * sales_volume)) OVER (ORDER BY year) > 0 
        THEN ROUND(((SUM(price_usd * sales_volume) - LAG(SUM(price_usd * sales_volume)) OVER (ORDER BY year)) * 100.0 / LAG(SUM(price_usd * sales_volume)) OVER (ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as revenue_growth_pct,
    CASE 
        WHEN LAG(AVG(price_usd)) OVER (ORDER BY year) > 0 
        THEN ROUND(((AVG(price_usd) - LAG(AVG(price_usd)) OVER (ORDER BY year)) * 100.0 / LAG(AVG(price_usd)) OVER (ORDER BY year))::numeric, 2)
        ELSE NULL 
    END as price_growth_pct
FROM bmw_sales
GROUP BY year
ORDER BY year;

-- =====================================================
-- GRANTS E PERMISSÕES
-- =====================================================

GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;
