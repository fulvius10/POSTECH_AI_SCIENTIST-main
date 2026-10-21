-- Pesquisa de reconciliação, rede municipal. Não cria tabela.
WITH resultados AS (
  SELECT *
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE rede = '3' AND serie = '2'
), elegiveis AS (
  SELECT ano, id_municipio, peso_aluno, alfabetizado
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  WHERE serie = '2' AND rede = '3'
    AND presenca = '1' AND preenchimento_caderno = '1'
    AND alfabetizado IN ('0', '1')
    AND proficiencia IS NOT NULL AND NOT IS_NAN(proficiencia) AND NOT IS_INF(proficiencia)
    AND peso_aluno > 0 AND NOT IS_NAN(peso_aluno) AND NOT IS_INF(peso_aluno)
), calculo AS (
  SELECT
    ano, id_municipio,
    COUNT(*) AS avaliados_elegiveis,
    SUM(peso_aluno) AS soma_pesos_avaliados,
    SUM(IF(alfabetizado = '1', peso_aluno, 0)) AS soma_pesos_alfabetizados,
    100 * SAFE_DIVIDE(SUM(IF(alfabetizado = '1', peso_aluno, 0)), SUM(peso_aluno)) AS taxa_ponderada,
    100 * AVG(IF(alfabetizado = '1', 1.0, 0.0)) AS taxa_sem_peso
  FROM elegiveis
  GROUP BY ano, id_municipio
)
SELECT
  COALESCE(r.ano, c.ano) AS ano,
  COALESCE(r.id_municipio, c.id_municipio) AS id_municipio,
  c.avaliados_elegiveis, c.soma_pesos_avaliados, c.soma_pesos_alfabetizados,
  c.taxa_ponderada, c.taxa_sem_peso,
  r.taxa_alfabetizacao AS taxa_agregado,
  m.taxa_alfabetizacao AS taxa_publicacao_metas,
  c.taxa_ponderada - r.taxa_alfabetizacao AS diferenca_agregado_pp,
  c.taxa_ponderada - m.taxa_alfabetizacao AS diferenca_publicacao_pp
FROM resultados AS r
FULL OUTER JOIN calculo AS c USING (ano, id_municipio)
LEFT JOIN `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio` AS m
  ON COALESCE(r.ano, c.ano) = m.ano
  AND COALESCE(r.id_municipio, c.id_municipio) = m.id_municipio
  AND m.rede = 'Municipal'
ORDER BY ano, id_municipio;
