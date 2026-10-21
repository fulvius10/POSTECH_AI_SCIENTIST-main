# Resultados municipais e metas de 2024

Investigação consolidada em 21/10/2026. Consultas de leitura no projeto
`postech-fase2-fulvius`. Nenhuma tabela analítica foi criada.

## Pergunta e recorte

Qual foi o resultado de alfabetização da rede municipal em cada município em 2024
e como ele se compara à meta pactuada para o mesmo ano?

Usar `municipio`, filtrando `ano = 2024`, `serie = '2'`, `rede = '3'`, e juntar com
`meta_alfabetizacao_municipio`, filtrando `ano = 2024` e `rede = 'Municipal'`.
Relacionar por `ano` e `id_municipio`. O mapeamento entre `3` e `Municipal` deve
ser explícito; a comparação não serve ao resultado público agregado, rede `5`.

Não juntar somente pelo município: as metas têm registros de 2023 e 2024 e a junção
sem ano multiplicaria linhas. As colunas `meta_alfabetizacao_2024` a
`meta_alfabetizacao_2030` representam anos-alvo; o campo `ano` representa o ano do
resultado na linha. As metas de 2024 e 2030 são iguais entre as duas linhas de cada
um dos 5.352 municípios, conforme verificado, mas isso não dispensa a chave anual.

O `LEFT JOIN` preserva os resultados sem correspondência. O filtro de rede das
metas fica na condição de junção, evitando eliminar as linhas sem meta.

## Métricas verificadas

| Métrica | Quantidade |
| --- | ---: |
| Resultados municipais no recorte | 5.448 |
| Linhas após a junção | 5.448 |
| Registros de metas de 2024, rede Municipal | 5.352 |
| Resultados com correspondência | 5.352 |
| Sem correspondência | 96 |
| Com correspondência, mas meta 2024 nula | 120 |
| Com resultado e meta 2024 preenchidos | 5.232 |
| Atingiram ou superaram a meta 2024 | 2.788 |
| Ficaram abaixo da meta 2024 | 2.444 |
| Resultado 2024 nulo no recorte | 0 |
| Diferenças > 0,01 p.p. entre os resultados das duas tabelas, nos pares | 0 |

- Correspondência: `5352 / 5448 = 98,24%`.
- Comparação possível: `5232 / 5448 = 96,04%`.
- Não confundir correspondência da chave com preenchimento do valor da meta.
- Não usar 5.448 como denominador de uma proporção de cumprimento calculada apenas
  sobre os 5.232 comparáveis.

Exemplo: Belo Horizonte (`3106200`), rede municipal, resultado 2024 de 68,58%, meta
2024 de 61,33%, saldo de +7,25 pontos percentuais. Isso comprova cumprimento em
2024; não significa cumprimento da meta de 2030.

## Grupo A: 96 municípios sem registro na tabela de metas

- Ausentes em ambos os anos da tabela de metas municipais.
- Todos os códigos têm sete dígitos.
- Remover espaços e converter códigos para inteiro não recuperou nenhum par.
- 94 tinham resultado na tabela `municipio` em 2023.
- Não é possível atribuir o grupo inteiro simplesmente à falta de resultado anterior.
- A causa individual dessa diferença de cobertura permanece pendente.

Decisão proposta: preservar o resultado e registrar `Sem registro de meta`.
Não aplicar 80% automaticamente como se fosse uma meta municipal publicada.

## Grupo B: 120 municípios com meta 2024 nula

- Têm registro nas metas em 2023 e 2024.
- O resultado de 2023 está nulo na tabela de metas em todos os 120.
- Todos têm metas futuras de 2025 a 2030, terminando em 80%.
- 70 têm resultado de 2023 na tabela `municipio`; 50 não têm esse registro.
- Em MG são 17 desse grupo e 12 do grupo A, totalizando 29 exceções.

Decisão proposta: preservar a meta nula e registrar `Meta 2024 ausente`. As metas
futuras publicadas podem ser analisadas para os anos correspondentes.

## Conferência dos 70 casos com os originais do Inep

Foram baixadas e preservadas sem alterações:

1. [Publicação original de 2023](../referencias/inep_resultados_e_metas_municipios_2023.xlsx),
   disponível no [Inep](https://download.inep.gov.br/avaliacao_da_alfabetizacao/resultados_e_metas_municipios.xlsx).
2. [Publicação original de 2024](../referencias/inep_resultados_e_metas_municipios_2024.xlsx),
   disponível no [Inep](https://download.inep.gov.br/alfabetiza_brasil/resultados_e_metas_municipios_2024.xlsx).

Nos 70 municípios, o arquivo de 2023 mostra `-` no resultado, na participação e
nas metas. A observação da linha 5472, aba `Divulgação Alfabet Municipio`, informa:

> municípios sem resultados são os que não participaram da avaliação ou que tiveram percentual de participação abaixo de 70%

O arquivo de 2024 contém os 70 municípios, mantendo vazios o resultado de 2023 e
a meta de 2024. As metas de 2025 e 2030 conferem com o BigQuery nos 70 casos.
As 120 metas de 2024 nulas também foram confirmadas no conjunto da planilha de 2024.

A [página do Inep](https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/avaliacao-da-alfabetizacao/resultados/2024)
registra alteração em 23/09/2025 para incluir metas de municípios sem resultados
em 2023. Isso é compatível com a presença de metas futuras e ausência da meta 2024,
mas não comprova o motivo individual de cada ausência.

### Origem da diferença

O código público da Base dos Dados indica dois produtos de origem:

- `municipio`: arquivo `DADOS/TS_MUNICIPIO.csv` dos pacotes de microdados de cada ano.
  [Preparação publicada](https://github.com/basedosdados/pipelines/blob/main/models/br_inep_avaliacao_alfabetizacao/code/ica_microdados.ipynb).
- `meta_alfabetizacao_municipio`: planilha de resultados e metas, com resultados
  de 2023 e 2024 reorganizados em linhas anuais.
  [Preparação publicada](https://github.com/basedosdados/pipelines/blob/main/models/br_inep_avaliacao_alfabetizacao/code/saeb_avalicao_alfabetizacao.ipynb).

Esses notebooks indicam a origem, mas não são uma prova independente de qual
revisão de código gerou cada carga atualmente publicada no BigQuery.

**Conclusão confirmada:** nos 70 casos, os vazios já existem na publicação do Inep;
não foram introduzidos pela nossa junção. Um resultado numérico no arquivo
agregado não equivale a resultado divulgado na publicação usada para metas.

**Limite da conclusão:** a nota apresenta não participação ou participação abaixo
de 70% como causas. Ela não identifica a causa de cada município; não afirmar que
todos os 70 tiveram participação abaixo de 70%.

Na etapa posterior de [decisão das fontes](05_decisoes_redes_territorio_fontes.md),
o ZIP original foi baixado e `TS_MUNICIPIO.csv` conferido diretamente: os 70 valores
coincidem com o BigQuery. Essa verificação supera a pendência de comparação com o
CSV original, mas não identifica o motivo individual da não divulgação.

### Exemplos municipais de MG

| Município | Código | Resultado 2023 em `municipio` | Resultado 2023 na publicação | Meta 2024 na publicação |
| --- | --- | ---: | --- | --- |
| Águas Formosas | 3100906 | 77,78% | Ausente | Ausente |
| Belmiro Braga | 3106101 | 33,60% | Ausente | Ausente |
| Veríssimo | 3171105 | 97,76% | Ausente | Ausente |

O [CSV dos 70 casos](../evidencias/comparacao_70_municipios.csv) contém nomes,
valores, células de origem e sinalização de ausência. A
[conferência resumida](../evidencias/resumo_conferencia.json) registra as contagens.

## Tratamento analítico proposto

1. Preservar todos os resultados e o motivo pelo qual a comparação está indisponível.
2. Não preencher nulo com zero, copiar meta de outro ano ou reconstruir meta não publicada.
3. Manter a origem do resultado de 2023 e sinalizar sua ausência na publicação de metas.
4. Manter resultado bruto, status de divulgação e elegibilidade para análise separados.
   Antes de usar esses resultados em evolução temporal ou IA, definir explicitamente
   se o estudo exige o universo oficialmente divulgado.
5. Não interpretar `Meta 2024 ausente` ou `Sem registro de meta` como desempenho ruim.
6. Medir correspondência e preenchimento separadamente. Investigar variações futuras
   em relação a este levantamento, sem baixar limites só para fazer uma execução passar.

## Meta 2030

Na tabela nacional consultada, `rede = 'Pública'` tem `meta_alfabetizacao_2030 = 80`.
As metas municipais de 2030 consultadas também são 80. Para distância à meta,
usar o valor pactuado da fonte. Universalização (100%) só pode aparecer como cenário
aspiracional identificado. Não substituir metas municipais ausentes pela meta nacional.
