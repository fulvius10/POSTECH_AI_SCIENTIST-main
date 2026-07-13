-- Consultas complementares para exploração analítica

-- 1. Top 10 produtos por faturamento
SELECT
  nome_produto,
  categoria,
  ROUND(SUM(valor_total), 2) AS faturamento
FROM datalake.curated_vendas_enriquecidas
WHERE status_venda = 'Concluída'
GROUP BY nome_produto, categoria
ORDER BY faturamento DESC
LIMIT 10;

-- 2. Desempenho por canal de venda
SELECT
  canal_venda,
  COUNT(DISTINCT id_venda) AS total_vendas,
  ROUND(SUM(valor_total), 2) AS faturamento,
  ROUND(AVG(valor_total), 2) AS ticket_medio
FROM datalake.curated_vendas_enriquecidas
WHERE status_venda = 'Concluída'
GROUP BY canal_venda
ORDER BY faturamento DESC;

-- 3. Faturamento por estado do cliente
SELECT
  estado_cliente,
  COUNT(DISTINCT id_cliente) AS clientes,
  ROUND(SUM(valor_total), 2) AS faturamento
FROM datalake.curated_vendas_enriquecidas
WHERE status_venda = 'Concluída'
GROUP BY estado_cliente
ORDER BY faturamento DESC;

-- 4. Top 10 clientes
SELECT *
FROM datalake.curated_cliente_360
ORDER BY faturamento_cliente DESC
LIMIT 10;

-- 5. Taxa de cancelamento
SELECT
  status_venda,
  COUNT(*) AS total_vendas,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentual
FROM datalake.curated_vendas_enriquecidas
GROUP BY status_venda;
