# Tech Challenge Fase 1 - Case NPS Preditivo

Este projeto identifica quais fatores operacionais mais afetam a satisfação em um
e-commerce e demonstra como antecipar clientes com risco de se tornarem
detratores antes da pesquisa de NPS.

## Resumo 

A base possui 2.500 pedidos e 19 variáveis originais, sem valores ausentes ou
registros duplicados. O quadro de satisfação exige ação: 74,0% dos pedidos são
detratores, apenas 4,4% são promotores e o NPS tradicional da amostra é **-69,6**.

Os principais pontos encontrados foram:

- o atraso é um ponto de ruptura: o NPS médio cai de 6,86 sem atraso para 1,28
  quando o atraso chega a cinco dias ou mais;
- reclamações acumuladas agravam fortemente a experiência: clientes com zero ou
  uma reclamação têm NPS médio 7,89, contra 2,82 entre clientes com seis ou mais;
- três ou mais contatos com atendimento estão associados a 90,4% de detratores;
- o tempo de resolução também importa: a taxa de detratores sobe de 64,2% em
  resoluções de até dois dias para 81,5% quando a resolução leva nove dias ou mais.

Associação não prova causalidade. Os resultados indicam onde investigar e testar
intervenções, mas não autorizam concluir sozinhos que uma variável causa o NPS.

## Objetivo

A pergunta orientadora é: **quais sinais da operação explicam a insatisfação e
permitem agir antes da pesquisa de NPS?** A resposta pode apoiar logística,
atendimento, produto, pricing, CRM e a liderança de experiência do cliente.

O alvo analítico principal é `nps_score`, coletado depois da experiência de compra.
Para a solução preditiva, o alvo foi transformado em `is_detractor`: valor 1 para
nota menor ou igual a 6 e valor 0 para notas acima de 6. Essa classificação foi
escolhida porque cria uma fila operacional direta de clientes que precisam de
atenção.

## Metodologia

1. Validação do contrato dos dados, unicidade dos identificadores, faixa do NPS e
   qualidade geral.
2. Criação das categorias oficiais: detratores (0 a 6), neutros (acima de 6 e
   abaixo de 9, devido aos decimais da base) e promotores (9 a 10).
3. EDA orientada a perguntas de negócio, com segmentação por atraso, reclamações,
   contatos, resolução e região.
4. Separação estratificada de 80% para treino e 20% para teste.
5. Comparação entre baseline, regressão logística e random forest.
6. Avaliação por ROC-AUC, average precision, precisão, recall e F1 dos detratores.

`repeat_purchase_30d` e `csat_internal_score` foram excluídos do modelo. A recompra
acontece depois do pedido e o momento de medição do CSAT não está documentado;
usar esses campos para uma previsão anterior a pesquisa criaria risco de vazamento
de informação. `customer_id` e `order_id` também foram excluídos porque são apenas
identificadores.

## Resultado do modelo

A regressão logística foi escolhida pela melhor discriminação no teste e por ser
mais explicável:

| Modelo | ROC-AUC | Average precision | Precisão detrator | Recall detrator |
|---|---:|---:|---:|---:|
| Regressão logística | 0,877 | 0,947 | 0,915 | 0,786 |
| Random forest | 0,869 | 0,930 | 0,901 | 0,838 |
| Baseline majoritário | 0,500 | 0,740 | 0,740 | 1,000 |

O baseline marca todos os clientes como detratores. Por isso, o recall de 1,0 não
representa inteligência nem capacidade de priorização; sua ROC-AUC de 0,5 confirma
que ele não ordena riscos. A regressão logística, por outro lado, separa os casos de
maior e menor risco com ROC-AUC 0,877. No conjunto de teste, ela identificou 291 dos
370 detratores e gerou 27 falsos alertas.

## Estrutura

```text
tech_challenge_fase_1_nps/
|-- data/
|   |-- raw/desafio_nps_fase_1.csv
|   `-- processed/                 # dados preparados e previsões
|-- models/                        # pipeline treinada
|-- reports/
|   |-- figures/                   # gráficos da EDA e do modelo
|   |-- analise_negocio.md
|   `-- *.csv / *.json             # tabelas e métricas auditáveis
|-- src/
|   |-- run_analysis.py
|   `-- score_new_orders.py
|-- presentation/                  # apresentacao executiva
|-- requirements.txt
`-- README.md
```

## Como reproduzir

No PowerShell, dentro desta pasta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src\run_analysis.py
```

O comando valida a base, recria as tabelas e figuras, treina os modelos e salva a
pipeline escolhida em `models/detractor_classifier.joblib`.

Para simular a priorização de novos pedidos:

```powershell
python src\score_new_orders.py --input data\raw\desafio_nps_fase_1.csv
```

O arquivo `data/processed/scored_orders.csv` será ordenado do maior para o menor
risco e terá uma faixa operacional (`Baixo`, `Alto` ou `Crítico`). Os limites são
iniciais e devem ser calibrados conforme capacidade e custo do time.

## Entregáveis

- [Análise conceitual e de negócio](reports/analise_negocio.md)
- [Gráficos da análise](reports/figures/)
- [Metricas dos modelos](reports/model_metrics.csv)
- [Apresentacao executiva](presentation/tech_challenge_nps_executivo_fase_1.pptx)

## Limitações

- a base não informa data do pedido; portanto, não foi possível fazer validação
  temporal nem verificar mudancas de comportamento;
- há um único pedido por cliente, impedindo avaliar evolução individual;
- o momento exato do `csat_internal_score` não foi documentado;
- o padrão de NPS tem valores decimais, enquanto pesquisas reais normalmente usam
  notas inteiras;
- a amostra pode ser sintética e não há informação sobre taxa de resposta da
  pesquisa, custo das intervenções ou SLA prometido;
- o modelo estima associações e risco, não efeito causal de uma ação.




