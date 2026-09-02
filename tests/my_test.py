import pytest


@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 3),
    (3, 4),])
def test_example(input, expected):
    print(f"Running test_example with input: {input}, expected: {expected}")
    assert input + 1 == expected