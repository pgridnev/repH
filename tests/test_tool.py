import subprocess, sys, json, textwrap, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def run(inp: str):
    p = subprocess.run([sys.executable, str(ROOT/"main.py")],
                       input=inp.encode("utf-8"),
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")

def test_numbers_strings_arrays_and_comment():
    code = textwrap.dedent(r'''
        * comment
        var a = 12
        var s = "hi"
        var arr = << 1, 2, << 3, 4 >> >>
    ''').strip()
    rc, out, err = run(code)
    assert rc == 0, err
    obj = json.loads(out)
    assert obj["a"] == 12
    assert obj["s"] == "hi"
    assert obj["arr"] == [1, 2, [3, 4]]

def test_postfix_add_sub():
    code = textwrap.dedent(r'''
        var a = 10
        var b = !(a 5 -)
        var c = !(b 7 +)
    ''').strip()
    rc, out, err = run(code)
    assert rc == 0, err
    obj = json.loads(out)
    assert obj["b"] == 5
    assert obj["c"] == 12

def test_chr():
    code = textwrap.dedent(r'''
        var x = 65
        var ch = !(x chr())
    ''').strip()
    rc, out, err = run(code)
    assert rc == 0, err
    obj = json.loads(out)
    assert obj["ch"] == "A"

def test_undefined_name_error():
    rc, out, err = run("var x = !(y 1 +)\n")
    assert rc != 0
    assert "неизвестное имя" in err.lower()

def test_syntax_error():
    rc, out, err = run("var x = << 1, 2 \n")
    assert rc != 0
    assert "синтаксическая ошибка" in err.lower()
