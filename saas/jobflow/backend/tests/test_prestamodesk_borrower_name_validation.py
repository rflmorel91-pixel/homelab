import pytest
from pydantic import ValidationError

from app.products.prestamodesk.schemas import BorrowerCreate, BorrowerUpdate


@pytest.mark.parametrize("schema", [BorrowerCreate, BorrowerUpdate])
def test_borrower_name_is_trimmed(schema):
    borrower = schema(full_name="  María Rodríguez  ")

    assert borrower.full_name == "María Rodríguez"


@pytest.mark.parametrize("schema", [BorrowerCreate, BorrowerUpdate])
@pytest.mark.parametrize("name", ["", "   ", " \t ", "\n"])
def test_borrower_name_rejects_blank_values(schema, name):
    with pytest.raises(ValidationError):
        schema(full_name=name)
