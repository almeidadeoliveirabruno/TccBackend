# 📄 Documento de Migração: SQL Server ➔ Neon PostgreSQL

Este documento descreve detalhadamente todas as alterações de código realizadas durante a migração do banco de dados do **Microsoft SQL Server** para o **PostgreSQL (Neon Cloud)**, explicando a motivação técnica e as diferenças arquiteturais entre os dois SGBDs.

---

## 🎯 Sumário Executivo

Durante a migração para o PostgreSQL (Neon), algumas queries e operações de ORM (SQLAlchemy) falharam com erros como:
- `psycopg2.errors.InvalidTextRepresentation: invalid input value for enum appointment_status: "REALIZADO"`
- `psycopg2.errors.InvalidTextRepresentation: invalid input value for enum dentist_status: "ATIVO"`
- Falha na execução de funções `func.year()` e `func.month()`.

Esses erros aconteceram devido a diferenças fundamentais de comportamento entre SQL Server e PostgreSQL:

| Aspecto | SQL Server | PostgreSQL (Neon) |
| :--- | :--- | :--- |
| **Case-Sensitivity** | Case-Insensitive por padrão (`Latin1_General_CI_AS`) | Case-Sensitive por padrão |
| **Tipos ENUM** | Geralmente emulados via `VARCHAR` + `CHECK` | Tipos nativos fortemente tipados (`CREATE TYPE ... AS ENUM`) |
| **Extração de Data** | Funções proprietárias `YEAR(col)`, `MONTH(col)` | Padrão SQL ANSI `EXTRACT(field FROM col)` |
| **Serialização SQLAlchemy** | Converte Enum para string maiúscula sem erro no banco | Exige exata correspondência com os labels do enum no banco |

---

## 💡 Guia Prático: Quando usar `.value` e quando NÃO usar?

Uma das maiores fontes de confusão ao trabalhar com Enums no SQLAlchemy é saber onde colocar ou não o `.value`. A regra de ouro é:

> 👉 **"Quem vai ler esse dado agora? É o Python ou é o Banco de Dados?"**

### 1. Entendendo a anatomia de um Enum Python
```python
class AppointmentStatus(str, Enum):
    AGENDADO = "agendado"
    #   ▲         ▲
    # .name     .value
```
* **`AppointmentStatus.AGENDADO`** é um **Objeto Python** complexo.
* **`AppointmentStatus.AGENDADO.value`** é apenas uma **String simples**: `"agendado"`.

---

### 2. Comparativo de Cenários:

#### Cenário A: Na definição da Tabela (`models/appointment.py`)
```python
status = Column(
    SqlEnum(
        AppointmentStatus,
        name="appointment_status",
        values_callable=lambda x: [e.value for e in x],  # 👈 1. Força o SQLAlchemy a usar o .value em vez do .name
    ),
    nullable=False,
    default=AppointmentStatus.AGENDADO,                  # 👈 2. SEM .value (interpretado pelo Python na criação do objeto)
    server_default=AppointmentStatus.AGENDADO.value,     # 👈 3. COM .value (escrito direto no SQL: DEFAULT 'agendado')
)
```
* **`default` (Python):** Usado quando você instancia um modelo em memória (`Appointment()`). O Python prefere o objeto Enum tipado.
* **`server_default` (Banco de Dados):** O PostgreSQL não sabe o que é uma classe Python; ele só entende comandos SQL puros. Precisa da string `"agendado"`.

---

#### Cenário B: Em Queries e Filtros (`db.query().filter(...)`)
```python
# 1. Filtro com .in_() — OBRIGATÓRIO usar .value:
db.query(Appointment).filter(
    Appointment.status.in_([
        AppointmentStatus.AGENDADO.value,   # "agendado"
        AppointmentStatus.CONFIRMADO.value  # "confirmado"
    ])
)

# 2. Filtro de igualdade simples:
db.query(Appointment).filter(
    Appointment.status == AppointmentStatus.REALIZADO.value  # Garante envio da string exata
)
```
**Por que no `.in_()` o `.value` é obrigatório?**  
Dentro de listas `in_([...])`, o SQLAlchemy trata os elementos como parâmetros crus e não consegue inferir a conversão de cada item individualmente. Sem `.value`, ele enviava o nome do membro em maiúsculo (`'CONFIRMADO'`), quebrando no PostgreSQL.

---

#### Cenário C: Colunas `VARCHAR` vs Colunas `SqlEnum`

No seu projeto existem dois tipos de colunas de status:

| Model | Tipo no Banco | Exemplo de Atribuição no Service |
| :--- | :--- | :--- |
| **`Appointment.status`** | **`SqlEnum` nativo** | `appointment.status = AppointmentStatus.CONFIRMADO` (O SQLAlchemy converte internamente) |
| **`Receivable.status`** | **`VARCHAR(10)`** | `receivable.status = ReceivableStatus.PAGO.value` (**Obrigatório** `.value`, pois a coluna espera texto) |

Como a tabela `receivables` foi modelada como `String(10)` com uma `CheckConstraint`, o banco espera uma string pura (`"pago"`), não aceitando o objeto Enum diretamente.

---

## 🛠️ Mudanças Realizadas por Arquivo

### 1. `models/dentist.py` & `models/appointment.py`

#### ❌ O que causava o problema:
No SQLAlchemy, ao declarar uma coluna de enum nativo com `SqlEnum(DentistStatus, name="dentist_status")` sem o parâmetro `values_callable`, o SQLAlchemy utiliza por padrão os **nomes dos membros Python** (`ATIVO`, `INATIVO`, `FERIAS`, `AFASTADO`) para criar o tipo no PostgreSQL e para serializar valores nas queries.

No banco PostgreSQL, o tipo enum foi criado com os valores em formato PascalCase/CamelCase (`'Ativo'`, `'Inativo'`, `'Ferias'`, `'Afastado'`) ou minúsculo (`'agendado'`, `'realizado'`). Quando o SQLAlchemy enviava `'ATIVO'`, o Postgres rejeitava com `InvalidTextRepresentation`.

#### ✅ Alteração aplicada:
Adicionou-se `values_callable=lambda x: [e.value for e in x]` nas definições das colunas:

```python
# models/dentist.py
status = Column(
    SqlEnum(
        DentistStatus,
        name="dentist_status",
        values_callable=lambda x: [e.value for e in x],  # Garante uso do valor (.value)
    ),
    nullable=False,
    default=DentistStatus.ATIVO,
    server_default=DentistStatus.ATIVO.value,
)
```

```python
# models/appointment.py
status = Column(
    SqlEnum(
        AppointmentStatus,
        name="appointment_status",
        values_callable=lambda x: [e.value for e in x],
    ),
    nullable=False,
    default=AppointmentStatus.AGENDADO,
    server_default=AppointmentStatus.AGENDADO.value,
)
```

**Por que:** O `values_callable` instrui o SQLAlchemy a mapear os membros do Enum Python sempre através do seu valor real (`.value`), garantindo sincronia total com o tipo registrado no PostgreSQL.

---

### 2. `enums/DentistStatus.py`

#### ❌ O que causava o problema:
No arquivo Python, o status de férias estava com acento: `FERIAS = "Férias"`. No entanto, no tipo enum do PostgreSQL ele foi criado como `'Ferias'` (sem acento).

#### ✅ Alteração aplicada:
```python
# enums/DentistStatus.py
class DentistStatus(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    FERIAS = "Ferias"      # Ajustado para corresponder ao label no PostgreSQL
    AFASTADO = "Afastado"
```

**Por que:** O PostgreSQL valida rigorosamente qualquer string comparada com um tipo ENUM. Havendo divergência de acentuação, o banco não permite a inserção/comparação.

---

### 3. `services/dashboard_service.py`

#### ❌ O que causava o problema:
1. O código utilizava `func.year(Appointment.appointment_date)` e `func.month(Appointment.appointment_date)`. O SQL Server possui funções internas `YEAR()` e `MONTH()`, mas o PostgreSQL não as possui nativamente na mesma sintaxe, exigindo a função `EXTRACT()`.
2. Em filtros ORM de agregação, algumas comparações usavam enums com divergência de maiúsculas/minúsculas.

#### ✅ Alteração aplicada:
1. Importou-se a função `extract` do SQLAlchemy:
```python
from sqlalchemy import func, and_, case, cast, Date, extract
```

2. Substituiu-se a chamada de agrupamento por ano/mês:
```python
# Antes (SQL Server):
group_cols = [
    func.year(Appointment.appointment_date).label("year"),
    func.month(Appointment.appointment_date).label("month"),
]
key_fn = lambda row: (row.year, row.month)

# Depois (PostgreSQL):
group_cols = [
    extract("year", Appointment.appointment_date).label("year"),
    extract("month", Appointment.appointment_date).label("month"),
]
key_fn = lambda row: (int(row.year), int(row.month))
```

**Por que:** A função `extract()` gera o SQL padrão ANSI (`EXTRACT(YEAR FROM appointment_date)`), suportado por todos os dialetos PostgreSQL, e converte o retorno numérico para `int` em Python para alimentar o dicionário de períodos.

---

### 4. `services/home_service.py`

#### ❌ O que causava o problema:
Na query de busca dos próximos agendamentos (`get_next_appointments_by_dentist`), a cláusula `in_()` continha:

```python
# Antes:
Appointment.status.in_([
    AppointmentStatus.AGENDADO.value,
    AppointmentStatus.CONFIRMADO        # Sem o .value!
])
```

Ao passar `AppointmentStatus.CONFIRMADO` diretamente dentro de uma lista misturada, o driver/SQLAlchemy serializava para a string `"CONFIRMADO"` em maiúsculo, disparando erro de enum inválido.

#### ✅ Alteração aplicada:
```python
# Depois:
Appointment.status.in_([
    AppointmentStatus.AGENDADO.value,
    AppointmentStatus.CONFIRMADO.value
])
```

**Por que:** Mantém uniformidade e garante que apenas os valores reais (`"agendado"`, `"confirmado"`) sejam enviados nos parâmetros da query SQL.

---

### 5. `services/patient_service.py` e `services/receivable_service.py`

#### ❌ O que causava o problema:
Nas rotinas de cálculo de estatísticas (`get_statistics_patients`) e listagem de contas (`get_receivables`), filtros aplicados a colunas SQLAlchemy com enums precisavam garantir o envio dos valores correspondentes esperados pelo banco.

#### ✅ Alteração aplicada:
- Padronização no uso de `.value` ao montar cláusulas de filtro ORM.
- Validação e compatibilidade em queries `distinct().count()`.

---

## 📋 Resumo das Regras para o PostgreSQL no Projeto

Para evitar novos erros ao criar novos endpoints ou models:

1. **Ao criar colunas Enum no SQLAlchemy:**
   Sempre use `values_callable=lambda x: [e.value for e in x]`:
   ```python
   status = Column(
       SqlEnum(MeuEnum, name="meu_enum_name", values_callable=lambda x: [e.value for e in x]),
       nullable=False
   )
   ```

2. **Ao filtrar colunas Enum em queries ORM:**
   Passe sempre o `.value` do enum:
   ```python
   query = query.filter(Model.status == MeuEnum.VALOR.value)
   ```

3. **Para manipulação de datas:**
   Prefira `extract("year", Coluna)` e `extract("month", Coluna)` em vez de funções de dialeto específico como `func.year()`.

4. **Strings e Enums são Case-Sensitive:**
   Valores como `"ativo"`, `"Ativo"` e `"ATIVO"` são considerados completamente diferentes pelo PostgreSQL. O código Python e os labels da tabela no banco devem sempre coincidir rigorosamente.
