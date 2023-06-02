from .mytoken import tokenize, TokenizeError
from .myast import *
from .myparser import Parser
from .mymain import Env
import io

def assemble(snippet):
    try:
        env = Env()
        tokens = tokenize(snippet.name, snippet.source)
        parser = Parser(tokens);
        ast = parser.parse()

        code = list()
        
        length = len(ast)

        print(*ast, sep='\n')
        
        for i in range(length): ast[i].calculate(env)
        for i in range(length): ast[i].preprocess(env)
        for i in range(length): code += ast[i].generate(env)
        
    except TokenizeError as err:
        return False, None, str(err)
    except ChipSyntaxError as err:
        return False, None, str(err)
    else:
        return True, io.BytesIO(bytes(code)), "Success!"
