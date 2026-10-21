# Tech Challenge Fase 2: alfabetização no Brasil

**Estado: investigação e planejamento. A pipeline ainda não foi implementada.**

Este diretório reúne as descobertas, consultas e evidências da investigação do
dataset `basedosdados.br_inep_avaliacao_alfabetizacao`. O objetivo do desafio é
construir posteriormente uma pipeline híbrida, com Bronze, Silver e Gold, execução
real em nuvem, qualidade, monitoramento e FinOps. A Gold deverá ser preservada para
a fase 3.

Registro consolidado em **21/10/2026**. Os números representam o estado consultado
da fonte nessa investigação, não uma garantia de que consultas futuras retornarão
os mesmos valores.

## Por onde começar

1. [Inventário e acesso](docs/01_inventario_e_acesso.md): fontes, volumes, recortes e autenticação.
2. [Resultados da investigação](docs/02_investigacao_metas_2024.md): junção, 216 exceções e comparação dos 70 casos com o Inep.
3. [Plano e requisitos](docs/03_plano_e_requisitos.md): próximos passos e checklist do enunciado.
4. [Enunciado original](referencias/enunciado_fase_2.pdf).
5. [Manifesto das fontes](referencias/manifesto.json): URLs, arquivos, tamanhos e SHA-256.
6. [Desenho proposto da base analítica](docs/04_desenho_base_analitica.md): tabelas, junções e decisões abertas.
7. [Decisões de rede, território e fonte](docs/05_decisoes_redes_territorio_fontes.md): regras fechadas e evidências.
8. [Alunos, pesos e recálculo](docs/06_elegibilidade_pesos_recalculo.md): regra de elegibilidade, fórmula e limites de reprodução.

## O que já foi verificado

- Projeto Google Cloud: `postech-fase2-fulvius`.
- BigQuery API habilitada e acesso pelo computador testado.
- Sete tabelas acessíveis: seis entidades obrigatórias e dicionário.
- Resultados municipais de 2024 comparados com metas da **rede municipal**.
- 5.448 resultados, 5.352 correspondências e 5.232 comparações possíveis.
- 96 municípios sem registro de meta e 120 com meta de 2024 ausente.
- Entre os 120, 70 têm resultado de 2023 em `municipio`, mas não na publicação de
  resultados e metas. As duas planilhas originais confirmam a diferença.
- Meta pactuada e cenário aspiracional são conceitos separados: a coluna nacional
  de 2030 para a rede Pública contém 80; universalização é a aspiração de 100%.

## Consultas para repetir a investigação

Abra os arquivos abaixo no editor SQL do BigQuery, com o projeto
`postech-fase2-fulvius` selecionado. São consultas de leitura, sem criação de tabelas.

| Arquivo | Objetivo |
| --- | --- |
| [01_inventario.sql](sql/01_inventario.sql) | Contagens e tamanhos nos metadados |
| [02_cobertura.sql](sql/02_cobertura.sql) | Anos, séries, redes e volumes de resultados |
| [03_resultados_municipais_metas_2024.sql](sql/03_resultados_municipais_metas_2024.sql) | Comparação por município, preservando ausências |
| [04_investigar_excecoes.sql](sql/04_investigar_excecoes.sql) | Detalhar os 216 casos e o resultado de 2023 |
| [05_metricas_da_juncao.sql](sql/05_metricas_da_juncao.sql) | Correspondência, preenchimento e cumprimento |
| [06_dicionario.sql](sql/06_dicionario.sql) | Interpretar códigos oficiais |
| [07_unicidade_das_chaves.sql](sql/07_unicidade_das_chaves.sql) | Detectar chaves repetidas antes de juntar |
| [08_contexto_metas_uf_brasil.sql](sql/08_contexto_metas_uf_brasil.sql) | Conferir anos, rede Pública e mudanças de metas históricas entre linhas |
| [09_codigos_territoriais_por_ano.sql](sql/09_codigos_territoriais_por_ano.sql) | Códigos distintos para conferir contra a DTB do respectivo ano |
| [10_perfil_alunos.sql](sql/10_perfil_alunos.sql) | Presença, preenchimento, pesos e corte de proficiência |
| [11_recalculo_municipal.sql](sql/11_recalculo_municipal.sql) | Taxa ponderada municipal e comparação entre fontes |
| [12_recalculo_publico_uf_brasil.sql](sql/12_recalculo_publico_uf_brasil.sql) | Agregação dos alunos públicos elegíveis por UF e no conjunto disponível |
| [13_chaves_e_excluidos_alunos.sql](sql/13_chaves_e_excluidos_alunos.sql) | Chave candidata e classificação nos registros excluídos |

O usuário informou ter salvo `03_resultados_municipais_metas_2024` no BigQuery
Studio. Este diretório guarda uma versão SQL com a mesma lógica; a consulta salva
não foi inspecionada por API para confirmar igualdade de conteúdo.

**Sandbox** é o modo de utilização do BigQuery. A consulta salva é um recurso do
projeto, contendo SQL; ela não é uma cópia dos resultados nem uma camada Bronze.

## Evidências locais

- [Planilha original de 2023](referencias/inep_resultados_e_metas_municipios_2023.xlsx).
- [Planilha original de 2024](referencias/inep_resultados_e_metas_municipios_2024.xlsx).
- [Comparação dos 70 municípios](evidencias/comparacao_70_municipios.csv).
- [Resumo da conferência](evidencias/resumo_conferencia.json).
- [Métricas retornadas pela consulta da junção](evidencias/metricas_juncao_2024.json).
- [Contexto consultado das metas de UF e Brasil](evidencias/contexto_metas_uf_brasil.json).
- [Conferência de rede, território e fontes originais](evidencias/decisoes_rede_territorio_fontes.json).
- [Resumo do recálculo ponderado](evidencias/resumo_recalculo_alunos.json).
- [Conferência municipal dos alunos](evidencias/recalculo_municipal_alunos.csv).

Os originais foram copiados sem alterações. Esses arquivos e consultas são material
de pesquisa, não representam ingestão, tratamento ou execução da futura pipeline.
Nenhuma credencial deve ser versionada.

## Verificação deste registro

- Sete SQLs validados por dry run no BigQuery.
- Consulta `05_metricas_da_juncao.sql` executada novamente e contagens confirmadas.
- Os 70 casos conferidos contra os dois originais, incluindo metas de 2025 e 2030.
- SHA-256 das três referências e links locais da documentação conferidos.

Essas verificações validam o material de investigação; não são testes da futura pipeline.

## Próximo passo

Definir o catálogo de qualidade e priorizar divergências materiais do recálculo.
Elegibilidade e fórmula foram documentadas no documento 06, com conferência
parcial: há diferenças entre produtos originais ainda sem causa determinada.
As tabelas propostas não foram criadas.
