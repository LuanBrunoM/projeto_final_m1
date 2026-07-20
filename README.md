# 🧳 Pipeline de Dados - Viagens a Serviço (Portal da Transparência)

Pipeline de dados completo (ETL), construído do zero, que baixa, organiza e
analisa os dados públicos de Viagens a Serviço do Governo Federal.

## 🎯 O problema que este projeto resolve

O Portal da Transparência disponibiliza os dados de viagens a serviço em
formato bruto (CSV), sem tratamento, com inconsistências de tipo, valores
ausentes e sem qualquer modelagem relacional. Este projeto transforma esses
dados brutos em informação confiável, permitindo responder perguntas de
negócio reais sobre os gastos públicos com viagens.

## 🛠️ Tecnologias utilizadas

- **Python** — extração, transformação e análise dos dados
- **PostgreSQL** — armazenamento, seguindo a Arquitetura Medallion
- **pandas** — leitura e manipulação dos dados em blocos (chunks)
- **psycopg2** — conexão e execução de comandos no PostgreSQL
- **gdown** — download automatizado do arquivo de dados no Google Drive
- **matplotlib / seaborn** — geração dos gráficos
- **Jupyter Notebook** — análise exploratória e camada Gold

## 🏗️ Arquitetura: Medallion (Raw → Silver → Gold)

| Camada     | O que é                                                                                                                     | Tabelas                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Raw**    | Cópia fiel dos CSVs originais. Todas as colunas `VARCHAR`, sem constraints.                                                 | `raw_viagem`, `raw_pagamento`, `raw_passagem`, `raw_trecho`             |
| **Silver** | Dados limpos e tipados (`DECIMAL`, `DATE`), com `PRIMARY KEY`, `FOREIGN KEY` e constraints (`NOT NULL`, `CHECK`, `UNIQUE`). | `silver_viagem`, `silver_pagamento`, `silver_passagem`, `silver_trecho` |
| **Gold**   | Métricas de negócio agregadas, criadas com `JOIN` + `GROUP BY`.                                                             | `gold_resumo_orgao` (tabela e view)                                     |

```
CSV bruto  ->  [1_extrair.py]      ->  tabelas RAW (texto puro)
tabelas RAW -> [2_transformar.py]  ->  tabelas SILVER (limpo e tipado)
tabelas SILVER -> [3_analise.ipynb] -> respostas + graficos (GOLD)
```

## 📁 Estrutura do repositório

```
.
├── .gitignore
├── 0_criar_banco.sql      # Cria as 8 tabelas (4 Raw + 4 Silver)
├── 1_extrair.py           # Baixa o .zip e carrega a camada Raw
├── 2_transformar.py       # Transforma Raw -> Silver
├── 3_analise.ipynb        # Perguntas de negocio + camada Gold
├── banco.py               # Funcoes de conexao com o PostgreSQL
├── config.py               # Configuracoes e leitura do .env
├── requirements.txt       # Dependencias do projeto
└── README.md
```

## 🚀 Como executar

**1. Clonar e criar o ambiente virtual**

```bash
git clone https://github.com/LuanBrunoM/projeto_final_m1.git
cd projeto_final_m1
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

**2. Configurar as credenciais**

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
```

Preencha o `.env` com as credenciais do seu PostgreSQL local.

**3. Criar o banco de dados**

Crie um banco chamado `transparencia` (ou o nome definido em
`POSTGRES_DATABASE` no `.env`) e rode:

```bash
psql -h localhost -U postgres -d transparencia -f 0_criar_banco.sql
```

(ou execute o conteúdo do arquivo direto na Query Tool do pgAdmin 4)

**4. Rodar o pipeline, em ordem**

```bash
python 1_extrair.py       # Baixa os dados e carrega a camada Raw
python 2_transformar.py   # Limpa, tipa e carrega a camada Silver
```

**5. Abrir a análise**

Abra `3_analise.ipynb` no Jupyter e execute as células em ordem. Ele cria a
camada Gold e responde às perguntas de negócio.

## ❓ Perguntas de negócio respondidas

1. Os 5 órgãos com maior custo total?
2. Os 3 destinos com maior custo médio por viagem?
3. A viagem de maior duração e seu custo total?
4. Qual o tipo de pagamento com maior valor médio?
5. Qual o meio de transporte mais usado nos trechos?
6. Qual UF de destino aparece em mais trechos?
7. Qual órgão pagou mais no total?

## 📊 Conclusões e insights

- O órgão com maior custo total em viagens foi o **Ministério da Justiça
  e Segurança Pública**, com gasto total de aproximadamente
  **R$ 490.813.500,00**, dividido em **75.742 viagens**.
- O destino com maior custo médio por viagem foi **Nova Maringá/MT**.
- A viagem mais longa registrada teve **383 dias** de duração, bem
  acima da média geral de aproximadamente **7 dias**.
- O tipo de pagamento com maior valor médio foi **Diárias**.
- O meio de transporte predominante nos trechos foi **Veículo Oficial**.
- A UF de destino mais frequente foi **São Paulo**.
- O ógão que mais pagou no total foi **Fundo Nacional de Segurança Pública**.
- **14.768 viagens** não tinham `nome_orgao_superior` preenchido na fonte original,
  sendo preenchido o valor `"Não informado"` na limpeza. Esse grupo, teve um custo total de
  aproximadamente **R$ 78,7 milhões**. Esse é um ponto a ser melhorado na fonte de dados original.

## 🔮 Possíveis melhorias

- Orquestrar o pipeline com uma ferramenta como Airflow.
- Registrar logs em arquivo, além dos print() no console.
- Orquestrar o pipeline com um script único, que roda as fases em
  sequência, em vez de executar cada `.py` manualmente.
