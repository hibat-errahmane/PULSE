import pytest

from src.complaints import categorize


def test_not_received():
    assert "not_received" in categorize("Simplesmente n\u00e3o recebi o produto")


def test_incomplete():
    assert "incomplete" in categorize("comprei 3 luminarias recebi apenas uma.")


def test_wrong_item_is_not_incomplete():
    c = categorize("paguei por um produto e veio outro (tamanho errado)")
    assert "wrong_item" in c
    assert "incomplete" not in c


@pytest.mark.xfail(reason="no rule yet for 'nao veio'; text analysis is paused")
def test_charger_missing():
    assert categorize("O carregador n\u00e3o veio") != []
