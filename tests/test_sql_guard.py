"""Run from the repository root: python -m unittest discover tests"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sql_guard import UnsafeQueryError, check_read_only

ALLOWED = [
    "SELECT * FROM emp",
    "SELECT Name FROM Artist LIMIT 10;",
    "SELECT ArtistId, COUNT(*) AS c FROM Track GROUP BY ArtistId ORDER BY c DESC LIMIT 3;",
    "SELECT e.name, d.name FROM emp e JOIN dept d ON e.dept_id = d.id",
    "SELECT * FROM emp WHERE id IN (SELECT id FROM dept)",
    "WITH a AS (SELECT 1 AS x) SELECT * FROM a",
    "SELECT 1 UNION SELECT 2",
    "SHOW TABLES",
    "DESCRIBE emp",
    "EXPLAIN SELECT * FROM emp",
    # Words that look dangerous but are only data.
    "SELECT * FROM emp WHERE note = 'please DROP TABLE emp'",
    "SELECT `delete` FROM emp",
    "SELECT deleted_at, updated_at FROM emp",
]

REFUSED = [
    "DELETE FROM emp",
    "DROP TABLE emp",
    "UPDATE emp SET name = 'x'",
    "ALTER TABLE emp ADD COLUMN x INT",
    "INSERT INTO emp VALUES (1)",
    "REPLACE INTO emp VALUES (1)",
    "TRUNCATE TABLE emp",
    "CREATE TABLE x (id INT)",
    "GRANT ALL ON *.* TO someone",
    "CALL some_procedure()",
    "SET GLOBAL max_connections = 1",
    "delete from emp",
    "DeLeTe FROM emp",
    "/* note */ DELETE FROM emp",
    # A safe statement hiding a second one.
    "SELECT * FROM emp; DROP TABLE emp",
    "SELECT 1; SELECT 2",
    # Read statements with side effects.
    "SELECT * FROM emp INTO OUTFILE '/tmp/x'",
    "SELECT * FROM emp INTO DUMPFILE '/tmp/x'",
    "SELECT * FROM emp FOR UPDATE",
    "SELECT LOAD_FILE('/etc/passwd')",
    "SELECT SLEEP(100)",
    "SELECT BENCHMARK(100000000, MD5('x'))",
    "EXPLAIN DELETE FROM emp",
    # Not SQL at all: refused rather than guessed at.
    "",
    "   ",
    "I cannot answer that question.",
]


class CheckReadOnly(unittest.TestCase):
    def test_allows_read_statements(self):
        for sql in ALLOWED:
            with self.subTest(sql=sql):
                self.assertTrue(check_read_only(sql))

    def test_refuses_everything_else(self):
        for sql in REFUSED:
            with self.subTest(sql=sql):
                with self.assertRaises(UnsafeQueryError):
                    check_read_only(sql)

    def test_strips_a_markdown_code_fence(self):
        self.assertEqual(check_read_only("```sql\nSELECT 1\n```"), "SELECT 1")

    def test_a_code_fence_does_not_hide_a_write(self):
        with self.assertRaises(UnsafeQueryError):
            check_read_only("```sql\nDROP TABLE emp\n```")


if __name__ == "__main__":
    unittest.main()
