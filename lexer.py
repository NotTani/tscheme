class Token:
    def __init__(self, type_, start, value, line, column):
        self.type = type_
        self.start = start
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token(type={self.type}, position={self.start}, value={self.value})"


class Lexer:
    DISALLOWED_IDENTIFIER_CHARS = '\"\'();\n\t '

    def __init__(self, source):
        self.position = 0
        self.line = 0
        self.column = 0
        self.token_start = 0

        self.source = source

    @property
    def atEnd(self):
        return self.position == len(self.source)

    def currentTokenValue(self):
        return self.source[self.token_start:self.position]

    def advance(self) -> str:
        self.position += 1

        c = self.source[self.position - 1]
        if c == '\n':
            self.line += 1
            self.column = 0
        else:
            self.column += 1

        return c

    def peek(self) -> str:
        if not self.atEnd:
            return self.source[self.position]

    def advanceThrough(self, predicate):
        advanced = 0
        while not self.atEnd and predicate(self.peek()):
            self.advance()
            advanced += 1
        return advanced

    def number(self):
        if self.peek() == 'x':  # hex
            self.advance()
            advanced_through = self.advanceThrough(lambda x: x.isdigit() or x.upper() in "ABCDEF")
            if advanced_through == 0:
                raise SyntaxError("Invalid hexadecimal identifier")

            return self.endToken("NUMBER", value=int(self.currentTokenValue(), 16))

        self.advanceThrough(lambda x: x.isdigit())

        if self.peek() == '.':
            self.advance()

        while not self.atEnd and self.peek().isdigit():
            self.advance()

        return self.endToken("NUMBER", value=float(self.currentTokenValue()))

    def endToken(self, type_, value=None):
        if not value:
            value = self.currentTokenValue()

        token = Token(type_, self.token_start, value, self.line, self.column)

        return token

    def string(self):
        self.advanceThrough(lambda x: x != '"')

        if self.atEnd:
            raise SyntaxError(f"Unterminated quote mark at line {self.line}")

        self.advance()
        return self.endToken("STRING", value=self.currentTokenValue()[1:-1])

    def identifier(self):
        self.advanceThrough(lambda x: x not in self.DISALLOWED_IDENTIFIER_CHARS)
        return self.endToken("IDENTIFIER")

    def tokens(self):
        while not self.atEnd:
            self.advanceThrough(lambda x: x in ['\t', '\n', ' '])

            if self.atEnd:
                break

            self.token_start = self.position

            char = self.advance()
            match char:
                case "(":
                    yield self.endToken("L_PAREN")
                case ")":
                    yield self.endToken("R_PAREN")
                case "\"":
                    yield self.string()
                case ";":
                    self.advanceThrough(lambda x: x != "\n")
                case _:
                    if char.isdigit():
                        yield self.number()
                    elif char not in self.DISALLOWED_IDENTIFIER_CHARS:
                        yield self.identifier()

        self.token_start = self.position
        yield self.endToken("EOF")


def main():
    print("tscheme_lexer")
    while True:
        i = input('>')
        print('\n'.join([repr(x) for x in Lexer(i).tokens()]))


if __name__ == '__main__':
    main()
