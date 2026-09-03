from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String, create_engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .schema import FundModelDefinition


class Base(DeclarativeBase):
    pass


class FundModelRow(Base):
    __tablename__ = "fund_models"
    id: Mapped[str] = mapped_column(String(150), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class FundModelVersionRow(Base):
    __tablename__ = "fund_model_versions"
    model_id: Mapped[str] = mapped_column(ForeignKey("fund_models.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class EntityDefinitionRow(Base):
    __tablename__ = "entity_definitions"
    model_id: Mapped[str] = mapped_column(String(150), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(150), primary_key=True)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class FieldDefinitionRow(Base):
    __tablename__ = "field_definitions"
    model_id: Mapped[str] = mapped_column(String(150), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(150), primary_key=True)
    field_name: Mapped[str] = mapped_column(String(150), primary_key=True)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class RelationshipDefinitionRow(Base):
    __tablename__ = "relationship_definitions"
    model_id: Mapped[str] = mapped_column(String(150), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(150), primary_key=True)
    relationship_name: Mapped[str] = mapped_column(String(150), primary_key=True)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class FundModelStore:
    """PostgreSQL-backed, immutable-version fund model store."""

    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def save(self, model: FundModelDefinition) -> FundModelDefinition:
        with Session(self.engine) as session, session.begin():
            if session.get(FundModelVersionRow, (model.id, model.version)) is not None:
                raise ValueError(f"Fund model version already exists: {model.id} v{model.version}")
            root = session.get(FundModelRow, model.id)
            if root is None:
                session.add(FundModelRow(id=model.id, name=model.name, description=model.metadata.get("description", ""), metadata_json=model.metadata))
            elif root.name != model.name:
                root.name = model.name
            session.add(FundModelVersionRow(model_id=model.id, version=model.version, status=model.status, definition_json=model.model_dump(mode="json")))
            for entity in model.entities:
                session.add(EntityDefinitionRow(model_id=model.id, version=model.version, entity_name=entity.name, definition_json=entity.model_dump(mode="json")))
                for field in entity.fields:
                    session.add(FieldDefinitionRow(model_id=model.id, version=model.version, entity_name=entity.name, field_name=field.name, definition_json=field.model_dump(mode="json")))
                for relationship in entity.relationships:
                    session.add(RelationshipDefinitionRow(model_id=model.id, version=model.version, entity_name=entity.name, relationship_name=relationship.name, definition_json=relationship.model_dump(mode="json")))
        return model

    def get(self, model_id: str, version: int | None = None) -> FundModelDefinition | None:
        with Session(self.engine) as session:
            if version is None:
                row = session.scalars(select(FundModelVersionRow).where(FundModelVersionRow.model_id == model_id).order_by(FundModelVersionRow.version.desc())).first()
            else:
                row = session.get(FundModelVersionRow, (model_id, version))
            return FundModelDefinition.model_validate(row.definition_json) if row else None

    def list(self, model_id: str | None = None) -> list[FundModelDefinition]:
        with Session(self.engine) as session:
            stmt = select(FundModelVersionRow).order_by(FundModelVersionRow.model_id, FundModelVersionRow.version)
            if model_id:
                stmt = stmt.where(FundModelVersionRow.model_id == model_id)
            return [FundModelDefinition.model_validate(row.definition_json) for row in session.scalars(stmt)]

    def next_version(self, model_id: str) -> int:
        return max((m.version for m in self.list(model_id)), default=0) + 1

    def activate(self, model_id: str, version: int) -> None:
        with Session(self.engine) as session, session.begin():
            target = session.get(FundModelVersionRow, (model_id, version))
            if target is None:
                raise KeyError(f"Fund model not found: {model_id} v{version}")
            session.execute(update(FundModelVersionRow).where(FundModelVersionRow.model_id == model_id).values(status="retired"))
            target.status = "active"
