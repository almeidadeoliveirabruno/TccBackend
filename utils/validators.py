# Este arquivo foi gerado com apoio do Claude (Anthropic).

import re

def _validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF verificando seus dois dígitos verificadores.
    """

    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    # Calcula o primeiro dígito verificador
    soma = 0

    for i in range(9):
        soma += int(cpf[i]) * (10 - i)

    resto = soma % 11

    if resto < 2:
        digito1 = 0
    else:
        digito1 = 11 - resto

    # Calcula o segundo dígito verificador
    soma = 0

    for i in range(10):
        soma += int(cpf[i]) * (11 - i)

    resto = soma % 11

    if resto < 2:
        digito2 = 0
    else:
        digito2 = 11 - resto

    return cpf[-2:] == f"{digito1}{digito2}"



def _validar_telefone(telefone: str) -> bool:
    """Valida telefone brasileiro: 10 dígitos (fixo) ou 11 dígitos (celular com 9)."""
    telefone = re.sub(r"\D", "", telefone)
    return len(telefone) in (10, 11)

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validar_email(email: str) -> bool:
    """Validação simples de formato de e-mail (mesma regra usada no front)."""
    '''exige um bloco de texto, um @, outro bloco de texto, um ponto, e mais um bloco de texto'''
    return bool(_EMAIL_REGEX.match(email or ""))