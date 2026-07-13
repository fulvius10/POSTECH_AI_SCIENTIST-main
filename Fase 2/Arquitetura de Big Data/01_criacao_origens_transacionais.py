# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Criação das origens transacionais da Aula 3
# MAGIC
# MAGIC Este notebook cria apenas as bases de origem que simulam sistemas transacionais e arquivos de chegada.
# MAGIC
# MAGIC A proposta é separar a origem das camadas Medallion. Aqui ainda não criamos Bronze, Silver nem Gold.
# MAGIC
# MAGIC Ao final, três tabelas Delta são gravadas no schema `origens`:
# MAGIC
# MAGIC - `origens.aula3_dynamodb_vendas_eventos_json`
# MAGIC - `origens.aula3_dms_clientes_eventos_json`
# MAGIC - `origens.aula3_vendas_arquivos_json`

# COMMAND ----------
# MAGIC %md
# MAGIC # Origem dos dados — DynamoDB, CDC/DMS e arquivos
# MAGIC 
# MAGIC Antes de criar as camadas Medallion, vamos simular três formas comuns de chegada de dados em um Lakehouse:
# MAGIC 
# MAGIC ## 1. Sistema transacional estilo DynamoDB
# MAGIC O DynamoDB é um banco NoSQL usado em aplicações transacionais. Os dados costumam chegar ao Lakehouse por eventos, por exportações ou por streams.
# MAGIC 
# MAGIC Neste tutorial, vamos simular eventos no formato parecido com **DynamoDB Streams**, com campos aninhados como `NewImage`, atributos tipados (`S`, `N`, `NULL`) e uma lista de itens da venda.
# MAGIC 
# MAGIC Para transformar esse JSON em tabela, vamos usar:
# MAGIC 
# MAGIC - `spark.createDataFrame()` para criar uma coluna com o JSON bruto sem usar `sparkContext`;
# MAGIC - `from_json()` para interpretar o texto JSON usando um schema;
# MAGIC - `explode()` para abrir a lista de itens da venda;
# MAGIC - acesso a campos aninhados como `dynamodb.NewImage.id_venda.N`;
# MAGIC - `cast()` para converter texto em número.
# MAGIC 
# MAGIC ## Observação importante sobre atributos tipados do DynamoDB
# MAGIC 
# MAGIC Nos eventos do DynamoDB, os valores costumam vir acompanhados do tipo do atributo. Por isso aparecem marcações como `S`, `N` e `NULL`.
# MAGIC 
# MAGIC Exemplo simplificado:
# MAGIC 
# MAGIC ```json
# MAGIC {
# MAGIC   "id_venda": { "N": "1" },
# MAGIC   "produto": { "S": "Notebook" },
# MAGIC   "cupom": { "NULL": true }
# MAGIC }
# MAGIC ```
# MAGIC 
# MAGIC Significado:
# MAGIC 
# MAGIC - `S` significa **String**, ou seja, texto. Exemplo: `{ "S": "Notebook" }`.
# MAGIC - `N` significa **Number**, ou seja, número. No JSON do DynamoDB, o número vem como texto, por exemplo `{ "N": "1" }`, então no Spark usamos `cast()` para converter.
# MAGIC - `NULL` indica valor nulo, por exemplo `{ "NULL": true }`.
# MAGIC 
# MAGIC Por isso, para pegar o `id_venda`, usamos algo como:
# MAGIC 
# MAGIC ```python
# MAGIC F.col("dynamodb.NewImage.id_venda.N").cast("int")
# MAGIC ```
# MAGIC 
# MAGIC A leitura é: entrar em `id_venda`, pegar o valor dentro de `N` e converter para inteiro.
# MAGIC 
# MAGIC ## 2. CDC ou DMS
# MAGIC CDC significa **Change Data Capture**. Ele captura mudanças feitas em uma origem transacional, como inserts, updates e deletes.
# MAGIC 
# MAGIC O AWS DMS pode entregar esses eventos para arquivos, filas ou storage. Aqui vamos simular eventos CDC/DMS da tabela de clientes.
# MAGIC 
# MAGIC ## 3. Arquivos
# MAGIC Também vamos mostrar uma opção de chegada por arquivos JSON em uma área de aterrissagem. No mundo real, essa área poderia receber arquivos CSV, JSON, Parquet ou Avro vindos de integrações, sistemas externos ou pipelines de ingestão. Nesta versão para Databricks Serverless, a simulação de arquivos usa JSON Lines em memória para evitar o erro de Public DBFS root desabilitado.
# MAGIC 
# MAGIC Depois dessas origens, o restante do tutorial continua usando os DataFrames `df_vendas` e `df_clientes`.
# MAGIC 
# MAGIC > No Databricks Serverless, evitamos `spark.sparkContext.parallelize()` porque o acesso direto ao SparkContext/JVM não é suportado. Por isso, os exemplos usam `spark.createDataFrame()` e `from_json()`.

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql import Window
import json

# -----------------------------------------------------------------------------
# 1) Origem transacional simulada: DynamoDB Streams
# -----------------------------------------------------------------------------
# Cada evento representa uma venda gravada em um sistema transacional.
# O campo itens.L é uma lista de objetos. Vamos usar explode() para abrir essa lista.

eventos_dynamodb_vendas = [
    {
        "eventID": "evt-001",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {
            "Keys": {"pk": {"S": "VENDA#1"}},
            "NewImage": {
                "id_venda": {"N": "1"},
                "data_venda": {"S": "2026-01-02"},
                "estado": {"S": "SP"},
                "id_cliente": {"N": "101"},
                "cupom": {"NULL": True},
                "origem": {"S": "Loja-SP"},
                "status_bruto": {"S": "ok"},
                "itens": {"L": [{"M": {"produto": {"S": "Notebook"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "3500.00"}}}]}
            }
        }
    },
    {
        "eventID": "evt-002",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#2"}}, "NewImage": {"id_venda": {"N": "2"}, "data_venda": {"S": "2026-01-02"}, "estado": {"S": "SP"}, "id_cliente": {"N": "101"}, "cupom": {"S": "CUPOM10"}, "origem": {"S": "Loja-SP"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Mouse"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "2"}, "preco_unitario": {"N": "80.00"}}}]}}}
    },
    {
        "eventID": "evt-003",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#3"}}, "NewImage": {"id_venda": {"N": "3"}, "data_venda": {"S": "2026-01-03"}, "estado": {"S": "RJ"}, "id_cliente": {"N": "102"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-RJ"}, "status_bruto": {"S": " ok "}, "itens": {"L": [{"M": {"produto": {"S": "Teclado"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "150.00"}}}]}}}
    },
    {
        "eventID": "evt-004",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#4"}}, "NewImage": {"id_venda": {"N": "4"}, "data_venda": {"S": "2026-01-03"}, "estado": {"S": "MG"}, "id_cliente": {"N": "103"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-MG"}, "status_bruto": {"S": "erro-cadastro"}, "itens": {"L": [{"M": {"produto": {"S": "Cadeira"}, "categoria": {"S": "Moveis"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "900.00"}}}]}}}
    },
    {
        "eventID": "evt-005",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#5"}}, "NewImage": {"id_venda": {"N": "5"}, "data_venda": {"S": "2026-01-04"}, "estado": {"S": "SP"}, "id_cliente": {"N": "104"}, "cupom": {"S": "FRETE"}, "origem": {"S": "Loja-SP"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Mesa"}, "categoria": {"S": "Moveis"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "1200.00"}}}]}}}
    },
    {
        "eventID": "evt-006",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#6"}}, "NewImage": {"id_venda": {"N": "6"}, "data_venda": {"S": "2026-01-04"}, "estado": {"NULL": True}, "id_cliente": {"N": "105"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-SP"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Monitor"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "2"}, "preco_unitario": {"N": "1100.00"}}}]}}}
    },
    {
        "eventID": "evt-007",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#7"}}, "NewImage": {"id_venda": {"N": "7"}, "data_venda": {"S": "2026-01-05"}, "estado": {"S": "BA"}, "id_cliente": {"N": "106"}, "cupom": {"S": "CUPOM5"}, "origem": {"S": "Loja-BA"}, "status_bruto": {"S": "pendente"}, "itens": {"L": [{"M": {"produto": {"S": "Headset"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "3"}, "preco_unitario": {"NULL": True}}}]}}}
    },
    {
        "eventID": "evt-008",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#8"}}, "NewImage": {"id_venda": {"N": "8"}, "data_venda": {"S": "2026-01-05"}, "estado": {"S": "BA"}, "id_cliente": {"N": "106"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-BA"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Webcam"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "420.00"}}}]}}}
    },
    {
        "eventID": "evt-009",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#9"}}, "NewImage": {"id_venda": {"N": "9"}, "data_venda": {"S": "2026-01-06"}, "estado": {"S": "SP"}, "id_cliente": {"N": "107"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-SP"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Notebook"}, "categoria": {"S": "Eletronicos"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "3600.00"}}}]}}}
    },
    {
        "eventID": "evt-010",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#10"}}, "NewImage": {"id_venda": {"N": "10"}, "data_venda": {"S": "2026-01-06"}, "estado": {"S": "RJ"}, "id_cliente": {"N": "108"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-RJ"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Cadeira"}, "categoria": {"S": "Moveis"}, "quantidade": {"N": "2"}, "preco_unitario": {"N": "850.00"}}}]}}}
    },
    # Evento duplicado para demonstrar dropDuplicates() na camada Silver.
    {
        "eventID": "evt-010-duplicado",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#10"}}, "NewImage": {"id_venda": {"N": "10"}, "data_venda": {"S": "2026-01-06"}, "estado": {"S": "RJ"}, "id_cliente": {"N": "108"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-RJ"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Cadeira"}, "categoria": {"S": "Moveis"}, "quantidade": {"N": "2"}, "preco_unitario": {"N": "850.00"}}}]}}}
    },
    {
        "eventID": "evt-011",
        "eventName": "INSERT",
        "eventSource": "aws:dynamodb",
        "dynamodb": {"Keys": {"pk": {"S": "VENDA#11"}}, "NewImage": {"id_venda": {"N": "11"}, "data_venda": {"S": "2026-01-07"}, "estado": {"S": "SP"}, "id_cliente": {"N": "104"}, "cupom": {"NULL": True}, "origem": {"S": "Loja-SP"}, "status_bruto": {"S": "ok"}, "itens": {"L": [{"M": {"produto": {"S": "Mesa"}, "categoria": {"S": "Moveis"}, "quantidade": {"N": "1"}, "preco_unitario": {"N": "1250.00"}}}]}}}
    }
]

json_dynamodb_vendas = [json.dumps(evento) for evento in eventos_dynamodb_vendas]

# Serverless não permite acesso direto ao SparkContext/JVM.
# Por isso, criamos um DataFrame de strings JSON e fazemos o parsing com from_json().
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

df_json_dynamodb_vendas = spark.createDataFrame([(linha,) for linha in json_dynamodb_vendas], "json_evento STRING")
df_raw_dynamodb_vendas = (
    df_json_dynamodb_vendas
    .select(F.from_json(F.col("json_evento"), schema_dynamodb_vendas).alias("evento"))
    .select("evento.*")
)

display(df_raw_dynamodb_vendas.select("eventID", "eventName", "eventSource", "dynamodb.NewImage"))

# explode() abre o array de itens da venda. Cada item vira uma linha.
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

# -----------------------------------------------------------------------------
# 2) Origem simulada: CDC/DMS para cadastro de clientes
# -----------------------------------------------------------------------------
# O campo Op representa a operação capturada: I = insert, U = update, D = delete.
# Neste exemplo, vamos manter apenas inserts e updates como estado final de clientes.

eventos_dms_clientes = [
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-01T09:00:00", "data": {"id_cliente": 101, "nome_cliente": "Ana", "segmento": "Premium", "data_cadastro": "2026/01/01"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-02T09:00:00", "data": {"id_cliente": 102, "nome_cliente": "Bruno", "segmento": "Standard", "data_cadastro": "2026/01/02"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-02T10:00:00", "data": {"id_cliente": 103, "nome_cliente": "Carla", "segmento": "Premium", "data_cadastro": "2026/01/02"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-03T09:00:00", "data": {"id_cliente": 104, "nome_cliente": "Diego", "segmento": "Standard", "data_cadastro": "2026/01/03"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-03T10:00:00", "data": {"id_cliente": 105, "nome_cliente": "Erica", "segmento": "Premium", "data_cadastro": "2026/01/03"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-04T09:00:00", "data": {"id_cliente": 106, "nome_cliente": "Fabio", "segmento": "Novo", "data_cadastro": "2026/01/04"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-04T10:00:00", "data": {"id_cliente": 107, "nome_cliente": "Gabriela", "segmento": "Novo", "data_cadastro": "2026/01/04"}},
    {"Op": "I", "table_name": "clientes", "commit_timestamp": "2026-01-05T09:00:00", "data": {"id_cliente": 108, "nome_cliente": "Helena", "segmento": "Premium", "data_cadastro": "2026/01/05"}},
    {"Op": "U", "table_name": "clientes", "commit_timestamp": "2026-01-06T09:00:00", "data": {"id_cliente": 106, "nome_cliente": "Fabio", "segmento": "Standard", "data_cadastro": "2026/01/04"}}
]

json_dms_clientes = [json.dumps(evento) for evento in eventos_dms_clientes]

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

df_json_dms_clientes = spark.createDataFrame([(linha,) for linha in json_dms_clientes], "json_evento STRING")
df_raw_dms_clientes = (
    df_json_dms_clientes
    .select(F.from_json(F.col("json_evento"), schema_dms_clientes).alias("evento"))
    .select("evento.*")
)

display(df_raw_dms_clientes)

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

# -----------------------------------------------------------------------------
# 3) Opção de origem por arquivos JSON
# -----------------------------------------------------------------------------
# Esta fonte simula arquivos chegando em uma pasta de landing.
# Ela é exibida como alternativa de ingestão e poderia alimentar a Bronze também.

vendas_arquivos = [
    (12, "2026-01-08", "Mesa Lateral", "Moveis", 1, 500.00, "PR", 109, None, "Arquivo-PR", "ok"),
    (13, "2026-01-08", "Mouse Gamer", "Eletronicos", 1, 220.00, "SP", 101, "CUPOM15", "Arquivo-SP", "ok")
]

schema_vendas_arquivos = """
id_venda INT,
data_venda STRING,
produto STRING,
categoria STRING,
quantidade INT,
preco_unitario DOUBLE,
estado STRING,
id_cliente INT,
cupom STRING,
origem STRING,
status_bruto STRING
"""

df_vendas_arquivos_origem = spark.createDataFrame(vendas_arquivos, schema=schema_vendas_arquivos)

# Em muitos workspaces Serverless, o Public DBFS root fica desabilitado.
# Por isso, esta simulação não grava em dbfs:/tmp. Ela representa arquivos JSON Lines
# já recebidos por uma landing zone e faz a leitura do conteúdo JSON de forma segura.
json_vendas_arquivos = [json.dumps(linha.asDict()) for linha in df_vendas_arquivos_origem.collect()]

df_json_vendas_arquivos = spark.createDataFrame(
    [(linha,) for linha in json_vendas_arquivos],
    "json_linha STRING"
)

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

df_vendas_arquivos = (
    df_json_vendas_arquivos
    .select(F.from_json(F.col("json_linha"), schema_vendas_arquivos_struct).alias("arquivo"))
    .select("arquivo.*")
)

print("Origem por arquivos simulada com JSON Lines em memória, sem usar dbfs:/tmp.")
display(df_vendas_arquivos)

display(df_raw_dynamodb_vendas.select("eventID", "eventName", "eventSource", "dynamodb.NewImage"))
display(df_raw_dms_clientes.orderBy("commit_timestamp"))

# COMMAND ----------
# MAGIC %md
# MAGIC # Persistência das origens
# MAGIC
# MAGIC As tabelas abaixo representam a chegada dos dados, antes da camada Bronze.
# MAGIC
# MAGIC O próximo notebook vai ler essas tabelas do schema `origens` e carregar a Bronze.

# COMMAND ----------
# Grava somente as origens transacionais no schema origens.
# As camadas Medallion serão carregadas nos notebooks seguintes.

catalogo_atual = spark.sql("SELECT current_catalog() AS catalogo").first()["catalogo"]
schema_atual = spark.sql("SELECT current_schema() AS schema").first()["schema"]

print("Catálogo atual:", catalogo_atual)
print("Schema atual:", schema_atual)

spark.sql("CREATE SCHEMA IF NOT EXISTS origens")

origem_dynamodb_vendas = "origens.aula3_dynamodb_vendas_eventos_json"
origem_dms_clientes = "origens.aula3_dms_clientes_eventos_json"
origem_vendas_arquivos = "origens.aula3_vendas_arquivos_json"

(
    df_json_dynamodb_vendas
    .withColumn("_sistema_origem", F.lit("dynamodb_stream_simulado"))
    .withColumn("_data_criacao_origem", F.current_timestamp())
    .write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(origem_dynamodb_vendas)
)

(
    df_json_dms_clientes
    .withColumn("_sistema_origem", F.lit("dms_cdc_simulado"))
    .withColumn("_data_criacao_origem", F.current_timestamp())
    .write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(origem_dms_clientes)
)

(
    df_json_vendas_arquivos
    .withColumn("_sistema_origem", F.lit("arquivo_json_lines_simulado"))
    .withColumn("_data_criacao_origem", F.current_timestamp())
    .write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(origem_vendas_arquivos)
)

print("Tabelas de origem criadas:")
for tabela in [origem_dynamodb_vendas, origem_dms_clientes, origem_vendas_arquivos]:
    print("-", tabela, "=>", spark.read.table(tabela).count(), "linhas")

print("Próximo passo: executar 02_carga_camada_bronze.py")
