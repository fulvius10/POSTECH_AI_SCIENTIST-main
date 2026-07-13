# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Carga da Camada Gold
# MAGIC
# MAGIC Este notebook lê a Silver e cria a Gold.
# MAGIC
# MAGIC A Gold contém tabelas analíticas prontas para consumo por dashboards, SQL e análises de negócio.

# COMMAND ----------
from pyspark.sql import functions as F

silver_vendas = "silver.aula3_vendas_tratadas"
silver_clientes = "silver.aula3_clientes_tratados"

for tabela in [silver_vendas, silver_clientes]:
    try:
        spark.read.table(tabela).limit(1).count()
    except Exception as erro:
        raise ValueError(f"Tabela {tabela} não encontrada. Execute primeiro 03_carga_camada_silver.py.") from erro

df_vendas_tratadas = spark.read.table(silver_vendas).drop("_data_processamento")
df_clientes_tratados = spark.read.table(silver_clientes).drop("_data_processamento")

# Processo Gold 1: enriquecimento da fato de vendas com a dimensão de clientes.
df_enriquecido = df_vendas_tratadas.join(df_clientes_tratados, on="id_cliente", how="left")

# Processo Gold 2: agregação por categoria.
df_analitico_categoria = (
    df_enriquecido
    .groupBy("categoria")
    .agg(
        F.count("*").alias("qtd_registros"),
        F.sum("valor_total").alias("faturamento_total"),
        F.avg("valor_total").alias("ticket_medio"),
        F.countDistinct("id_cliente").alias("clientes_distintos")
    )
    .withColumn("faturamento_total", F.round(F.col("faturamento_total"), 2))
    .withColumn("ticket_medio", F.round(F.col("ticket_medio"), 2))
    .orderBy(F.desc("faturamento_total"))
)

# Processo Gold 3: agregação por estado e segmento.
df_analitico_estado_segmento = (
    df_enriquecido
    .groupBy("estado_final", "segmento")
    .agg(
        F.sum("valor_total").alias("faturamento_total"),
        F.count("*").alias("qtd_vendas")
    )
    .withColumn("faturamento_total", F.round(F.col("faturamento_total"), 2))
    .orderBy("estado_final", F.desc("faturamento_total"))
)

display(df_enriquecido.orderBy("id_venda"))
display(df_analitico_categoria)
display(df_analitico_estado_segmento)

# COMMAND ----------
# MAGIC %md
# MAGIC # Escrita da Gold
# MAGIC
# MAGIC As tabelas abaixo são os produtos analíticos finais desta aula.

# COMMAND ----------
spark.sql("CREATE SCHEMA IF NOT EXISTS gold")

gold_categoria = "gold.aula3_analitico_categoria"
gold_estado_segmento = "gold.aula3_analitico_estado_segmento"

(
    df_analitico_categoria
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_categoria)
)

(
    df_analitico_estado_segmento
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(gold_estado_segmento)
)

print("Tabelas Gold criadas:")
for tabela in [gold_categoria, gold_estado_segmento]:
    print("-", tabela, "=>", spark.read.table(tabela).count(), "linhas")

spark.sql("SHOW TABLES IN gold").show(truncate=False)
