-- Notebook: 01_dw_hands_on
-- Execute cada bloco separadamente para acompanhar a construção do Data Warehouse.

-- 1. Bancos de dados
CREATE DATABASE IF NOT EXISTS dw_staging;
CREATE DATABASE IF NOT EXISTS dw;

-- 2. Staging: vendas
CREATE OR REPLACE TABLE dw_staging.vendas_raw AS
SELECT
  CAST(id_venda AS INT)                AS id_venda,
  CAST(id_cliente AS INT)              AS id_cliente,
  CAST(id_produto AS INT)              AS id_produto,
  CAST(data_venda AS DATE)             AS data_venda,
  CAST(quantidade AS INT)              AS quantidade,
  CAST(valor_total AS DOUBLE)          AS valor_total,
  CAST(id_loja AS INT)                 AS id_loja,
  CAST(id_vendedor AS INT)             AS id_vendedor,
  CAST(preco_unitario AS DOUBLE)       AS preco_unitario,
  CAST(desconto_percentual AS INT)     AS desconto_percentual,
  TRIM(forma_pagamento)                AS forma_pagamento,
  TRIM(canal_venda)                    AS canal_venda,
  TRIM(status_venda)                   AS status_venda
FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/vendas.csv',
  format => 'csv', header => 'true'
);

-- 3. Staging: clientes
CREATE OR REPLACE TABLE dw_staging.clientes_raw AS
SELECT
  CAST(id_cliente AS INT)   AS id_cliente,
  TRIM(nome_cliente)        AS nome_cliente,
  LOWER(TRIM(email))        AS email,
  TRIM(cidade)              AS cidade,
  TRIM(estado)              AS estado,
  TRIM(segmento)            AS segmento,
  CAST(data_cadastro AS DATE) AS data_cadastro
FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/clientes.csv',
  format => 'csv', header => 'true'
);

-- 4. Staging: produtos
CREATE OR REPLACE TABLE dw_staging.produtos_raw AS
SELECT
  CAST(id_produto AS INT)       AS id_produto,
  TRIM(nome_produto)            AS nome_produto,
  TRIM(categoria)               AS categoria,
  TRIM(marca)                   AS marca,
  CAST(preco_unitario AS DOUBLE) AS preco_lista,
  TRIM(ativo)                   AS ativo
FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/produtos.csv',
  format => 'csv', header => 'true'
);

-- 5. Staging: lojas
CREATE OR REPLACE TABLE dw_staging.lojas_raw AS
SELECT
  CAST(id_loja AS INT) AS id_loja,
  TRIM(nome_loja)      AS nome_loja,
  TRIM(cidade)         AS cidade,
  TRIM(estado)         AS estado,
  TRIM(tipo_loja)      AS tipo_loja
FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/lojas.csv',
  format => 'csv', header => 'true'
);

-- 6. Staging: vendedores
CREATE OR REPLACE TABLE dw_staging.vendedores_raw AS
SELECT
  CAST(id_vendedor AS INT) AS id_vendedor,
  TRIM(nome_vendedor)      AS nome_vendedor,
  CAST(id_loja AS INT)     AS id_loja,
  TRIM(equipe)             AS equipe
FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/vendedores.csv',
  format => 'csv', header => 'true'
);

-- 7. Dimensões
CREATE OR REPLACE TABLE dw.dim_cliente AS
SELECT * FROM dw_staging.clientes_raw;

CREATE OR REPLACE TABLE dw.dim_produto AS
SELECT * FROM dw_staging.produtos_raw;

CREATE OR REPLACE TABLE dw.dim_loja AS
SELECT * FROM dw_staging.lojas_raw;

CREATE OR REPLACE TABLE dw.dim_vendedor AS
SELECT * FROM dw_staging.vendedores_raw;

CREATE OR REPLACE TABLE dw.dim_tempo AS
SELECT DISTINCT
  data_venda,
  YEAR(data_venda)                         AS ano,
  MONTH(data_venda)                        AS mes,
  DATE_FORMAT(data_venda, 'yyyy-MM')       AS ano_mes,
  QUARTER(data_venda)                      AS trimestre,
  DAYOFWEEK(data_venda)                    AS dia_semana_numero,
  DATE_FORMAT(data_venda, 'EEEE')          AS dia_semana
FROM dw_staging.vendas_raw;

-- 8. Fato de vendas
CREATE OR REPLACE TABLE dw.fato_vendas AS
SELECT
  id_venda, id_cliente, id_produto, id_loja, id_vendedor,
  data_venda, quantidade, preco_unitario,
  desconto_percentual, valor_total,
  forma_pagamento, canal_venda, status_venda
FROM dw_staging.vendas_raw;

-- 9. Conferência
SHOW TABLES IN dw;
SELECT COUNT(*) AS total_vendas FROM dw.fato_vendas;

-- 10. Consulta analítica: faturamento por categoria e mês
SELECT
  t.ano_mes,
  p.categoria,
  ROUND(SUM(f.valor_total), 2) AS faturamento
FROM dw.fato_vendas f
JOIN dw.dim_produto p ON f.id_produto = p.id_produto
JOIN dw.dim_tempo t   ON f.data_venda = t.data_venda
WHERE f.status_venda = 'Concluída'
GROUP BY t.ano_mes, p.categoria
ORDER BY t.ano_mes, faturamento DESC;
