# Aula 3 - Manipulando Dados com Spark no Databricks

Este material organiza o tutorial da Aula 3 em etapas separadas para facilitar a explicacao em sala.

A ideia e mostrar primeiro quais dados simulam as origens transacionais e depois carregar cada camada da arquitetura Medallion em um processo proprio:

1. Criacao das origens transacionais
2. Carga da camada Bronze
3. Carga da camada Silver
4. Carga da camada Gold
5. Execucao do tutorial principal de manipulacao com PySpark

## Arquivos do Projeto

Use os arquivos `.ipynb` para importar diretamente no Databricks.

| Ordem | Arquivo | Objetivo |
| --- | --- | --- |
| 1 | `01_criacao_origens_transacionais.ipynb` | Cria as bases simuladas no schema `origens` |
| 2 | `02_carga_camada_bronze.ipynb` | Le as origens e grava as tabelas Bronze |
| 3 | `03_carga_camada_silver.ipynb` | Le Bronze, trata os dados e grava Silver |
| 4 | `04_carga_camada_gold.ipynb` | Le Silver, gera agregacoes e grava Gold |
| 5 | `tutorial_hands_on_spark_aula3_databricks_free_edition.ipynb` | Tutorial principal de manipulacao com PySpark |

Os arquivos `.py` possuem o mesmo conteudo em formato exportado do Databricks.

## Pre-requisitos

- Conta no Databricks Free Edition.
- Notebook conectado ao compute Serverless.
- Importar tambem a pasta `imagens` para que as figuras do tutorial principal aparecam corretamente.

## Como Importar no Databricks

1. Acesse o workspace do Databricks.
2. No menu esquerdo, clique em **Workspace**.
3. Entre na pasta onde deseja salvar o material da aula.
4. Clique em **Import**.
5. Importe os arquivos `.ipynb` deste projeto.
6. Confirme que os notebooks aparecem na pasta do workspace.
7. Abra cada notebook e selecione o compute **Serverless**, quando necessario.

## Ordem de Execucao

Execute os notebooks nesta ordem.

### 1. Criacao das Origens

Abra e execute:

```text
01_criacao_origens_transacionais.ipynb
```

Este notebook cria o schema `origens` e grava:

```text
origens.aula3_dynamodb_vendas_eventos_json
origens.aula3_dms_clientes_eventos_json
origens.aula3_vendas_arquivos_json
```

Essas tabelas simulam os dados chegando de sistemas transacionais e arquivos.

### 2. Carga da Bronze

Abra e execute:

```text
02_carga_camada_bronze.ipynb
```

Este notebook le o schema `origens`, interpreta os JSONs e grava:

```text
bronze.aula3_dynamodb_vendas_raw
bronze.aula3_dms_clientes_raw
bronze.aula3_vendas_raw
bronze.aula3_clientes_raw
bronze.aula3_vendas_arquivos_raw
```

A Bronze guarda dados brutos ou proximos da origem, com metadados de ingestao.

### 3. Carga da Silver

Abra e execute:

```text
03_carga_camada_silver.ipynb
```

Este notebook le a Bronze, aplica limpeza, padronizacao, tipagem e deduplicacao, e grava:

```text
silver.aula3_vendas_tratadas
silver.aula3_clientes_tratados
```

A Silver contem dados tratados e reutilizaveis.

### 4. Carga da Gold

Abra e execute:

```text
04_carga_camada_gold.ipynb
```

Este notebook le a Silver, cruza vendas com clientes, gera agregacoes e grava:

```text
gold.aula3_analitico_categoria
gold.aula3_analitico_estado_segmento
```

A Gold contem tabelas analiticas prontas para consumo.

### 5. Tutorial Principal

Depois das quatro cargas, execute:

```text
tutorial_hands_on_spark_aula3_databricks_free_edition.ipynb
```

Esse notebook usa as tabelas ja criadas para ensinar leitura, selecao, filtros, limpeza, joins, agregacoes, funcoes de janela, performance e persistencia com PySpark.

## Como Validar no Catalog

Depois de executar os notebooks, abra **Catalog** no menu esquerdo do Databricks e confira os schemas:

```text
origens
bronze
silver
gold
```

Tambem e possivel validar com SQL:

```sql
SHOW TABLES IN origens;
SHOW TABLES IN bronze;
SHOW TABLES IN silver;
SHOW TABLES IN gold;
```

## Fluxo Didatico

```text
origens
  -> bronze
      -> silver
          -> gold
              -> tutorial principal
```

Cada notebook representa um processo separado do pipeline:

- `01`: simula os sistemas de origem.
- `02`: faz a ingestao para Bronze.
- `03`: transforma dados brutos em dados tratados.
- `04`: cria visoes analiticas.
- `tutorial principal`: explora os comandos PySpark usando as bases criadas.

## Limpeza do Ambiente

O tutorial principal possui uma celula de limpeza opcional.

Ela vem travada por padrao:

```python
EXECUTAR_LIMPEZA = False
```

Para apagar as tabelas criadas, altere manualmente para:

```python
EXECUTAR_LIMPEZA = True
```

Execute essa celula somente no final da aula ou quando o professor solicitar.

## Problemas Comuns

### Tabela nao encontrada

Se aparecer erro dizendo que uma tabela nao existe, confira se os notebooks anteriores foram executados na ordem correta.

Exemplo: se o notebook `03_carga_camada_silver` falhar, execute antes o `02_carga_camada_bronze`.

### Compute desconectado

No Databricks Free Edition, a sessao Serverless pode desconectar apos algum tempo sem uso. Reconecte o notebook ao Serverless e execute novamente as celulas necessarias.

### Imagens nao aparecem

Importe a pasta `imagens` junto com o material da aula. O tutorial principal referencia os arquivos PNG dessa pasta.

### DBFS bloqueado

O material evita gravar em `dbfs:/tmp`, porque alguns workspaces Serverless bloqueiam o Public DBFS root. As tabelas principais sao gravadas como Delta gerenciado com `saveAsTable()`.
