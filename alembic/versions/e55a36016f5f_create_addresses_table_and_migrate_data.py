"""create_addresses_table_and_migrate_data

Revision ID: e55a36016f5f
Revises: db1fc5ae4b83
Create Date: 2026-09-26 01:56:45.378993

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'e55a36016f5f'
down_revision: Union[str, Sequence[str], None] = 'db1fc5ae4b83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. Cria a tabela addresses se não existir
    if 'addresses' not in insp.get_table_names():
        op.create_table(
            'addresses',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('street', sa.String(), nullable=False),
            sa.Column('number', sa.String(), nullable=False),
            sa.Column('complement', sa.String(), nullable=True),
            sa.Column('neighborhood', sa.String(), nullable=False),
            sa.Column('city', sa.String(), nullable=False),
            sa.Column('state', sa.String(), nullable=False),
            sa.Column('cep', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_addresses_id'), 'addresses', ['id'], unique=False)

    # 2. Adiciona coluna address_id nas tabelas dentists e patients se ainda não existirem
    dentist_cols = [c['name'] for c in insp.get_columns('dentists')]
    patient_cols = [c['name'] for c in insp.get_columns('patients')]

    if 'address_id' not in dentist_cols:
        op.add_column('dentists', sa.Column('address_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_dentists_address_id', 'dentists', 'addresses', ['address_id'], ['id'], ondelete='SET NULL')

    if 'address_id' not in patient_cols:
        op.add_column('patients', sa.Column('address_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_patients_address_id', 'patients', 'addresses', ['address_id'], ['id'], ondelete='SET NULL')

    # 3. Migra dados existentes de dentistas e pacientes se houver colunas antigas com dados
    if 'street' in dentist_cols:
        dentists_res = bind.execute(sa.text("SELECT id, street, number, complement, neighborhood, city, state, cep FROM dentists WHERE street IS NOT NULL"))
        for row in dentists_res:
            addr_res = bind.execute(
                sa.text("""
                    INSERT INTO addresses (street, number, complement, neighborhood, city, state, cep, created_at)
                    VALUES (:street, :number, :complement, :neighborhood, :city, :state, :cep, NOW())
                    RETURNING id
                """),
                {
                    "street": row[1] or "",
                    "number": row[2] or "",
                    "complement": row[3],
                    "neighborhood": row[4] or "",
                    "city": row[5] or "",
                    "state": row[6] or "",
                    "cep": row[7]
                }
            )
            addr_id = addr_res.scalar()
            bind.execute(
                sa.text("UPDATE dentists SET address_id = :addr_id WHERE id = :id"),
                {"addr_id": addr_id, "id": row[0]}
            )

    if 'street' in patient_cols:
        patients_res = bind.execute(sa.text("SELECT id, street, number, complement, neighborhood, city, state, cep FROM patients WHERE street IS NOT NULL"))
        for row in patients_res:
            addr_res = bind.execute(
                sa.text("""
                    INSERT INTO addresses (street, number, complement, neighborhood, city, state, cep, created_at)
                    VALUES (:street, :number, :complement, :neighborhood, :city, :state, :cep, NOW())
                    RETURNING id
                """),
                {
                    "street": row[1] or "",
                    "number": row[2] or "",
                    "complement": row[3],
                    "neighborhood": row[4] or "",
                    "city": row[5] or "",
                    "state": row[6] or "",
                    "cep": row[7]
                }
            )
            addr_id = addr_res.scalar()
            bind.execute(
                sa.text("UPDATE patients SET address_id = :addr_id WHERE id = :id"),
                {"addr_id": addr_id, "id": row[0]}
            )

    # 4. Remove colunas legadas de endereço de dentists e patients
    for col in ['street', 'number', 'complement', 'neighborhood', 'city', 'state', 'cep']:
        if col in dentist_cols:
            op.drop_column('dentists', col)
        if col in patient_cols:
            op.drop_column('patients', col)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dentist_cols = [c['name'] for c in insp.get_columns('dentists')]
    patient_cols = [c['name'] for c in insp.get_columns('patients')]

    # 1. Readiciona as colunas em dentists e patients
    for col in ['street', 'number', 'neighborhood', 'city', 'state', 'complement', 'cep']:
        if col not in dentist_cols:
            op.add_column('dentists', sa.Column(col, sa.String(), nullable=True))
        if col not in patient_cols:
            op.add_column('patients', sa.Column(col, sa.String(), nullable=True))

    # 2. Migra os dados de volta de addresses para dentists e patients
    bind.execute(sa.text("""
        UPDATE dentists d
        SET street = a.street,
            number = a.number,
            complement = a.complement,
            neighborhood = a.neighborhood,
            city = a.city,
            state = a.state,
            cep = a.cep
        FROM addresses a
        WHERE d.address_id = a.id
    """))

    bind.execute(sa.text("""
        UPDATE patients p
        SET street = a.street,
            number = a.number,
            complement = a.complement,
            neighborhood = a.neighborhood,
            city = a.city,
            state = a.state,
            cep = a.cep
        FROM addresses a
        WHERE p.address_id = a.id
    """))

    # 3. Remove FKs e colunas address_id
    op.drop_constraint('fk_dentists_address_id', 'dentists', type_='foreignkey')
    op.drop_constraint('fk_patients_address_id', 'patients', type_='foreignkey')
    op.drop_column('dentists', 'address_id')
    op.drop_column('patients', 'address_id')

    # 4. Remove tabela addresses
    op.drop_index(op.f('ix_addresses_id'), table_name='addresses')
    op.drop_table('addresses')
