from sloperator.runner import check_program


def test_valid_syntax_passes_even_with_runtime_errors():
    assert check_program("hallucinate(missing)✨") is None


def test_syntax_errors_are_reported():
    error = check_program("slop x = 1")
    assert error is not None
    assert error.message == "expected ✨ after variable declaration, but reached end of file"


def test_lexical_errors_are_reported():
    error = check_program('hallucinate("hi")✨')
    assert error is not None
    assert error.message == "straight quotes are not supported, use “ and ” for strings"
