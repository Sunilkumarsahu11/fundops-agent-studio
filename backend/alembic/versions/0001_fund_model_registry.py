"""create configurable fund model registry tables

Revision ID: 0001_fund_model_registry
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_fund_model_registry"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fund_models",
        sa.Column("id", sa.String(150), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_table(
        "fund_model_versions",
        sa.Column("model_id", sa.String(150), sa.ForeignKey("fund_models.id"), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("definition_json", sa.JSON(), nullable=False),
    )
    for table, columns in {
        "entity_definitions": ["entity_name"],
        "field_definitions": ["entity_name", "field_name"],
        "relationship_definitions": ["entity_name", "relationship_name"],
    }.items():
        if table == "entity_definitions":
            op.create_table(table, sa.Column("model_id", sa.String(150), primary_key=True), sa.Column("version", sa.Integer(), primary_key=True), sa.Column("entity_name", sa.String(150), primary_key=True), sa.Column("definition_json", sa.JSON(), nullable=False))
        elif table == "field_definitions":
            op.create_table(table, sa.Column("model_id", sa.String(150), primary_key=True), sa.Column("version", sa.Integer(), primary_key=True), sa.Column("entity_name", sa.String(150), primary_key=True), sa.Column("field_name", sa.String(150), primary_key=True), sa.Column("definition_json", sa.JSON(), nullable=False))
        else:
            op.create_table(table, sa.Column("model_id", sa.String(150), primary_key=True), sa.Column("version", sa.Integer(), primary_key=True), sa.Column("entity_name", sa.String(150), primary_key=True), sa.Column("relationship_name", sa.String(150), primary_key=True), sa.Column("definition_json", sa.JSON(), nullable=False))


def downgrade() -> None:
    op.drop_table("relationship_definitions")
    op.drop_table("field_definitions")
    op.drop_table("entity_definitions")
    op.drop_table("fund_model_versions")
    op.drop_table("fund_models")
