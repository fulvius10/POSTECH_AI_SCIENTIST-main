-- Leitura de metadados; não cria tabelas nem extrai microdados.
SELECT
  table_id AS tabela,
  row_count AS registros,
  size_bytes AS bytes_logicos,
  TIMESTAMP_MILLIS(last_modified_time) AS ultima_alteracao
FROM `basedosdados.br_inep_avaliacao_alfabetizacao.__TABLES__`
ORDER BY table_id;
