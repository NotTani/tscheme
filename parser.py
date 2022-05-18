from dataclasses import dataclass
from lexer import Lexer, Token


@dataclass
class Atom:
    type: str
    value: any
    pos: (int, int)

    def __repr__(self):
        if self.type == "SYMBOL":
            return f":{self.value}"
        return repr(self.value)


@dataclass
class SExpression:
    values: list
    pos: (int, int)

    def __repr__(self):
        return f"({' '.join([str(v) for v in self.values])})"


@dataclass
class Program:
    expressions: list[SExpression]

    def __repr__(self):
        return '\\n'.join([repr(v) for v in self.expressions])


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def next_token(self):
        self.current += 1
        return self.tokens[self.current - 1]

    def peek(self):
        return self.tokens[self.current]

    def parse(self):
        if self.peek().type == "EOF":
            return Program([])

        expressions = []

        while self.peek().type != "EOF":
            expressions.append(self.parse_s_expression())

        return Program(expressions)

    def parse_s_expression(self):
        current = self.next_token()

        if current.type in ["NUMBER", "STRING", "IDENTIFIER", "SYMBOL"]:
            return Atom(
                type=current.type,
                value=current.value,
                pos=(current.line, current.column)
            )
        elif current.type == "L_PAREN":
            items = []
            while self.peek().type not in ["R_PAREN", "EOF"]:
                s_expr = self.parse_s_expression()
                items.append(s_expr)

            if self.peek().type != "R_PAREN":
                raise SyntaxError("Unbalanced Parenthesis")

            self.next_token()

            return SExpression(values=items, pos=(current.line, current.column))
        else:
            raise Exception(f"Unexpected {current.type} on line {current.line}")


def main():
    print("t_scheme parser")
    while True:
        i = input('>')
        tokens = list(Lexer(i).tokens())
        print(f"Tokens: {', '.join([repr(t) for t in tokens])}")
        print(Parser(tokens).parse())


if __name__ == '__main__':
    main()
