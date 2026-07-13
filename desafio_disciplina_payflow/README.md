# Desafio da Disciplina - PayFlow Credit Risk

Projeto separado do Tech Challenge de NPS. Aqui aplicamos o CRISP-DM para estimar a probabilidade de um cliente entrar em `default` nos primeiros 90 dias apos a concessao de credito.

## Regra de negocio

- **Unidade:** cliente/proposta no momento da decisao de credito.
- **Acao observada:** `default_90d = 1` quando o cliente entra em default em ate 90 dias; caso contrario, `0`.
- **Horizonte:** 90 dias, alinhado a dor de inadimplencia inicial descrita no enunciado.
- **Decisao apoiada:** seguir a politica normal de credito ou encaminhar a proposta para revisao manual.
- **Importante:** o score nao deve ser usado como unica justificativa para recusar credito.

## Leakage e governanca

As seguintes colunas sao conhecidas somente depois da concessao e ficam fora do treinamento e da API:

- `parcelas_pagas_ate_3m`
- `atraso_primeira_parcela_dias`
- `status_apos_90d`

`id_cliente` e apenas identificador. `idade` e mantida para auditorias por faixa etaria, mas foi excluida do modelo operacional como decisao conservadora de governanca.

## Estrutura

```text
desafio_disciplina_payflow/
|-- api/                 # FastAPI
|-- data/raw/            # CSV e dicionario originais
|-- data/processed/      # previsoes do holdout
|-- docs/                # documento final autoexplicativo
|-- examples/            # exemplo de requisicao
|-- models/              # pipeline serializado
|-- presentation/        # apresentacao executiva
|-- reports/             # metricas, tabelas e figuras
|-- src/                 # treinamento CRISP-DM
|-- tests/               # testes da API
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## Como executar

No PowerShell:

```powershell
cd "D:\postech\POSTECH_AI_SCIENTIST-main\desafio_disciplina_payflow"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\src\train_model.py
```

## Rodar a API

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

Abra `http://127.0.0.1:8000/docs` para testar pelo Swagger.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Criterio de threshold

O threshold e escolhido em previsoes out-of-fold do treino, minimizando um custo ilustrativo:

- falso negativo: R$ 10.000 (default nao identificado);
- falso positivo: R$ 500 (oportunidade/revisao adicional).

Esses valores sao premissas didaticas. Em producao, devem ser substituidos por LGD, EAD, margem e custo operacional reais da PayFlow.

## Limites

- A base e sintetica e nao possui data de concessao; por isso usamos holdout e validacao cruzada estratificados, nao split temporal.
- A performance real so pode ser medida quando o target maturar, 90 dias depois.
- Antes de uso real sao necessarios validacao juridica, politica de credito, avaliacao de vies, seguranca, LGPD e aprovacao humana.

## Entregaveis

- [Documento final autoexplicativo](docs/relatorio_payflow_crisp_dm.docx)
- [Apresentacao executiva](presentation/payflow_credit_risk_executivo.pptx)
- [Analise CRISP-DM](reports/analise_crisp_dm.md)
