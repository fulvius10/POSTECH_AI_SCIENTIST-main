# Inventário e acesso à fonte

Consolidação da investigação de 21/10/2026.

## Fonte e acesso

- [Dataset na Base dos Dados](https://basedosdados.org/dataset/073a39d4-89cf-4068-b1e8-34ed0d9c0b72).
- Dataset BigQuery: `basedosdados.br_inep_avaliacao_alfabetizacao`.
- Projeto de execução das consultas: `postech-fase2-fulvius`.
- [Console do projeto](https://console.cloud.google.com/bigquery?project=postech-fase2-fulvius).
- Localização informada nos metadados das sete tabelas: `US`.

O acesso por BigQuery já foi testado. Consultar a fonte pública a partir do nosso
projeto não copia os dados para ele. A forma de ingestão definitiva ainda deve ser
decidida e justificada em custo, atualização e arquitetura.

## Inventário

Contagens e bytes obtidos dos metadados. Bytes lógicos não são tamanho de CSV ou
Parquet, volume de transferência nem estimativa de custo mensal.

| Tabela | Linhas | Bytes lógicos |
| --- | ---: | ---: |
| `uf` | 145 | 10.330 |
| `municipio` | 23.995 | 1.832.061 |
| `alunos` | 3.867.999 | 268.545.240 |
| `meta_alfabetizacao_brasil` | 3 | 270 |
| `meta_alfabetizacao_uf` | 81 | 7.374 |
| `meta_alfabetizacao_municipio` | 10.704 | 1.151.232 |
| `dicionario` | 27 | 1.174 |

Não foi encontrado particionamento por tempo nos metadados consultados. Selecionar
poucas colunas é relevante: `LIMIT` sozinho não garante redução de bytes lidos.

## Cobertura observada

As tabelas `alunos`, `municipio` e `uf` contêm resultados de **2023 e 2024**, todos
com `serie = '2'`. Isso não significa que todas as tabelas de metas se restrinjam
a esses anos. A cobertura de cada entidade deve ser verificada separadamente.

| Tabela | Ano | Rede e número de linhas |
| --- | --- | --- |
| `alunos` | 2023 | 2: 155.140; 3: 1.592.299 |
| `alunos` | 2024 | 2: 280.258; 3: 1.840.277; 4: 25 |
| `municipio` | 2023 | 2: 1.149; 3: 5.448; 5: 4.950 |
| `municipio` | 2024 | 0: 398; 2: 1.086; 3: 5.448; 5: 5.516 |
| `uf` | 2023 | 2: 22; 3: 24; 5: 24 |
| `uf` | 2024 | 0: 1; 2: 24; 3: 25; 5: 25 |

Essas são contagens de registros, não de alunos avaliados. Não assumir cobertura
completa de todos os territórios ou redes. Os 25 registros de alunos de rede privada
em 2024 são um ponto para investigação, não um erro já comprovado.

## Chaves e códigos

- `municipio`: chave candidata `(ano, id_municipio, serie, rede)`.
- Metas municipais: chave candidata `(ano, id_municipio, rede)`.
- Não foram encontradas repetições dessas chaves nas tabelas consultadas.
- `id_municipio` é texto e deve preservar o código territorial de sete dígitos.
- `municipio` e `alunos` não têm coluna `sigla_uf`. O enriquecimento territorial
  precisará de um mapeamento oficial, caso seja necessário mostrar UF e nomes.
- O dicionário diferencia rede municipal (`3`), estadual (`2`), privada (`4`),
  pública estadual e municipal (`5`), entre outros códigos. Consultar o dicionário
  por tabela; os códigos não devem ser presumidos a partir de outra entidade.
- As metas municipais usam o texto `Municipal`, não o código `3`.
- Não há coluna `serie` nas metas municipais. A documentação da avaliação define
  o universo do 2º ano; o resultado usado na comparação é filtrado explicitamente.

## Autenticação local

Para repetir em outro computador, instalar Google Cloud CLI, autenticar a própria
conta e selecionar um projeto autorizado:

```powershell
gcloud config set project postech-fase2-fulvius
gcloud auth application-default login
```

O login de bibliotecas (ADC) é separado do login usado pelos comandos do CLI.
Não copiar tokens, senhas ou arquivos de credenciais para o repositório.
O projeto não concede automaticamente acesso a outra pessoa que clone o código.

A BigQuery API foi habilitada e as consultas de leitura funcionaram. O aviso do
`gcloud init` sobre Compute Engine não impediu esses testes. Não foi necessário
habilitar Compute Engine para a investigação.

## Pendências

- Conferir semântica, cobertura e chaves de metas nacionais e estaduais.
- Definir o mapeamento territorial e seu papel como fonte auxiliar.
- Validar universo, presença e pesos antes de recalcular taxas pelos alunos.
- Medir extração e armazenamento do desenho definitivo. As consultas de pesquisa
  não constituem ainda a medição FinOps completa exigida no desafio.
