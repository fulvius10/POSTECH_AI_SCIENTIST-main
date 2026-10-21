-- Pesquisa de duplicidade da chave candidata e classificação fora da avaliação válida.
WITH duplicadas AS (
  SELECT ano, id_municipio, id_escola, id_aluno, serie, rede, COUNT(*) AS repeticoes
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  GROUP BY ano, id_municipio, id_escola, id_aluno, serie, rede
  HAVING COUNT(*) > 1
), excluidos AS (
  SELECT ano, COUNT(*) AS sem_avaliacao_valida,
    COUNTIF(alfabetizado = '0') AS classificados_zero,
    COUNTIF(alfabetizado = '1') AS classificados_um
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  WHERE presenca = '0' OR preenchimento_caderno = '0'
  GROUP BY ano
)
SELECT
  e.*,
  (SELECT COUNT(*) FROM duplicadas d WHERE d.ano = e.ano) AS chaves_candidatas_duplicadas,
  (SELECT COALESCE(SUM(repeticoes - 1), 0) FROM duplicadas d WHERE d.ano = e.ano) AS linhas_repetidas_excedentes
FROM excluidos e
ORDER BY ano;
