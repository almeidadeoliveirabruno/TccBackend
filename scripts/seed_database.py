import os
import sys
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

# Adiciona a raiz do Backend ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from core.security import hash_cpf, encrypt_cpf
from enums.DentistStatus import DentistStatus
from enums.ExpenseCategory import ExpenseCategory
from enums.ExpenseStatus import ExpenseStatus
from enums.ProcedureCategory import ProcedureCategory
from enums.ReceivableStatus import ReceivableStatus
from models.clinic import Clinic
from models.specialty import Specialty
from models.schedule import Schedule
from models.address import Address
from models.dentist import Dentist
from models.associations.dentist_schedules import DentistSchedule
from models.patient import Patient
from models.procedure import Procedure
from models.appointment import Appointment, AppointmentStatus
from models.associations.appointment_procedure import AppointmentProcedure
from models.receivable import Receivable
from models.expense import Expense


def generate_valid_cpf(seed_num: int) -> str:
    """Gera um CPF matematicamente válido com base em um número base."""
    random.seed(seed_num)
    digits = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(8)]
    
    # Primeiro dígito verificador
    s1 = sum(digits[i] * (10 - i) for i in range(9))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    digits.append(d1)
    
    # Segundo dígito verificador
    s2 = sum(digits[i] * (11 - i) for i in range(10))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    digits.append(d2)
    
    return "".join(map(str, digits))


def seed():
    db = SessionLocal()
    try:
        print("=== Iniciando Seed do Banco de Dados ===")
        
        # 1. Buscar a clínica existente
        clinic = db.query(Clinic).first()
        if not clinic:
            print("Erro: Nenhuma clínica encontrada!")
            return
        
        clinic_id = clinic.id
        print(f"Clínica selecionada: {clinic.nome} (ID: {clinic_id})")

        # 2. Especialidades
        specialty_names = [
            "Ortodontia",
            "Endodontia",
            "Implantodontia",
            "Periodontia",
            "Odontopediatria",
            "Prótese Dentária",
            "Estética Dental",
            "Cirurgia Bucomaxilofacial"
        ]
        specialties_map = {}
        for s_name in specialty_names:
            spec = db.query(Specialty).filter(Specialty.name == s_name).first()
            if not spec:
                spec = Specialty(name=s_name)
                db.add(spec)
                db.flush()
            specialties_map[s_name] = spec
        print(f"Especialidades preparadas: {len(specialties_map)}")

        # 3. Horários Base (Schedules)
        schedules_data = [
            (time(8, 0), time(12, 0)),
            (time(13, 0), time(18, 0)),
            (time(8, 0), time(18, 0)),
        ]
        schedules_map = {}
        for t_begin, t_end in schedules_data:
            sch = db.query(Schedule).filter(
                Schedule.time_begin == t_begin,
                Schedule.time_end == t_end
            ).first()
            if not sch:
                sch = Schedule(time_begin=t_begin, time_end=t_end)
                db.add(sch)
                db.flush()
            schedules_map[(t_begin, t_end)] = sch
        print(f"Horários padrão preparados: {len(schedules_map)}")

        # 4. Criar 4 Dentistas
        dentists_info = [
            {
                "name": "Dr. Carlos Eduardo Silva",
                "email": "carlos.silva@odontolink.com.br",
                "phone": "24988771122",
                "cro": "RJ-45210",
                "cpf": generate_valid_cpf(101),
                "specialties": ["Periodontia", "Estética Dental"],
                "street": "Rua 33", "number": "120", "neighborhood": "Vila Santa Cecília", "city": "Volta Redonda", "state": "RJ", "cep": "27260-000"
            },
            {
                "name": "Dra. Mariana Guimarães Costa",
                "email": "mariana.costa@odontolink.com.br",
                "phone": "24988772233",
                "cro": "RJ-52184",
                "cpf": generate_valid_cpf(102),
                "specialties": ["Ortodontia", "Odontopediatria"],
                "street": "Avenida Paulo de Frontin", "number": "450", "neighborhood": "Aterrado", "city": "Volta Redonda", "state": "RJ", "cep": "27213-000"
            },
            {
                "name": "Dr. Rodrigo Ferreira Santos",
                "email": "rodrigo.santos@odontolink.com.br",
                "phone": "24988773344",
                "cro": "RJ-38971",
                "cpf": generate_valid_cpf(103),
                "specialties": ["Implantodontia", "Cirurgia Bucomaxilofacial"],
                "street": "Rua São João", "number": "85", "neighborhood": "Centro", "city": "Barra Mansa", "state": "RJ", "cep": "27310-000"
            },
            {
                "name": "Dra. Juliana Barros Peixoto",
                "email": "juliana.peixoto@odontolink.com.br",
                "phone": "24988774455",
                "cro": "RJ-49832",
                "cpf": generate_valid_cpf(104),
                "specialties": ["Endodontia", "Prótese Dentária"],
                "street": "Rua 16", "number": "310", "neighborhood": "Vila Santa Cecília", "city": "Volta Redonda", "state": "RJ", "cep": "27259-000"
            }
        ]

        dentists_created = []
        for d_data in dentists_info:
            d_cpf_hash = hash_cpf(d_data["cpf"])
            existing_dentist = db.query(Dentist).filter(
                Dentist.clinic_id == clinic_id,
                Dentist.cpf_hash == d_cpf_hash
            ).first()

            if not existing_dentist:
                addr = Address(
                    street=d_data["street"],
                    number=d_data["number"],
                    neighborhood=d_data["neighborhood"],
                    city=d_data["city"],
                    state=d_data["state"],
                    cep=d_data["cep"],
                )
                db.add(addr)
                db.flush()

                dentist = Dentist(
                    name=d_data["name"],
                    email=d_data["email"],
                    phone=d_data["phone"],
                    cpf_hash=d_cpf_hash,
                    cpf_encrypted=encrypt_cpf(d_data["cpf"]),
                    cro=d_data["cro"],
                    status=DentistStatus.ATIVO,
                    clinic_id=clinic_id,
                    address_id=addr.id
                )
                for sp_name in d_data["specialties"]:
                    dentist.specialties.append(specialties_map[sp_name])
                
                db.add(dentist)
                db.flush()

                # Adicionar grade de horários de Segunda a Sexta (dias 1 a 5)
                sch_morning = schedules_map[(time(8, 0), time(12, 0))]
                sch_afternoon = schedules_map[(time(13, 0), time(18, 0))]
                for day in range(1, 6):
                    db.add(DentistSchedule(dentist_id=dentist.id, schedule_id=sch_morning.id, day_of_week=day))
                    db.add(DentistSchedule(dentist_id=dentist.id, schedule_id=sch_afternoon.id, day_of_week=day))
                db.flush()
                dentists_created.append(dentist)
            else:
                dentists_created.append(existing_dentist)

        print(f"Dentistas prontos: {len(dentists_created)}")

        # 5. Criar 6 Pacientes
        patients_info = [
            {
                "name": "Camila Rocha Miranda",
                "email": "camila.rocha@gmail.com",
                "phone": "24992110011",
                "cpf": generate_valid_cpf(201),
                "birth_date": "1994-05-12",
                "gender": "Feminino",
                "health_plan": "Unimed Odonto",
                "profession": "Advogada",
                "observations": "Sensibilidade nos molares superiores.",
                "street": "Rua 21", "number": "45", "neighborhood": "Vila Santa Cecília", "city": "Volta Redonda", "state": "RJ", "cep": "27260-120"
            },
            {
                "name": "Lucas Mendes Ribeiro",
                "email": "lucas.mendes@hotmail.com",
                "phone": "24992110022",
                "cpf": generate_valid_cpf(202),
                "birth_date": "1988-11-23",
                "gender": "Masculino",
                "health_plan": "Amil Dental",
                "profession": "Engenheiro de Software",
                "observations": "Bruxismo noturno, usa placa miorrelaxante.",
                "street": "Rua Lions Club", "number": "210", "neighborhood": "Aterrado", "city": "Volta Redonda", "state": "RJ", "cep": "27213-200"
            },
            {
                "name": "Beatriz Fernandes Souza",
                "email": "beatriz.souza@gmail.com",
                "phone": "24992110033",
                "cpf": generate_valid_cpf(203),
                "birth_date": "2001-03-15",
                "gender": "Feminino",
                "health_plan": "SulAmérica Odonto",
                "profession": "Estudante",
                "observations": "Tratamento ortodôntico em andamento.",
                "street": "Avenida Amaral Peixoto", "number": "890", "neighborhood": "São João", "city": "Volta Redonda", "state": "RJ", "cep": "27253-000"
            },
            {
                "name": "Gabriel Henrique Silveira",
                "email": "gabriel.silveira@outlook.com",
                "phone": "24992110044",
                "cpf": generate_valid_cpf(204),
                "birth_date": "1979-08-30",
                "gender": "Masculino",
                "health_plan": "Bradesco Dental",
                "profession": "Arquiteto",
                "observations": "Histórico de implante dental no dente 16.",
                "street": "Rua Neme Cecílio", "number": "54", "neighborhood": "Retiro", "city": "Volta Redonda", "state": "RJ", "cep": "27275-100"
            },
            {
                "name": "Amanda Vasconcelos Lima",
                "email": "amanda.vasconcelos@gmail.com",
                "phone": "24992110055",
                "cpf": generate_valid_cpf(205),
                "birth_date": "1992-07-19",
                "gender": "Feminino",
                "health_plan": "Particular",
                "profession": "Médica",
                "observations": "Alérgica a dipirona.",
                "street": "Rua Dezenove", "number": "102", "neighborhood": "Bela Vista", "city": "Volta Redonda", "state": "RJ", "cep": "27261-000"
            },
            {
                "name": "Felipe Duarte Carvalho",
                "email": "felipe.carvalho@yahoo.com.br",
                "phone": "24992110066",
                "cpf": generate_valid_cpf(206),
                "birth_date": "1985-04-08",
                "gender": "Masculino",
                "health_plan": "OdontoPrev",
                "profession": "Professor",
                "observations": "Interesse em clareamento estético.",
                "street": "Rua Custódio Ferreira Leite", "number": "78", "neighborhood": "Vila Mury", "city": "Volta Redonda", "state": "RJ", "cep": "27281-500"
            }
        ]

        patients_created = []
        for p_data in patients_info:
            p_cpf_hash = hash_cpf(p_data["cpf"])
            existing_patient = db.query(Patient).filter(
                Patient.clinic_id == clinic_id,
                Patient.cpf_hash == p_cpf_hash
            ).first()

            if not existing_patient:
                addr = Address(
                    street=p_data["street"],
                    number=p_data["number"],
                    neighborhood=p_data["neighborhood"],
                    city=p_data["city"],
                    state=p_data["state"],
                    cep=p_data["cep"],
                )
                db.add(addr)
                db.flush()

                patient = Patient(
                    name=p_data["name"],
                    email=p_data["email"],
                    phone=p_data["phone"],
                    cpf_hash=p_cpf_hash,
                    cpf_encrypted=encrypt_cpf(p_data["cpf"]),
                    birth_date=p_data["birth_date"],
                    gender=p_data["gender"],
                    observations=p_data["observations"],
                    health_plan=p_data["health_plan"],
                    profession=p_data["profession"],
                    address_id=addr.id,
                    clinic_id=clinic_id
                )
                db.add(patient)
                db.flush()
                patients_created.append(patient)
            else:
                patients_created.append(existing_patient)

        # Incluir também outros pacientes existentes se houver
        all_patients = db.query(Patient).filter(Patient.clinic_id == clinic_id).all()
        print(f"Pacientes prontos no banco: {len(all_patients)}")

        # 6. Criar 8 Procedimentos
        procedures_info = [
            {
                "name": "Consulta Inicial / Avaliação",
                "category": ProcedureCategory.PREVENTIVO.value,
                "price": Decimal("150.00"),
                "duration": 30,
                "description": "Exame clínico intraoral completo, anamnese detalhada e plano de tratamento.",
                "status": True
            },
            {
                "name": "Profilaxia e Raspagem Supragengival",
                "category": ProcedureCategory.PREVENTIVO.value,
                "price": Decimal("220.00"),
                "duration": 45,
                "description": "Remoção de placa bacteriana, cálculo dentário com ultrassom e polimento coronário.",
                "status": True
            },
            {
                "name": "Restauração em Resina Composta",
                "category": ProcedureCategory.RESTAURADOR.value,
                "price": Decimal("280.00"),
                "duration": 45,
                "description": "Remoção de cárie e restauração estética direta com resina fotopolimerizável.",
                "status": True
            },
            {
                "name": "Clareamento Dental em Consultório",
                "category": ProcedureCategory.ESTETICO.value,
                "price": Decimal("850.00"),
                "duration": 60,
                "description": "Sessão de clareamento dental com gel de alta concentração ativado por luz.",
                "status": True
            },
            {
                "name": "Tratamento Endodôntico (Canal)",
                "category": ProcedureCategory.ENDODONTIA.value,
                "price": Decimal("650.00"),
                "duration": 60,
                "description": "Descontaminação, instrumentação rotatória e obturação dos canais radiculares.",
                "status": True
            },
            {
                "name": "Extração Dentária Simples",
                "category": ProcedureCategory.CIRURGICO.value,
                "price": Decimal("320.00"),
                "duration": 45,
                "description": "Exodontia de dente erupcionado com anestesia local e sutura.",
                "status": True
            },
            {
                "name": "Manutenção de Aparelho Ortodôntico",
                "category": ProcedureCategory.ORTODONTICO.value,
                "price": Decimal("180.00"),
                "duration": 30,
                "description": "Troca de arcos, ligaduras elásticas e ativação do aparelho fixo.",
                "status": True
            },
            {
                "name": "Instalação de Implante Dentário Titânio",
                "category": ProcedureCategory.CIRURGICO.value,
                "price": Decimal("2200.00"),
                "duration": 90,
                "description": "Fase cirúrgica com colocação de implante osseointegrável de titânio cone morse.",
                "status": True
            }
        ]

        procedures_created = []
        for proc_data in procedures_info:
            proc = db.query(Procedure).filter(
                Procedure.clinic_id == clinic_id,
                Procedure.name == proc_data["name"]
            ).first()

            if not proc:
                proc = Procedure(
                    clinic_id=clinic_id,
                    name=proc_data["name"],
                    category=proc_data["category"],
                    price=proc_data["price"],
                    duration=proc_data["duration"],
                    description=proc_data["description"],
                    status=proc_data["status"]
                )
                db.add(proc)
                db.flush()
            procedures_created.append(proc)

        print(f"Procedimentos prontos: {len(procedures_created)}")

        # 7. Criar 20 Consultas
        # 17 consultas passadas dispersas em Julho, Agosto e Setembro 2026 (até 26/09/2026)
        # 3 consultas futuras (28, 29, 30 de Setembro 2026)
        
        # Lista com as 20 consultas com datas, horários, dentistas, pacientes, procedimentos e dentes
        appointments_seed_data = [
            # --- Julho 2026 (6 consultas passadas) ---
            {
                "date": date(2026, 7, 6), "time_begin": time(9, 0), "time_end": time(9, 30),
                "dentist_idx": 0, "patient_idx": 0, "proc_indices": [0], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Primeira consulta de avaliação clínica. Plano preventivo definido."
            },
            {
                "date": date(2026, 7, 10), "time_begin": time(10, 0), "time_end": time(10, 45),
                "dentist_idx": 0, "patient_idx": 0, "proc_indices": [1], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_debito", "is_paid": True,
                "notes": "Profilaxia e raspagem realizadas. Ótima resposta gengival."
            },
            {
                "date": date(2026, 7, 14), "time_begin": time(14, 0), "time_end": time(14, 45),
                "dentist_idx": 0, "patient_idx": 1, "proc_indices": [2], "teeth": ["14"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_credito", "is_paid": True,
                "notes": "Restauração ocluso-mesial no dente 14 em resina."
            },
            {
                "date": date(2026, 7, 18), "time_begin": time(9, 30), "time_end": time(10, 0),
                "dentist_idx": 1, "patient_idx": 2, "proc_indices": [6], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Manutenção ortodôntica mensal, troca de arcos 0.16 NiTi."
            },
            {
                "date": date(2026, 7, 22), "time_begin": time(15, 0), "time_end": time(16, 0),
                "dentist_idx": 3, "patient_idx": 3, "proc_indices": [4], "teeth": ["26"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_credito", "is_paid": True,
                "notes": "Tratamento de canal finalizado no dente 26 sem dor pós-operatória."
            },
            {
                "date": date(2026, 7, 28), "time_begin": time(11, 0), "time_end": time(11, 45),
                "dentist_idx": 2, "patient_idx": 4, "proc_indices": [5], "teeth": ["38"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "dinheiro", "is_paid": True,
                "notes": "Exodontia simples do dente 38 com boa hemostasia."
            },

            # --- Agosto 2026 (7 consultas passadas) ---
            {
                "date": date(2026, 8, 4), "time_begin": time(8, 30), "time_end": time(9, 0),
                "dentist_idx": 0, "patient_idx": 5, "proc_indices": [0], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Avaliação clínica para planejamento estético."
            },
            {
                "date": date(2026, 8, 7), "time_begin": time(10, 0), "time_end": time(11, 0),
                "dentist_idx": 0, "patient_idx": 5, "proc_indices": [3], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_credito", "is_paid": True,
                "notes": "Clareamento em consultório - 3 aplicações de 15 minutos."
            },
            {
                "date": date(2026, 8, 11), "time_begin": time(14, 0), "time_end": time(14, 45),
                "dentist_idx": 0, "patient_idx": 1, "proc_indices": [1], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_debito", "is_paid": True,
                "notes": "Limpeza de rotina e aplicação tópica de flúor."
            },
            {
                "date": date(2026, 8, 17), "time_begin": time(9, 0), "time_end": time(9, 30),
                "dentist_idx": 1, "patient_idx": 2, "proc_indices": [6], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Ativação ortodôntica mensal."
            },
            {
                "date": date(2026, 8, 20), "time_begin": time(13, 30), "time_end": time(15, 0),
                "dentist_idx": 2, "patient_idx": 3, "proc_indices": [7], "teeth": ["46"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_credito", "is_paid": True,
                "notes": "Cirurgia de implante dentário na região do dente 46."
            },
            {
                "date": date(2026, 8, 25), "time_begin": time(16, 0), "time_end": time(16, 45),
                "dentist_idx": 0, "patient_idx": 4, "proc_indices": [2], "teeth": ["21"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Restauração estética de resina no dente 21."
            },
            {
                "date": date(2026, 8, 28), "time_begin": time(10, 30), "time_end": time(11, 15),
                "dentist_idx": 3, "patient_idx": 0, "proc_indices": [2], "teeth": ["36"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_debito", "is_paid": True,
                "notes": "Restauração direta em resina composta no dente 36."
            },

            # --- Setembro 2026 (4 consultas passadas até hoje) ---
            {
                "date": date(2026, 9, 3), "time_begin": time(9, 0), "time_end": time(9, 45),
                "dentist_idx": 0, "patient_idx": 4, "proc_indices": [1], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Profilaxia completa sem queixas."
            },
            {
                "date": date(2026, 9, 10), "time_begin": time(14, 0), "time_end": time(14, 30),
                "dentist_idx": 1, "patient_idx": 2, "proc_indices": [6], "teeth": [None],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Manutenção ortodôntica regular."
            },
            {
                "date": date(2026, 9, 16), "time_begin": time(15, 0), "time_end": time(15, 45),
                "dentist_idx": 0, "patient_idx": 5, "proc_indices": [2], "teeth": ["11"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "cartao_credito", "is_paid": True,
                "notes": "Faceta em resina composta no dente 11."
            },
            {
                "date": date(2026, 9, 23), "time_begin": time(11, 0), "time_end": time(11, 45),
                "dentist_idx": 2, "patient_idx": 1, "proc_indices": [5], "teeth": ["48"],
                "status": AppointmentStatus.REALIZADO, "payment_method": "pix", "is_paid": True,
                "notes": "Extração de terceiro molar inferior direito."
            },

            # --- Setembro 2026 (3 consultas futuras: 28, 29, 30) ---
            {
                "date": date(2026, 9, 28), "time_begin": time(9, 0), "time_end": time(9, 45),
                "dentist_idx": 0, "patient_idx": 0, "proc_indices": [1], "teeth": [None],
                "status": AppointmentStatus.CONFIRMADO, "payment_method": None, "is_paid": False,
                "notes": "Consulta de revisão semestral confirmada pelo paciente via WhatsApp."
            },
            {
                "date": date(2026, 9, 29), "time_begin": time(14, 0), "time_end": time(15, 0),
                "dentist_idx": 0, "patient_idx": 3, "proc_indices": [3], "teeth": [None],
                "status": AppointmentStatus.AGENDADO, "payment_method": None, "is_paid": False,
                "notes": "Agendado para sessão de clareamento estético em consultório."
            },
            {
                "date": date(2026, 9, 30), "time_begin": time(10, 30), "time_end": time(11, 0),
                "dentist_idx": 1, "patient_idx": 2, "proc_indices": [6], "teeth": [None],
                "status": AppointmentStatus.AGENDADO, "payment_method": None, "is_paid": False,
                "notes": "Manutenção do alinhador ortodôntico."
            }
        ]

        appointments_created = []
        for app_data in appointments_seed_data:
            d = dentists_created[app_data["dentist_idx"] % len(dentists_created)]
            p = all_patients[app_data["patient_idx"] % len(all_patients)]
            
            # Criar Appointment diretamente
            appointment = Appointment(
                clinic_id=clinic_id,
                dentist_id=d.id,
                patient_id=p.id,
                appointment_date=app_data["date"],
                time_begin=app_data["time_begin"],
                time_end=app_data["time_end"],
                status=app_data["status"],
                confirmation_message_sent=True if app_data["is_paid"] or app_data["status"] == AppointmentStatus.CONFIRMADO else False,
                notes=app_data["notes"]
            )
            db.add(appointment)
            db.flush()

            # Adicionar AppointmentProcedure
            total_amount = Decimal("0")
            for p_idx, tooth in zip(app_data["proc_indices"], app_data["teeth"]):
                proc = procedures_created[p_idx]
                app_proc = AppointmentProcedure(
                    appointment_id=appointment.id,
                    procedure_id=proc.id,
                    tooth=tooth,
                    unit_price=proc.price
                )
                db.add(app_proc)
                total_amount += proc.price
            db.flush()

            # Adicionar Receivable
            if app_data["is_paid"]:
                paid_datetime = datetime.combine(app_data["date"], app_data["time_end"])
                receivable = Receivable(
                    appointment_id=appointment.id,
                    clinic_id=clinic_id,
                    total_amount=total_amount,
                    status="pago",
                    due_date=app_data["date"],
                    paid_at=paid_datetime,
                    payment_method=app_data["payment_method"],
                    notes=f"Pagamento recebido via {app_data['payment_method']} referente à consulta."
                )
            else:
                receivable = Receivable(
                    appointment_id=appointment.id,
                    clinic_id=clinic_id,
                    total_amount=total_amount,
                    status="pendente",
                    due_date=app_data["date"],
                    paid_at=None,
                    payment_method=None,
                    notes="Aguardando atendimento e pagamento no balcão."
                )
            db.add(receivable)
            db.flush()
            appointments_created.append(appointment)

        print(f"Consultas criadas: {len(appointments_created)} (17 passadas e pagas, 3 futuras)")

        # 8. Criar 10 Despesas (Expenses) dispersas em Julho, Agosto e Setembro 2026
        expenses_data = [
            # Julho
            {
                "description": "Aluguel Comercial do Consultório - Julho/2026",
                "category": ExpenseCategory.ALUGUEL.value,
                "amount": Decimal("3500.00"),
                "due_date": date(2026, 7, 5),
                "paid_at": datetime(2026, 7, 5, 10, 30),
                "status": ExpenseStatus.PAGO.value,
                "notes": "Pago via transferência PIX para imobiliária."
            },
            {
                "description": "Dental Cremer - Resinas, Ácido Fosfórico e Anestésicos",
                "category": ExpenseCategory.MATERIAL_ODONTOLOGICO.value,
                "amount": Decimal("1250.80"),
                "due_date": date(2026, 7, 10),
                "paid_at": datetime(2026, 7, 9, 14, 20),
                "status": ExpenseStatus.PAGO.value,
                "notes": "NF 45892 - Reposição de estoque de dentística."
            },
            {
                "description": "Enel Distribuição - Energia Elétrica Julho",
                "category": ExpenseCategory.CONTAS_FIXAS.value,
                "amount": Decimal("485.40"),
                "due_date": date(2026, 7, 15),
                "paid_at": datetime(2026, 7, 14, 11, 0),
                "status": ExpenseStatus.PAGO.value,
                "notes": "Débito em conta corrente."
            },
            # Agosto
            {
                "description": "Aluguel Comercial do Consultório - Agosto/2026",
                "category": ExpenseCategory.ALUGUEL.value,
                "amount": Decimal("3500.00"),
                "due_date": date(2026, 8, 5),
                "paid_at": datetime(2026, 8, 5, 9, 15),
                "status": ExpenseStatus.PAGO.value,
                "notes": "Pago via PIX."
            },
            {
                "description": "Dental Speed - Luvas de Nitrilo, Máscaras e Babadores",
                "category": ExpenseCategory.MATERIAL_ODONTOLOGICO.value,
                "amount": Decimal("890.00"),
                "due_date": date(2026, 8, 12),
                "paid_at": datetime(2026, 8, 11, 16, 45),
                "status": ExpenseStatus.PAGO.value,
                "notes": "NF 12903 - Material descartável para biossegurança."
            },
            {
                "description": "Laboratório de Prótese Dental Art - Coroas Cerâmicas",
                "category": ExpenseCategory.LABORATORIO.value,
                "amount": Decimal("1650.00"),
                "due_date": date(2026, 8, 20),
                "paid_at": datetime(2026, 8, 20, 15, 30),
                "status": ExpenseStatus.PAGO.value,
                "notes": "Serviços protéticos de zircônia e dissilicato."
            },
            # Setembro
            {
                "description": "Aluguel Comercial do Consultório - Setembro/2026",
                "category": ExpenseCategory.ALUGUEL.value,
                "amount": Decimal("3500.00"),
                "due_date": date(2026, 9, 5),
                "paid_at": datetime(2026, 9, 5, 11, 0),
                "status": ExpenseStatus.PAGO.value,
                "notes": "Pago via PIX."
            },
            {
                "description": "Software OdontoLink - Licença Cloud e Backups",
                "category": ExpenseCategory.SOFTWARE.value,
                "amount": Decimal("299.90"),
                "due_date": date(2026, 9, 10),
                "paid_at": datetime(2026, 9, 10, 8, 0),
                "status": ExpenseStatus.PAGO.value,
                "notes": "Assinatura mensal recorrente no cartão corporativo."
            },
            {
                "description": "Manutenção Preventiva de Compressor e Autoclave",
                "category": ExpenseCategory.MANUTENCAO.value,
                "amount": Decimal("650.00"),
                "due_date": date(2026, 9, 28),
                "paid_at": None,
                "status": ExpenseStatus.PENDENTE.value,
                "notes": "Visita técnica de revisão semestral agendada."
            },
            {
                "description": "Enel Distribuição - Energia Elétrica Setembro",
                "category": ExpenseCategory.CONTAS_FIXAS.value,
                "amount": Decimal("512.30"),
                "due_date": date(2026, 9, 30),
                "paid_at": None,
                "status": ExpenseStatus.PENDENTE.value,
                "notes": "Boleto bancário a vencer no fim do mês."
            }
        ]

        expenses_created = []
        for exp_data in expenses_data:
            expense = Expense(
                clinic_id=clinic_id,
                description=exp_data["description"],
                category=exp_data["category"],
                amount=exp_data["amount"],
                due_date=exp_data["due_date"],
                paid_at=exp_data["paid_at"],
                status=exp_data["status"],
                notes=exp_data["notes"]
            )
            db.add(expense)
            db.flush()
            expenses_created.append(expense)

        print(f"Despesas criadas: {len(expenses_created)} (8 pagas, 2 pendentes)")

        db.commit()
        print("=== Seed finalizado com SUCESSO e salvo no banco de dados! ===")

    except Exception as e:
        db.rollback()
        print(f"ERRO durante o seed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
