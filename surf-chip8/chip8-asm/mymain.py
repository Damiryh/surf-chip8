from mytoken import *
from myast import *
from myparser import *

class Env:
    def __init__(self, offset = 0):
        self.c = dict()
        self.address = offset

    def define(self, name):
        self.c[name] = self.address

    def next(self, step=1):
        self.address += step

    def get(self, name):
        return self.c[name]



code = list()

try:
    with open('src.ch8', 'r') as inp:
        source = inp.read().strip()
    
    tokens = tokenize('src.ch8', source)
    p = Parser(tokens)
    ast = p.parse()
    env = Env()
    
    for i in range(len(ast)): ast[i].calculate(env)
    for i in range(len(ast)): ast[i].preprocess(env)
    for i in range(len(ast)): code += ast[i].generate(env)
    
except ChipSyntaxError as err:
    print(err)
    #print(*tokens, sep='\n')
    #print(*ast, sep='\n')

else:
    #print(*ast, sep='\n')
    #print(*map(hex, code))

    with open('out.bin', 'wb') as out:
        out.write(bytes(code))

    print('Done!')
