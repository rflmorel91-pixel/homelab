import pytest
from pydantic import ValidationError

from app.products.prestamodesk.collections_schemas import (
    CollectionActivityCreate,
)


def test_collection_activity_outcome_is_trimmed():
    activity = CollectionActivityCreate(
        channel="phone",
        outcome="  Cliente contactado  ",
        contacted_at="2026-10-02T14:00:00Z",
    )

    assert activity.outcome == "Cliente contactado"


@pytest.mark.parametrize("outcome", ["", "   ", "\t\n"])
def test_collection_activity_rejects_blank_outcome(outcome):
    with pytest.raises(ValidationError):
        CollectionActivityCreate(
            channel="phone",
            outcome=outcome,
            contacted_at="2026-10-02T14:00:00Z",
        )
