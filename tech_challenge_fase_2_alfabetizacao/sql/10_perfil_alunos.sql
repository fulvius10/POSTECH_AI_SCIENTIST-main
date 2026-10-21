-- Pesquisa: elegibilidade, pesos e coerência dos microdados. Não cria tabelas.
SELECT
  ano,
  rede,
  presenca,
  preenchimento_caderno,
  COUNT(*) AS registros,
  COUNTIF(alfabetizado IN ('0', '1')) AS classificacao_valida,
  COUNTIF(alfabetizado IS NULL) AS classificacao_nula,
  COUNTIF(alfabetizado IS NOT NULL AND alfabetizado NOT IN ('0', '1')) AS classificacao_desconhecida,
  COUNTIF(proficiencia IS NOT NULL AND NOT IS_NAN(proficiencia) AND NOT IS_INF(proficiencia)) AS proficiencia_valida,
  COUNTIF(peso_aluno IS NULL) AS peso_nulo,
  COUNTIF(peso_aluno = 0) AS peso_zero,
  COUNTIF(peso_aluno < 0) AS peso_negativo,
  COUNTIF(IS_NAN(peso_aluno) OR IS_INF(peso_aluno)) AS peso_nao_finito,
  COUNTIF(peso_aluno > 0 AND NOT IS_NAN(peso_aluno) AND NOT IS_INF(peso_aluno)) AS peso_positivo_finito,
  MIN(peso_aluno) AS menor_peso,
  MAX(peso_aluno) AS maior_peso,
  COUNTIF(
    alfabetizado IN ('0', '1')
    AND proficiencia IS NOT NULL
    AND NOT IS_NAN(proficiencia) AND NOT IS_INF(proficiencia)
    AND SAFE_CAST(alfabetizado AS INT64) != IF(proficiencia >= 743, 1, 0)
  ) AS divergencia_classificacao_corte
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
GROUP BY ano, rede, presenca, preenchimento_caderno
ORDER BY ano, rede, presenca, preenchimento_caderno;
