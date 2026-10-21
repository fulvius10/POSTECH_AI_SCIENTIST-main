-- Investigar cobertura e variação da meta histórica entre contextos da fonte.
-- O campo ano é ano do resultado na linha, não data comprovada de publicação.
SELECT
  'BRASIL' AS nivel_territorial,
  'BR' AS id_territorio,
  ano AS ano_referencia_fonte,
  rede,
  taxa_alfabetizacao,
  meta_alfabetizacao_2024,
  meta_alfabetizacao_2030
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil`
UNION ALL
SELECT
  'UF',
  sigla_uf,
  ano,
  rede,
  taxa_alfabetizacao,
  meta_alfabetizacao_2024,
  meta_alfabetizacao_2030
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf`
ORDER BY nivel_territorial, id_territorio, ano_referencia_fonte;
