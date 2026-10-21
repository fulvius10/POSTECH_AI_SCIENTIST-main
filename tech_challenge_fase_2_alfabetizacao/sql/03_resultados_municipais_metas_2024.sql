-- Rede municipal: código 3 em municipio e texto Municipal nas metas.
-- O filtro de rede das metas no ON preserva resultados sem correspondência.
SELECT
  r.id_municipio,
  r.ano,
  r.taxa_alfabetizacao AS resultado_2024,
  m.meta_alfabetizacao_2024,
  ROUND(r.taxa_alfabetizacao - m.meta_alfabetizacao_2024, 2)
    AS saldo_pontos_percentuais,
  m.meta_alfabetizacao_2030,
  CASE
    WHEN m.id_municipio IS NULL THEN 'Sem registro de meta'
    WHEN m.meta_alfabetizacao_2024 IS NULL THEN 'Meta 2024 ausente'
    WHEN r.taxa_alfabetizacao IS NULL THEN 'Resultado ausente'
    WHEN r.taxa_alfabetizacao >= m.meta_alfabetizacao_2024 THEN 'Atingiu'
    ELSE 'Não atingiu'
  END AS situacao
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio` AS r
LEFT JOIN `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio` AS m
  ON r.id_municipio = m.id_municipio
  AND r.ano = m.ano
  AND m.rede = 'Municipal'
WHERE r.ano = 2024
  AND r.serie = '2'
  AND r.rede = '3'
ORDER BY r.id_municipio;
