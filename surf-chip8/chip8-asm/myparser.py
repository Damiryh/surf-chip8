from mytoken import *
from myast import *

ARGS = {
    (TokenType.KEYWORD, 'K'): ArgType.KEY,
    (TokenType.KEYWORD, 'DT'): ArgType.DELAY_TIMER,
    (TokenType.KEYWORD, 'ST'): ArgType.SOUND_TIMER,
    (TokenType.KEYWORD, 'I'): ArgType.INDEX,
    (TokenType.KEYWORD, 'B'): ArgType.BCD,
    (TokenType.KEYWORD, 'F'): ArgType.FLAGS,
}

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def curr(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def next(self):
        self.pos += 1

    def match(self, t, v=None):
        if self.curr().type != t or (v and v != self.curr().value):
            return False
        self.next()
        return True
    
    def consume(self, t, v=None):
        if not self.match(t, v):
            message = f"{t} excepted here" if not v else f"{t} '{v}' excepted here"
            raise ChipSyntaxError(self.curr().location, message)
    
    def parse(self):
        ast = []
        while self.curr().type != TokenType.EOF:
            ast.append(self.statement())
        return ast

    def statement(self):
        if self.curr().type == TokenType.IDENTIFITER:
            return self.label()
        elif self.curr().type == TokenType.MNEMONIC:
            return self.instruction()
        elif self.match(TokenType.SYMBOL, '.'):
            return self.directive()

    def label(self):
        l = Label(self.curr().value, self.curr().location); self.next()
        self.consume(TokenType.SYMBOL, ':')
        return l

    def instruction(self):
        i = Instruction(self.curr().value, self.curr().location); self.next()

        if self.curr().type in [TokenType.MNEMONIC]: return i
        i.append(self.argument())

        while self.match(TokenType.SYMBOL, ','):
            i.append(self.argument())

        return i

    def directive(self):
        i = Directive(self.curr().value, self.curr().location); self.next()

        if self.curr().type in [TokenType.MNEMONIC]: return i
        i.append(self.argument())
    
        while self.match(TokenType.SYMBOL, ','):
            i.append(self.argument())
    
        return i

    def argument(self):
        if self.match(TokenType.SYMBOL, '['):
            if self.match(TokenType.KEYWORD, 'I'):
                arg = Argument(ArgType.INDEX_ADDR, NullValue())
            else:
                arg = Argument(ArgType.ADDRESS, self.value())
            self.consume(TokenType.SYMBOL, ']')
        
        elif self.match(TokenType.SYMBOL, '@'):
            arg = Argument(ArgType.REG, self.value())
        elif self.match(TokenType.SYMBOL, '!'):
            arg = Argument(ArgType.NIBBLE, self.value())
        elif (self.curr().type, self.curr().value) in ARGS.keys():
            a = (self.curr().type, self.curr().value)
            arg = Argument(ARGS[a], NullValue())
            self.next()
        else:
            arg = Argument(ArgType.BYTE, self.value())

        return arg

    def value(self):
        if self.curr().type == TokenType.IDENTIFITER:
            v = Identifier(self.curr().value)
            self.next()
            return v
        elif self.curr().type == TokenType.NUMBER:
            v = Number(self.curr().value)
            self.next()
            return v
