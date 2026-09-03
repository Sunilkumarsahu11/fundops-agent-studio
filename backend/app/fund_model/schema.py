from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    MONEY = "money"
    ENUM = "enum"
    REFERENCE = "reference"
    JSON = "json"


class FieldDefinition(BaseModel):
    name: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    type: FieldType
    required: bool = False
    nullable: bool = True
    description: str = ""
    default: Any = None
    enum_values: list[str] = Field(default_factory=list)
    reference_entity: str | None = None
    validation: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_configuration(self) -> "FieldDefinition":
        if self.type == FieldType.ENUM and not self.enum_values:
            raise ValueError("enum_values is required for enum fields")
        if self.type == FieldType.REFERENCE and not self.reference_entity:
            raise ValueError("reference_entity is required for reference fields")
        if self.required and self.nullable:
            raise ValueError("a required field cannot be nullable")
        return self


class RelationshipDefinition(BaseModel):
    name: str = Field(min_length=1)
    target_entity: str = Field(min_length=1)
    cardinality: str = Field(pattern=r"^(one|many)$")
    foreign_key: str | None = None
    required: bool = False


class EntityDefinition(BaseModel):
    name: str = Field(min_length=1, pattern=r"^[A-Z][A-Za-z0-9]*$")
    label: str
    description: str = ""
    version: int = Field(default=1, ge=1)
    fields: list[FieldDefinition] = Field(default_factory=list)
    relationships: list[RelationshipDefinition] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_names(self) -> "EntityDefinition":
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate field names in entity {self.name}")
        return self


class FundModelDefinition(BaseModel):
    id: str = Field(min_length=1)
    name: str
    version: int = Field(default=1, ge=1)
    status: str = Field(default="draft", pattern=r"^(draft|active|retired)$")
    entities: list[EntityDefinition] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_entities(self) -> "FundModelDefinition":
        names = [entity.name for entity in self.entities]
        if len(names) != len(set(names)):
            raise ValueError("Entity names must be unique within a fund model")
        return self
