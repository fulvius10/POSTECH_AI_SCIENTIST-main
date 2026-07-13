# PayFlow Credit Risk - CRISP-DM na pratica

## Resumo executivo

A PayFlow precisa reduzir a inadimplencia nos primeiros 90 dias sem paralisar a concessao de credito. A solucao proposta estima, no momento da analise da proposta, a probabilidade de `default_90d`. O score nao toma a decisao final: ele prioriza casos de maior risco para revisao humana e deve ser combinado com politica de credito, capacidade de pagamento e regras regulatorias.

A base possui 5.000 clientes e prevalencia de default de 12,18%. O modelo selecionado foi Random Forest com calibracao sigmoid. No holdout de 1.250 clientes, obteve ROC-AUC 0,728, Average Precision 0,350 e Brier Score 0,095. Com threshold didatico de 0,06, o recall de defaults foi 84,2%, ao custo de muitos falsos positivos. Essa troca e intencional porque a premissa usada considera um default perdido vinte vezes mais caro que uma revisao indevida.

## 1. Business Understanding

### Dor, stakeholders e decisao

- Diretoria e Risco de Credito: equilibrar crescimento e qualidade da carteira.
- Cobranca: antecipar volume e priorizar clientes com maior risco.
- Comercial e Produto: reduzir recusas indiscriminadas e manter conversao saudavel.
- Compliance, Juridico e DPO: garantir explicabilidade, LGPD, nao discriminacao e rastreabilidade.
- Cliente: receber uma decisao consistente e contestavel.

A decisao melhorada e: seguir a politica normal de credito ou encaminhar a proposta para revisao manual. Nao recomendamos recusa automatica baseada apenas no modelo.

### Target

- Unidade: cliente/proposta de credito.
- Acao: `default_90d = 1` quando houve default em ate 90 dias apos a concessao; caso contrario, `0`.
- Periodo: 90 dias, pois esse e o horizonte da dor relatada e permite medir inadimplencia inicial.
- Momento da inferencia: imediatamente antes da concessao.

### Metas de negocio e analiticas

KPIs de negocio sugeridos: reduzir perda esperada nos primeiros 90 dias, manter taxa de aprovacao dentro do apetite de risco, diminuir sobrecarga de cobranca e acompanhar taxa de revisao manual. Metricas analiticas: ROC-AUC, Average Precision, recall, precision, Brier Score/calibracao, matriz de confusao e custo por threshold.

## 2. Data Understanding

A base sintetica contem 5.000 linhas e 23 colunas, sem duplicidade de linhas ou de `id_cliente`. Ha 609 defaults, equivalentes a 12,18%, caracterizando desbalanceamento moderado.

Ausencias:

- `renda_mensal`: 192 registros (3,84%).
- `tempo_emprego_anos`: 526 registros (10,52%).

No mundo real, os dados viriam de CRM/cadastro, core bancario, bureau, motor de credito, app/site/loja/parceiros e atendimento. A definicao do target viria do desempenho contratual observado no core de cobranca depois de 90 dias.

## 3. Data Preparation

### Leakage

Foram removidas antes do split:

- `parcelas_pagas_ate_3m`: so existe depois de tres meses.
- `atraso_primeira_parcela_dias`: depende do comportamento posterior a concessao.
- `status_apos_90d`: descreve diretamente o desfecho futuro.

Uma regressao logistica treinada propositalmente com essas colunas obteve AUC, Average Precision e acuracia de 1,0. Isso nao representa excelencia: representa vazamento. Em producao essas informacoes ainda nao existem no momento da decisao.

### Outras exclusoes e tratamentos

- `id_cliente`: removido porque apenas identifica o registro.
- `idade`: analisada para equidade, mas removida do modelo operacional por governanca conservadora.
- Ausentes numericos: mediana calculada no treino, com indicadores de ausencia.
- Categoricas: imputacao pela moda e one-hot encoding com categorias desconhecidas permitidas.
- Numericas: padronizacao para tornar a regressao logistica estavel e comparavel.
- Outliers: auditados pelo criterio IQR, mas nao removidos automaticamente. Valores extremos de renda, valor solicitado e atraso podem ser eventos de negocio validos; binarios e contagens com muitos zeros tornam o IQR enganoso e exigem regra de dominio.

Todo tratamento fica dentro de um `Pipeline` do scikit-learn, evitando que estatisticas do teste vazem para o treino.

## 4. Modeling

Foram comparados:

- Dummy pela prevalencia: baseline minimo, sem poder discriminativo.
- Regressao logistica: simples, explicavel e adequada como baseline real.
- Random Forest: captura relacoes nao lineares e interacoes.

A selecao usou a maior Average Precision media em validacao cruzada estratificada de cinco partes. A Random Forest foi selecionada e recebeu calibracao sigmoid em dados de treino. A calibracao e necessaria porque o produto entregue e uma probabilidade, nao apenas uma ordenacao de risco.

## 5. Evaluation

O dataset nao possui data de concessao. Portanto, um split temporal verdadeiro nao pode ser executado. Foi usado holdout estratificado de 25% mais cross-validation estratificada no treino. Em uma base real, a recomendacao e treinar em meses anteriores e testar nos meses seguintes.

Resultados do modelo calibrado no holdout:

- ROC-AUC: 0,728.
- Average Precision: 0,350, contra prevalencia de 0,122.
- Brier Score: 0,095.
- Threshold 0,50: precision 60,5%, recall 15,1%.
- Threshold 0,06: precision 16,1%, recall 84,2%.

O threshold de 0,06 foi calculado em previsoes out-of-fold do treino, assumindo custo de R$ 10.000 por falso negativo e R$ 500 por falso positivo. Sao valores ilustrativos; a PayFlow deve substitui-los por EAD, LGD, margem, custo de capital e custo operacional reais.

As variaveis mais importantes por permutacao foram atraso maximo nos ultimos 12 meses, valor solicitado, renda mensal, inadimplencias anteriores, juros e score de credito. Importancia nao prova causalidade.

## 6. Deployment

A API FastAPI oferece:

- `GET /health`: saude e versoes carregadas.
- `POST /predict`: recebe somente dados disponiveis na decisao e devolve probabilidade, threshold, classe, faixa de risco, acao recomendada, versao do modelo e versao do target.

Campos extras sao rejeitados. Assim, uma tentativa de enviar `status_apos_90d` recebe erro 422. O endpoint recomenda revisao humana para probabilidades acima do threshold, em vez de recusa automatica.

## MLOps e governanca

- Logging: request ID, timestamp, versao do modelo/target, probabilidades, decisao e latencia; evitar dados pessoais desnecessarios.
- Drift de entrada: PSI, KS, categorias novas e taxa de ausentes por variavel.
- Drift de score: distribuicao das probabilidades e proporcao por faixa de risco.
- Performance: somente apos maturacao de 90 dias, recalcular AUC, AP, Brier, recall, precision e custo.
- Equidade: comparar taxas, calibracao e erros por regiao e faixa etaria; investigar diferencas, sem concluir vies apenas por amostras pequenas.
- Retreinamento: trimestral ou quando houver deterioracao persistente, drift relevante ou mudanca de produto/politica.
- Versionamento: dados, codigo, features, modelo, threshold e `default_90d_v1` devem ser versionados em conjunto.
- Aprovacao: challenger passa por validacao independente, Compliance/Juridico e teste em shadow/canary antes de substituir o champion.

## Conclusao

O prototipo demonstra o processo completo do problema ao servico de inferencia. Ele e adequado para aprendizagem e prova de conceito, mas nao para decisao real sem dados temporais, custos reais, validacao independente, avaliacao juridica e monitoramento apos 90 dias.
