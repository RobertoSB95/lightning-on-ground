# tests/test_data_processing.py
import pytest
from data_processing import normalizar_dato, calculate_distance


# ── normalizar_dato ───────────────────────────────────────────────

def test_normalizar_dato_string_normal():
    assert normalizar_dato("hola") == "hola"

def test_normalizar_dato_none_retorna_none():
    assert normalizar_dato(None) is None

def test_normalizar_dato_vacio_retorna_none():
    assert normalizar_dato("   ") is None

def test_normalizar_dato_int():
    assert normalizar_dato("42", "int") == 42

def test_normalizar_dato_float():
    assert normalizar_dato("3.14", "float") == 3.14

def test_normalizar_dato_int_vacio_retorna_none():
    assert normalizar_dato("", "int") is None


# ── calculate_distance ────────────────────────────────────────────

def test_vehiculo_lejos_de_base_UY():
    # Montevideo — lejos de la base
    assert calculate_distance(-34.9011, -56.1645, "UY") is True

def test_vehiculo_en_base_UY():
    # Coordenadas casi iguales a la base UY
    assert calculate_distance(-33.38056, -56.52361, "UY") is False

def test_vehiculo_lejos_de_base_ARG():
    # Buenos Aires — lejos de la base ARG
    assert calculate_distance(-34.6037, -58.3816, "ARG") is True

def test_vehiculo_en_base_ARG():
    # Coordenadas casi iguales a la base ARG
    assert calculate_distance(-28.43817, -56.08829, "ARG") is False

def test_pais_desconocido_lanza_error():
    with pytest.raises(ValueError):
        calculate_distance(-33.0, -56.0, "BR")