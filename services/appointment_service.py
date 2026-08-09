"""
Lógica central de agendamento.

Responsabilidades:
- Validar regras de negócio.
- Garantir isolamento por clínica.
- Calcular duração automaticamente.
- Validar conflitos.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from models.appointment import Appointment, AppointmentStatus
from models.associations.appointment_procedure import AppointmentProcedure
from models.associations.dentist_schedules import DentistSchedule
from models.dentist import Dentist, DentistStatus
from models.patient import Patient
from models.procedure import Procedure
from models.schedule import Schedule
import math
from schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    TableDataLine,
    TableDetail,
    TableDetailProcedure,
    AppointmentProcedureOut
)
from typing import Optional


# ==========================================================
# HELPERS
# ==========================================================


def _build_display(name: str, tooth: Optional[str]) -> str:
    return f"{name} • Dente {tooth}" if tooth else name

def _get_dentist_or_404(
    db: Session,
    dentist_id: int,
    clinic_id: str,
) -> Dentist:
    """
    Busca um dentista da clínica.

    Também garante que ele esteja ativo.
    """

    dentist = (
        db.query(Dentist)
        .filter(
            Dentist.id == dentist_id,
            Dentist.clinic_id == clinic_id,
        )
        .first()
    )

    if dentist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dentista não encontrado",
        )

    if dentist.status != DentistStatus.ATIVO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dentista não está disponível",
        )

    return dentist


def _get_patient_or_404(
    db: Session,
    patient_id: int,
    clinic_id: str,
) -> Patient:
    """
    Busca um paciente da clínica.
    """

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
        )
        .first()
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente não encontrado",
        )

    return patient


def _get_procedures_or_404(
    db: Session,
    procedures_data,
    clinic_id: str,
) -> list[Procedure]:
    """
    Busca os procedimentos enviados no body.

    Retorna somente os objetos Procedure.
    """

    procedure_ids = [
        item.procedure_id
        for item in procedures_data
    ]

    procedures = (
        db.query(Procedure)
        .filter(
            Procedure.id.in_(procedure_ids),
            Procedure.clinic_id == clinic_id,
        )
        .all()
    )

    found_ids = {
        procedure.id
        for procedure in procedures
    }

    '''missing_ids verifica se algum dos IDs enviados não foi encontrado no banco.'''
    missing_ids = set(procedure_ids) - found_ids

    '''if missing_ids entra no if se algum dos IDs enviados não foi encontrado no banco.'''
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedimentos não encontrados: {sorted(missing_ids)}",
        )

    for procedure in procedures:

        if not procedure.status:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Procedimento '{procedure.name}' está inativo",
            )

        if procedure.duration is None or procedure.duration <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Procedimento '{procedure.name}' não possui duração cadastrada",
            )

    return procedures


def _total_duration(
    procedures: list[Procedure],
) -> int:
    """
    Soma a duração de todos os procedimentos.
    """

    return sum(
        procedure.duration
        for procedure in procedures
    )


def _procedures_price_map(
    procedures: list[Procedure],
) -> dict[int, Decimal]:
    """
    Mapa procedure_id -> preço (Decimal).

    Usado para travar o valor do procedimento no
    momento do agendamento (unit_price), já que
    Procedure.price pode mudar depois. Procedure.price
    já é Numeric/Decimal no banco, então não precisa
    de conversão via str().
    """

    return {
        procedure.id: procedure.price
        for procedure in procedures
    }


def _compute_time_end(
    time_begin: time,
    duration_minutes: int,
) -> time:
    """
    Calcula automaticamente o horário final.

    Também impede consultas que terminem
    depois da meia-noite.
    """

    base = datetime.combine(
        date.today(),
        time_begin,
    )

    end = base + timedelta(
        minutes=duration_minutes
    )

    if end.date() != base.date():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consulta ultrapassa o limite do dia",
        )

    return end.time()


def _validate_working_hours(
    db: Session,
    dentist_id: int,
    appointment_date: date,
    time_begin: time,
    time_end: time,
) -> None:
    """
    Verifica se o horário solicitado está
    dentro do expediente do dentista.
    """

    # Python:
    # segunda = 0
    #
    # Banco:
    # domingo = 0

    day_of_week = (
        appointment_date.weekday() + 1
    ) % 7

    schedules = (
        db.query(Schedule)
        .join(
            DentistSchedule,
            DentistSchedule.schedule_id == Schedule.id,
        )
        .filter(
            DentistSchedule.dentist_id == dentist_id,
            DentistSchedule.day_of_week == day_of_week,
        )
        .all()
    )

    if not schedules:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dentista não atende nesse dia",
        )

    valid = any(
        schedule.time_begin <= time_begin
        and schedule.time_end >= time_end
        for schedule in schedules
    )

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Horário fora do expediente",
        )


def _validate_no_conflict(
    db: Session,
    dentist_id: int,
    patient_id: int,
    appointment_date: date,
    time_begin: time,
    time_end: time,
    exclude_id: int | None = None,
) -> None:
    """
    Impede conflito de horários.

    Verifica conflitos tanto para
    o dentista quanto para o paciente.
    """

    active_statuses = [
        AppointmentStatus.AGENDADO,
        AppointmentStatus.CONFIRMADO,
    ]

    query = (
        db.query(Appointment)
        .filter(
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(active_statuses),

            Appointment.time_begin < time_end,
            Appointment.time_end > time_begin,

            or_(
                Appointment.dentist_id == dentist_id,
                Appointment.patient_id == patient_id,
            ),
        )
    )

    if exclude_id is not None:
        query = query.filter(
            Appointment.id != exclude_id
        )

    conflict = query.first()

    if conflict is None:
        return

    if conflict.dentist_id == dentist_id:
        detail = "Dentista já possui consulta nesse horário"
    else:
        detail = "Paciente já possui consulta nesse horário"

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )

# ==========================================================
# CREATE
# ==========================================================


def create_appointment(
    db: Session,
    appointment_create: AppointmentCreate,
    clinic_id: str,
) -> Appointment:
    """
    Cria um novo agendamento.

    Fluxo:
    1. Valida dentista.
    2. Valida paciente.
    3. Valida procedimentos.
    4. Calcula (ou usa) o horário final.
    5. Valida expediente.
    6. Valida conflitos.
    7. Cria Appointment.
    8. Cria AppointmentProcedure (travando unit_price).
    """

    _get_dentist_or_404(
        db,
        appointment_create.dentist_id,
        clinic_id,
    )

    _get_patient_or_404(
        db,
        appointment_create.patient_id,
        clinic_id,
    )

    procedures = _get_procedures_or_404(
        db,
        appointment_create.procedures,
        clinic_id,
    )

    # Permite que o horário final seja informado
    # manualmente. Caso contrário calcula pela
    # duração dos procedimentos.
    if appointment_create.time_end:

        if appointment_create.time_end <= appointment_create.time_begin:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Horário final deve ser maior que o horário inicial",
            )

        time_end = appointment_create.time_end

    else:

        time_end = _compute_time_end(
            appointment_create.time_begin,
            _total_duration(procedures),
        )

    _validate_working_hours(
        db,
        appointment_create.dentist_id,
        appointment_create.appointment_date,
        appointment_create.time_begin,
        time_end,
    )

    _validate_no_conflict(
        db,
        appointment_create.dentist_id,
        appointment_create.patient_id,
        appointment_create.appointment_date,
        appointment_create.time_begin,
        time_end,
    )

    appointment = Appointment(
        clinic_id=clinic_id,
        dentist_id=appointment_create.dentist_id,
        patient_id=appointment_create.patient_id,
        appointment_date=appointment_create.appointment_date,
        time_begin=appointment_create.time_begin,
        time_end=time_end,
        status=AppointmentStatus.AGENDADO,
        confirmation_message_sent=False,
        notes=appointment_create.notes,
    )

    db.add(appointment)

    # Gera o ID antes de criar as associações.
    db.flush()

    # Mapa procedure_id -> preço, para travar o
    # valor no momento do agendamento.
    price_map = _procedures_price_map(procedures)

    # Cria os vínculos com os procedimentos.
    for item in appointment_create.procedures:

        appointment.procedure_items.append(
            AppointmentProcedure(
                procedure_id=item.procedure_id,
                tooth=item.tooth,
                unit_price=price_map[item.procedure_id],
            )
        )

    db.flush()
    db.refresh(appointment)

#todo: criar a conta a receber aqui, com status "pendente" e total_amount = soma dos unit_price. Se o pagamento for parcelado, criar os installments também.
    return appointment


# ==========================================================
# HORÁRIOS DISPONÍVEIS
# ==========================================================


def get_available_times(
    db: Session,
    dentist_id: int,
    appointment_date: date,
    duration_minutes: int,
    clinic_id: str,
) -> list[str]:
    """
    Retorna os horários livres de um dentista.

    O frontend usa esta função para preencher
    automaticamente o select de horários.
    """

    _get_dentist_or_404(
        db,
        dentist_id,
        clinic_id,
    )

    day_of_week = (
        appointment_date.weekday() + 1
    ) % 7

    schedules = (
        db.query(Schedule)
        .join(
            DentistSchedule,
            DentistSchedule.schedule_id == Schedule.id,
        )
        .filter(
            DentistSchedule.dentist_id == dentist_id,
            DentistSchedule.day_of_week == day_of_week,
        )
        .all()
    )

    if not schedules:
        return []

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.dentist_id == dentist_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(
                [
                    AppointmentStatus.AGENDADO,
                    AppointmentStatus.CONFIRMADO,
                ]
            ),
        )
        .all()
    )

    available = []

    for schedule in schedules:

        current = datetime.combine(
            appointment_date,
            schedule.time_begin,
        )

        limit = datetime.combine(
            appointment_date,
            schedule.time_end,
        )

        while current + timedelta(minutes=duration_minutes) <= limit:

            candidate_begin = current.time()

            candidate_end = (
                current
                + timedelta(minutes=duration_minutes)
            ).time()

            conflict = any(
                appointment.time_begin < candidate_end
                and appointment.time_end > candidate_begin
                for appointment in appointments
            )

            if not conflict:
                available.append(
                    candidate_begin.strftime("%H:%M")
                )

            # Intervalo padrão entre horários.
            current += timedelta(minutes=15)

    return available

# ==========================================================
# GET
# ==========================================================

def get_appointment_by_id(
    db: Session,
    appointment_id: int,
    clinic_id: str,
) -> Appointment:
    """
    Retorna um agendamento da clínica.
    """

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.clinic_id == clinic_id,
        )
        .first()
    )

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )

    return appointment


def get_appointments_by_clinic_id(
    db: Session,
    clinic_id: str,
    dentist_id: int | None = None,
    patient_id: int | None = None,
    appointment_date: date | None = None,
    appointment_status: AppointmentStatus | None = None,
) -> list[Appointment]:
    """
    Lista os agendamentos da clínica.
    """

    query = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic_id)
    )

    if dentist_id is not None:
        query = query.filter(
            Appointment.dentist_id == dentist_id
        )

    if patient_id is not None:
        query = query.filter(
            Appointment.patient_id == patient_id
        )

    if appointment_date is not None:
        query = query.filter(
            Appointment.appointment_date == appointment_date
        )

    if appointment_status is not None:
        query = query.filter(
            Appointment.status == appointment_status
        )

    return (
        query.order_by(
            Appointment.appointment_date,
            Appointment.time_begin,
        )
        .all()
    )


# ==========================================================
# UPDATE
# ==========================================================

def update_appointment(
    db: Session,
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    clinic_id: str,
) -> Appointment:
    """
    Reagenda uma consulta.
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    new_date = (
        appointment_update.appointment_date
        or appointment.appointment_date
    )

    new_begin = (
        appointment_update.time_begin
        or appointment.time_begin
    )

    if appointment_update.procedures is not None:

        procedures = _get_procedures_or_404(
            db,
            appointment_update.procedures,
            clinic_id,
        )

    else:

        procedures = [
            item.procedure
            for item in appointment.procedure_items
        ]

    if appointment_update.time_end:

        if appointment_update.time_end <= new_begin:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Horário final deve ser maior que o inicial",
            )

        new_end = appointment_update.time_end

    else:

        new_end = _compute_time_end(
            new_begin,
            _total_duration(procedures),
        )

    _validate_working_hours(
        db,
        appointment.dentist_id,
        new_date,
        new_begin,
        new_end,
    )

    _validate_no_conflict(
        db,
        appointment.dentist_id,
        appointment.patient_id,
        new_date,
        new_begin,
        new_end,
        exclude_id=appointment.id,
    )

    appointment.appointment_date = new_date
    appointment.time_begin = new_begin
    appointment.time_end = new_end

    if appointment_update.notes is not None:
        appointment.notes = appointment_update.notes

    if appointment_update.procedures is not None:

        appointment.procedure_items.clear()

        # Recalcula os preços apenas quando os
        # procedimentos foram de fato alterados.
        price_map = _procedures_price_map(procedures)

        for item in appointment_update.procedures:

            appointment.procedure_items.append(
                AppointmentProcedure(
                    procedure_id=item.procedure_id,
                    tooth=item.tooth,
                    unit_price=price_map[item.procedure_id],
                )
            )

    # Mudou a consulta, precisa reconfirmar.
    appointment.status = AppointmentStatus.AGENDADO
    appointment.confirmation_message_sent = False

    db.flush()
    db.refresh(appointment)

    return appointment


# ==========================================================
# CONFIRMAÇÕES
# ==========================================================

def confirm_appointment(
    db: Session,
    appointment_id: int,
    clinic_id: str,
) -> Appointment:
    """
    Confirma presença do paciente.
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    appointment.status = AppointmentStatus.CONFIRMADO

    db.flush()
    db.refresh(appointment)

    return appointment


def mark_confirmation_message_sent(
    db: Session,
    appointment_id: int,
    clinic_id: str,
) -> Appointment:
    """
    Marca que o WhatsApp foi enviado.
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    appointment.confirmation_message_sent = True

    db.flush()
    db.refresh(appointment)

    return appointment


def update_appointment_status(
    db: Session,
    appointment_id: int,
    new_status: AppointmentStatus,
    clinic_id: str,
) -> Appointment:
    """
    Atualiza o status da consulta.
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    appointment.status = new_status

    db.flush()
    db.refresh(appointment)

    return appointment


def update_appointment_notes(
    db: Session,
    appointment_id: int,
    notes: Optional[str],
    clinic_id: str,
) -> Appointment:
    """
    Atualiza só a observação da consulta. Endpoint exclusivo da tela
    de Atendimento (edição restrita: status / dente / observações).

    Não reaproveita update_appointment: aquela função reagenda a
    consulta inteira (data, horário, procedimentos) e força o status
    de volta para AGENDADO -- efeito colateral indesejado só pra
    salvar uma observação.
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    appointment.notes = notes

    db.flush()
    db.refresh(appointment)

    return appointment


# ==========================================================
# DELETE
# ==========================================================

def delete_appointment(
    db: Session,
    appointment_id: int,
    clinic_id: str,
) -> None:
    """
    Cancelamento lógico.
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    appointment.status = AppointmentStatus.CANCELADO

    db.flush()


# ==========================================================
# QUERYS / TABELA E ESTATÍSTICAS
# ==========================================================


def sum_procedures(
    procedure_items: list[AppointmentProcedure],
) -> Decimal:
    """
    Soma o unit_price de uma lista de AppointmentProcedure.

    unit_price já vem travado no momento do agendamento (ver
    create_appointment / update_appointment), então essa soma
    reflete o valor cobrado, não o preço atual de Procedure.
    """

    return sum(
        (item.unit_price for item in procedure_items),
        Decimal("0"),
    )


def _get_table_statistics(
    db: Session,
    clinic_id: str,
) -> dict[str, float | int]:
    """
    Estatísticas gerais da clínica.

    - total_appointments: total de agendamentos.
    - no_show_count: quantos foram marcados como falta.
    - unique_patients: pacientes distintos atendidos.
    - revenue: soma do unit_price dos agendamentos não
      cancelados.
    """

    base_filter = (
        Appointment.clinic_id == clinic_id,
    )

    total_de_agendamentos = (
        db.query(func.count(Appointment.id))
        .filter(*base_filter)
        .scalar()
    )

    faltas = (
        db.query(func.count(Appointment.id))
        .filter(
            *base_filter,
            Appointment.status == AppointmentStatus.FALTOU,
        )
        .scalar()
    )

    pacientes_unicos = (
        db.query(func.count(func.distinct(Appointment.patient_id)))
        .filter(*base_filter)
        .scalar()
    )

    receita = (
        db.query(
            func.coalesce(
                func.sum(AppointmentProcedure.unit_price), 0
            )
        )
        .join(
            Appointment,
            Appointment.id == AppointmentProcedure.appointment_id,
        )
        .filter(
            *base_filter,
            Appointment.status != AppointmentStatus.CANCELADO,
        )
        .scalar()
    )

    return {
        "total_de_agendamentos": total_de_agendamentos or 0,
        "quantidade_de_faltas": faltas or 0,
        "pacientes_atendidos": pacientes_unicos or 0,
        "receita": float(receita or 0),
    }

def get_appointments_by_clinic_id_for_table(
    db: Session,
    clinic_id: str,
    page: int = 1,
    page_size: int = 10,
    dentist: str | None = None,
    patient: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    status: AppointmentStatus | None = None,
):
    """
    Lista agendamentos no formato TableDataLine, paginado,
    junto com as estatísticas para os cards do topo.
    """

    skip = (page - 1) * page_size

    # Soma de unit_price por agendamento, calculada à parte
    # e ligada via outerjoin (agendamento sem procedimento
    # ainda aparece, com total_price = 0).
    price_subquery = (
        db.query(
            AppointmentProcedure.appointment_id.label("appointment_id"),
            func.sum(AppointmentProcedure.unit_price).label("total_price"),
        )
        .group_by(AppointmentProcedure.appointment_id)
        .subquery()
    )

    query = (
        db.query(
            Appointment.id,
            Patient.name.label("patient_name"),
            Dentist.name.label("dentist_name"),
            Appointment.appointment_date,
            Appointment.time_begin,
            Appointment.status,
            Appointment.confirmation_message_sent,
            func.coalesce(price_subquery.c.total_price, 0).label(
                "total_price"
            ),
        )
        .join(Appointment.patient)
        .join(Appointment.dentist)
        .outerjoin(
            price_subquery,
            price_subquery.c.appointment_id == Appointment.id,
        )
        .filter(Appointment.clinic_id == clinic_id)
    )

    if dentist:
        like = f"%{dentist}%"
        query = query.filter(Dentist.name.ilike(like))

    if patient:
        like = f"%{patient}%"
        query = query.filter(Patient.name.ilike(like))

    if start_date:
        query = query.filter(
            Appointment.appointment_date >= start_date
        )

    if end_date:
        query = query.filter(
            Appointment.appointment_date <= end_date
        )

    if status:
        query = query.filter(Appointment.status == status)

    # order_by(None) evita carregar o ORDER BY dentro do
    # SELECT COUNT(*) gerado pelo .count().
    total = query.order_by(None).count()

    rows = (
        query.order_by(
            Appointment.appointment_date,
            Appointment.time_begin,
        )
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Nomes dos procedimentos de cada agendamento da página atual,
    # buscados numa query só (evita N+1 -- uma query por linha).
    row_ids = [row.id for row in rows]

    procedures_map: dict[int, list[str]] = {}
    if row_ids:
        proc_rows = (
            db.query(
                AppointmentProcedure.appointment_id,
                Procedure.name,
            )
            .join(Procedure, Procedure.id == AppointmentProcedure.procedure_id)
            .filter(AppointmentProcedure.appointment_id.in_(row_ids))
            .all()
        )
        for appointment_id, procedure_name in proc_rows:
            procedures_map.setdefault(appointment_id, []).append(procedure_name)

    items = [
        TableDataLine(
            id=row.id,
            pacient_name=row.patient_name,
            dentist_name=row.dentist_name,
            time_day=(
                f"{row.appointment_date.strftime('%d/%m/%Y')} "
                f"{row.time_begin.strftime('%H:%M')}"
            ),
            procedures=procedures_map.get(row.id, []),
            total_price=float(row.total_price or 0),
            status=row.status,
            confirmation_message_sent=row.confirmation_message_sent,
        )
        for row in rows
    ]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)) if total else 1,
        "statistics": _get_table_statistics(db, clinic_id),
    }


# ==========================================================
# DETALHE (TableDetail)
# ==========================================================


def _build_appointment_detail(
    appointment: Appointment,
) -> TableDetail:
    """
    Monta o TableDetail a partir de um Appointment já
    carregado (com dentist, patient e procedure_items).
    """

    procedures = [
        TableDetailProcedure(
            id=item.id,
            name=item.procedure.name,
            tooth=item.tooth,
            price=float(item.unit_price),
        )
        for item in appointment.procedure_items
    ]

    total_price = sum_procedures(appointment.procedure_items)

    duration = int(
        (
            datetime.combine(date.today(), appointment.time_end)
            - datetime.combine(date.today(), appointment.time_begin)
        ).total_seconds()
        // 60
    )

    return TableDetail(
        id=appointment.id,
        pacient_name=appointment.patient.name,
        dentist_name=appointment.dentist.name,
        time_day=(
            f"{appointment.appointment_date.strftime('%d/%m/%Y')} "
            f"{appointment.time_begin.strftime('%H:%M')}"
        ),
        procedures=procedures,
        total_price=float(total_price),
        duration=duration,
        status=appointment.status,
        confirmation_message_sent=appointment.confirmation_message_sent,
        notes=appointment.notes or "",
    )


def get_appointment_detail_by_id(
    db: Session,
    appointment_id: int,
    clinic_id: str,
) -> TableDetail:
    """
    Detalhe de um agendamento (tela ao clicar na linha
    da tabela).
    """

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        clinic_id,
    )

    return _build_appointment_detail(appointment)


def update_appointment_detail(
    db: Session,
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    clinic_id: str,
) -> TableDetail:
    """
    Atualiza o agendamento (reaproveita update_appointment,
    com todas as validações de expediente/conflito já
    aplicadas) e devolve o resultado no formato TableDetail.
    """

    appointment = update_appointment(
        db,
        appointment_id,
        appointment_update,
        clinic_id,
    )

    return _build_appointment_detail(appointment)

def update_procedure_tooth(
    db: Session,
    procedure_item_id: int,
    tooth: Optional[str],
    clinic_id: str,
) -> AppointmentProcedureOut:
    item = (
        db.query(AppointmentProcedure)
        .join(Appointment, AppointmentProcedure.appointment_id == Appointment.id)
        .filter(
            AppointmentProcedure.id == procedure_item_id,
            Appointment.clinic_id == clinic_id,
        )
        .first()
    )
 
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedimento não encontrado.",
        )
 
    item.tooth = tooth
    db.commit()
    db.refresh(item)
 
    return AppointmentProcedureOut(
        id=item.id,
        name=item.procedure.name,
        tooth=item.tooth,
        display=_build_display(item.procedure.name, item.tooth),
    )