from enum import Enum

class ExpenseCategory(str, Enum):
    ALUGUEL = "aluguel"                      # aluguel do consultório/sala
    CONTAS_FIXAS = "contas_fixas"            # água, luz, internet, telefone
    MATERIAL_ODONTOLOGICO = "material_odontologico"  # luvas, resina, anestésico, etc.
    EQUIPAMENTO = "equipamento"              # compra/manutenção de equipamento (autoclave, cadeira, raio-x)
    LABORATORIO = "laboratorio"              # laboratório de prótese
    SALARIO = "salario"                      # folha de pagamento (dentistas, recepção, etc.)
    PRO_LABORE = "pro_labore"                # retirada dos sócios
    MARKETING = "marketing"                  # anúncios, redes sociais, panfletos
    SOFTWARE = "software"                    # sistemas, assinaturas, licenças
    CONTABILIDADE = "contabilidade"          # honorários contábeis
    IMPOSTOS = "impostos"                    # tributos, taxas, alvarás
    LIMPEZA = "limpeza"                      # material e serviço de limpeza
    MANUTENCAO = "manutencao"                # reparos gerais do espaço
    OUTROS = "outros"