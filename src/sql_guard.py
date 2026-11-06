"""Decides whether model-written SQL may run.

This check happens in code, before the database is touched, because an
instruction in a prompt cannot stop a query that has already been executed.

It uses an allowlist: a query runs only if it parses as a single known read
statement. Anything else is refused, including SQL that cannot be parsed.

For a stronger guarantee, also connect with a database user that only has
SELECT rights. Then a bug here still could not change any data.
"""

import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

REFUSAL = "I'm sorry, but I can only run read-only queries, so I did not run this one."

_READ_STATEMENTS = (exp.Select, exp.SetOperation, exp.Show, exp.Describe)

# Allowed roots can still contain these, such as SELECT ... INTO or FOR UPDATE.
_FORBIDDEN_PARTS = (
    exp.Into,
    exp.Lock,
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,
    exp.Set,
)

# Read files from the server, or tie up the connection.
_FORBIDDEN_FUNCTIONS = {"load_file", "sleep", "benchmark", "get_lock", "release_lock"}

_CODE_FENCE = re.compile(r"^\s*```[a-zA-Z]*\s*|\s*```\s*$")


class UnsafeQueryError(ValueError):
    """The SQL is not a single read-only statement."""


def check_read_only(sql: str) -> str:
    """Returns the SQL if it is safe to run, and raises UnsafeQueryError if not."""
    cleaned = _CODE_FENCE.sub("", sql or "").strip()
    if not cleaned:
        raise UnsafeQueryError("The query is empty.")

    try:
        statements = [s for s in sqlglot.parse(cleaned, read="mysql") if s is not None]
    except SqlglotError as error:
        raise UnsafeQueryError("The query could not be parsed.") from error

    if len(statements) != 1:
        raise UnsafeQueryError("Only one statement can run at a time.")

    statement = statements[0]
    if not isinstance(statement, _READ_STATEMENTS):
        raise UnsafeQueryError(f"{type(statement).__name__} statements are not allowed.")

    for node in statement.walk():
        if isinstance(node, _FORBIDDEN_PARTS):
            raise UnsafeQueryError(f"{type(node).__name__} is not allowed.")
        if isinstance(node, exp.Func) and node.sql_name().lower() in _FORBIDDEN_FUNCTIONS:
            raise UnsafeQueryError(f"{node.sql_name()} is not allowed.")
        if isinstance(node, exp.Anonymous) and str(node.this).lower() in _FORBIDDEN_FUNCTIONS:
            raise UnsafeQueryError(f"{node.this} is not allowed.")

    return cleaned
