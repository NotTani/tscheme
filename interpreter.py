import functools
import operator
from functools import reduce
import traceback

from lexer import Lexer
from parser import Program, SExpression, Atom, Parser


TOP_LEVEL = {
    't': True,
    'f': False,
    'nil': None,
    '+': lambda *args: reduce(operator.add, args),
    '-': lambda *args: reduce(operator.sub, args),
    '*': lambda *args: reduce(operator.mul, args),
    '/': lambda *args: reduce(operator.truediv, args),
    'car': lambda x: SExpression([x.values[0]], pos=x.pos),
    'cdr': lambda x: SExpression(x.values[1:], pos=x.pos),
    'format': lambda format_string, *format_values: print(format_string.format(*format_values))
}


class Environment:
    def __init__(self, local, enclosing=None):
        super().__init__()

        if enclosing is None:
            enclosing = TOP_LEVEL

        self.local = local
        self.enclosing = enclosing

    def get(self, key, default=None):
        try:
            return self.local[key]
        except KeyError:
            return self.enclosing.get(key, default)

    def __repr__(self):
        return f"Env({self.local}, enclosing={self.enclosing})"


class Lambda:
    def __init__(self, args: list[Atom], body: SExpression, env=None):
        if not env:
            env = Environment(local={}, enclosing=TOP_LEVEL)
        self.env = env

        self.args = [arg.value for arg in args]
        self.body = body

    def __call__(self, *args):
        assert len(args) == len(self.args), "Function called with wrong number of arguments"
        self.env.local.update(dict(zip(self.args, args)))
        return eval_expression(self.body, env=self.env)

    def __repr__(self):
        return f"#(ANONYMOUS FUNCTION at f{hex(id(self))} WITH ARGS ({', '.join(self.args)}))"


def is_identifier(value):
    return isinstance(value, Atom) and value.type == "IDENTIFIER"


def resolve_atom(value: Atom, env):
    if isinstance(value, Atom):
        if value.type == "IDENTIFIER":
            if (v := env.get(value.value, None)) is not None:
                return v
            else:
                raise RuntimeError(f"Could not dereference unknown identifier `{value.value}` at {value.pos}")
        elif value.type == "SYMBOL":
            return value
        return value.value
    return value


def eval_expression(value: SExpression | Atom, env=None):
    if not env:
        env = TOP_LEVEL

    if isinstance(value, Atom):
        value = resolve_atom(value, env)
        return value

    elif isinstance(value, SExpression):
        match value.values:
            case []:
                return None
            case [op, *args]:  # function call
                op_name = op.value.lower() if is_identifier(op) else None

                if is_identifier(op) and op_name == "cond":
                    assert len(args) == 3, f"cond at {value.pos} must take 3 args"

                    predicate = eval_expression(args[0])
                    assert isinstance(predicate, bool), f"the first argument of cond must be a bool at {value.pos}"
                    assert isinstance(args[1], SExpression), f"the second argument of cond must be an S-Expression"
                    assert isinstance(args[2], SExpression), f"the third argument of cond must be an S-Expression"

                    if predicate:
                        return eval_expression(args[1])
                    else:
                        return eval_expression(args[2])
                elif is_identifier(op) and op_name == "lambda":
                    assert len(args) == 2, f"lambda at {value.pos} must have two args"
                    return Lambda(args[0].values, args[1])

                elif is_identifier(op) and op_name == "let":
                    assert len(args) == 2, f"let must take 2 args"
                    assert is_identifier(args[0]), "the first argument of let must be an identifier"

                    env[args[0].value] = eval_expression(args[1])
                elif is_identifier(op) and op_name == "defmacro":
                    assert len(args) == 2, f"defmacro at {value.pos} must have two args"

                elif not callable(resolve_atom(op, env)):
                    return SExpression(list(map(eval_expression, [op, *args])), pos=value.pos)
                else:
                    op_func = resolve_atom(op, env)
                    args = list(map(functools.partial(eval_expression, env=env), args))
                    return op_func(*args)


def eval_and_print_program(p: Program):
    for statement in p.expressions:
        print(repr(eval_expression(statement)))


if __name__ == "__main__":
    print("tscheme repl")
    while (i := input('>')) != '(exit)':
        tokens = list(Lexer(i).tokens())
        # print(f"Tokens: {', '.join([repr(t) for t in tokens])}")
        # print(f"Parsed output: {Parser(tokens).parse()}")
        try:
            eval_and_print_program(Parser(tokens).parse())
        except Exception as e:

            print(e)
