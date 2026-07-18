"""
2_transformar.py
-----------------
Fase 2: Transformação e camada Silver (2_transformar.py): copiar Raw para Silver 
convertendo os tipos (texto para DECIMAL e DATE), respeitando a integridade referencial e 
calculando as colunas valor_total e duracao_dias.
"""

from datetime import datetime
import pandas as pd
import banco
from config import TAMANHO_BLOCO


# =============================================================================
# Funções de limpeza/conversão de tipos
# =============================================================================

def limpar_valor(texto):
    
    # Converte valores para float e retorna None se o texto estiver vazio ou não for um número válido.
    
    if texto is None:
        return None

    texto = texto.strip()  # remove espaços em branco no inicio/fim

    if texto == "": # campos vázios são convertidos em None
        return None

    # Remove o ponto de milhar (se houver) e troca a vírgula decimal por ponto
    texto_limpo = texto.replace(".", "").replace(",", ".")

    try:
        return float(texto_limpo)
    except ValueError:
        return None


def limpar_data(texto):
    
    # Converte uma data no formato DD/MM/AAAA (texto) para um objeto date do Python.
    # Retorna None se o texto estiver vazio ou nao for uma data valida.
    
    if texto is None:
        return None

    texto = texto.strip()

    if texto == "":
        return None

    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def limpar_texto(texto):

    # Remove espaços sobrando e converte valores "Sem informacao" ou string vazia para None.
    
    if texto is None:
        return None

    texto = texto.strip()

    if texto == "" or texto.lower() == "sem informação":
        return None

    return texto


def limpar_inteiro(texto):

    # Converte um texto numérico inteiro para int
    
    valor = limpar_valor(texto)

    if valor is None:
        return None

    return int(valor)


# =============================================================================
# Funções de cálculo de colunas derivadas (usadas so em silver_viagem)
# =============================================================================

def calcular_valor_total(valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos):

    # Soma os quatro valores da viagem para obter o valor total gasto. Valores ausentes (None) sao tratados como 0.
    
    if valor_diarias is None:
        valor_diarias = 0

    if valor_passagens is None:
        valor_passagens = 0

    if valor_devolucao is None:
        valor_devolucao = 0

    if valor_outros_gastos is None:
        valor_outros_gastos = 0

    valor_total = valor_diarias + valor_passagens + valor_devolucao + valor_outros_gastos

    return valor_total


def calcular_duracao_dias(data_inicio, data_fim):
    
    # Calcula a duração da viagem em dias, a partir das datas de início e fim ja convertidas. 
    # Retorna None se qualquer uma das duas datas estiver ausente.
    
    if data_inicio is None or data_fim is None:
        return None

    return (data_fim - data_inicio).days


# =============================================================================
# Carregamento da tabela silver_viagem
# =============================================================================

# Mapeia cada coluna da RAW para a função de limpeza que deve ser aplicada.
LIMPEZA_VIAGEM = {
    "id_processo_viagem": limpar_texto,
    "num_proposta": limpar_texto,
    "situacao": limpar_texto,
    "viagem_urgente": limpar_texto,
    "cod_orgao_superior": limpar_texto,
    "nome_orgao_superior": limpar_texto,
    "nome_viajante": limpar_texto,
    "cargo": limpar_texto,
    "data_inicio": limpar_data,
    "data_fim": limpar_data,
    "destinos": limpar_texto,
    "motivo": limpar_texto,
    "valor_diarias": limpar_valor,
    "valor_passagens": limpar_valor,
    "valor_devolucao": limpar_valor,
    "valor_outros_gastos": limpar_valor,
}
COLUNAS_RAW_VIAGEM = list(LIMPEZA_VIAGEM.keys())


def carregar_silver_viagem(conexao):

    # Lê os dados de raw_viagem, aplica as conversoes de tipo e os calculos necessarios, e insere o resultado em silver_viagem. 
    # A tabela silver_viagem será a primeria a ser carregada, já que as outras possuem id_viagem como FOREIGN KEY.

    query = f"SELECT {', '.join(COLUNAS_RAW_VIAGEM)} FROM raw_viagem"

    sql_insert = """
        INSERT INTO silver_viagem (
            id_viagem, num_proposta, situacao, viagem_urgente,
            cod_orgao_superior, nome_orgao_superior, nome_viajante, cargo,
            data_inicio, data_fim, destinos, motivo,
            valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos,
            valor_total, duracao_dias
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    total_linhas = 0
    for bloco in pd.read_sql(query, conexao, chunksize=TAMANHO_BLOCO):
        linhas = []
        for _, linha in bloco.iterrows():
            # Aplica a funcao de limpeza correspondente a cada coluna
            dados = {col: func(linha[col]) for col, func in LIMPEZA_VIAGEM.items()}

            # nome_orgao_superior e NOT NULL na Silver, mas alguns registros
            # da tabela raw vem sem esse dado preenchido. Em vez de descartar a 
            # linha inteira é preenchido o valor "Não informado" na coluna.
            if dados["nome_orgao_superior"] is None:
                dados["nome_orgao_superior"] = "Não informado"

            valor_total = calcular_valor_total(
                dados["valor_diarias"], dados["valor_passagens"],
                dados["valor_devolucao"], dados["valor_outros_gastos"],
            )
            duracao_dias = calcular_duracao_dias(dados["data_inicio"], dados["data_fim"])

            linhas.append((*dados.values(), valor_total, duracao_dias))

        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_linhas += len(linhas)

    print(f"  -> silver_viagem: {total_linhas} linhas carregadas.")


# =============================================================================
# Carregamento da tabela silver_passagem
# =============================================================================

# Mapeia cada coluna da RAW para a função de limpeza que deve ser aplicada.
LIMPEZA_PASSAGEM = {
    "id_processo_viagem": limpar_texto,
    "meio_transporte": limpar_texto,
    "pais_origem_ida": limpar_texto,
    "uf_origem_ida": limpar_texto,
    "cidade_origem_ida": limpar_texto,
    "pais_destino_ida": limpar_texto,
    "uf_destino_ida": limpar_texto,
    "cidade_destino_ida": limpar_texto,
    "valor_passagem": limpar_valor,
    "taxa_servico": limpar_valor,
    "data_emissao": limpar_data,
}
COLUNAS_RAW_PASSAGEM = list(LIMPEZA_PASSAGEM.keys())


def carregar_silver_passagem(conexao):
    
    # Lê os dados de raw_passagem, aplica as conversões de tipo e insere o resultado em silver_passagem.
    
    query = f"SELECT {', '.join(COLUNAS_RAW_PASSAGEM)} FROM raw_passagem"

    sql_insert = """
        INSERT INTO silver_passagem (
            id_viagem, meio_transporte, pais_origem_ida, uf_origem_ida,
            cidade_origem_ida, pais_destino_ida, uf_destino_ida, cidade_destino_ida,
            valor_passagem, taxa_servico, data_emissao
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    total_linhas = 0
    for bloco in pd.read_sql(query, conexao, chunksize=TAMANHO_BLOCO):
        linhas = []
        for _, linha in bloco.iterrows():
            dados = {col: func(linha[col]) for col, func in LIMPEZA_PASSAGEM.items()}
            linhas.append(tuple(dados.values()))

        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_linhas += len(linhas)

    print(f"  -> silver_passagem: {total_linhas} linhas carregadas.")


# =============================================================================
# Carga da tabela silver_pagamento
# =============================================================================

LIMPEZA_PAGAMENTO = {
    "id_processo_viagem": limpar_texto,
    "num_proposta": limpar_texto,
    "nome_orgao_pagador": limpar_texto,
    "nome_ug_pagadora": limpar_texto,
    "tipo_pagamento": limpar_texto,
    "valor": limpar_valor,
}
COLUNAS_RAW_PAGAMENTO = list(LIMPEZA_PAGAMENTO.keys())


def carregar_silver_pagamento(conexao):
    
    # Lê os dados de raw_pagamento, aplica as conversoes de tipo e insere o resultado em silver_pagamento.
    
    query = f"SELECT {', '.join(COLUNAS_RAW_PAGAMENTO)} FROM raw_pagamento"

    sql_insert = """
        INSERT INTO silver_pagamento (
            id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
            tipo_pagamento, valor
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        )
    """

    total_linhas = 0
    for bloco in pd.read_sql(query, conexao, chunksize=TAMANHO_BLOCO):
        linhas = []
        for _, linha in bloco.iterrows():
            dados = {col: func(linha[col]) for col, func in LIMPEZA_PAGAMENTO.items()}
            linhas.append(tuple(dados.values()))

        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_linhas += len(linhas)

    print(f"  -> silver_pagamento: {total_linhas} linhas carregadas.")


# =============================================================================
# Carga da tabela silver_trecho
# =============================================================================

LIMPEZA_TRECHO = {
    "id_processo_viagem": limpar_texto,
    "sequencia_trecho": limpar_inteiro,
    "origem_data": limpar_data,
    "origem_uf": limpar_texto,
    "origem_cidade": limpar_texto,
    "destino_data": limpar_data,
    "destino_uf": limpar_texto,
    "destino_cidade": limpar_texto,
    "meio_transporte": limpar_texto,
    "numero_diarias": limpar_valor,
}
COLUNAS_RAW_TRECHO = list(LIMPEZA_TRECHO.keys())


def carregar_silver_trecho(conexao):
    
    # Lê os dados de raw_trecho, aplica as conversoes de tipo e insere o resultado em silver_trecho. 
    
    query = f"SELECT {', '.join(COLUNAS_RAW_TRECHO)} FROM raw_trecho"

    sql_insert = """
        INSERT INTO silver_trecho (
            id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
            destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    total_linhas = 0
    for bloco in pd.read_sql(query, conexao, chunksize=TAMANHO_BLOCO):
        linhas = []
        for _, linha in bloco.iterrows():
            dados = {col: func(linha[col]) for col, func in LIMPEZA_TRECHO.items()}
            linhas.append(tuple(dados.values()))

        banco.inserir_em_lote(conexao, sql_insert, linhas)
        total_linhas += len(linhas)

    print(f"  -> silver_trecho: {total_linhas} linhas carregadas.")


# =============================================================================
# Truncate das tabelas
# =============================================================================

def truncar_tabelas(conexao, tabelas):
    
    # Função para esvaziar as tabelas antes de serem carregadas. Diferente dos 
    # carregamentos, no Truncate a tabela silver_viagem será a última tabela a ser 
    # limpa por conta da FOREIGN KEY id_viagem presente nas demais tabelas.
    
    lista_tabelas = ", ".join(tabelas)
    banco.executar(conexao, f"TRUNCATE TABLE {lista_tabelas}")


# =============================================================================
# Chamada das funções
# =============================================================================

def main():
    
    # Orquestra o fluxo completo da Fase 2: limpa as tabelas Silver e carrega os dados transformados.
    
    print("Fase 2 - Transformação e camada SILVER")

    print("1. Conectando ao banco...")
    conexao = banco.conectar()

    try:
        print("2. Limpando as tabelas SILVER...")
        truncar_tabelas(
            conexao,
            ["silver_trecho", "silver_pagamento", "silver_passagem", "silver_viagem"],
        )

        # Carga na ordem normal da FK: viagem primeiro, depois as demais tabelas que dependem de id_viagem como FOREIGN KEY.
        print("3. Carregando as tabelas SILVER...")
        carregar_silver_viagem(conexao)
        carregar_silver_passagem(conexao)
        carregar_silver_pagamento(conexao)
        carregar_silver_trecho(conexao)
    finally:
        conexao.close()

    print("Transformação concluida com sucesso.")


if __name__ == "__main__":
    main()