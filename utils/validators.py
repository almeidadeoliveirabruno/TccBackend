# Este arquivo foi gerado com apoio do Claude (Anthropic).

import re


def validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF verificando seus 2 dígitos verificadores.

    Um CPF tem 11 dígitos: os 9 primeiros são a "base" e os 2 últimos
    são calculados matematicamente a partir dela (checksum). Isso serve
    para detectar erros de digitação e CPFs inventados aleatoriamente.
    """
    cpf = re.sub(r"\D", "", cpf)  # remove pontos, traço etc., deixa só números

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:  # rejeita sequências tipo 111.111.111-11
        return False

    def calcular_digito(cpf_parcial: str, peso_inicial: int) -> int:
        """
        Calcula um dígito verificador.

        Multiplica cada dígito de `cpf_parcial` por um peso decrescente
        (começando em `peso_inicial`), soma tudo, tira o resto da divisão
        por 11 e aplica a regra oficial da Receita Federal:
          - resto < 2  -> dígito = 0
          - resto >= 2 -> dígito = 11 - resto
        """
        soma = sum(
            int(digito) * peso
            for digito, peso in zip(cpf_parcial, range(peso_inicial, 1, -1))
        )
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # 1º dígito verificador: usa os 9 primeiros dígitos, pesos de 10 a 2
    digito1 = calcular_digito(cpf[:9], 10)

    # 2º dígito verificador: usa os 9 primeiros + o 1º dígito já calculado
    # (10 dígitos ao todo), pesos de 11 a 2
    digito2 = calcular_digito(cpf[:10], 11)

    # Compara os dígitos calculados com os 2 últimos dígitos do CPF informado
    return cpf[-2:] == f"{digito1}{digito2}"


def validar_telefone(telefone: str) -> bool:
    """Valida telefone brasileiro: 10 dígitos (fixo) ou 11 dígitos (celular com 9)."""
    telefone = re.sub(r"\D", "", telefone)
    return len(telefone) in (10, 11)