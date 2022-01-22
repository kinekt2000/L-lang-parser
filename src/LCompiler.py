import sys, getopt, os

from sly.yacc import YaccError

from LLexer import LLexer
from LParser import LParser, Node


##########################
##### UTIL FUNCTIONS #####
##########################
def named(obj_, name_):
    return isinstance(obj_, Node) and obj_.name == name_


##########################
#####    COMPILER    #####
##########################
def ast_node(func):
    def wrapper(self, node, level=0):
        if node.name != func.__name__:
            raise LCompilerError(f"Node[{node.name!r}] passed into {func.__name__}")
        code = func(self, node, level or 0)
        if isinstance(code, str) and level is not None:
            return [code]
        return code
    return wrapper


class LCompilerError(Exception):
    def __init__(self, *args: object):
        super().__init__(*args)

class LCompiler:
    indent = " "*4

    def __init__(self) -> None:
        self.lines = []
        self.args = 0

    def compile(self, ast: Node):
        self.lines = self.PROG(ast)
        return self.lines

    def __bin_op(self, e1, e2, op):
        return f"({getattr(self, e1.name)(e1, None)}{op}{getattr(self, e2.name)(e2, None)})"

    def __un_op(self, e, op):
        return f"{op}{getattr(self, e.name)(e, None)}"

    @ast_node
    def PROG(self, node, level=0):
        lines = []
        lines.extend(["import sys", "", ""])
        fdefs = [node for node in node.value if named(node, "FDEF")]

        for fdef in fdefs:
            lines.extend(self.FDEF(fdef, level))
        lines.extend([
            "if __name__ == '__main__':",
            self.indent+"try:",
            self.indent*2+f"print(f\"returned: {{main(*sys.argv[1:{self.args+1}]) or 0}}\")",
            self.indent+"except NameError:",
            self.indent*2+"print(\"Entry point 'main' not defined\")",
            ""
        ])
        return lines

    @ast_node
    def FDEF(self, node, level=0):
        args = [arg_node.value for arg_node in node.FARGS.value or [] if named(arg_node, "FARG")]
        if node.FNAME.value == "main":
            args = [f'{arg}=0' for arg in args]
            self.args = len(args)
        return [
            f"{self.indent*level}def {node.FNAME.value}({','.join(args)}):",
            *self.FBODY(node.FBODY, level),
            "", ""
        ]

    @ast_node
    def FBODY(self, node, level=0):
        if node.value is None:
            return f"{self.indent*(level+1)}pass"
        lines = []
        for op in node.value:
            lines.extend(getattr(self, op.name)(op, level+1))
        return lines

    @ast_node
    def VARASGN(self, node, level):
        exp = node.value[1]
        return f"{self.indent*level}{node.VAR.value} = {getattr(self, exp.name)(exp, None)}"

    @ast_node
    def IF(self, node, level):
        cond = node.COND.value[0]
        branch_then = node.BRANCH0
        branch_else = node.BRANCH1
        lines = [f"{self.indent*level}if {getattr(self, cond.name)(cond, None)}:{'pass' if branch_then.value is None else ''}"]
        if branch_then.value is not None:
            lines.extend(self.BRANCH(branch_then, level))

        if branch_else.value is not None:
            lines.extend([
                f"{self.indent*level}else:",
                *self.BRANCH(branch_else, level)
            ])
        return lines

    @ast_node
    def BRANCH(self, node, level):
        lines = []
        for op in node.value:
            lines.extend(getattr(self, op.name)(op, level+1))
        return lines

    @ast_node
    def WHILE(self, node, level):
        cond = node.COND.value[0]
        branch = node.BRANCH
        lines = [f"{self.indent*level}if {getattr(self, cond.name)(cond, None)}:{'pass' if branch.value is None else ''}"]
        if branch.value is not None:
            lines.extend(*self.BRANCH(branch, level))
        return lines

    @ast_node
    def READ(self, node, level):
        return [
            f"{self.indent*level}{node.VAR.value} = input()",
            f"{self.indent*level}try:",
            f"{self.indent*(level+1)}{node.VAR.value} = int({node.VAR.value})",
            f"{self.indent*level}except ValueError:",
            f"{self.indent*(level+1)}{node.VAR.value} = float({node.VAR.value})",
        ]
            

    @ast_node
    def WRITE(self, node, level):
        exp = node.value[0]
        return f"{self.indent*level}print({getattr(self, exp.name)(exp, None)})"

    @ast_node
    def RETURN(self, node, level):
        exp = node.value[0]
        return f"{self.indent*level}return {getattr(self, exp.name)(exp, None)}"

    @ast_node
    def VAR(self, node, level):
        return f"{self.indent*level}{node.value}"

    @ast_node
    def FCALL(self, node, level):
        name = node.FNAME.value
        args = [getattr(self, exp.name)(exp, None) for exp in node.value[1:]]
        return f"{self.indent*level}{name}({', '.join(args)})"

    @ast_node
    def ADD(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '+')}"

    @ast_node
    def SUB(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '-')}"

    @ast_node
    def MUL(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '*')}"

    @ast_node
    def DIV(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '/')}"

    @ast_node
    def POW(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '**')}"

    @ast_node
    def NEG(self, node, level):
        return f"{self.indent*level}{self.__un_op(node.value[0], '-')}"

    @ast_node
    def AND(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], ' and ')}"

    @ast_node
    def OR(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], ' or ')}"

    @ast_node
    def NOT(self, node, level):
        return f"{self.indent*level}{self.__un_op(node.value[0], 'not ')}"

    @ast_node
    def EQU(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '==')}"

    @ast_node
    def NEQ(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '!=')}"

    @ast_node
    def LEQ(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '<=')}"

    @ast_node
    def LES(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '<')}"

    @ast_node
    def GEQ(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '>=')}"

    @ast_node
    def GRT(self, node, level):
        return f"{self.indent*level}{self.__bin_op(node.value[0], node.value[1], '>')}"

    @ast_node
    def INT(self, node, level=0):
        return f"{self.indent*level}{node.value}"
    
    @ast_node
    def FLOAT(self, node, level):
        return f"{self.indent*level}{node.value}"


##########################
#### ARGUMENTS PARSER ####
##########################
def parse_cliargs(shortopts:str="", longopts:list[str]=[]):
    argv = sys.argv[1:]
    options = []
    arguments = []

    while(True):
        opts, argv = getopt.getopt(argv, shortopts, longopts)
        options.extend(opts)
        if not argv: break
        arguments.append(argv.pop(0))

    return options, arguments


def make_options(opts, args):
    options={
        'inputfile': None,
        'outputfile': None,
    }
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            print_help()
            exit(0)
    for opt, arg in opts:
        if opt in ["-o", "--output"]:
            if options['outputfile']:
                print(f"Output file already set as {options['outputfile']!r} before.")
                print(f"Remove redundant '-o' or '--output' flags")
                exit(1)
            if opt == "-o" and arg == "utput":
                print(f"Output file is 'utput.{options['fileformat']}'. You probably meant to use the '--output' (doubledashed)")
                accept = input(f"Use 'utput{options['fileformat']}' as output file? (y/n): ")
                while(accept != "y"):
                    if accept == "n":
                        exit(1)
                    else:
                        print(f"Unknown answer {accept!r}")
                        accept = input("Use 'utput' as output file? (y/n): ")
            elif arg == "":
                print("Output file can't be empty")
                exit(1)
            options['outputfile'] = f"{arg}.py"
    if args:
        inputfile = args[0]
        if inputfile == "elp":
            print(f"Input file is 'elp'. You probably meant to use the '--help' (doubledashed)")
            accept = input(f"Use 'elp' as input file? (y/n): ")
            while(accept != "y"):
                if accept == "n":
                    exit(1)
                else:
                    print(f"Unknown answer {accept!r}")
                    accept = input("Use 'elp' as input file? (y/n): ")
        if inputfile == "":
            print("Input file can't be empty")
            exit(1)
        options['inputfile'] = inputfile
    else:
        print("Input file not specified. Use 'LCompiler.py -h' for help")
        exit(1)

    return options

def print_help():
    print("NAME:")
    print("\tLCompiler - compiler into python for non-exsitend L lang")
    
    print("SYNOPSIS:")
    print("\tLCompiler [options]... input_file")
    
    print("DESCRIPTION:")
    print("\tWrite arguments to the standard output.\n")
    print("\tOptions:")
    print("\t  -h,    --help\t\t\tDisplay info about program.")
    print("\t  -o[=], --output[=]\t\tOutput file. If not specified, printed into stdout.")

    print("\tArguments:")
    print("\t  input_file\t\t\tRequired. File with L lang source to be compiled.\n")


if __name__ == "__main__":
    try:
        opts, args = parse_cliargs("hf:o:i:", ["help", "format=", "output=", "image-output="])
    except getopt.GetoptError as e:
        print(e)
        print("use 'LParser -h' for help")
        exit(2)

    options = make_options(opts, args)

    try:
        input_fp = open(options['inputfile'], "r")
    except IOError as error:
        print(error)
        exit(0)

    with input_fp:
        text = "".join(input_fp.readlines())
        lexer = LLexer()
        parser = LParser(text)
        compiler = LCompiler()

        try:
            ast = parser.parse(lexer.tokenize(text))
        except YaccError as error:
            print(error)
            exit(0)

        lines = compiler.compile(ast)

        if options['outputfile']:
            os.makedirs(os.path.dirname(f"{options['outputfile']}"), exist_ok=True)
            try:
                output_fp = open(f"{options['outputfile']}", "x", encoding="utf-8")
            except FileExistsError:
                print(f"'{options['outputfile']}' alreasy exist")
                while((answer:=input(f"Rewrite '{options['outputfile']}'? (y/n): ")) != "y"):
                    if answer == "n":
                        print("Output printed into stdout")
                        print(os.linesep.join(lines))
                        output_fp = None
                        break
                    else:
                        print(f"Unknown answer {answer!r}")
                else:
                    output_fp = open(f"{options['outputfile']}", "w", encoding="utf-8")
            except IOError as error:
                print(error)
                exit(0)

            if output_fp:
                with output_fp:
                    for line in lines:
                        output_fp.write(line + "\n")
                    print(f"Code compiled into {os.path.abspath(output_fp.name)}")
        else:
            print(os.linesep.join(lines))

        if parser.warns:
            for warn in parser.warns:
                print(f"WARNING::{warn}")
