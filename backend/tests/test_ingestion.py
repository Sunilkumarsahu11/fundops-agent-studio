import json

from app.fund_model.default_model import build_default_model
from app.ingestion.excel import read_excel
from app.ingestion.json_reader import read_json
from app.ingestion.mapper import suggest_mappings
from app.ingestion.models import SourceFormat
from app.ingestion.normalizer import normalize_value
from app.ingestion.pipeline import ingest


def test_json_reader_discovers_table_and_types():
    tables = read_json({"valuations": [{"Valuation Date": "2026-06-30", "Fair Value": "1,250,000"}]}, "v.json")
    assert tables[0].name == "valuations"
    assert tables[0].columns[0].inferred_type == "date"
    assert tables[0].columns[1].inferred_type == "number"


def test_mapping_preserves_unmapped_columns():
    model = build_default_model()
    tables = read_json([{"Valuation Date": "2026-06-30", "Fair Value": 10, "Unknown": "x"}], "v.json")
    result = suggest_mappings(tables, model)
    assert any(item.source_field == "Unknown" for item in result.unmapped)


def test_normalization():
    assert normalize_value("1,250,000", "money") == 1250000.0
    assert normalize_value("30/06/2026", "date") == "2026-06-30"
    assert normalize_value("yes", "boolean") is True


def test_ingestion_creates_canonical_records_with_provenance():
    model = build_default_model()
    payload = json.dumps([{"valuation_id": "V1", "valuation_date": "2026-06-30", "value": "1,250,000", "currency": "GBP"}]).encode()
    result = ingest("v.json", payload, SourceFormat.JSON, model)
    assert result.records
    assert result.records[0]["model_id"] == model.id
    assert result.records[0]["provenance"]


def test_excel_reader_imports_workbook():
    from io import BytesIO
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Portfolio"
    sheet.append(["Valuation Date", "Fair Value"])
    sheet.append(["2026-06-30", 100])
    stream = BytesIO()
    workbook.save(stream)
    tables = read_excel(stream.getvalue(), "portfolio.xlsx")
    assert tables[0].name == "Portfolio"
    assert tables[0].rows[0]["Fair Value"] == 100
