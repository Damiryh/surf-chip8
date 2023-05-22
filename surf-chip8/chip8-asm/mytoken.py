from dataclasses import dataclass
from enum import Enum

SYMBOLS = set('.,:@[](){}!')
HEX = set('0123456789abcdef')
MNEMONICS = {
    'cls', 'ret', 'jp', 'call',
    'se', 'sne', 'ld', 'add',
    'ld', 'or', 'xor', 'and',
    'sub', 'shr', 'subn', 'shl',
    'sne', 'rnd', 'drw', 'skp', 'sknp'
}
REGS = {'I', 'F', 'B', 'DT', 'ST', 'K'}

class TokenizeError(BaseException):
    def __init__(self, location, message):
        super().__init__(self)
        self.location = location
        self.message = message

    def __repr__(self):
        return f"{self.location} Tokenize error: {self.message}"

    def __str__(self):
        return self.__repr__()

@dataclass
class Location:
    source: str = "repl"
    pos: int = 0
    line: int = 1
    column: int = 1

    def step(self, ch='.'):
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def next(self, pos):
        return Location(self.source, pos, self.line, self.column + (pos - self.pos))

    def copy(self):
        return Location(self.source, self.pos, self.line, self.column)
    
    def __repr__(self):
        return f"{self.source},{self.pos}:{self.line}:{self.column}"

class TokenType(Enum):
    IDENTIFITER = 1
    MNEMONIC = 2
    KEYWORD = 3
    NUMBER = 4
    SYMBOL = 5
    COMMENT = 6
    UNKNOWN = 0
    EOF = -1

@dataclass
class Token:
    type: TokenType
    value: str
    location: Location

    def __repr__(self):
        return f"{self.type} <{self.value}>" if self.value else f"{self.type}"

def trim_space(source, start):
    end = start.copy()
    for i in range(start.pos, len(source)):
        if not source[i].isspace(): break
        end.step(source[end.pos])
    return None, end

def tokenize_word(source, start):
    end = start.next(len(source))
    for i in range(start.pos, len(source)):
        if not source[i].isalnum():
            end = start.next(i)
            break

    value = source[start.pos:end.pos]
    type_ = TokenType.IDENTIFITER
    
    if value in MNEMONICS:
        type_ = TokenType.MNEMONIC
    elif value in REGS:
        type_ = TokenType.KEYWORD

    return Token(type_, value, start), end

def tokenize_dec(source, start):
    end = start.next(len(source))
    for i in range(start.pos, len(source)):
        if not source[i].isdigit():
            end = start.next(i)
            if source[end.pos].isalpha(): raise TokenizeError(start, "Wrong DEC")
            break
    
    value = int(source[start.pos:end.pos])
    type_ = TokenType.NUMBER

    return Token(type_, value, start), end


def tokenize_hex(source, start):
    start.step()
    end = start.next(len(source))
    for i in range(start.pos, len(source)):
        if not source[i] in HEX:
            end = start.next(i)
            if source[end.pos].isalpha(): raise TokenizeError(start, "Wrong HEX")
            break
    
    value = int(source[start.pos:end.pos], 16)
    type_ = TokenType.NUMBER

    return Token(type_, value, start), end

def tokenize_symbol(source, start):
    token = Token(TokenType.SYMBOL, source[start.pos], start)
    end = start.copy(); end.step()
    return token, end


def tokenize_comment(source, start):
    start.step()
    end = start.next(len(source))
    for i in range(start.pos, len(source)):
        if source[i] == '\n':
            end = start.next(i)
            break
    return None, end


def tokenize(path, source):
    location = Location(path)
    tokens = list()
    token = None

    while True:
        _, location = trim_space(source, location)
        if location.pos >= len(source): break
        
        if source[location.pos].isalpha():
            token, location = tokenize_word(source, location)
        elif source[location.pos].isdigit():
            token, location = tokenize_dec(source, location)
        elif source[location.pos] == '#':
            token, location = tokenize_hex(source, location)
        elif source[location.pos] in SYMBOLS:
            token, location = tokenize_symbol(source, location)
        elif source[location.pos] == ';':
            token, location = tokenize_comment(source, location)
        
        if token: tokens.append(token)

    tokens.append(Token(TokenType.EOF, '', len(source)))
    return tokens

if __name__ == '__main__':
    try:            
        with open('test.asm', 'r') as f:
            tokens = tokenize('test.asm', f.read())
            print(*tokens, sep='\n')
    except TokenizeError as err:
        print(err)
    except KeyboardInterrupt:
        print()
