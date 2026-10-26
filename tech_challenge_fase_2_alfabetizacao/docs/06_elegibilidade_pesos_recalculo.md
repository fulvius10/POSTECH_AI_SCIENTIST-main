# Elegibilidade, pesos e recálculo da alfabetização

Investigação de 21/10/2026. Consultas de leitura e conferência dos arquivos originais;
nenhuma pipeline foi implementada. A fórmula foi definida, mas o recálculo NÃO
reproduz todos os indicadores publicados; divergências permanecem explícitas.

## Dicionário e unidade de análise

Conferidos os dicionários ORIGINAIS de 2023 e 2024, aba `TS_ALUNO`:

- C7: série 2 = 2º ano do Ensino Fundamental.
- C9: dependência administrativa 2 = Estadual, 3 = Municipal, 4 = Privada.
- C12:C13: presença 0 = ausente, 1 = presente. A UF define sua regra de presença.
- C14: preenchimento 0 = prova não preenchida, 1 = preenchida.
- B16: peso do aluno na prova de Língua Portuguesa.
- B17: proficiência equalizada com a escala do Saeb.
- B18:C18: alfabetizado 0 = não, 1 = sim; critério de proficiência **maior ou igual a 743**.

Referências:
[2023](../referencias/inep_microdados_2023/Dicionario_Microdados_AEEB_2023.xlsx) e
[2024](../referencias/inep_microdados_2024/Dicionario_Microdados_AEEB_2024.xlsx).
No BigQuery, esses campos estão normalizados como `serie`, `rede`, `presenca`,
`preenchimento_caderno`, `peso_aluno`, `proficiencia` e `alfabetizado`.

Cada aluno avaliado entra uma vez no grupo de ano, território, série e rede.
A chave candidata `(ano, id_municipio, id_escola, id_aluno, serie, rede)` não teve
repetições na fonte consultada. Isso não prova que `id_aluno` isoladamente seja
globalmente único ou que permita acompanhar a criança entre anos.

## Regra de elegibilidade

Para a taxa municipal: série 2 e rede 3. Para a taxa pública de UF e do conjunto
disponível do país: série 2 e redes 2/3, sem misturar privada ou federal.

Dentro do recorte, incluir a avaliação quando:

1. `presenca = '1'`;
2. `preenchimento_caderno = '1'`;
3. `proficiencia` preenchida e finita;
4. `alfabetizado` em `0` ou `1`;
5. `peso_aluno` preenchido, finito e estritamente positivo.

Presença e preenchimento são critérios do universo avaliado. Proficiência,
classificação e peso são também condições de validade: se faltarem num registro
presente/preenchido, contabilizar a anomalia e bloquear a conferência afetada até
investigação. Não excluir silenciosamente um peso ruim para produzir uma taxa.
Na consulta de pesquisa, todos esses critérios foram explicitados no filtro;
o perfil independente verifica se ele oculta anomalias.

Um ausente e um presente sem prova preenchida ficam fora do numerador E do
denominador. `alfabetizado = 0` sozinho não identifica uma avaliação válida.

O critério territorial de participação mínima para divulgação é outra regra.
Não confundir o filtro de aluno elegível com excluir do recálculo os municípios
sem resultado divulgado. Preservar o recálculo desses territórios identificado
como conferência, respeitando a política de publicação do documento 05. Não
reconstruir a participação oficial apenas com a proporção de presentes entre
linhas do arquivo; o denominador de participação precisa de definição própria.

## O que foi observado

Todos os registros têm classificação 0/1, inclusive os não avaliados. Os ausentes
ou presentes sem prova preenchida têm classificação 0 e peso/proficiência nulos.
Não tratá-los como alunos avaliados que não se alfabetizaram.

No recorte público (redes 2 e 3):

| Ano | Registros | Ausentes | Presentes sem preenchimento | Elegíveis |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 1.747.439 | 244.381 | 249 | 1.502.809 |
| 2024 | 2.120.535 | 267.771 | 936 | 1.851.828 |

Em 2024 há mais 25 registros privados: 1 ausente e 24 elegíveis no universo
privado. Eles não participam da taxa pública. Não confundir esse número com os
2.120.535 registros das redes 2 e 3.

Nos registros presentes/preenchidos de ambas as edições:

- Peso sempre positivo e finito; proficiência preenchida e finita.
- Nenhum peso zero/negativo/não finito; nenhum código de classificação desconhecido.
- Nenhuma divergência entre `alfabetizado` e o corte `proficiencia >= 743`.
- Existem pesos menores que 1 em 2023 (mínimo observado 0,0952381) e maiores que
  1. Não arredondar, impor mínimo 1, substituir por 1 ou limitar pesos altos.

Ver [perfil](../evidencias/perfil_alunos.json) e
[chaves e excluídos](../evidencias/chaves_e_excluidos_alunos.json).

## Fórmula definida

Para um grupo compatível de avaliações elegíveis:

```text
taxa (%) = 100 × soma(peso do aluno × indicador de alfabetizado)
                    / soma(peso do aluno)
```

O indicador vale 1 para alfabetizado e 0 para não alfabetizado. Numerador e
denominador usam EXATAMENTE o mesmo conjunto elegível. O denominador não é número
de matriculados, número bruto de linhas nem número de presentes sem prova válida.

Exemplo didático: dois alunos avaliados, um alfabetizado com peso 3 e outro não
alfabetizado com peso 1. A taxa ponderada é `100 × 3/4 = 75%`, não a contagem simples
de 50%. Peso representa a contribuição estatística atribuída ao registro; não é
nota do aluno. Não é necessário normalizar os pesos para aplicar essa razão.

Sem avaliações elegíveis ou com soma de pesos inválida, a taxa fica indisponível,
nunca zero. Preservar contagem de elegíveis, somas de pesos, numerador e razões
de exclusão junto à taxa, para permitir auditoria. Soma de pesos não deve ser
rotulada automaticamente como matrículas oficiais ou participação oficial.

Para passar do município à UF, somar numeradores e denominadores dos alunos do
universo escolhido e depois dividir. Não calcular média simples dos percentuais
municipais; também não ponderar esses percentuais apenas pelo número de linhas.

## Conferência executada

### Exemplos de 2024

| Recorte | Elegíveis | Soma dos pesos | Numerador ponderado | Taxa recalculada | Taxa publicada/da fonte |
| --- | ---: | ---: | ---: | ---: | ---: |
| Belo Horizonte, Municipal | 11.276 | 13.575,99 | 9.310,11 | 68,577761% | 68,58% |
| Belmiro Braga, Municipal | 29 | 30,04 | 17,32 | 57,656458% | 57,69% |
| Conjunto público disponível do país | 1.851.828 | 2.109.149,905224 | 1.248.608,780513 | 59,199622% | 59,20% nacional |

Na rede municipal de Belo Horizonte, a taxa sem peso seria 68,925151%, mostrando
que o peso tem efeito real no resultado.

A aproximação nacional de 2024 é uma conferência favorável, mas não prova
reprodução exata de todos os recortes nem identidade completa dos universos.
Os valores ponderados usam os pesos com a precisão disponibilizada na fonte.

### Comparação municipal ampla

O SQL usa junção completa com os resultados para preservar recálculos sem agregado
e agregados sem microdados. Comparando com a tabela `municipio`, rede municipal:

| Ano | Pares com taxa nas duas fontes | Pares com diferença absoluta até 0,01 p.p. | Pares com diferença maior que 0,01 p.p. | Agregados sem recálculo |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 4.821 | 4.028 | 793 | 627 |
| 2024 | 5.448 | 3.879 | 1.569 | 0 |

Esse 0,01 p.p. é uma faixa DESCRITIVA para contar diferenças; não é tolerância
de aceitação aprovada. Comparações com a publicação de metas têm precisão própria,
especialmente nos resultados de 2023 exibidos com uma casa decimal.

Também há recálculo sem resultado municipal correspondente: 1 município em 2023
e 2 em 2024. Eles foram preservados nas evidências, sem substituir a fonte.

Os 627 agregados sem recálculo em 2023 são de SP. O Leia-Me original de 2023,
página 17, informa que `TS_ALUNO` foi publicado sem as informações de São Paulo.
Logo, o agregado de todos os alunos disponíveis de 2023 (57,462163%) não deve ser
apresentado como reprodução do indicador nacional publicado (55,9%).

### Limitação de comparabilidade entre fontes

Uma investigação pontual encontrou indício de diferença na classificação da rede
de uma escola entre alunos e agregados. Isso não comprova um problema generalizado
nem autoriza reclassificar registros. A conferência geral deve distinguir diferença
de universo, precisão e cobertura, preservando a referência publicada. Não incluir
ausentes, ampliar tolerâncias ou alterar pesos apenas para reproduzir um valor.
Os arquivos específicos desse estudo de caso não integram o repositório.

## Tratamento acordado para o desenho

1. Aplicar a fórmula e a elegibilidade definidas como recálculo dos microdados disponíveis.
2. Usar `alfabetizado` como classificação fornecida, conferindo com `proficiencia >= 743`.
   Divergência futura não deve ser corrigida automaticamente trocando uma variável pela outra.
3. Separar validade do registro, cobertura territorial e reconciliação do resultado.
4. Não aumentar tolerâncias para fazer diferenças grandes passarem.
5. Manter a publicação de resultados/metas como referência de cumprimento, conforme
   documento 05; mostrar a taxa recalculada na conferência sem sobrescrever a oficial.
6. Uma investigação de divergência preserva valor, grupo, fonte e motivo pendente.
   O [catálogo de qualidade](07_catalogo_qualidade.md) distingue erro de processamento
   bloqueante de divergência informativa entre fontes; não afirmar que o recálculo
   está integralmente validado.

As regras bloqueantes e informativas estão no documento 07. A implementação
da pipeline continua fora do escopo desta etapa.
