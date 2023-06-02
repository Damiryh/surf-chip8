from dataclasses import dataclass
from enum import Enum

class ChipSyntaxError(BaseException):
    def __init__(self, location, message):
        super().__init__(self)
        self.location = location
        self.message = message

    def __repr__(self):
        return f"{self.location} {self.message}"

    def __str__(self):
        return self.__repr__()

class Statement:
    def calculate(self, env): pass
    def preprocess(self, env): pass
    def generate(self, env): return []
    def locate(): return self.location

class Value: pass

class Identifier(Value):
    def __init__(self, name):
        self.name = name

    def get(self, env):
        return env.get(self.name)

    def __repr__(self):
        return f"ID '{self.name}'"

class Number(Value):
    def __init__(self, v):
        self.v = v

    def get(self, env):
        return self.v

    def __repr__(self):
        return f"NUM {self.v}"

class NullValue(Value):
    def get(self, v):
        return 0

    def __repr__(self):
        return f"NULL"

class ArgType(Enum):
    INDEX = 1
    DELAY_TIMER = 2
    SOUND_TIMER = 3
    BCD = 4
    KEY = 5
    FLAGS = 6
    REG = 7
    ADDRESS = 8
    BYTE = 9
    NIBBLE = 10
    INDEX_ADDR = 11

@dataclass
class Argument:
    type_: ArgType
    value: Value

    def __repr__(self):
        return f"{self.type_} <{self.value}>"

    def preprocess(self, env):
        if type(self.value) == Identifier:
            return Argument(self.type_, Number(self.value.get(env)))
        else: return self

    def get(self, env, requested_type=None):
        if requested_type and self.type_ != requested_type:
            print('err')
            return 0
        if self.type_ == ArgType.BYTE:
            return self.value.get(env) & 0xff
        elif self.type_ == ArgType.NIBBLE:
            return self.value.get(env) & 0x0f
        elif self.type_ == ArgType.REG:
            return self.value.get(env) & 0x0f
        elif self.type_ == ArgType.ADDRESS:
            return self.value.get(env) & 0xfff
        else: return 0 # Args without literal value
            

class Label(Statement):
    def __init__(self, name, location):
        self.location = location
        self.name = name

    def __repr__(self):
        return f"LABEL '{self.name}'"
    
    def calculate(self, env):
        env.define(self.name)

def nnn(opcode, addr):
    return opcode | (addr & 0xfff)

def n(opcode, nib):
    return opcode | (nib & 0xf)

def vx(opcode, r):
    return opcode | ((r & 0xf) << 8)

def vy(opcode, r):
    return opcode | ((r & 0xf) << 4)

def kk(opcode, v):
    return opcode | (v & 0xff)

def vx_vy(opcode, args, env):
    return vx(vy(opcode, args[1].get(env)), args[0].get(env))

def vx_kk(opcode, args, env):
    return vx(kk(opcode, args[1].get(env)), args[0].get(env))

def vx_vy_n(opcode, args, env):
    return kk(vx_vy(opcode, args, env), args[2].get(env))

def vx_src(opcode, args, env):
    return vx(opcode, args[0].get(env))

def vx_dest(opcode, args, env):
    return vx(opcode, args[1].get(env))

def narg(opcode, args, env): pass

INSTRUCTION_SET = {
    ('cls', tuple()): 0x00e0,
    ('ret', tuple()): 0x00ee,
    ('jp', (ArgType.ADDRESS,)): 0x1000,
    ('call', (ArgType.ADDRESS,)): 0x2000,
    ('se', (ArgType.REG, ArgType.BYTE)): 0x3000,
    ('sne', (ArgType.REG, ArgType.BYTE)): 0x4000,
    ('se', (ArgType.REG, ArgType.REG)): 0x5000,
    ('ld', (ArgType.REG, ArgType.BYTE)): 0x6000,
    ('add', (ArgType.REG, ArgType.BYTE)): 0x7000,
    ('ld', (ArgType.REG, ArgType.REG)): 0x8000,
    ('or', (ArgType.REG, ArgType.REG)): 0x8001,
    ('and', (ArgType.REG, ArgType.REG)): 0x8002,
    ('xor', (ArgType.REG, ArgType.REG)): 0x8003,
    ('add', (ArgType.REG, ArgType.REG)): 0x8004,
    ('sub', (ArgType.REG, ArgType.REG)): 0x8005,
    ('shr', (ArgType.REG, ArgType.REG)): 0x8006,
    ('subn', (ArgType.REG, ArgType.REG)): 0x8007,
    ('shl', (ArgType.REG, ArgType.REG)): 0x800e,
    ('sne', (ArgType.REG, ArgType.REG)): 0x9000,
    ('ld', (ArgType.INDEX, ArgType.ADDRESS)): 0xa000,
    ('jp', (ArgType.REG, ArgType.ADDRESS)): 0xb000,
    ('rnd', (ArgType.REG, ArgType.BYTE)): 0xc000,
    ('drw', (ArgType.REG, ArgType.REG, ArgType.NIBBLE)): 0xd000,
    ('skp', (ArgType.REG,)): 0xe09e,
    ('sknp', (ArgType.REG,)): 0xe0a1,
    ('ld', (ArgType.REG, ArgType.DELAY_TIMER)): 0xf007,
    ('ld', (ArgType.REG, ArgType.KEY)): 0xf00a,
    ('ld', (ArgType.DELAY_TIMER, ArgType.REG)): 0xf015,
    ('ld', (ArgType.SOUND_TIMER, ArgType.REG)): 0xf018,
    ('add', (ArgType.INDEX, ArgType.REG)): 0xf01e,
    ('ld', (ArgType.FLAGS, ArgType.REG)): 0xf029,
    ('ld', (ArgType.BCD, ArgType.REG)): 0xf033,
    ('ld', (ArgType.INDEX_ADDR, ArgType.REG)): 0xf055,
    ('ld', (ArgType.REG, ArgType.INDEX_ADDR)): 0xf065
}

class Instruction(Statement):
    def __init__(self, mnemo, location):
        self.mnemo = mnemo
        self.args = list()
        self.location = location

    def append(self, arg):
        self.args.append(arg)

    def __repr__(self):
        s = f"INSTRUCTION '{self.mnemo} ("
        for arg in self.args:
            s += arg.__repr__() + '; '
        s += ')'
        return s

    def calculate(self, env):
        env.next(2)

    def preprocess(self, env):
        try:
            for i, arg in enumerate(self.args):
                self.args[i] = arg.preprocess(env)
        except:
            raise ChipSyntaxError(self.location, f"Unknown {self.args[i].value}")

    def generate(self, env):
        form = (self.mnemo, tuple(map(lambda arg: arg.type_, self.args)))
        if not (form in INSTRUCTION_SET):
            raise ChipSyntaxError(self.location, f"Unknown INSTRUCTION '{self.mnemo}' or wrong args")

        opcode = INSTRUCTION_SET[form]

        if form[1] == tuple():
            pass
        elif form[1] == (ArgType.REG, ArgType.REG):
            opcode = vx_vy(opcode, self.args, env)
        elif form[1] == (ArgType.REG, ArgType.BYTE):
            opcode = vx_kk(opcode, self.args, env)
        elif form[1] == (ArgType.ADDRESS,):
            opcode = nnn(opcode, self.args[0].get(env))
        elif form[1] == (ArgType.REG, ArgType.REG, ArgType.NIBBLE):
            opcode = vx_vy_n(opcode, self.args, env)
        elif form[1][0] == ArgType.REG:
            opcode = vx(opcode, self.args[0].get(env))
        elif form[1][1] == ArgType.REG:
            opcode = vx(opcode, self.args[1].get(env))
        elif form[1][1] == ArgType.ADDRESS:
            opcode = nnn(opcode, self.args[1].get(env))

        return [(opcode >> 8) & 0xff, opcode & 0xff]
        

class Directive(Statement):
    def __init__(self, name, location):
        self.name = name
        self.args = list()
        self.location = location

    def append(self, arg):
        self.args.append(arg)

    def __repr__(self):
        s = f"DIRECTIVE '{self.name} ("
        for arg in self.args:
            s += arg.__repr__() + '; '
        s += ')'
        return s
    
    def calculate(self, env):
        form = (self.name, tuple(map(lambda arg: arg.type_, self.args)))
        
        if self.name == 'org' and form[1] == (ArgType.ADDRESS,):
            env.address = self.args[0].get(env)
        elif self.name == 'db' and len(self.args) != 0:
            env.next(len(self.args))
        else:
            raise ChipSyntaxError(self.location, f"Unknown DIRECTIVE '{self.name}' or wrong args here")

    def preprocess(self, env):
        for i, arg in enumerate(self.args):
            self.args[i] = arg.preprocess(env)

    def generate(self, env):
        code = list()
        
        if self.name == 'db':
            for arg in self.args:
                code.append(arg.get(env, requested_type=ArgType.BYTE))
        
        return code
        

