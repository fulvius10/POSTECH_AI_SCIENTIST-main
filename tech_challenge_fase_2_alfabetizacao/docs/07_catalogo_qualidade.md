# Catálogo de qualidade

Versão 1, definida em 21/10/2026. Em 26/10, batch e streaming simulado passaram a
executar parte deste contrato, também no Cloud Shell. Resultados ficam em
`data/audit/`, `data/cloud_audit/` e `data/streaming/`; as evidências selecionadas
estão em `evidencias/`. O catálogo completo continua sendo a referência de
requisitos. Os comandos agora notificam falhas via ntfy, com histórico em
`data/alerts/` e `data/monitor/`; o escopo e as limitações constam no README.

## Política de publicação

- **Bloqueante:** sem aprovação de todas as regras obrigatórias, a execução falha
  e não publica a próxima camada/versão analítica. A versão anterior válida fica
  disponível. Não transformar erro em sucesso num `except` genérico.
- **Informativa:** registra alerta ou limitação, preserva os dados e permite
  publicação com status explícito. Dado indisponível não vira zero nem indicador
  de baixo desempenho.
- **Não aplicável:** somente quando o produto/etapa está fora do escopo declarado
  da execução. Regra obrigatória que não rodou não equivale a aprovação.

As condições abaixo avaliam o produto e o recorte declarados no contrato: tabela,
ano, rede, série, nível territorial e versão/contexto da fonte. Não extrapolar
limites de 2024 para uma edição nova sem novo levantamento.

Bronze preserva o material de origem, inclusive registros inválidos, para auditoria.
Uma falha não autoriza apagar esse histórico. Os dados não aprovados não avançam
para consumo analítico. Publicar uma camada significa promover a versão inteira
validada, não deixar algumas tabelas novas e outras antigas após uma falha.

## Regras bloqueantes

| ID | Verificação | Condição de aprovação | Por que bloqueia |
| --- | --- | --- | --- |
| B01 | Fontes e estrutura obrigatórias | As seis entidades e o dicionário previstos no contrato estão disponíveis; colunas essenciais e tipos são compatíveis | Falta de fonte ou coluna impede interpretar/integrar os dados |
| B02 | Conteúdo e rastreabilidade da extração | A fonte esperada não está vazia sem justificativa; snapshot, fonte e recorte identificáveis; cópia histórica preservada | Evita publicar uma extração incompleta ou perder a origem |
| B03 | Chaves | Nenhuma chave obrigatória nula, malformada ou repetida no grão definido | Duplicidade e identificação ambígua alteram somas e junções |
| B04 | Domínios e números | Nenhum código desconhecido de rede/série/presença/preenchimento/classificação; percentuais normalizados preenchidos finitos entre 0 e 100; pesos preenchidos não negativos e finitos | Evita converter código novo em categoria válida ou produzir indicador impossível |
| B05 | Cadastro territorial | 100% dos códigos educacionais encontram exatamente um território no cadastro do respectivo ano; associação UF compatível | Não há lacuna territorial conhecida nos recortes investigados |
| B06 | Cardinalidade das junções | Cada resultado encontra no máximo uma meta após selecionar o contexto; junção não multiplica nem elimina linhas indevidamente | Uma junção pode funcionar tecnicamente e alterar o indicador |
| B07 | Correspondência e preenchimento das metas | Nenhuma chave esperada sem par ou meta esperada ausente fora das exceções específicas do recorte; correspondência e preenchimento medidos separadamente | Impede que falha de chave ou perda de valor seja confundida com ausência já conhecida da fonte |
| B08 | Universo e tempo | Comparação anual com mesmo território, rede, série/escopo e ano-alvo; referência 2030 rotulada separadamente; operador e contexto da meta respeitados | Impede comparar Municipal com Pública ou meta de outro ano sem identificação |
| B09 | Validade de alunos avaliados | Entre presentes com prova preenchida, nenhum peso nulo/zero/não finito, proficiência nula/não finita ou classificação inválida | Excluir esses registros silenciosamente alteraria o denominador |
| B10 | Coerência da classificação | Nenhum aluno com avaliação válida contradiz `alfabetizado = 1` se e somente se `proficiencia >= 743` | A classificação fornecida e a proficiência discordariam sobre o numerador |
| B11 | Fórmula e estados de ausência | Numerador e denominador usam o mesmo conjunto elegível; resultados finitos e coerentes; nenhum nulo convertido em zero; sem meta/resultado não recebe status de cumprimento | Protege a interpretação da taxa e dos saldos |
| B12 | Contexto e seleção de fonte | Uma fonte/contexto escolhido por campo e chave; nenhuma divergência impeditiva original/BigQuery da mesma publicação sem decisão registrada | Evita sobrescrever o passado ou escolher arbitrariamente um valor conflitante |
| B13 | Integridade da saída | Contagens, grupos, somas e classificações conciliam com a etapa anterior; nenhuma linha some sem destino registrado | Impede publicar perda de dados ou filtro não explicado |
| B14 | Histórico da qualidade | Resultados das validações e métricas de execução foram persistidos antes da promoção | Uma mensagem no terminal não comprova a qualidade da versão publicada |
| B15 | Origem e eventos, quando houver streaming | Oficial/simulado identificados; evento inválido não chega à Silver/Gold; um evento repetido não altera o resultado duas vezes; destinos de todos os eventos contabilizados | Impede contaminação do indicador e dupla contagem |

Precisões sobre os limites:

- B03 usa a chave no grão de cada tabela. Nos alunos, a candidata investigada é
  `(ano, id_municipio, id_escola, id_aluno, serie, rede)`; não presumir ID de aluno
  global. Na Bronze, duplicidade de recebimento de evento pode ser legítima;
  unicidade lógica é cobrada na etapa tratada, não pela exclusão do bruto.
- B04 não impõe mínimo 1 ao peso: pesos fracionários positivos são válidos. Peso
  zero não é usado no cálculo e, se aparecer em avaliação presente/preenchida,
  reprova B09. Nulo esperado em ausente não reprova B09. Proficiência não recebe
  faixa arbitrária que ainda não foi validada no dicionário.
- B11 não exige que todo grupo tenha avaliações válidas. Com denominador ausente
  ou zero, o resultado deve ficar indisponível. Se o sistema publicar 0% nessa
  situação, a regra falha. Percentual verdadeiro de 0% é diferente de ausência.
- B12 distingue divergência de conteúdo de normalização documentada. Exemplo:
  precisão original diferente da Base dos Dados pode ser transformação conhecida;
  não constitui licença para aceitar qualquer diferença.
- B15 permite rejeitar/quarentenar eventos inválidos e reconhecer duplicados como
  comportamento esperado. Isso gera alerta se o destino e a contagem estiverem
  persistidos. Evento inválido que avançou ou duplicado contado duas vezes bloqueia.

Qualquer falha bloqueante encerra a execução responsável pela publicação afetada
como falha. Não continuar promovendo suas outras saídas. Se futuramente houver
produtos independentes, seus escopos e execuções deverão ser declarados separados;
isso não é uma exceção improvisada para esconder uma validação reprovada.

## Regras informativas e alertas

| ID | Situação | Tratamento exigido para permitir publicação |
| --- | --- | --- |
| A01 | Ausência de registro ou de valor de meta já confirmada na fonte | Preservar resultado e motivo; comparação indisponível; medir contagem e correspondência |
| A02 | Resultado ou recálculo ausente por cobertura conhecida | Preservar ausência e escopo; não rotular agregado parcial como reprodução nacional completa |
| A03 | Recálculo dos alunos difere do indicador publicado | Registrar ambos, diferença e hipótese quando houver; não sobrescrever o publicado nem apresentar a conferência como aprovada |
| A04 | Precisão diferente, com normalização conferida | Preservar valor original, valor normalizado, precisão e regra aplicada; exibir a limitação |
| A05 | Novo período ou nova publicação disponível fora do recorte congelado | Registrar disponibilidade; incorporar só numa versão/contexto deliberadamente escolhido |
| A06 | Variação de volume, distribuição, peso ou taxa sem violação de contrato | Comparar com referência por recorte e abrir triagem; não chamar variação real de erro automaticamente |
| A07 | Eventos atrasados, inválidos ou duplicados tratados conforme contrato | Registrar motivo, destino, quantidade e latência; usar somente eventos válidos e únicos na saída |

Não há um limite estatístico de volume ou mudança de taxa calibrado com apenas dois
anos. Na versão inicial, mudança de quantidade/distribuição deve ser informada,
sem inventar um corte percentual genérico. Fonte obrigatória vazia, perda de
registros e quebra de contrato continuam bloqueantes, conforme B01/B02/B13.
Prazos operacionais de latência e notificação dependerão da arquitetura, ainda não
escolhida; não alegar que já existe um SLA medido.

## Exceções conhecidas: números não bastam

Para o recorte municipal de 2024, série 2/rede 3, a referência é:

| Métrica | Levantamento |
| --- | ---: |
| Resultados municipais | 5.448 |
| Correspondências de meta | 5.352 |
| Sem registro de meta | 96 |
| Com registro, mas meta 2024 vazia | 120 |
| Comparações possíveis | 5.232 |
| Correspondência bruta | 98,237885% |
| Comparações possíveis / resultados | 96,035242% |

Essas quantidades não são um teste do tipo "até 96 perdas está bom". As exceções
devem ser reconhecidas pelas CHAVES e pelo contexto da fonte. Uma chave com
problema não pode substituir outra e passar porque a contagem permaneceu igual.

Decisão para B07: exigir **100% das correspondências esperadas**, admitindo somente
as ausências específicas já verificadas na fonte daquele contexto. Mostrar sempre
também a taxa bruta de 98,24%, sem mascará-la com uma taxa ajustada. Para o cadastro
territorial (B05), a referência é 100% sem exceções nos recortes testados.

As 120 metas nulas seguem A01 quando o nulo e sua chave forem confirmados na fonte.
Se uma nova chave ficar sem par ou perder meta no recorte congelado, não ampliar
a lista automaticamente: interromper a publicação, investigar a causa e registrar
eventual revisão do contrato/exceção. Melhorias de preenchimento também devem
atualizar a referência de forma rastreável, sem manter exceções obsoletas.

O cadastro operacional de exceções ainda não foi criado. Na implementação, deverá
ser derivado das fontes preservadas e consultas de investigação, com chave, razão,
evidência, contexto e regra aplicável. Uma edição nova precisa de referência própria.

## Como classificar as divergências

Registrar separadamente erro do processamento e diferença entre produtos da fonte:

| Tipo | Resultado |
| --- | --- |
| Junção multiplicou linhas, rede mapeada errada ou cálculo aplicado incorretamente | Falha bloqueante; corrigir o processamento |
| BigQuery e original da mesma publicação discordam além de transformação verificada | Falha bloqueante na seleção do campo; revisão documentada |
| Alunos e agregado publicado discordam, mas cada fonte foi preservada e a fórmula está correta | Alerta A03; recálculo não homologado nesse recorte; indicador publicado permanece referência |
| Falta de microdados para reproduzir o universo completo | Alerta A02; conferência indisponível ou parcial, não "divergência de cálculo" |
| Diferença compatível com precisão comprovada | Informativa A04; sem corrigir o dado bruto |

Não adotar 0,01 p.p. como tolerância universal. Esse valor foi usado apenas para
descrever a distribuição das diferenças na investigação. Para correspondência
de um número com sua representação publicada, usar a precisão/regra documentada
de cada campo. O arredondamento para exibição nunca decide cumprimento de meta.

Diferenças em pontos percentuais e diferenças na escala de proficiência terão
unidades próprias. Uma conferência não executada ou sem cobertura fica
`NAO_AVALIAVEL`; um recálculo divergente fica `DIVERGENTE`; concordância segundo
regra documentada fica `COMPATIVEL_NA_PRECISAO`. Nenhum desses estados deve ser
confundido com situação de cumprimento da meta.

## Registro persistente proposto

São estruturas lógicas de auditoria, ainda não tabelas implementadas:

### Execução

`id_execucao`, início/fim, etapa, recorte, fontes/snapshots, versão do código e do
contrato, duração, linhas de entrada/saída, status e referência da versão publicada.
Estados finais: `SUCESSO`, `SUCESSO_COM_ALERTAS` ou `FALHA`. Não preencher uma
versão publicada quando a promoção não ocorreu. Registrar também falhas de ingestão.

### Resultado de cada regra

`id_execucao`, `id_regra`, severidade, escopo, valor observado, limite/condição,
numerador e denominador quando houver taxa, exceções aplicadas, quantidade afetada,
estado (`APROVADA`, `ALERTA`, `REPROVADA`, `NAO_APLICAVEL`) e evidência.
Uma regra obrigatória não executada impede aprovação. Falhas técnicas de validação
não devem ser registradas como ausência de problemas.

### Divergência

`id_divergencia`, chave/recorte (ano, território, rede, série), campo, unidades,
fontes A/B e snapshots, valores A/B, diferença assinada/absoluta, estado de
conferência, regra relacionada, hipótese, evidência, primeira/última ocorrência,
responsável pela análise e decisão. Quando um valor faltar, a diferença fica nula,
com motivo, e não zero.

Fluxo de análise: `ABERTA` → `EM_ANALISE` → `RESOLVIDA` ou `LIMITACAO_ACEITA`.
Aceitar uma limitação não significa corrigir o valor, homologar a equivalência
ou dispensar futuras verificações. Registrar justificativa, responsável, escopo
e condição de revisão; a execução seguinte verifica novamente. O estado de
conferência permanece divergente/indisponível enquanto essa for a realidade.

Não incluir registros completos de alunos ou credenciais no relatório de erros.
Preferir contagens e chaves técnicas mínimas, com detalhes restritos quando
necessários. O histórico deve acumular execuções, não sobrescrever a anterior.

## Exemplos de comportamento esperado

| Ocorrência | Decisão |
| --- | --- |
| Junção transforma 5.448 resultados em 5.600 linhas | B06 reprova; não publicar |
| Os 96 municípios conhecidos continuam sem registro de meta no mesmo contexto | A01; publicar com ausência identificada e taxa bruta registrada |
| Uma chave adicional perde correspondência | B07 reprova até investigação; não alterar limite só para passar |
| Peso nulo em aluno ausente | Exclusão esperada do universo; contabilizar |
| Peso nulo em aluno presente com prova preenchida | B09 reprova a execução de recálculo responsável |
| Recálculo territorial difere do indicador, mas fontes e fórmula estão íntegras | A03; registrar diferença e recálculo não homologado, mantendo referência publicada |
| Campo da fonte contém `>80`, mas o cálculo afirma que exatamente 80 satisfaz esse operador | B08/B11 reprovam; separar comparação estrita de distância à meta numérica da Base dos Dados |
| Validações não puderam ser persistidas | B14 reprova; não promover a versão |

Na implementação, demonstrar pelo menos uma falha bloqueante antes da publicação,
verificar preservação da versão anterior, resultado persistido e notificação de
falha. Esses testes e mecanismos continuam pendentes.

## Próximo passo

Desenhar a arquitetura de execução e escolher serviços para ingestão, armazenamento,
processamento, validação e observabilidade. A partir dela, definir cadência, SLA,
destino persistente da auditoria, canal de notificação e responsáveis. Não construir
esses componentes antes de discutir o desenho com o usuário.
