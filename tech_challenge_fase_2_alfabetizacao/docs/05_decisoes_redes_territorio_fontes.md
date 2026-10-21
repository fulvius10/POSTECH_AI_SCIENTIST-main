# Decisões: rede, território e fonte

Decisões de modelagem em 21/10/2026. Nenhuma pipeline ou tabela foi implementada.
Este documento fecha as três decisões levantadas no desenho e prevalece sobre
as pendências equivalentes da primeira proposta.

## 1. Rede Pública: significado e regra do projeto

O dicionário ORIGINAL dos microdados do Inep foi conferido no ZIP de 2023.
Na aba `TS_ESTADO`, célula C7, e em `TS_MUNICIPIO`, C9:

| Código | Universo explícito no dicionário |
| --- | --- |
| 2 | Estadual |
| 3 | Municipal |
| 5 | Pública (Estadual e Municipal) |
| 6 | Pública (Federal, Estadual e Municipal) |

Referência preservada:
[Dicionario_Microdados_AEEB_2023.xlsx](../referencias/inep_microdados_2023/Dicionario_Microdados_AEEB_2023.xlsx).
Origem: [ZIP do Inep](https://download.inep.gov.br/dados_abertos/microdados_avaliacao_da_alfabetizacao_2023.zip).
O dicionário da Base dos Dados apresenta a mesma distinção.

**Decisão para os dados investigados:** usar o recorte Estadual + Municipal,
código 5 nos resultados agregados, para a comparação pública de UF; manter a
publicação nacional identificada como Pública nesse mesmo contexto da avaliação.
Normalizar como `PUBLICA_ESTADUAL_MUNICIPAL`. Não mapear código 6 para essa categoria.
Para municípios, normalizar código 3 e texto Municipal como `MUNICIPAL`.

Separar evidência de decisão: o dicionário define explicitamente os códigos 5 e 6.
A planilha de metas rotula a rede apenas como Pública; a ponte entre esse rótulo
e o código 5 é uma regra operacional deste projeto, apoiada na reconciliação exata
dos 25 resultados públicos de UF de 2024 disponíveis nas duas fontes. Não é uma
definição universal de qualquer uso do termo Pública. A comunicação oficial do
[RS](https://estado.rs.gov.br/como-o-governo-do-estado-esta-investindo-na-alfabetizacao-das-criancas)
também explicita estadual e municipal nesse contexto de metas, mas não substitui
a documentação de outras edições da avaliação.

Na agregação futura de alunos, esse universo corresponde às dependências 2 e 3,
com os filtros de elegibilidade ainda a definir. Não somar uma linha agregada 5
com suas componentes 2 e 3. Série, ano e avaliação também precisam coincidir.

Mudança de dicionário, presença de outro universo ou divergência nova não autoriza
ampliar o mapa automaticamente. Preservar o código original e abrir uma revisão
de contrato; código desconhecido deve bloquear a comparação afetada.

## 2. Cadastro territorial: IBGE DTB por ano

**Decisão:** usar a Divisão Territorial Brasileira (DTB) do IBGE correspondente ao
ano do resultado, com código completo de município de sete dígitos como texto.
Para o primeiro relatório, DTB 2024. Para resultados históricos de 2023, DTB 2023.

Fontes oficiais preservadas:

- [DTB 2023](../referencias/IBGE_DTB_2023.zip), [origem IBGE](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2023/DTB_2023.zip).
- [DTB 2024](../referencias/IBGE_DTB_2024.zip), [origem IBGE](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2024/DTB_2024.zip).
- [Cadastro das 27 UFs](../referencias/IBGE_estados.json), obtido na
  [API do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=id)
  para acrescentar siglas pelo código UF. O código/nome UF histórico vem da DTB;
  não apresentar a data de coleta da API como uma versão histórica.

Foram lidos os relatórios municipais ODS dentro dos ZIPs; UF, código completo e
nome do município vieram dos campos nomeados no relatório. Não usar uma lista
manual de nomes, o código TSE ou o código IBGE de seis dígitos como chave.
O [IBGE documenta](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)
que o código municipal tem sete dígitos e que o cadastro muda ao longo do tempo.

Conferência de códigos distintos das tabelas educacionais contra a DTB do mesmo ano:

| Fonte | Ano | Códigos distintos | Correspondências | Sem correspondência |
| --- | ---: | ---: | ---: | ---: |
| `municipio` | 2023 | 5.514 | 5.514 | 0 |
| `municipio` | 2024 | 5.516 | 5.516 | 0 |
| `alunos` | 2023 | 4.873 | 4.873 | 0 |
| `alunos` | 2024 | 5.519 | 5.519 | 0 |
| `meta_alfabetizacao_municipio` | 2023 | 5.352 | 5.352 | 0 |
| `meta_alfabetizacao_municipio` | 2024 | 5.352 | 5.352 | 0 |

Essas contagens incluem todas as redes das fontes, não só o recorte municipal
de 5.448 resultados. A DTB lida tem 5.570 códigos em 2023 e 5.571 em 2024; o
código adicional de 2024 é `5101837`. Não interpretar isso como mudança na amostra
educacional. Preservar as convenções estatísticas do IBGE para DF e outros casos,
sem inventar uma rede municipal para o Distrito Federal.

Chave da dimensão proposta: `(ano_cadastro, id_municipio)`. Registrar também o
snapshot e a data-base do relatório. Ao consolidar uma dimensão única de
territórios, preservar essa associação anual numa tabela de vínculo territorial.
Em análises de 2030 sobre os municípios observados em 2024, usar a geografia-base
2024 explicitamente; não inventar um cadastro futuro de 2030.

A taxa de correspondência territorial atual é 100% nos seis recortes. Portanto,
um código educacional novo sem par deverá impedir a publicação analítica afetada
até investigação. Não confundir esse critério com os 98,24% de correspondência
das metas: são junções distintas, com lacunas diferentes.

## 3. Precedência de fontes e tratamento de divergências

### Separar a pergunta de acompanhamento da pergunta de conferência

| Finalidade | Fonte de referência |
| --- | --- |
| Cumprimento de meta pactuada | Publicação de resultados e metas do Inep, no contexto selecionado, acessada pelas tabelas de metas da Base dos Dados e conferida contra o original |
| Resultados detalhados por série/rede e investigação | Tabelas `municipio`/`uf`, com origem nos arquivos agregados dos microdados |
| Recalcular e conferir o indicador | `alunos`, com elegibilidade e pesos validados; não substitui resultado publicado |

**Decisão:** na visão de acompanhamento oficial, usar o resultado divulgado na
publicação de metas e sua própria meta. Preservar ao lado o resultado agregado
dos microdados e o status da conferência. Isso especifica a política que estava
aberta no desenho: o agregado deixa de ser o único resultado principal da Gold
de cumprimento. As seis entidades continuam necessárias, inclusive para a
conferência e para as análises de recortes não disponíveis na publicação.

Uma tabela de metas preenchida não deve ser tomada como evidência de que todos os
seus campos já foram confrontados com o original. Registrar por campo/recorte a
situação da conferência. Se o BigQuery divergir do original da MESMA publicação:
preservar ambos, marcar divergência e bloquear a publicação afetada até registrar
a decisão. O original verificado é a autoridade semântica; não editar a fonte
pública nem aplicar correções avulsas escondidas.

### Regras de seleção

1. Fixar o ano do relatório, a publicação/contexto, o recorte e a cópia da fonte.
   O relatório-base de 2024 usa as linhas de referência 2024 e as fontes preservadas.
2. Não usar `MAX(ano)` ou o último arquivo disponível para sobrescrever o passado.
   A linha de referência não prova a data de publicação.
3. Preservar valores originais, operador, precisão e valor normalizado. Arredondar
   para exibição não muda o valor usado no cálculo. Tolerâncias de conferência
   devem refletir a precisão DOCUMENTADA de cada campo, não um 0,01 universal.
4. Uma diferença compatível com arredondamento é sinalizada como tal somente após
   verificar a precisão. Nunca usar tolerância para decidir que uma meta foi atingida.
5. Uma revisão oficial identificada pode originar uma nova versão do relatório,
   com fonte e justificativa. Não alterar a versão congelada silenciosamente.
6. Se o resultado não estiver divulgado na publicação, não usar automaticamente
   o valor dos microdados como resultado divulgado. Manter ambas as informações
   e a comparação oficial indisponível.
7. Se não houver meta, não usar uma de outra rede, território ou ano.

Exemplo já conferido: a meta nacional de 2024 é 59,9 na publicação original de
2024 (aba Divulgação Alfabet UF e Brasil, H3) e na linha 2024 do BigQuery; a linha
2025 informa 60,0. Para o relatório de 2024 fica 59,9, com a divergência de contexto
preservada. Não concluir, sem evidência, que ocorreu revisão ou arredondamento.

O resultado nacional original contém mais casas decimais (G3:
59,19727062879876) que o BigQuery (59,2). A saída do desafio pode manter o valor
normalizado publicado pela Base dos Dados, identificando essa normalização e
preservando o original para conferência; os saldos mostrados com duas casas são
aproximados. Não misturar precisão por fonte dentro de um mesmo cálculo.

### O caso especial do operador de meta

A planilha original de UF/Brasil escreve metas de 2030 como `> 80`, e o código
público de preparação da Base dos Dados normaliza essa representação para 80.
O enunciado pede usar a coluna pactuada da Base dos Dados, que contém 80.

Decisão: preservar `meta_texto_original`, `operador_original` e
`meta_percentual_bd`. Distância à meta numérica do desafio usa 80 e será rotulada
assim. Caso seja calculado cumprimento segundo o texto original `>80`, exigir
estritamente mais de 80. Exatamente 80 satisfaz `>=80`, mas não `>80`; não ocultar
a distinção. Aplicar o mesmo cuidado a outros anos que contenham operador na
publicação (por exemplo, a meta 2024 de CE). Nenhuma dessas representações vira
100%. Universalização permanece um cenário aspiracional separado.

## Evidência adicional: os 70 resultados de 2023

Foi conferido diretamente `DADOS/TS_MUNICIPIO.csv` do ZIP original. Os 70 valores
do recorte série 2/rede 3 coincidem com `municipio` no BigQuery. O
[CSV original](../referencias/inep_microdados_2023/TS_MUNICIPIO_2023.csv) e o
[resumo da verificação](../evidencias/decisoes_rede_territorio_fontes.json) foram preservados.

Portanto, as duas fontes efetivamente diferem em divulgação, não apenas por uma
hipótese sobre o notebook: os valores estão no agregado original, mas não na
planilha de divulgação/metas. Continua desconhecida a causa individual de não
divulgação para cada município dentro das alternativas descritas pelo Inep.

## Efeito no desenho e próximos passos

- Redes com significado explícito e códigos originais preservados.
- Território ligado ao ano de referência.
- Gold de acompanhamento com resultado da publicação, resultado agregado,
  proveniência, status de divulgação e conferência separados.
- Histórico de metas e precisão preservado, sem preenchimento automático.

As três decisões estão fechadas para o recorte investigado. Próximas decisões:
elegibilidade/pesos dos alunos, tolerâncias por campo e catálogo de regras
bloqueantes/informativas. Só depois avançar para arquitetura e implementação.
