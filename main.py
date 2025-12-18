import sys
from parser import parse_program, evaluate_program, to_json, ConfigError, SyntaxErr

def eprint(msg: str):
    sys.stderr.buffer.write((msg + "\n").encode("utf-8"))

def main():
    try:
        src = sys.stdin.read()
        tree = parse_program(src)
        env = evaluate_program(tree)
        sys.stdout.buffer.write(to_json(env).encode("utf-8"))
        return 0
    except SyntaxErr as e:
        eprint(f"Синтаксическая ошибка: строка {e.line}, столбец {e.column}")
        return 2
    except ConfigError as e:
        eprint(str(e))
        return 3
    except Exception as e:
        eprint(str(e))
        return 4

if __name__ == "__main__":
    raise SystemExit(main())
