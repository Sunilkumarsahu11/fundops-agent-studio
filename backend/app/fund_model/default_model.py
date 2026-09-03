from .schema import EntityDefinition, FieldDefinition, FieldType, FundModelDefinition, RelationshipDefinition


def default_fund_model() -> FundModelDefinition:
    """Starter private-markets model. It is configuration, not application code."""
    return FundModelDefinition(
        id="private-markets-core",
        name="Private Markets Core",
        version=1,
        status="active",
        entities=[
            EntityDefinition(
                name="Fund",
                label="Fund",
                fields=[
                    FieldDefinition(name="fund_id", label="Fund ID", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="name", label="Fund Name", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="currency", label="Base Currency", type=FieldType.STRING),
                ],
            ),
            EntityDefinition(
                name="Investor",
                label="Investor",
                fields=[
                    FieldDefinition(name="investor_id", label="Investor ID", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="name", label="Investor Name", type=FieldType.STRING, required=True, nullable=False),
                ],
            ),
            EntityDefinition(
                name="Commitment",
                label="Commitment",
                fields=[
                    FieldDefinition(name="commitment_id", label="Commitment ID", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="amount", label="Commitment Amount", type=FieldType.MONEY),
                    FieldDefinition(name="currency", label="Currency", type=FieldType.STRING),
                ],
                relationships=[
                    RelationshipDefinition(name="fund", target_entity="Fund", cardinality="one", foreign_key="fund_id", required=True),
                    RelationshipDefinition(name="investor", target_entity="Investor", cardinality="one", foreign_key="investor_id", required=True),
                ],
            ),
            EntityDefinition(
                name="Valuation",
                label="Valuation",
                fields=[
                    FieldDefinition(name="valuation_id", label="Valuation ID", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="valuation_date", label="Valuation Date", type=FieldType.DATE),
                    FieldDefinition(name="value", label="Value", type=FieldType.MONEY),
                    FieldDefinition(name="currency", label="Currency", type=FieldType.STRING),
                ],
                relationships=[
                    RelationshipDefinition(name="investment", target_entity="Investment", cardinality="one", foreign_key="investment_id"),
                ],
            ),
            EntityDefinition(
                name="Investment",
                label="Investment",
                fields=[
                    FieldDefinition(name="investment_id", label="Investment ID", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="name", label="Investment Name", type=FieldType.STRING),
                    FieldDefinition(name="cost", label="Cost", type=FieldType.MONEY),
                ],
                relationships=[
                    RelationshipDefinition(name="fund", target_entity="Fund", cardinality="one", foreign_key="fund_id"),
                ],
            ),
            EntityDefinition(
                name="CapitalCall",
                label="Capital Call",
                fields=[
                    FieldDefinition(name="capital_call_id", label="Capital Call ID", type=FieldType.STRING, required=True, nullable=False),
                    FieldDefinition(name="call_date", label="Call Date", type=FieldType.DATE),
                    FieldDefinition(name="amount", label="Amount", type=FieldType.MONEY),
                    FieldDefinition(name="currency", label="Currency", type=FieldType.STRING),
                ],
                relationships=[
                    RelationshipDefinition(name="commitment", target_entity="Commitment", cardinality="one", foreign_key="commitment_id"),
                ],
            ),
        ],
    )
