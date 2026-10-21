-- Conferência com os microdados disponíveis, não substitui resultado divulgado.
-- Prefixo UF do código IBGE, conferido contra a DTB na investigação territorial.
WITH elegiveis AS (
  SELECT ano, SUBSTR(id_municipio, 1, 2) AS codigo_uf, peso_aluno, alfabetizado
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  WHERE serie = '2' AND rede IN ('2', '3')
    AND presenca = '1' AND preenchimento_caderno = '1'
    AND alfabetizado IN ('0', '1')
    AND proficiencia IS NOT NULL AND NOT IS_NAN(proficiencia) AND NOT IS_INF(proficiencia)
    AND peso_aluno > 0 AND NOT IS_NAN(peso_aluno) AND NOT IS_INF(peso_aluno)
)
SELECT
  ano,
  codigo_uf, -- NULL identifica o agregado dos microdados disponíveis no ano.
  COUNT(*) AS elegiveis,
  SUM(peso_aluno) AS soma_pesos,
  SUM(IF(alfabetizado = '1', peso_aluno, 0)) AS pesos_alfabetizados,
  100 * SAFE_DIVIDE(SUM(IF(alfabetizado = '1', peso_aluno, 0)), SUM(peso_aluno)) AS taxa_ponderada
FROM elegiveis
GROUP BY GROUPING SETS ((ano, codigo_uf), (ano))
ORDER BY ano, codigo_uf;
