from dataclasses import dataclass

SYMBOLS = set(".,:$&<>{}()[]@")
HEX = set('0123456789abcdef')
MNEMONICS = {
    'cls', 'ret', 'jp', 'call', 'se', 'sne', 'ld', 'add',
    'ld', 'or', 'xor', 'and', 'sub', 'shr', 'subn', 'shl',
    'sne', 'rnd', 'drw', 'skp', 'sknp'
}

REGS = { 'I', 'F', 'B', 'ST', 'DT' }

class ChipAsmError(BaseException):
    def __init__(self, owner, location, message):
        super().__init__(self)
        self.owner = owner
        self.location = location
        self.message = message

    def __repr__(self):
        pos, line, column = self.location
        return f"{pos}:{line}:{column} <{self.owner}> {self.message}."

    def __str__(self):
        return self.__repr__()

@dataclass
class Token:
    type_: str
    pos: int
    line: int
    column: int
    value: str

    def __repr__(self):
        return f"{self.type_} '{self.value}'"
    
    def locate(self):
        return (self.pos, self.line, self.column)

    def get(self):
        if self.type_ == "DEC":
            return int(self.value, 10)
        elif self.type_ == "HEX":
            return int(self.value, 16)
        else:
            return self.value


def trim_left(src, pos, line, column):
    for i in range(pos, len(src)):
        if src[i] == '\n':
            column = 1
            line += 1
        if not src[i].isspace(): break
    else: i = len(src)
    return (None, i, line, column)


def tokenize_word(src, pos, line, column):
    for i in range(pos, len(src)):
        if not (src[i].isalpha() or src[i].isdigit()): break
    else: i = len(src)

    token = Token("IDENTIFIER", pos, line, column, src[pos:i])

    if token.value in MNEMONICS:
        token.type_ = 'MNEMONIC'
    elif token.value in REGS:
        token.type_ = 'REG'
    
    return (token, i, line, column + len(token.value))


def tokenize_comment(src, pos, line, column):
    for i in range(pos, len(src)):
        if src[i] == '\n': break
    else: i = len(src)

    token = Token('COMMENT', pos, line, column, src[pos:i])
    return (token, i, line, column + len(token.value))


def tokenize_symbol(src, pos, line, column):
    token = Token('SYMBOL', pos, line, column, src[pos])
    return token, pos+1, line, column+1


def tokenize_dec(src, pos, line, column):
    for i in range(pos, len(src)):
        if not src[i].isdigit(): break
    else: i = len(src)

    if src[i].isalpha():
        raise ChipAsmError("Tokenizer", (pos, line, column), "Wrong decimal")

    token = Token('DEC', pos, line, column, src[pos:i])
    return (token, i, line, column + len(token.value))


def tokenize_hex(src, pos, line, column):
    for i in range(pos+1, len(src)):
        if not src[i].lower() in HEX: break
    else: i = len(src)

    if src[i].isalpha():
        raise ChipAsmError("Tokenizer", (pos, line, column), "Wrong hexadecimal")

    token = Token('HEX', pos, line, column, src[pos+1:i])
    return (token, i, line, column + len(token.value))


def tokenize(src):
    tokens = []; pos = 0; line = 1; column = 1;
    
    while True:
        token, pos, line, column = trim_left(src, pos, line, column)
        if pos >= len(src): break
        if src[pos] == '#':
            token, pos, line, column = tokenize_hex(src, pos, line, column)
        elif src[pos] == ';':
            _, pos, line, column = tokenize_comment(src, pos, line, column)
        elif src[pos].isdigit():
            token, pos, line, column = tokenize_dec(src, pos, line, column)
        elif src[pos].isalpha():
            token, pos, line, column = tokenize_word(src, pos, line, column)
        elif src[pos] in SYMBOLS:
            token, pos, line, column = tokenize_symbol(src, pos, line, column)
        else:
            raise ChipAsmError("Tokenizer", (pos, line, column), f"Unknown symbol '{src[pos]}'")
        
        if token: tokens.append(token)

    tokens.append(Token("EOF", pos, line, column, "EOF"))
    return tokens

class Environment:
    def __init__(self, offset=0, consts=dict()):
        self.address = offset
        self.consts = consts

    def define(self, name):
        self.consts[name] = self.address

    def next(self, step):
        self.address += step

    def get(self, token):
        if not (token.value in self.consts.keys()):
            raise ChipAsmError("Preprocessor", token.locate(), f"Unknown identifier '{token.value}'")
        return self.consts[token.value]

@dataclass
class Argument:
    type_: str
    value_: Token

    def __init__(self, type_, value_=None):
        self.type_ = type_
        self.value_ = value_
    
    def __repr__(self):
        return f"{self.type_} <{self.value_}>" if self.value_ else f"{self.type_}"

    def preprocess(self, env):
        if self.value_ and self.value_.type_ == "IDENTIFIER":
            self.value_.type_ = "DEC"
            identifier = self.value_
            self.value_.value = str(env.get(identifier))
            

class Statement:
    def calculate_address(self, env): pass
    def preprocess(self, env): pass


class Label(Statement):
    def __init__(self, name):
        self.name = name

    def calculate(self, env):
        env.define(self.name)

    def __repr__(self):
        return f"LABEL '{self.name}'"


class Instruction(Statement):
    def __init__(self, mnemonic, *args):
        self.mnemonic = mnemonic
        self.args = list(args)

    def append(self, arg):
        self.args.append(arg)

    def calculate(self, env):
        env.next(2)
    
    def preprocess(self, env):
        for i in range(len(self.args)):
            self.args[i].preprocess(env)
    
    def __repr__(self):
        s = f"INSTRUCTION {self.mnemonic}\n"
        for arg in self.args:
            s += f"\t{arg}\n"
        return s[:-1]

class Directive(Statement):
    def __init__(self, name, *args):
        self.name = name
        self.args = list(args)
    
    def append(self, arg):
        self.args.append(arg)

    def calculate(self, env):
        if self.name == "org":
            if (len(self.args) != 1):
                raise ChipAsmError(
                    "Generator",
                    self.args[-1].value_.locate(),
                    f"Directive ORG requires ADDRESS only"
                )
            
            if self.args[0].type_ != "ADDRESS" or self.args[0].value_.type_ == "IDENTIFIER":
                raise ChipAsmError(
                    "Generator",
                    self.args[0].value_.locate(),
                    f"Wrong argument for directive ORG"
                )
            env.address = self.args[0].value_.get()
    
    def preprocess(self, env):
        for i in range(len(self.args)):
            self.args[i].preprocess(env)
    
    def __repr__(self):
        s = f"DIRECTIVE {self.name}\n"
        for arg in self.args:
            s += f"\t{arg}\n"
        return s[:-1]
        
class Parser:
    def __init__(self, tokens, ast):
        self.tokens = tokens
        self.ast = ast
        self.pos = 0
    
    def parse(self):
        self.pos = 0

        while self.current().type_ != "EOF":
            self.ast.append(self.statement())

        return self.ast
    
    def current(self):
        return self.tokens[self.pos]
        
    def check(self, type_, value=None):
        curr = self.current()
        return (curr.type_ == type_) and ((value == None) or (curr.value == value))
    
    def match(self, type_, value=None):
        if not self.check(type_, value): return False
        self.pos += 1
        return True

    def consume(self, type_, value=None):
        if not self.check(type_, value):
            if value == None:
                message = f"{type_} excepted"
            else:
                message = f"{type_} '{value}' excepted"
            
            raise ChipAsmError("Parser", self.current().locate(), message)
        self.pos += 1
    
    def statement(self):
        if self.check("MNEMONIC"): return self.instruction()
        elif self.check("IDENTIFIER"): return self.label()
        elif self.match("SYMBOL", '.'): return self.directive()
        else:
            raise ChipAsmError(
                "Parser",
                self.current().locate(),
                "Excepted MNEMONIC or label IDENTIFIER or DIRECTIVE"
            )

    def label(self):
        lbl = Label(self.current().value); self.pos += 1
        self.consume("SYMBOL", ':')
        return lbl

    def directive(self):
        drv = Directive(self.current().value); self.pos += 1
        if self.check("MNEMONIC") or self.check("IDENTIFIER") or self.check("SYMBOL", '.'):
            return drv

        drv.append(self.argument())
        while self.match("SYMBOL", ','):
            drv.append(self.argument())

        return drv
    
    
    def instruction(self):
        instr = Instruction(self.current().value); self.pos += 1
        if self.check("MNEMONIC") or self.check("IDENTIFIER"):
            return instr

        instr.append(self.argument())
        while self.match("SYMBOL", ','):
            instr.append(self.argument())

        return instr

    def argument(self):
        if self.match("SYMBOL", '['):
            arg = Argument("ADDRESS", self.value())
            self.consume("SYMBOL", ']')
        elif self.match("SYMBOL", '&'):
            arg = Argument("ADDRESS", self.value())
        elif self.match("SYMBOL", '@'):
            arg = Argument("REG", self.value())
        elif self.match("REG", 'ST'):
            arg = Argument("SOUND_TIMER")
        elif self.match("REG", 'DT'):
            arg = Argument("DELAY_TIMER")
        elif self.match("REG", 'I'):
            arg = Argument("INDEX")
        elif self.match("REG", 'F'):
            arg = Argument("FLAGS")
        elif self.match("REG", 'B'):
            arg = Argument("BCD")
        elif self.check("HEX") or self.check("DEC") or self.check("IDENTIFIER"):
            arg = Argument("BYTE", self.value())
        else:
            raise ChipAsmError("Parser", self.current().locate(), "Wrong argument")

        return arg

    def value(self):
        if self.check("HEX") or self.check("DEC") or self.check("IDENTIFIER"):
            v = self.current()
            self.pos += 1
            return v
        else:
            raise ChipAsmError("Parser", self.current().locate(), "Wrong value")

try:
    env = Environment()
    tokens = tokenize("start: place:")
    parser = Parser(tokens, [])
    ast = parser.parse()

    for i in range(len(ast)):
        ast[i].calculate(env)

    for i in range(len(ast)):
        ast[i].preprocess(env)
    
except ChipAsmError as e:
    print(e)

print(env.consts)
print(*tokens, sep='\n', end='\n\n')
print(*ast, sep='\n', end='\n\n')
