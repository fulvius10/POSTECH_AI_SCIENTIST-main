-- Zero significa nenhuma chave repetida. Esta consulta ainda não bloqueia publicação.
SELECT 'municipio' AS tabela, COUNT(*) AS chaves_duplicadas
FROM (
  SELECT ano, id_municipio, serie, rede
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  GROUP BY ano, id_municipio, serie, rede
  HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'meta_alfabetizacao_municipio', COUNT(*)
FROM (
  SELECT ano, id_municipio, rede
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  GROUP BY ano, id_municipio, rede
  HAVING COUNT(*) > 1
);
