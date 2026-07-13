# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Carga da Camada Silver
# MAGIC
# MAGIC Este notebook lê a Bronze e cria a Silver.
# MAGIC
# MAGIC A Silver aplica limpeza, padronização, tipagem e deduplicação para deixar as tabelas reutilizáveis.

# COMMAND ----------
from pyspark.sql import functions as F

bronze_vendas = "bronze.aula3_vendas_raw"
bronze_clientes = "bronze.aula3_clientes_raw"

for tabela in [bronze_vendas, bronze_clientes]:
    try:
        spark.read.table(tabela).limit(1).count()
    except Exception as erro:
        raise ValueError(f"Tabela {tabela} não encontrada. Execute primeiro 02_carga_camada_bronze.py.") from erro

df_vendas = spark.read.table(bronze_vendas).drop("_data_ingestao", "_fonte")
df_clientes = spark.read.table(bronze_clientes).drop("_data_ingestao", "_fonte")

# Processo Silver 1: seleção do contrato de colunas usado pela aula.
df_base = df_vendas.select(
    "id_venda", "data_venda", "produto", "categoria", "quantidade",
    "preco_unitario", "estado", "id_cliente", "cupom", "origem", "status_bruto"
)

# Processo Silver 2: padronização de nomes, tipos, textos e campos calculados.
df_tratado = (
    df_base
    .withColumnRenamed("data_venda", "dt_venda")
    .withColumn("valor_total", F.col("quantidade") * F.col("preco_unitario"))
    .withColumn("canal", F.lit("Loja Online"))
    .withColumn(
        "faixa_valor",
        F.when(F.col("valor_total") >= 3000, F.lit("Alta"))
         .when(F.col("valor_total") >= 1000, F.lit("Media"))
         .otherwise(F.lit("Baixa"))
    )
    .withColumn("status_tratado", F.trim(F.regexp_replace(F.col("status_bruto"), "-", " ")))
    .withColumn("dt_venda", F.to_date(F.col("dt_venda"), "yyyy-MM-dd"))
    .withColumn("estado_final", F.coalesce(F.col("estado"), F.lit("NAO_INFORMADO")))
    .withColumn("origem_padronizada", F.regexp_replace(F.col("origem"), "-", "_"))
    .fillna({"preco_unitario": 0.0, "cupom": "SEM_CUPOM"})
    .dropna(subset=["produto", "id_cliente"])
    .drop("estado", "status_bruto")
)

# Processo Silver 3: deduplicação e tipagem da dimensão de clientes.
df_silver_vendas = (
    df_tratado
    .dropDuplicates(["id_venda", "produto", "id_cliente", "dt_venda"])
    .withColumn("_data_processamento", F.current_timestamp())
)

df_silver_clientes = (
    df_clientes
    .withColumn("data_cadastro", F.to_date(F.col("data_cadastro"), "yyyy/MM/dd"))
    .dropDuplicates(["id_cliente"])
    .withColumn("_data_processamento", F.current_timestamp())
)

display(df_silver_vendas.orderBy("id_venda"))
display(df_silver_clientes.orderBy("id_cliente"))

# COMMAND ----------
# MAGIC %md
# MAGIC # Escrita da Silver
# MAGIC
# MAGIC As tabelas Silver serão usadas pela camada Gold para gerar visões analíticas.

# COMMAND ----------
spark.sql("CREATE SCHEMA IF NOT EXISTS silver")

silver_vendas = "silver.aula3_vendas_tratadas"
silver_clientes = "silver.aula3_clientes_tratados"

(
    df_silver_vendas
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(silver_vendas)
)

(
    df_silver_clientes
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(silver_clientes)
)

print("Tabelas Silver criadas:")
for tabela in [silver_vendas, silver_clientes]:
    print("-", tabela, "=>", spark.read.table(tabela).count(), "linhas")

print("Próximo passo: executar 04_carga_camada_gold.py")
