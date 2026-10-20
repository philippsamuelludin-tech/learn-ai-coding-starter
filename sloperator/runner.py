import sys
from dataclasses import dataclass
from io import StringIO
from typing import TextIO

from sloperator.errors import SlopError
from sloperator.evaluator import Interpreter
from sloperator.lexer import tokenize
from sloperator.parser import parse
from sloperator.parser.ast import Program

PYTHON_RECURSION_LIMIT = 20_000


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int


def _prepare(source: str) -> tuple[Program | None, SlopError | None]:
    if sys.getrecursionlimit() < PYTHON_RECURSION_LIMIT:
        sys.setrecursionlimit(PYTHON_RECURSION_LIMIT)
    try:
        return parse(tokenize(source)), None
    except SlopError as error:
        return None, error


def check_program(source: str) -> SlopError | None:
    """Check the source lexically and syntactically without running it."""
    _, error = _prepare(source)
    return error


def run_program(source: str, out: TextIO) -> SlopError | None:
    program, error = _prepare(source)
    if error is not None:
        return error
    assert program is not None
    try:
        Interpreter(out).run(program)
    except SlopError as error:
        return error
    return None


def run_source(source: str) -> RunResult:
    out = StringIO()
    error = run_program(source, out)
    if error is None:
        return RunResult(out.getvalue(), "", 0)
    return RunResult(out.getvalue(), f"{error}\n", 1)
