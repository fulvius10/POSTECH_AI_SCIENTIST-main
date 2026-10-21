WITH resultados AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE ano = 2024 AND serie = '2' AND rede = '3'
), metas AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  WHERE ano = 2024 AND rede = 'Municipal'
), comparacao AS (
  SELECT
    r.*,
    m.id_municipio AS id_meta,
    m.meta_alfabetizacao_2024,
    m.taxa_alfabetizacao AS taxa_na_tabela_metas
  FROM resultados AS r
  LEFT JOIN metas AS m USING (ano, id_municipio)
)
SELECT
  (SELECT COUNT(*) FROM resultados) AS linhas_resultado,
  (SELECT COUNT(*) FROM metas) AS linhas_meta,
  COUNT(*) AS linhas_apos_join,
  COUNTIF(id_meta IS NOT NULL) AS com_correspondencia,
  COUNTIF(id_meta IS NULL) AS sem_correspondencia,
  COUNTIF(id_meta IS NOT NULL AND meta_alfabetizacao_2024 IS NULL) AS meta_2024_nula,
  COUNTIF(taxa_alfabetizacao IS NULL) AS resultado_nulo,
  COUNTIF(taxa_alfabetizacao IS NOT NULL AND meta_alfabetizacao_2024 IS NOT NULL) AS comparaveis,
  COUNTIF(taxa_alfabetizacao >= meta_alfabetizacao_2024) AS atingiu,
  COUNTIF(taxa_alfabetizacao < meta_alfabetizacao_2024) AS nao_atingiu,
  COUNTIF(ABS(taxa_alfabetizacao - taxa_na_tabela_metas) > 0.01) AS divergencias_acima_001_pp,
  100 * SAFE_DIVIDE(COUNTIF(id_meta IS NOT NULL), COUNT(*)) AS correspondencia_percentual,
  100 * SAFE_DIVIDE(
    COUNTIF(taxa_alfabetizacao IS NOT NULL AND meta_alfabetizacao_2024 IS NOT NULL),
    COUNT(*)
  ) AS comparaveis_percentual
FROM comparacao;
