"""Safe equation parser for the function-car game (no eval, no imports beyond math).

    f = parse("y = 2x^2 - 3sin(x) + 1")
    f(1.5)  ->  a number

Supports: + - * / ^ ** parentheses, implicit multiplication (2x, 3(x+1), x(x-4)),
x, pi, e, and the functions sin cos tan sqrt abs ln log exp floor ceil.
Raises ValueError with a friendly message when the text can't be understood.
"""
import math

FUNCS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt,
    "abs": abs, "ln": math.log, "log": math.log10, "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil,
}
CONSTS = {"pi": math.pi, "e": math.e}
NAMES = sorted(list(FUNCS) + list(CONSTS) + ["x"], key=len, reverse=True)  # longest first


def _tokenize(s):
    s = s.lower().replace(" ", "").replace("**", "^").replace("×", "*").replace("−", "-")
    for superscript, power in (("²", "2"), ("³", "3"), ("⁴", "4"), ("⁵", "5"),
                               ("⁶", "6"), ("⁷", "7"), ("⁸", "8"), ("⁹", "9")):
        s = s.replace(superscript, "^" + power)
    for prefix in ("y=", "f(x)="):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    if not s:
        raise ValueError("Type an equation, like 2x + 1")
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isdigit() or c == ".":
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] == "."):
                j += 1
            try:
                toks.append(("num", float(s[i:j])))
            except ValueError:
                raise ValueError("Bad number '%s'" % s[i:j])
            i = j
        elif c in "+-*/^(),":
            toks.append((c, c))
            i += 1
        else:
            for n in NAMES:
                if s.startswith(n, i):
                    toks.append(("name", n))
                    i += len(n)
                    break
            else:
                raise ValueError("I don't know '%s'" % c)
    return toks


class _Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i][0] if self.i < len(self.t) else None

    def take(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def expr(self):
        left = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()[0]
            right = self.term()
            left = (lambda a, b: lambda x: a(x) + b(x))(left, right) if op == "+" else \
                   (lambda a, b: lambda x: a(x) - b(x))(left, right)
        return left

    def term(self):
        left = self.unary()
        while True:
            k = self.peek()
            if k == "*":
                self.take()
                right = self.unary()
            elif k == "/":
                self.take()
                right = self.unary()
                left = (lambda a, b: lambda x: a(x) / b(x))(left, right)
                continue
            elif k in ("num", "name", "("):  # implicit multiplication: 2x, 3(x+1)
                right = self.power()
            else:
                return left
            left = (lambda a, b: lambda x: a(x) * b(x))(left, right)

    def unary(self):
        if self.peek() == "-":
            self.take()
            inner = self.unary()
            return lambda x: -inner(x)
        if self.peek() == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == "^":
            self.take()
            exp = self.unary()  # right-associative; allows x^-1
            return lambda x: base(x) ** exp(x)
        return base

    def atom(self):
        k = self.peek()
        if k is None:
            raise ValueError("The equation ends too early")
        kind, val = self.take()
        if kind == "num":
            return lambda x: val
        if kind == "(":
            inner = self.expr()
            if self.peek() != ")":
                raise ValueError("Missing a closing )")
            self.take()
            return inner
        if kind == "name":
            if val == "x":
                return lambda x: x
            if val in CONSTS:
                c = CONSTS[val]
                return lambda x: c
            if self.peek() != "(":
                raise ValueError("%s needs brackets, like %s(x)" % (val, val))
            self.take()
            inner = self.expr()
            if self.peek() != ")":
                raise ValueError("Missing a closing )")
            self.take()
            fn = FUNCS[val]
            return lambda x: fn(inner(x))
        raise ValueError("Unexpected '%s'" % kind)


def parse(text):
    """Return a function f(x). Raises ValueError for text we can't read."""
    p = _Parser(_tokenize(text))
    f = p.expr()
    if p.i != len(p.t):
        raise ValueError("Something is out of place near '%s'" % p.t[p.i][1])
    return f


def safe_eval(f, x):
    """f(x) as a float, or None where it is undefined (divide by 0, sqrt(-1), ...)."""
    try:
        v = f(x)
        v = float(v)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v
