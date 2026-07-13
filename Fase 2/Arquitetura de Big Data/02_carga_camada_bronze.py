# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Carga da Camada Bronze
# MAGIC
# MAGIC Este notebook lê as tabelas do schema `origens` e cria a camada Bronze.
# MAGIC
# MAGIC A Bronze preserva rastreabilidade e mantém dados próximos da chegada, com metadados de ingestão.

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql import Window

origem_dynamodb_vendas = "origens.aula3_dynamodb_vendas_eventos_json"
origem_dms_clientes = "origens.aula3_dms_clientes_eventos_json"
origem_vendas_arquivos = "origens.aula3_vendas_arquivos_json"

for tabela in [origem_dynamodb_vendas, origem_dms_clientes, origem_vendas_arquivos]:
    try:
        spark.read.table(tabela).limit(1).count()
    except Exception as erro:
        raise ValueError(f"Tabela {tabela} não encontrada. Execute primeiro 01_criacao_origens_transacionais.py.") from erro

schema_atributo_s = T.StructType([
    T.StructField("S", T.StringType(), True)
])

schema_atributo_n = T.StructType([
    T.StructField("N", T.StringType(), True)
])

schema_atributo_s_null = T.StructType([
    T.StructField("S", T.StringType(), True),
    T.StructField("NULL", T.BooleanType(), True)
])

schema_atributo_n_null = T.StructType([
    T.StructField("N", T.StringType(), True),
    T.StructField("NULL", T.BooleanType(), True)
])

schema_item_venda = T.StructType([
    T.StructField("M", T.StructType([
        T.StructField("produto", schema_atributo_s, True),
        T.StructField("categoria", schema_atributo_s, True),
        T.StructField("quantidade", schema_atributo_n, True),
        T.StructField("preco_unitario", schema_atributo_n_null, True)
    ]), True)
])

schema_dynamodb_vendas = T.StructType([
    T.StructField("eventID", T.StringType(), True),
    T.StructField("eventName", T.StringType(), True),
    T.StructField("eventSource", T.StringType(), True),
    T.StructField("dynamodb", T.StructType([
        T.StructField("Keys", T.StructType([
            T.StructField("pk", schema_atributo_s, True)
        ]), True),
        T.StructField("NewImage", T.StructType([
            T.StructField("id_venda", schema_atributo_n, True),
            T.StructField("data_venda", schema_atributo_s, True),
            T.StructField("estado", schema_atributo_s_null, True),
            T.StructField("id_cliente", schema_atributo_n, True),
            T.StructField("cupom", schema_atributo_s_null, True),
            T.StructField("origem", schema_atributo_s, True),
            T.StructField("status_bruto", schema_atributo_s, True),
            T.StructField("itens", T.StructType([
                T.StructField("L", T.ArrayType(schema_item_venda), True)
            ]), True)
        ]), True)
    ]), True)
])

schema_dms_clientes = T.StructType([
    T.StructField("Op", T.StringType(), True),
    T.StructField("table_name", T.StringType(), True),
    T.StructField("commit_timestamp", T.StringType(), True),
    T.StructField("data", T.StructType([
        T.StructField("id_cliente", T.IntegerType(), True),
        T.StructField("nome_cliente", T.StringType(), True),
        T.StructField("segmento", T.StringType(), True),
        T.StructField("data_cadastro", T.StringType(), True)
    ]), True)
])

schema_vendas_arquivos_struct = T.StructType([
    T.StructField("id_venda", T.IntegerType(), True),
    T.StructField("data_venda", T.StringType(), True),
    T.StructField("produto", T.StringType(), True),
    T.StructField("categoria", T.StringType(), True),
    T.StructField("quantidade", T.IntegerType(), True),
    T.StructField("preco_unitario", T.DoubleType(), True),
    T.StructField("estado", T.StringType(), True),
    T.StructField("id_cliente", T.IntegerType(), True),
    T.StructField("cupom", T.StringType(), True),
    T.StructField("origem", T.StringType(), True),
    T.StructField("status_bruto", T.StringType(), True)
])

# COMMAND ----------
# MAGIC %md
# MAGIC # Transformações da Bronze
# MAGIC
# MAGIC Aqui acontecem processos típicos de entrada: parse de JSON, abertura de campos aninhados e consolidação técnica inicial.

# COMMAND ----------
# Leitura das origens

df_json_dynamodb_vendas = spark.read.table(origem_dynamodb_vendas).select("json_evento")
df_json_dms_clientes = spark.read.table(origem_dms_clientes).select("json_evento")
df_json_vendas_arquivos = spark.read.table(origem_vendas_arquivos).select("json_linha")

# Processo Bronze 1: parse dos eventos DynamoDB e preservação do bruto estruturado.
df_raw_dynamodb_vendas = (
    df_json_dynamodb_vendas
    .select(F.from_json(F.col("json_evento"), schema_dynamodb_vendas).alias("evento"))
    .select("evento.*")
)

# Processo Bronze 2: explode dos itens da venda para uma tabela tabular de vendas.
df_vendas = (
    df_raw_dynamodb_vendas
    .withColumn("item", F.explode(F.col("dynamodb.NewImage.itens.L")))
    .select(
        F.col("dynamodb.NewImage.id_venda.N").cast("int").alias("id_venda"),
        F.col("dynamodb.NewImage.data_venda.S").alias("data_venda"),
        F.col("item.M.produto.S").alias("produto"),
        F.col("item.M.categoria.S").alias("categoria"),
        F.col("item.M.quantidade.N").cast("int").alias("quantidade"),
        F.col("item.M.preco_unitario.N").cast("double").alias("preco_unitario"),
        F.col("dynamodb.NewImage.estado.S").alias("estado"),
        F.col("dynamodb.NewImage.id_cliente.N").cast("int").alias("id_cliente"),
        F.col("dynamodb.NewImage.cupom.S").alias("cupom"),
        F.col("dynamodb.NewImage.origem.S").alias("origem"),
        F.col("dynamodb.NewImage.status_bruto.S").alias("status_bruto")
    )
)

# Processo Bronze 3: parse dos eventos CDC/DMS e consolidação do último estado de clientes.
df_raw_dms_clientes = (
    df_json_dms_clientes
    .select(F.from_json(F.col("json_evento"), schema_dms_clientes).alias("evento"))
    .select("evento.*")
)

janela_cliente_cdc = Window.partitionBy("data.id_cliente").orderBy(F.col("commit_timestamp").desc())

df_clientes = (
    df_raw_dms_clientes
    .filter(F.col("Op").isin("I", "U"))
    .withColumn("ordem_evento", F.row_number().over(janela_cliente_cdc))
    .filter(F.col("ordem_evento") == 1)
    .select(
        F.col("data.id_cliente").cast("int").alias("id_cliente"),
        F.col("data.nome_cliente").alias("nome_cliente"),
        F.col("data.segmento").alias("segmento"),
        F.col("data.data_cadastro").alias("data_cadastro")
    )
)

# Processo Bronze 4: parse da origem alternativa por arquivos, para demonstrar landing zone.
df_vendas_arquivos = (
    df_json_vendas_arquivos
    .select(F.from_json(F.col("json_linha"), schema_vendas_arquivos_struct).alias("arquivo"))
    .select("arquivo.*")
)

display(df_raw_dynamodb_vendas.select("eventID", "eventName", "eventSource", "dynamodb.NewImage"))
display(df_raw_dms_clientes.orderBy("commit_timestamp"))
display(df_vendas.orderBy("id_venda"))
display(df_clientes.orderBy("id_cliente"))

# COMMAND ----------
# MAGIC %md
# MAGIC # Escrita da Bronze
# MAGIC
# MAGIC As tabelas abaixo ficam disponíveis para a próxima etapa do pipeline, a camada Silver.

# COMMAND ----------
spark.sql("CREATE SCHEMA IF NOT EXISTS bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS silver")
spark.sql("CREATE SCHEMA IF NOT EXISTS gold")

bronze_dynamodb_vendas_raw = "bronze.aula3_dynamodb_vendas_raw"
bronze_dms_clientes_raw = "bronze.aula3_dms_clientes_raw"
bronze_vendas = "bronze.aula3_vendas_raw"
bronze_clientes = "bronze.aula3_clientes_raw"
bronze_vendas_arquivos = "bronze.aula3_vendas_arquivos_raw"

(
    df_raw_dynamodb_vendas
    .withColumn("_data_ingestao", F.current_timestamp())
    .withColumn("_fonte", F.lit("origens.aula3_dynamodb_vendas_eventos_json"))
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(bronze_dynamodb_vendas_raw)
)

(
    df_raw_dms_clientes
    .withColumn("_data_ingestao", F.current_timestamp())
    .withColumn("_fonte", F.lit("origens.aula3_dms_clientes_eventos_json"))
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(bronze_dms_clientes_raw)
)

(
    df_vendas
    .withColumn("_data_ingestao", F.current_timestamp())
    .withColumn("_fonte", F.lit("dynamodb_stream_explodido"))
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(bronze_vendas)
)

(
    df_clientes
    .withColumn("_data_ingestao", F.current_timestamp())
    .withColumn("_fonte", F.lit("dms_cdc_consolidado"))
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(bronze_clientes)
)

(
    df_vendas_arquivos
    .withColumn("_data_ingestao", F.current_timestamp())
    .withColumn("_fonte", F.lit("arquivo_json_lines_simulado"))
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .saveAsTable(bronze_vendas_arquivos)
)

print("Tabelas Bronze criadas:")
for tabela in [bronze_dynamodb_vendas_raw, bronze_dms_clientes_raw, bronze_vendas, bronze_clientes, bronze_vendas_arquivos]:
    print("-", tabela, "=>", spark.read.table(tabela).count(), "linhas")

print("Próximo passo: executar 03_carga_camada_silver.py")
