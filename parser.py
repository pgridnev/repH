import json
from dataclasses import dataclass
from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput

@dataclass
class SyntaxErr(Exception):
    line: int
    column: int

class ConfigError(Exception):
    pass

GRAMMAR = r"""
%import common.ESCAPED_STRING
%import common.WS_INLINE
%import common.NEWLINE -> _NL
%ignore WS_INLINE

COMMENT: /\*[^\r\n]*/
%ignore COMMENT

start: (_NL | stmt)*

stmt: decl _NL*

decl: "var" NAME "=" expr

?expr: const_expr
     | value

const_expr: "!(" rpn ")"
rpn: (NAME | NUMBER | OP | CHR)+

OP: "+" | "-"
CHR.2: "chr()"

?value: number
      | string
      | array

number: NUMBER
string: ESCAPED_STRING
array: "<<" [value ("," value)*] ">>"

NAME: /[a-z]+(?!\()/
NUMBER: /[1-9][0-9]*/
"""

_lark = Lark(GRAMMAR, parser="lalr", maybe_placeholders=False)

def parse_program(src: str) -> Tree:
    try:
        return _lark.parse(src)
    except UnexpectedInput as e:
        raise SyntaxErr(line=getattr(e, "line", 1), column=getattr(e, "column", 1))

def _unescape_string(s: str) -> str:
    return json.loads(s)

def _eval_value(node, env):
    if isinstance(node, Tree):
        if node.data == "number":
            return int(node.children[0])
        if node.data == "string":
            return _unescape_string(str(node.children[0]))
        if node.data == "array":
            out = []
            for ch in node.children:
                out.append(_eval_value(ch, env))
            return out
        if node.data == "value":
            return _eval_value(node.children[0], env)
    if isinstance(node, Token):
        if node.type == "NUMBER":
            return int(node)
        if node.type == "ESCAPED_STRING":
            return _unescape_string(str(node))
        if node.type == "NAME":
            name = str(node)
            if name not in env:
                raise ConfigError(f"Неизвестное имя: {name}")
            return env[name]
    raise ConfigError("Ошибка вычисления")

def _eval_rpn(tokens, env):
    st = []
    for t in tokens:
        if not isinstance(t, Token):
            raise ConfigError("Ошибка вычисления")
        if t.type == "NAME":
            name = str(t)
            if name not in env:
                raise ConfigError(f"Неизвестное имя: {name}")
            st.append(env[name])
        elif t.type == "NUMBER":
            st.append(int(t))
        elif t.type == "CHR":
            if len(st) < 1:
                raise ConfigError("Ошибка вычисления: chr() требует 1 аргумент")
            x = st.pop()
            if not isinstance(x, int):
                raise ConfigError("Ошибка вычисления: chr() ожидает число")
            st.append(chr(x))
        elif t.type == "OP":
            if len(st) < 2:
                raise ConfigError("Ошибка вычисления: недостаточно аргументов")
            b = st.pop()
            a = st.pop()
            if not isinstance(a, int) or not isinstance(b, int):
                raise ConfigError("Ошибка вычисления: операции + и - только для чисел")
            if str(t) == "+":
                st.append(a + b)
            else:
                st.append(a - b)
        else:
            raise ConfigError("Ошибка вычисления")
    if len(st) != 1:
        raise ConfigError("Ошибка вычисления: выражение некорректно")
    return st[0]

def _eval_expr(node, env):
    if isinstance(node, Tree):
        if node.data == "const_expr":
            rpn_tree = node.children[0]
            return _eval_rpn(rpn_tree.children, env)
        if node.data == "expr":
            return _eval_expr(node.children[0], env)
        if node.data == "value":
            return _eval_value(node.children[0], env)
        if node.data in ("number", "string", "array"):
            return _eval_value(node, env)
        if len(node.children) == 1:
            return _eval_expr(node.children[0], env)
    return _eval_value(node, env)

def evaluate_program(tree: Tree) -> dict:
    env = {}
    for ch in tree.children:
        if isinstance(ch, Tree) and ch.data == "stmt":
            decl = ch.children[0]
            name = str(decl.children[0])
            expr = decl.children[1]
            env[name] = _eval_expr(expr, env)
    return env

def to_json(env: dict) -> str:
    return json.dumps(env, ensure_ascii=False, indent=2) + "\n"
