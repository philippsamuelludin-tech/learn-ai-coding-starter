import pytest

from sloperator.lexer import TokenType, tokenize
from sloperator.parser import parse
from sloperator.parser.ast import Binary, ExprStmt, Grouping, Literal
from sloperator.runner import run_source


def only_expression(source: str):
    (statement,) = parse(tokenize(source))
    assert isinstance(statement, ExprStmt)
    return statement.expression


def run(source: str) -> str:
    result = run_source(source)
    assert result.stderr == "", result.stderr
    return result.stdout


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", "14"),  # 2 + (3 * 4), not (2 + 3) * 4
        ("2 * 3 + 4", "10"),  # (2 * 3) + 4
        ("2 + 6 / 2", "5"),  # 2 + (6 / 2), not (2 + 6) / 2
        ("1 + 2 * 3 - 4", "3"),  # 1 + (2 * 3) - 4
        ("2 * 3 * 4 + 1", "25"),  # (2 * 3 * 4) + 1
    ],
)
def test_multiplication_binds_tighter_than_addition(expression: str, expected: str):
    assert run(f"hallucinate({expression})✨") == f"{expected}\n"


def test_parser_nests_multiplication_below_addition():
    expr = only_expression("2 + 3 * 4✨")
    assert isinstance(expr, Binary) and expr.operator.type is TokenType.PLUS
    assert isinstance(expr.right, Binary) and expr.right.operator.type is TokenType.STAR
    assert isinstance(expr.left, Literal) and expr.left.value == 2


def test_parser_nests_multiplication_below_addition_on_the_left():
    expr = only_expression("2 * 3 + 4✨")
    assert isinstance(expr, Binary) and expr.operator.type is TokenType.PLUS
    assert isinstance(expr.left, Binary) and expr.left.operator.type is TokenType.STAR


def test_division_shares_the_multiplication_precedence_level():
    expr = only_expression("2 + 6 / 2✨")
    assert isinstance(expr, Binary) and expr.operator.type is TokenType.PLUS
    assert isinstance(expr.right, Binary) and expr.right.operator.type is TokenType.SLASH


def test_grouping_overrides_multiplication_precedence():
    expr = only_expression("(2 + 3) * 4✨")
    assert isinstance(expr, Binary) and expr.operator.type is TokenType.STAR
    assert isinstance(expr.left, Grouping)
    assert run("hallucinate((2 + 3) * 4)✨") == "20\n"
