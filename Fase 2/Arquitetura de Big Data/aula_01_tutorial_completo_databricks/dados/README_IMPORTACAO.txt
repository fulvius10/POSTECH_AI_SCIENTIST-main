DADOS DA AULA 01 - ARQUITETURA DE DADOS: DATA LAKE VS DATA WAREHOUSE

ARQUIVO PRINCIPAL
- vendas.csv: possui 1.000 registros e pode substituir diretamente o CSV do roteiro.
  As seis primeiras colunas mantêm compatibilidade com o SQL original:
  id_venda, id_cliente, id_produto, data_venda, quantidade, valor_total.

ARQUIVOS COMPLEMENTARES
- clientes.csv: dimensão de clientes com 300 registros.
- produtos.csv: dimensão de produtos com 100 registros.
- lojas.csv: dimensão de lojas com 20 registros.
- vendedores.csv: dimensão de vendedores com 60 registros.
- vendas_minimal.csv: versão simplificada com exatamente as seis colunas originais.
- dicionario_dados.csv: descrição resumida das principais colunas.

UPLOAD NO DATABRICKS
Faça o upload de vendas.csv para:
  /Volumes/workspace/default/tutorial_fiap/vendas.csv

Para os exercícios complementares, faça upload dos demais arquivos no mesmo volume:
  /Volumes/workspace/default/tutorial_fiap/

OBSERVAÇÃO
O SQL original continuará funcionando com vendas.csv porque as colunas adicionais
são ignoradas na criação da staging e permanecem disponíveis na camada RAW do Data Lake.
