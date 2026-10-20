# Fix the broken `\t` escape in SlopLang

## The bug

`examples/tab.slop` contains:

```slop
— Does the tab escape work?
hallucinate(“name\tscore”)✨
```

Running it prints `nametscore`. The `\t` escape produces a literal `t`
(byte `0x74`) instead of a tab character (byte `0x09`).

## Where the bug is

`sloperator/lexer/scanner.py` — the `ESCAPES` mapping (around line 40):

```python
ESCAPES: dict[str, str] = {
    "n": "\n",
    "t": "t",
    "”": "”",
    "\\": "\\",
}
```

The `"t"` entry is wrong. `Scanner.string()` looks up each escape character in
this table and appends the mapped value to the string literal, so this entry
is exactly what lands in the parsed string.

`docs/spec.md` (line 57) states the intended behavior: strings "support
escapes `\n`, `\t`, `\”`, and `\\`".

## What you are allowed to change

- `sloperator/lexer/scanner.py` — only the value of the `"t"` entry in
  `ESCAPES`.
- `tests/test_lexer.py` — you may add test cases for escape sequences.

Do not change anything else. Specifically:

- Leave the `"n"`, `"”"`, and `"\\"` entries in `ESCAPES` exactly as they are.
- Do not add, remove, or rename any escape sequence. `\n`, `\t`, `\”`, and
  `\\` are the only four the language supports.
- Do not modify the parser, evaluator, interpreter, runner, or `docs/spec.md`.
- Do not refactor the escape handling into a new function, class, or table.
- Do not edit any file under `examples/`.
- Do not change the behavior of any other escape, and do not make the fix
  conditional on anything.

## How to prove the fix worked

1. The full test suite must stay green:

   ```bash
   uv run pytest -q
   ```

2. `examples/tab.slop` must print a real tab. Check the actual bytes — this
   bug is easy to miss in normal terminal output, where a tab and a `t` can
   look alike:

   ```bash
   uv run sloperator.py examples/tab.slop | od -c
   ```

   Before the fix the output is:

   ```
   n   a   m   e   t   s   c   o   r   e  \n
   ```

   After the fix it must be:

   ```
   n   a   m   e  \t   s   c   o   r   e  \n
   ```

   Note `\t` (`0x09`), not `t` (`0x74`).

3. Add a regression test so this cannot break again silently. Assert on the
   *decoded* string value, not on the raw source text, so the test fails for
   the right reason:

   ```python
   assert tokenize("“a\\tb”")[0].literal == "a\tb"
   ```

   The existing `test_lexical_errors` cases only cover *unknown* escapes,
   which is why this bug went unnoticed. The new test should assert what a
   *known* escape decodes to.

## Report back

State which files you changed, paste the `od -c` output, and paste the
relevant pytest output. If you changed anything outside the two files allowed
above, say so explicitly.
