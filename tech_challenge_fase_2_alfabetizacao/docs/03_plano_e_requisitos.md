# Plano antes da implementação

**Registro histórico do planejamento de 21/10/2026.** Os estados abaixo descrevem
aquela etapa; para implementação, evidências e pendências atuais da entrega,
consulte o [README](../README.md).

Estado em 21/10/2026: investigação documentada. Acesso ao BigQuery não equivale
à implementação da pipeline exigida no desafio.

## Próximo passo: contrato da base analítica

Uma [primeira proposta do contrato](04_desenho_base_analitica.md) foi documentada.
Revisar e discutir o desenho abaixo antes de criar camadas ou recursos.

1. **Significado de cada linha.** Proposta: um resultado por ano, município, série
   e rede; tabelas estaduais e nacionais em seus próprios níveis de agregação.
   Não somar ou calcular média simples de percentuais municipais para substituir
   um indicador nacional ponderado.
2. **Metas em formato anual.** Proposta: uma linha por território, rede e ano-alvo,
   em vez de uma coluna por ano de meta. Preservar o ano do resultado/referência,
   a publicação de origem e eventuais versões. Não assumir que metas repetidas
   entre linhas são versões distintas nem removê-las sem conferir consistência.
3. **Recortes compatíveis.** Mapear redes usando o dicionário; separar Municipal,
   Estadual e Pública. Validar semântica de metas nacionais e estaduais, incluindo
   o universo exato de Pública, antes de ligá-las aos resultados.
4. **Território.** Decidir como obter nomes e UFs por código oficial. Uma dimensão
   auxiliar não dispensa o uso das seis entidades obrigatórias.
5. **Estados de comparação.** Distinguir atingiu, não atingiu, meta ausente,
   registro de meta ausente e resultado ausente. A ausência na publicação deve
   ter sinalização própria e não apagar o valor do arquivo agregado.
6. **Papel dos alunos.** Definir agregação ponderada com alunos avaliados,
   tratamento de presença/preenchimento e confronto com os indicadores publicados.
   Ainda falta executar essa validação.
7. **Qualidade.** Propor regras bloqueantes e informativas para chaves,
   domínios, correspondência, preenchimento e divergência entre fontes. Definir
   limites justificados e o comportamento quando a fonte mudar. Duplicidade que
   multiplica linhas e códigos de rede desconhecidos são candidatos a bloqueio;
   as lacunas conhecidas devem ficar identificadas, com política explícita.

Resultado esperado dessa etapa: desenho das tabelas, mapa das junções e catálogo
de regras. É documentação de decisões; não implica construir a pipeline.

## Sequência posterior, ainda não executada

1. Escolher serviços e forma de ingestão com justificativa de custo e atualização.
2. Implementar um caminho batch completo, preservando histórico e validações.
3. Incorporar streaming simulado e distinguir origem oficial de simulada.
4. Demonstrar execução normal e falha bloqueante, persistir métricas e testar alerta.
5. Medir consumo e projetar custos mensais.
6. Testar reprodução em clone limpo e preparar apresentação e vídeo.

## Requisitos do enunciado e situação

Fonte: [enunciado original](../referencias/enunciado_fase_2.pdf).

| Critério | Pontos | O que deverá ser demonstrado | Situação |
| --- | ---: | --- | --- |
| Ingestão híbrida | 15 | Batch; recepção e processamento incremental de eventos; inválidos, duplicados e garantias | Pendente |
| Medalhão | 15 | Bronze histórica, Silver validada e Gold analítica preservada para fase 3 | Pendente |
| Qualidade | 10 | Regras bloqueantes/informativas; correspondência após cada join; falha real antes da publicação; resultados persistidos | Investigação inicial documentada; mecanismos pendentes |
| Observabilidade | 10 | Duração, volumes, status e latência reais; histórico persistido; notificação de falhas e responsável | Pendente |
| FinOps | 10 | Quantidades medidas e tabela de serviço, unidade, preço e custo mensal projetado | Pendente |
| Cloud e organização | 10 | Pipeline executada em AWS/GCP/Azure com IDs de jobs, logs, contagens e evidências | Acesso GCP testado; pipeline pendente |
| README e documentação | 5 | Diagrama fiel, escolhas, reprodução, limitações, IA e link do vídeo | Documentação de pesquisa iniciada |
| Vídeo executivo | 15 | Até 5 minutos, com pelo menos um integrante e números rastreáveis | Pendente |

Regras transversais a manter:

- Usar efetivamente UF, Município, Alunos e as três entidades de metas. Usar também
  o dicionário para interpretar os códigos.
- Preservar histórico Bronze de fato; conferir se o modo de escrita apaga execuções.
- Se simulação se juntar ao oficial, manter origem identificável.
- Não capturar falha bloqueante e terminar com sucesso.
- Medir latência com horários distintos de produção e ingestão.
- Não descrever alertas, CI, orquestração ou recursos planejados como existentes.
- Justificar acesso por BigQuery ou download; considerar custo, transferência e atualização.
- Dependências com versão, configurações externas e nenhuma credencial versionada.
- Explicar limites do Sandbox e projetar o desenho de produção quando aplicável.
- Base de IA sem vazamento do alvo. Dois anos de resultados não sustentam por si
  uma previsão temporal robusta até 2030; cenários devem ser identificados como tal.

Diferenciais, depois dos obrigatórios: confronto ponderado de microdados e
indicadores, orquestração, infraestrutura como código, testes de transformação e
investigação documentada de anomalias. Este registro contribui para o último item.

## Aprendizado da entrega da fase 1

O feedback fornecido pelo usuário registrou nota 80/90, elogiou análise, modelagem,
clareza e cuidado com vazamento e correlação/causalidade. Apontou falta do PPT na
entrega e recomendou incluir link do GitHub.

Na fase 2, preparar os links e materiais junto com o desenvolvimento, testar acesso
ao repositório e ao vídeo, e conferir se números de gráficos, slides e código coincidem.
O PDF exige vídeo; PPT é uma recomendação de organização baseada no feedback,
não um requisito explícito adicional do enunciado.
