-- Consulta de pesquisa para conferir os códigos com a DTB do mesmo ano.
-- Não faz ingestão nem cria dimensão territorial.
SELECT 'municipio' AS fonte, ano, id_municipio
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
GROUP BY ano, id_municipio
UNION ALL
SELECT 'alunos', ano, id_municipio
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
GROUP BY ano, id_municipio
UNION ALL
SELECT 'metas_municipais', ano, id_municipio
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
GROUP BY ano, id_municipio
ORDER BY fonte, ano, id_municipio;
