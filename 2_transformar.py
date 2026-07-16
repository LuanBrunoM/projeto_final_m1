"""
2_transformar.py
-----------------
Fase 2 - Transformação e camada Silver (2_transformar.py): copiar Raw
para Silver convertendo os tipos (texto para DECIMAL e DATE), respeitando
a integridade referencial e calculando as colunas valor_total e duracao_dias.
"""

from datetime import datetime
import banco

# from config import PASTA_DADOS

# =============================================================================
# Funcoes de limpeza/conversao de tipos
# =============================================================================


def limpar_valor(texto):
    # Converte as colunas de valores para float e transforma valores vazios em nulos

    if texto is None:
        return None

    texto = texto.strip()  # remove espaços em branco no inicio/fim

    if texto == "":
        return None

    # Remove o ponto de milhar e troca a virgula decimal por ponto
    texto_limpo = texto.replace(".", "").replace(",", ".")

    try:
        return float(texto_limpo)
    except ValueError:
        return None


def limpar_data(texto):

    # Converte uma data no formato DD/MM/AAAA (texto) para um
    # objeto date do Python. Retorna None se o texto estiver vazio ou nao
    # for uma data valida.

    if texto is None:
        return None

    texto = texto.strip()

    if texto == "":
        return None

    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
        # converte o valor para datetime apenas com a data, sem a hora
    except ValueError:
        return None


# teste para limpar_valor()
casos_valor = [
    "1272,97",
    "",
    "1.240,09",
    None,
    "  50,00  ",
    "abc",
]

print("Teste limpa valor...")
for caso in casos_valor:
    resultado = limpar_valor(caso)
    print(f"entrada={caso!r:20} -> resultado={resultado!r}")


# teste para limpar_data
casos_data = [
    "17/09/2024",
    "",
    None,
    "  25/12/2025  ",
    "2024-09-17",
]

print()
print("Teste limpa data...")
for caso in casos_data:
    resultado = limpar_data(caso)
    print(f"entrada={caso!r:20} -> resultado={resultado!r}")
