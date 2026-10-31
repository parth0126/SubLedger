"""Initial schema: plans, customers, subscriptions, invoices, payment attempts, ledger.

Revision ID: 0001
Revises:
Create Date: 2026-10-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True, length=32)


def _created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "billing_cycle",
            _enum("ck_plans_billing_cycle", "monthly", "quarterly", "yearly"),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", _enum("ck_plans_status", "active", "inactive"), nullable=False),
        _created_at(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price > 0", name="ck_plans_price_positive"),
        sa.PrimaryKeyConstraint("id", name="pk_plans"),
    )
    op.create_index("ix_plans_status", "plans", ["status"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("contact_details", sa.JSON(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
    )
    op.create_index("ix_customers_email", "customers", ["email"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column(
            "status", _enum("ck_subscriptions_status", "active", "cancelled"), nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("current_period_start", sa.Date(), nullable=False),
        sa.Column("current_period_end", sa.Date(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.CheckConstraint(
            "current_period_end > current_period_start", name="ck_subscriptions_period_order"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_subscriptions_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], name="fk_subscriptions_plan_id_plans", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
    )
    op.create_index("ix_subscriptions_customer_id", "subscriptions", ["customer_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index(
        "uq_subscriptions_active_customer_plan",
        "subscriptions",
        ["customer_id", "plan_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "status",
            _enum(
                "ck_invoices_status",
                "draft",
                "issued",
                "partially_paid",
                "paid",
                "overdue",
                "void",
            ),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        _created_at(),
        sa.CheckConstraint("amount_due > 0", name="ck_invoices_amount_due_positive"),
        sa.CheckConstraint("amount_paid >= 0", name="ck_invoices_amount_paid_non_negative"),
        sa.CheckConstraint("amount_paid <= amount_due", name="ck_invoices_amount_paid_within_due"),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            name="fk_invoices_subscription_id_subscriptions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_invoices_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_invoices"),
        sa.UniqueConstraint(
            "subscription_id", "period_start", name="uq_invoices_subscription_period"
        ),
    )
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index("ix_invoices_customer_id", "invoices", ["customer_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "status", _enum("ck_payment_attempts_status", "success", "failed"), nullable=False
        ),
        sa.Column("provider_reference", sa.String(255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        _created_at(),
        sa.CheckConstraint("amount > 0", name="ck_payment_attempts_amount_positive"),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            name="fk_payment_attempts_invoice_id_invoices",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payment_attempts"),
    )
    op.create_index("ix_payment_attempts_invoice_id", "payment_attempts", ["invoice_id"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column(
            "entry_type",
            _enum(
                "ck_ledger_entries_entry_type",
                "invoice_created",
                "payment_success",
                "payment_failure",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("reference_id", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_ledger_entries_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            name="fk_ledger_entries_invoice_id_invoices",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ledger_entries"),
    )
    op.create_index(
        "ix_ledger_entries_customer_id_created_at", "ledger_entries", ["customer_id", "created_at"]
    )
    op.create_index("ix_ledger_entries_invoice_id", "ledger_entries", ["invoice_id"])
    op.create_index("ix_ledger_entries_reference_id", "ledger_entries", ["reference_id"])

    # Enforce append-only semantics at the database level as well as in the ORM.
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_ledger_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'ledger_entries is append-only: % is not allowed', TG_OP;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_ledger_entries_no_update_delete
            BEFORE UPDATE OR DELETE ON ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_ledger_entries_no_truncate
            BEFORE TRUNCATE ON ledger_entries
            FOR EACH STATEMENT EXECUTE FUNCTION prevent_ledger_mutation();
            """
        )


def downgrade() -> None:
    op.drop_table("ledger_entries")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS prevent_ledger_mutation()")
    op.drop_table("payment_attempts")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("customers")
    op.drop_table("plans")
