-- Contagens por recorte, não denominadores de taxas de alfabetização.
SELECT 'uf' AS tabela, ano, serie, rede, COUNT(*) AS registros
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.uf`
GROUP BY ano, serie, rede
UNION ALL
SELECT 'municipio', ano, serie, rede, COUNT(*)
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
GROUP BY ano, serie, rede
UNION ALL
SELECT 'alunos', ano, serie, rede, COUNT(*)
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
GROUP BY ano, serie, rede
ORDER BY tabela, ano, serie, rede;
