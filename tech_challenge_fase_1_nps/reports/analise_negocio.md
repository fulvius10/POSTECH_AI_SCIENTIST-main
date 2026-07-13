# Análise de negócio - Case NPS Preditivo

## 1. Entendimento do negócio

### Qual problema está sendo resolvido?

Hoje a empresa descobre a insatisfação somente depois que a jornada termina e a
pesquisa é respondida. O problema é transformar sinais que já existem na operação -
pedido, entrega e atendimento - em uma leitura antecipada do risco. Assim, a empresa
pode priorizar clientes vulneráveis, corrigir falhas e evitar que um problema
operacional se transforme em perda de relacionamento.

### Por que o NPS importa para um e-commerce?

O NPS resume a disposição do cliente em recomendar a marca. Ele não substitui
métricas operacionais ou financeiras, mas funciona como um termômetro da experiência
completa. Em e-commerce, onde o cliente compara alternativas rapidamente e troca de
fornecedor com pouco atrito, uma experiência ruim pode reduzir a recompra, aumentar
o custo de atendimento e gerar comunicação negativa.

### Áreas beneficiadas

- **Logística:** priorizar atrasos, reduzir reincidências e rever transportadoras ou
  rotas com baixo desempenho.
- **Atendimento:** identificar contatos repetidos, reduzir tempo de resolução e criar
  recuperação proativa da experiência.
- **CRM e marketing:** separar campanhas de fidelização de campanhas de recuperação
  e evitar ofertas inadequadas a clientes com problema aberto.
- **Produto e jornada digital:** investigar motivos de contato e reclamação para
  remover fricções recorrentes.
- **Pricing e comercial:** avaliar se frete, desconto ou parcelamento alteram a
  percepção de valor, sem confundir correlação com causalidade.
- **Estratégia/CX:** acompanhar NPS por segmento, dimensionar perdas e coordenar
  planos entre áreas.

### Impacto esperado

- **Recompra:** clientes insatisfeitos tendem a reduzir novas compras ou migrar para
  concorrentes. Na base, a recompra em 30 dias está fortemente associada ao NPS,
  mas ela é um resultado posterior e não deve ser usada para prever o próprio NPS.
- **Boca a boca:** detratores podem amplificar experiências negativas em redes
  sociais, sites de reclamação e avaliações de produto; promotores podem reduzir a
  dependência de mídia paga por indicação espontânea.
- **Market share:** a acumulação de churn e reputação negativa pode reduzir conversão
  e participação. O NPS sozinho não mede market share, mas pode funcionar como sinal
  antecedente quando analisado junto a métricas comerciais.

Indicadores complementares recomendados: recompra em 30/60/90 dias, churn, lifetime
value, taxa de devolução, cancelamento, prazo prometido versus realizado, entrega no
prazo, first contact resolution, backlog, custo por contato, CSAT, CES, taxa de
resposta da pesquisa, reclamações públicas, conversão, participação de mercado e
benchmarks comparáveis de NPS.

## 2. Definição da target

`nps_score` representa a satisfação declarada em uma escala de 0 a 10 e foi
escolhida porque é a medida diretamente ligada ao problema apresentado. Ela é
coletada após a experiência de compra. Para a etapa preditiva, transformamos a nota
em `is_detractor`, onde 1 representa nota até 6 e 0 representa nota acima de 6.

A classificação foi escolhida em vez da regressão porque a primeira decisão do
negócio é binária: intervir ou não intervir. Além disso, prever uma nota com casas
decimais sugere uma precisão que a pesquisa não oferece. A probabilidade de detração
permite ordenar uma fila conforme capacidade operacional.

Riscos de uso inadequado:

- tratar NPS como prova de causalidade;
- usar variáveis observadas somente depois da pesquisa (vazamento);
- punir times ou transportadoras sem controlar diferenças de mix;
- ignorar clientes que não respondem a pesquisa;
- transformar o score em decisão automática sem supervisão;
- usar os mesmos limites para sempre, sem monitorar drift e calibração.

## 3. EDA orientada ao negócio

### Diagnóstico geral

A base possui 2.500 pedidos, sem ausentes ou duplicidades. O NPS médio é 4,38, mas a
métrica corporativa deve usar as categorias: 74,0% detratores, 21,6% neutros e 4,4%
promotores. O NPS tradicional é, portanto, 4,4 - 74,0 = **-69,6**.

### Fatores mais críticos

1. **Atraso da entrega.** Sem atraso, o NPS médio é 6,86 e 36,5% são detratores.
   Com 3-4 dias, o NPS cai para 3,10 e 91,8% são detratores. Com cinco dias ou
   mais, o NPS médio chega a 1,28 e a detração chega a 99,4%.
2. **Reclamações.** Com zero ou uma reclamação, o NPS médio é 7,89 e a detração é
   7,6%. Com seis ou mais, o NPS cai para 2,82 e a detração chega a 94,5%.
3. **Contatos repetidos.** Sem contato, a taxa de detratores é 59,2%; com três ou
   mais contatos, sobe para 90,4%. Contato não é necessariamente a causa: ele pode
   ser um sinal de um problema anterior que não foi resolvido.
4. **Tempo de resolução.** A detração passa de 64,2% para resoluções em até dois
   dias para 81,5% quando o prazo é de nove dias ou mais.

### Ponto de ruptura

O salto mais claro aparece a partir de **três dias de atraso**, quando mais de nove
em cada dez pedidos já são detratores. Um segundo ponto operacional é **três ou mais
contatos**, também com detração superior a 90%. Esses limites não são universais;
devem ser validados em novas safras e por tipo de pedido.

### Perfil de maior e menor NPS

O perfil de maior satisfação é operacional, não demográfico: pouco ou nenhum atraso,
poucas reclamações e resolução rápida. Região, idade, tempo de relacionamento, valor
e quantidade de itens apresentam diferenças pequenas nesta amostra. Isso é positivo
para a ação: a empresa deve corrigir processos, e não rotular pessoas.

## 4. Estratégia preditiva opcional

A solução classifica o risco de detração antes da pesquisa. Foram usadas apenas
variáveis de cliente, pedido, logística e atendimento disponíveis até o encerramento
operacional da jornada. `repeat_purchase_30d`, `csat_internal_score`, identificadores
e a própria nota de NPS foram excluídos.

Os dados foram separados de forma estratificada: 2.000 pedidos para treino e 500
para teste. A estratificação preserva a proporção de detratores. Comparamos um
baseline, regressão logística e random forest. A regressão logística atingiu ROC-AUC
0,877, precisão de 91,5% e recall de 78,6% para detratores. Foi escolhida por combinar
capacidade de ordenação e explicabilidade.

Na prática, o modelo deve pontuar pedidos quando os dados finais de entrega e
atendimento estiverem disponíveis, antes do disparo da pesquisa. A probabilidade
alimenta uma fila: risco crítico recebe contato proativo ou compensação; risco alto
recebe acompanhamento; risco baixo segue o fluxo padrão. O limite deve refletir
capacidade da equipe, custo do falso alerta e custo de perder um detrator.

## Recomendacoes priorizadas

1. Criar alerta em tempo real para pedidos que atinjam três dias de atraso e uma
   rotina ainda mais urgente para cinco dias ou mais.
2. Tratar o segundo contato como sinal de escalonamento e o terceiro como incidente
   crítico, preservando contexto para evitar que o cliente repita a historia.
3. Definir dono e prazo para reclamações, com prioridade a clientes que acumulam
   quatro ou mais registros.
4. Testar recuperação de experiência (informação proativa, frete ou beneficio) por
   experimento controlado, medindo NPS, recompra e custo incremental.
5. Implantar um painel semanal com detração por atraso, reclamações, contatos e
   tempo de resolução, acompanhado de intervalos e volume de cada segmento.
6. Monitorar o modelo por safra: ROC-AUC, recall, precisão, calibração, drift e impacto
   real das intervenções.

## Limitações e riscos

Não existem datas, SLA prometido, transportadora, categoria de produto, motivo do
contato, devolução nem taxa de resposta. Há um pedido por cliente e a amostra pode
ser sintética. Assim, não foi possível validar no tempo, avaliar clientes recorrentes
ou estimar efeito causal. A implantação exige teste prospectivo, governança e revisão
humana. O modelo deve priorizar cuidado, nunca negar atendimento ou criar tratamento
discriminatório.




