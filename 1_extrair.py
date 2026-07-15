"""
=============================================================================
1_extrair.py
------------
Fase 1 do pipeline: Extração e camada RAW
=============================================================================
"""

import zipfile
import gdown
import pandas as pd
import banco
from config import (
    ARQUIVOS,
    CSV_ENCODING,
    CSV_SEPARADOR,
    DRIVE_FILE_ID,
    PASTA_DADOS,
    TAMANHO_BLOCO,
)

# A lista é usada para montar o INSERT (nomes das colunas e quantidade de marcadores %s)
# e para nomear as colunas na hora de criar a tabela RAW.
COLUNAS_CSV = {
    "viagem": [
        "id_processo_viagem",
        "num_proposta",
        "situacao",
        "viagem_urgente",
        "justificativa_urgencia",
        "cod_orgao_superior",
        "nome_orgao_superior",
        "cod_orgao_solicitante",
        "nome_orgao_solicitante",
        "cpf_viajante",
        "nome_viajante",
        "cargo",
        "funcao",
        "descricao_funcao",
        "data_inicio",
        "data_fim",
        "destinos",
        "motivo",
        "valor_diarias",
        "valor_passagens",
        "valor_devolucao",
        "valor_outros_gastos",
    ],
    "pagamento": [
        "id_processo_viagem",
        "num_proposta",
        "cod_orgao_superior",
        "nome_orgao_superior",
        "cod_orgao_pagador",
        "nome_orgao_pagador",
        "cod_ug_pagadora",
        "nome_ug_pagadora",
        "tipo_pagamento",
        "valor",
    ],
    "passagem": [
        "id_processo_viagem",
        "num_proposta",
        "meio_transporte",
        "pais_origem_ida",
        "uf_origem_ida",
        "cidade_origem_ida",
        "pais_destino_ida",
        "uf_destino_ida",
        "cidade_destino_ida",
        "pais_origem_volta",
        "uf_origem_volta",
        "cidade_origem_volta",
        "pais_destino_volta",
        "uf_destino_volta",
        "cidade_destino_volta",
        "valor_passagem",
        "taxa_servico",
        "data_emissao",
        "hora_emissao",
    ],
    "trecho": [
        "id_processo_viagem",
        "num_proposta",
        "sequencia_trecho",
        "origem_data",
        "origem_pais",
        "origem_uf",
        "origem_cidade",
        "destino_data",
        "destino_pais",
        "destino_uf",
        "destino_cidade",
        "meio_transporte",
        "numero_diarias",
        "missao",
    ],
}


def baixar_zip():
    # Baixa o .zip do Google Drive e salva dentro da pasta data/
    # como 'viagens.zip'. Caso a pasta não exista, ela será criada.

    # Garante que a pasta data/ existe antes de tentar salvar o zip nela.
    # exist_ok=True evita erro caso a pasta ja exista.
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    caminho_zip = PASTA_DADOS / "viagens.zip"

    # Usa a biblioteca gdown para baixar o arquivo zip do google drive, usando o DRIVE_FILE_ID do config.py.
    # Caso ocorra um erro no download, será impresso uma mensagem de erro, junto do erro original (Exception as erro)
    try:
        gdown.download(id=DRIVE_FILE_ID, output=str(caminho_zip), quiet=False)
    except Exception as erro:
        raise RuntimeError(
            f"Falha ao baixar o arquivo do Google Drive (ID={DRIVE_FILE_ID})."
            f"Detalhe: {erro}"
        )

    return caminho_zip


def descompactar_zip(caminho_zip):
    # Extrai os arquivos do .zip para dentro da pasta data/.
    try:
        with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
            zip_ref.extractall(PASTA_DADOS)
    except zipfile.BadZipFile as erro:
        # Verifica se o arquivo baixado é uma arquivo .zip. Caso não seja, será considerado como erro/arquivo corrompido
        raise RuntimeError(
            f"O arquivo baixado pode ter vindo corrompido." f"Detalhe: {erro}"
        )


def truncar_tabela(conexao, tabela):
    # Esvazia a tabela antes de carrega-la, dessa forma os dados não serão duplicados caso o código seja executado mais de uma vez.
    banco.executar(conexao, f"TRUNCATE TABLE {tabela}")


def carregar_csv_para_raw(conexao, chave_arquivo):
    # Le um dos 4 CSVs em blocos (chunks) e insere o conteudo, na tabela RAW correspondente.

    # Busca no dicionario ARQUIVOS (config.py) as informacoes desse arquivo
    # especifico: nome do csv e nome da tabela raw de destino. colunas e a
    # lista de nomes limpos, na mesma ordem das colunas originais do CSV.
    info = ARQUIVOS[chave_arquivo]
    caminho_csv = PASTA_DADOS / info["csv"]
    tabela = info["tabela_raw"]
    colunas = COLUNAS_CSV[chave_arquivo]

    if not caminho_csv.exists():
        raise RuntimeError(
            f"Arquivo {caminho_csv} nao encontrado apos a extracao do zip."
        )

    truncar_tabela(conexao, tabela)

    # Monta o texto do INSERT dinamicamente, baseado na quantidade de colunas dessa tabela
    marcadores = ", ".join(["%s"] * len(colunas))
    sql_insert = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({marcadores})"

    total_linhas = 0
    try:
        # Leitura da tabela e criação do DataFrame
        df_tabela = pd.read_csv(
            caminho_csv,
            sep=CSV_SEPARADOR,
            encoding=CSV_ENCODING,
            dtype=str,
            keep_default_na=False,
            chunksize=TAMANHO_BLOCO,
        )
        for bloco in df_tabela:
            linhas = [
                tuple(linha) for linha in bloco.to_numpy()
            ]  # Transforma as linhas em tuplas
            banco.inserir_em_lote(conexao, sql_insert, linhas)
            total_linhas += len(linhas)
    except Exception as erro:
        raise RuntimeError(
            f"Falha ao carregar '{info['csv']}' na tabela '{tabela}'. Detalhe: {erro}"
        )

    print(f"  -> {tabela}: {total_linhas} linhas carregadas.")


def main():
    print("Fase 1 - Extracao e camada RAW")

    print("1. Baixando o .zip do Google Drive...")
    caminho_zip = baixar_zip()

    print("2. Descompactando...")
    descompactar_zip(caminho_zip)

    print("3. Conectando ao banco...")
    conexao = banco.conectar()

    try:
        print("4. Carregando os CSVs nas tabelas RAW...")
        for chave in ARQUIVOS:
            carregar_csv_para_raw(conexao, chave)
    finally:
        conexao.close()

    print("Extracao concluida com sucesso.")


if __name__ == "__main__":
    main()
