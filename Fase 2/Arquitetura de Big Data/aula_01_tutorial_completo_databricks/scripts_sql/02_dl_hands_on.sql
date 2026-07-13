-- Notebook: 02_dl_hands_on
-- Implementação de Data Lake em camadas: RAW, REFINED e CURATED.

CREATE DATABASE IF NOT EXISTS datalake;

-- 1. Camada RAW: preserva o conteúdo dos arquivos como foi recebido
CREATE OR REPLACE TABLE datalake.raw_vendas AS
SELECT * FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/vendas.csv',
  format => 'csv', header => 'true'
);

CREATE OR REPLACE TABLE datalake.raw_clientes AS
SELECT * FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/clientes.csv',
  format => 'csv', header => 'true'
);

CREATE OR REPLACE TABLE datalake.raw_produtos AS
SELECT * FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/produtos.csv',
  format => 'csv', header => 'true'
);

CREATE OR REPLACE TABLE datalake.raw_lojas AS
SELECT * FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/lojas.csv',
  format => 'csv', header => 'true'
);

CREATE OR REPLACE TABLE datalake.raw_vendedores AS
SELECT * FROM read_files(
  '/Volumes/workspace/default/tutorial_fiap/vendedores.csv',
  format => 'csv', header => 'true'
);

-- 2. Camada REFINED: tipagem, padronização e regras básicas de qualidade
CREATE OR REPLACE TABLE datalake.refined_vendas AS
SELECT
  TRY_CAST(id_venda AS INT)                AS id_venda,
  TRY_CAST(id_cliente AS INT)              AS id_cliente,
  TRY_CAST(id_produto AS INT)              AS id_produto,
  TRY_CAST(data_venda AS DATE)             AS data_venda,
  TRY_CAST(quantidade AS INT)              AS quantidade,
  TRY_CAST(valor_total AS DOUBLE)          AS valor_total,
  TRY_CAST(id_loja AS INT)                 AS id_loja,
  TRY_CAST(id_vendedor AS INT)             AS id_vendedor,
  TRY_CAST(preco_unitario AS DOUBLE)       AS preco_unitario,
  TRY_CAST(desconto_percentual AS INT)     AS desconto_percentual,
  TRIM(forma_pagamento)                    AS forma_pagamento,
  TRIM(canal_venda)                        AS canal_venda,
  TRIM(status_venda)                       AS status_venda
FROM datalake.raw_vendas
WHERE TRY_CAST(id_venda AS INT) IS NOT NULL
  AND TRY_CAST(valor_total AS DOUBLE) >= 0;

CREATE OR REPLACE TABLE datalake.refined_clientes AS
SELECT
  TRY_CAST(id_cliente AS INT)    AS id_cliente,
  INITCAP(TRIM(nome_cliente))    AS nome_cliente,
  LOWER(TRIM(email))             AS email,
  INITCAP(TRIM(cidade))          AS cidade,
  UPPER(TRIM(estado))            AS estado,
  TRIM(segmento)                 AS segmento,
  TRY_CAST(data_cadastro AS DATE) AS data_cadastro
FROM datalake.raw_clientes
WHERE TRY_CAST(id_cliente AS INT) IS NOT NULL;

CREATE OR REPLACE TABLE datalake.refined_produtos AS
SELECT
  TRY_CAST(id_produto AS INT)        AS id_produto,
  TRIM(nome_produto)                 AS nome_produto,
  TRIM(categoria)                    AS categoria,
  TRIM(marca)                        AS marca,
  TRY_CAST(preco_unitario AS DOUBLE) AS preco_lista,
  TRIM(ativo)                        AS ativo
FROM datalake.raw_produtos
WHERE TRY_CAST(id_produto AS INT) IS NOT NULL;

CREATE OR REPLACE TABLE datalake.refined_lojas AS
SELECT
  TRY_CAST(id_loja AS INT) AS id_loja,
  TRIM(nome_loja)          AS nome_loja,
  INITCAP(TRIM(cidade))    AS cidade,
  UPPER(TRIM(estado))      AS estado,
  TRIM(tipo_loja)          AS tipo_loja
FROM datalake.raw_lojas
WHERE TRY_CAST(id_loja AS INT) IS NOT NULL;

CREATE OR REPLACE TABLE datalake.refined_vendedores AS
SELECT
  TRY_CAST(id_vendedor AS INT) AS id_vendedor,
  INITCAP(TRIM(nome_vendedor)) AS nome_vendedor,
  TRY_CAST(id_loja AS INT)     AS id_loja,
  TRIM(equipe)                 AS equipe
FROM datalake.raw_vendedores
WHERE TRY_CAST(id_vendedor AS INT) IS NOT NULL;

-- 3. Camada CURATED: produto analítico de vendas enriquecidas
CREATE OR REPLACE TABLE datalake.curated_vendas_enriquecidas AS
SELECT
  v.id_venda, v.data_venda,
  YEAR(v.data_venda)                   AS ano,
  MONTH(v.data_venda)                  AS mes,
  DATE_FORMAT(v.data_venda, 'yyyy-MM') AS ano_mes,
  v.quantidade, v.preco_unitario,
  v.desconto_percentual, v.valor_total,
  v.forma_pagamento, v.canal_venda, v.status_venda,
  c.id_cliente, c.nome_cliente, c.segmento,
  c.cidade AS cidade_cliente, c.estado AS estado_cliente,
  p.id_produto, p.nome_produto, p.categoria, p.marca,
  l.id_loja, l.nome_loja, l.cidade AS cidade_loja, l.estado AS estado_loja,
  vd.id_vendedor, vd.nome_vendedor, vd.equipe
FROM datalake.refined_vendas v
LEFT JOIN datalake.refined_clientes c   ON v.id_cliente = c.id_cliente
LEFT JOIN datalake.refined_produtos p   ON v.id_produto = p.id_produto
LEFT JOIN datalake.refined_lojas l      ON v.id_loja = l.id_loja
LEFT JOIN datalake.refined_vendedores vd ON v.id_vendedor = vd.id_vendedor;

-- 4. Curated: faturamento mensal por categoria
CREATE OR REPLACE TABLE datalake.curated_faturamento_categoria_mensal AS
SELECT
  ano_mes,
  categoria,
  COUNT(DISTINCT id_venda)        AS total_vendas,
  SUM(quantidade)                 AS itens_vendidos,
  ROUND(SUM(valor_total), 2)      AS faturamento_total,
  ROUND(AVG(valor_total), 2)      AS ticket_medio
FROM datalake.curated_vendas_enriquecidas
WHERE status_venda = 'Concluída'
GROUP BY ano_mes, categoria;

-- 5. Curated: visão Cliente 360 simplificada
CREATE OR REPLACE TABLE datalake.curated_cliente_360 AS
SELECT
  id_cliente,
  nome_cliente,
  segmento,
  cidade_cliente,
  estado_cliente,
  COUNT(DISTINCT id_venda)       AS quantidade_compras,
  ROUND(SUM(valor_total), 2)     AS faturamento_cliente,
  ROUND(AVG(valor_total), 2)     AS ticket_medio,
  MAX(data_venda)                AS ultima_compra
FROM datalake.curated_vendas_enriquecidas
WHERE status_venda = 'Concluída'
GROUP BY id_cliente, nome_cliente, segmento, cidade_cliente, estado_cliente;

-- 6. Curated: desempenho comercial das lojas
CREATE OR REPLACE TABLE datalake.curated_desempenho_loja AS
SELECT
  id_loja,
  nome_loja,
  cidade_loja,
  estado_loja,
  COUNT(DISTINCT id_venda)       AS total_vendas,
  ROUND(SUM(valor_total), 2)     AS faturamento_total,
  ROUND(AVG(valor_total), 2)     AS ticket_medio
FROM datalake.curated_vendas_enriquecidas
WHERE status_venda = 'Concluída'
GROUP BY id_loja, nome_loja, cidade_loja, estado_loja;

-- 7. Validação de volume entre RAW e REFINED
SELECT 'raw_vendas' AS tabela, COUNT(*) AS registros FROM datalake.raw_vendas
UNION ALL
SELECT 'refined_vendas', COUNT(*) FROM datalake.refined_vendas;

-- 8. Consulta final
SELECT *
FROM datalake.curated_faturamento_categoria_mensal
ORDER BY ano_mes, faturamento_total DESC;
