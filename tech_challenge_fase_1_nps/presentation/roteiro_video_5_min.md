# Roteiro executivo - vídeo de até 5 minutos

Antes de gravar, inclua na capa o nome do grupo e dos integrantes. O texto abaixo
é um guia de fala; use linguagem natural e não leia cada número do slide.

## Slide 1 - Abertura (0:00-0:25)

"Olá, somos [nome do grupo]. Nosso desafio foi entender por que alguns clientes de
um e-commerce se tornam promotores e outros detratores, e como a empresa pode agir
antes mesmo de receber a pesquisa de NPS. Analisamos 2.500 pedidos, combinando
informações do pedido, entrega e atendimento."

## Slide 2 - Dimensão do problema (0:25-0:55)

"O primeiro diagnóstico é preocupante. Setenta e quatro por cento dos pedidos são
detratores e apenas 4,4% são promotores. Isso gera um NPS tradicional de menos
69,6. Portanto, nossa pergunta deixou de ser apenas por que o NPS caiu: buscamos
onde a operação consegue intervir antes que a experiência termine mal."

## Slide 3 - Atraso como ruptura (0:55-1:30)

"O atraso é o ponto de ruptura mais claro. Sem atraso, a nota média é 6,86. Com três
a quatro dias, mais de nove em cada dez clientes já são detratores. A partir de
cinco dias, a taxa chega a 99,4%. Nossa primeira recomendação é criar um alerta no
terceiro dia, antes que a recuperação se torne muito mais difícil."

## Slide 4 - Reclamações e contatos (1:30-2:05)

"A experiência também se deteriora quando os problemas se acumulam. Com zero ou uma
reclamação, apenas 7,6% são detratores; com seis ou mais, são 94,5%. Três ou mais
contatos com atendimento também estão associados a 90,4% de detratores. O contato
não é necessariamente a causa; ele sinaliza que um problema anterior continua sem
solução. Por isso, o segundo contato já deve escalar o caso."

## Slide 5 - Solução preditiva (2:05-2:50)

"Como etapa adicional, construímos um classificador para estimar a probabilidade de
o cliente ser detrator. Excluímos recompra e CSAT porque podem representar
informação do futuro. A regressão logística alcançou ROC-AUC de 0,877, acima do
baseline de 0,5. Em termos práticos, o modelo não decide sozinho: ele ordena uma
fila para o time priorizar quem tem maior risco."

## Slide 6 - Plano de ação (2:50-3:35)

"Propomos três movimentos. Agora, alertar no terceiro dia de atraso e no segundo
contato. Nos próximos 30 a 60 dias, testar recuperação proativa, como atualização
clara, contato especializado ou compensação. Em 90 dias, medir NPS, recompra e
custo da intervenção, recalibrando limites com base no resultado real."

## Slide 7 - Limitações e governança (3:35-4:15)

"Os resultados mostram associação, não causalidade. A base não informa data, SLA,
transportadora ou taxa de resposta, e possui apenas um pedido por cliente. Por isso,
a implantação deve começar como experimento prospectivo, com grupo de controle,
revisão humana, monitoramento de drift e cuidado para não criar tratamento
discriminatório."

## Slide 8 - Encerramento (4:15-4:45)

"Em resumo, a empresa não precisa esperar a pesquisa para cuidar da experiência.
Os três gatilhos prioritários são: três dias de atraso, o segundo contato e o
acúmulo de reclamações. Com alertas, recuperação proativa e medição de impacto, o
NPS deixa de ser apenas um indicador tardio e passa a orientar ação operacional.
Obrigado."

## Margem de segurança (4:45-5:00)

Reserve os 15 segundos finais para uma pausa, troca de apresentador ou pequena
variação de ritmo. O vídeo não deve ultrapassar cinco minutos.

