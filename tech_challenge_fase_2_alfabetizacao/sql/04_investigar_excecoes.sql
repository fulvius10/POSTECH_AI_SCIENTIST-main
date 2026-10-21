-- Os 216 casos na fonte investigada; resultado esperado pode mudar com atualizações.
WITH resultados_2024 AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE ano = 2024 AND serie = '2' AND rede = '3'
), resultados_2023 AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE ano = 2023 AND serie = '2' AND rede = '3'
), metas_2024 AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  WHERE ano = 2024 AND rede = 'Municipal'
), metas_2023 AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  WHERE ano = 2023 AND rede = 'Municipal'
)
SELECT
  r.id_municipio,
  r.ano,
  IF(m.id_municipio IS NULL, 'Sem registro de meta', 'Meta 2024 ausente') AS motivo,
  r.taxa_alfabetizacao AS resultado_2024,
  p.taxa_alfabetizacao AS resultado_2023_em_municipio,
  a.taxa_alfabetizacao AS resultado_2023_em_metas,
  a.percentual_participacao AS participacao_2023_em_metas,
  a.id_municipio IS NOT NULL AS tem_registro_meta_2023,
  m.meta_alfabetizacao_2024,
  m.meta_alfabetizacao_2025,
  m.meta_alfabetizacao_2030
FROM resultados_2024 AS r
LEFT JOIN metas_2024 AS m USING (ano, id_municipio)
LEFT JOIN resultados_2023 AS p ON r.id_municipio = p.id_municipio
LEFT JOIN metas_2023 AS a ON r.id_municipio = a.id_municipio
WHERE m.id_municipio IS NULL OR m.meta_alfabetizacao_2024 IS NULL
ORDER BY motivo, r.id_municipio;
