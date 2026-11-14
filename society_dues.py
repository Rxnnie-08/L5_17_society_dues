import ast
import operator
import os
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE dues (flat TEXT, month TEXT, amount INTEGER, paid INTEGER)")
TREASURER_PASSWORD = os.environ.get("TREASURER_PASSWORD")

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def addDue(flat, month, amount, history=[]):
    conn.execute("INSERT INTO dues VALUES (?, ?, ?, 0)", (flat, month, amount))
    history.append((flat, month))
    return history
def collect(flat, month):
    row = conn.execute("SELECT amount FROM dues WHERE flat = ? AND month = ?", (flat, month)).fetchone()
    if row:
        conn.execute("UPDATE dues SET paid = 1 WHERE flat = ? AND month = ?", (flat, month))
        return row[0]


def safe_eval(node):
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if (isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    raise ValueError("unsupported expression")


def penalty(rule):
    try:
        late_fee = safe_eval(ast.parse(rule, mode="eval"))
    except (ValueError, SyntaxError, TypeError, ZeroDivisionError, RecursionError):
        late_fee = 0
    return late_fee


def pending():
    rows = conn.execute("SELECT flat FROM dues WHERE paid = 0").fetchall()
    if rows != None:
        return [r[0] for r in rows]
    return []


def main():
    addDue("A-101", "Oct", 2500)
    addDue("A-102", "Oct", 2500)
    print(collect("A-101", "Oct"))
    print(penalty("50 * 2"))
    print(pending())


main()