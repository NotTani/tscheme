import operator
from functools import reduce
import traceback

from lexer import Lexer
from parser import Program, SExpression, Atom, Parser

TOP_LEVEL = {
    'z': True,
    'f': False,
    'nil': None,
    '+': lambda *args: reduce(operator.add, args),
    '-': lambda *args: reduce(operator.sub, args),
    '*': lambda *args: reduce(operator.mul, args),
    '/': lambda *args: reduce(operator.truediv, args),
    'car': lambda x: SExpression([x.values[0]], pos=x.pos),
    'cdr': lambda x: SExpression(x.values[1:], pos=x.pos)
}


class Environment(dict):
    def __init__(self, enclosing=None):
        super().__init__()

        if enclosing is None:
            enclosing = TOP_LEVEL

        self.enclosing = enclosing

    def get(self, key, default=None):
        print(f"{super().get(key) = }")
        return k if (k := super().get(key)) else self.enclosing.get(key, default)
        # except KeyError:
        #     return self.enclosing.get(key, default)


class Lambda:
    def __init__(self, args: list[Atom], body: SExpression, env=None):
        if not env:
            env = Environment(TOP_LEVEL)
        self.env = env

        self.args = [arg.value for arg in args]
        self.body = body

    def __call__(self, *args):
        call_env = Environment(enclosing=self.env)
        call_env.update(dict(zip(self.args, args)))
        return eval_expression(self.body, env=call_env)

    def __repr__(self):
        return f"#(ANONYMOUS FUNCTION WITH ARGS ({', '.join(self.args)}))"


def is_identifier(value):
    return isinstance(value, Atom) and value.type == "IDENTIFIER"


def resolve_atom(value: Atom, env):
    if isinstance(value, Atom):
        if value.type == "IDENTIFIER":
            if (v := env.get(value.value, None)) is not None:
                return v
            else:
                raise RuntimeError(f"Could not dereference unknown identifier `{value.value}` at {value.pos}")
        return value.value
    return value


def eval_expression(value: SExpression | Atom, env=None):
    if not env:
        env = TOP_LEVEL

    if isinstance(value, Atom):
        return resolve_atom(value, env)
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
                elif not callable(resolve_atom(op, env)):
                    return SExpression(list(map(eval_expression, [op, *args])), pos=value.pos)
                else:
                    op_func = resolve_atom(op, env)
                    args = list(map(eval_expression, args))
                    return op_func(*args)


def eval_and_print_program(p: Program):
    for statement in p.expressions:
        print(eval_expression(statement))


if __name__ == "__main__":
    print("tscheme repl")
    while (i := input('>')) != '(exit)':
        tokens = list(Lexer(i).tokens())
        # print(f"Tokens: {', '.join([repr(t) for t in tokens])}")
        # print(f"Parsed output: {Parser(tokens).parse()}")
        try:
            eval_and_print_program(Parser(tokens).parse())
        except BaseException as e:
            traceback.print_exc()
