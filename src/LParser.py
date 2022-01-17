from __future__ import annotations
import sys, getopt, os, re
from typing import Literal
from collections.abc import Iterable
import six

try:
    import anytree
    from anytree import Node as TreeNode, RenderTree
    from anytree.exporter import JsonExporter, UniqueDotExporter
except ModuleNotFoundError as e:
    print("'anytree' not imported.")
    print(e)
    anytree = None

try:
    import pydot
except ModuleNotFoundError as e:
    print("'pydot' not imported.")
    print(e)
    pydot = None

try:
    from sly import Parser
    from sly.yacc import YaccError
except ModuleNotFoundError as e:
    print("'sly' not imported")
    print(e)
    print("try 'pip install sly'")
    exit(3)

try:
    from LLexer import LLexer
except ImportError as e:
    print("Can't import 'LLexer'.")
    print("Put it near the 'LParser'")
    exit(3)

##########################
##### UTIL FUNCTIONS #####
##########################
def iterable(arg):
    return (
        isinstance(arg, Iterable)
        and not isinstance(arg, six.string_types)
    )

def find_column(text, token):
    last_cr = text.rfind('\n', 0, token.index)
    if last_cr < 0:
        last_cr = 0
    column = (token.index - last_cr)
    return column

def get_trailing_number(s:str):
    m = re.search(r"^([a-zA-Z]*)(\d*)$", s)
    name = m.group(1)
    number = m.group(2)
    return name, int(number) if number else 0

##########################
#####    AST ATOM    #####
##########################
class Node:
    def __init__(self, name, value:tuple[Node]|Node|str|int):
        self.name = name
        self.value = (value,) if isinstance(value, Node) else value

    def __repr__(self):
        return f"<{__name__}.Node[{self.name!r}] object at {hex(id(self))}>"

    def __str__(self, level=0):
        indent = 2
        ret = " "*indent*level + f"Node[{self.name!r}]"
        if iterable(self.value):
            ret += "\n"
            for child in self.value:
                ret += child.__str__(level+1)
        else:
            ret += f":{self.value}\n"
        return(ret)

    def __getattr__(self, __name: str):
        if iterable(self.value):
            name, number = get_trailing_number(__name)
            approp_childs = [node for node in self.value if isinstance(node, Node) and node.name == name]
            approp_childs_l = len(approp_childs)
            if approp_childs_l == 0:
                raise AttributeError(f"Node[{self.name}] object has no attribute {name!r}")
            if number >= approp_childs_l:
                raise AttributeError(f"Node[{self.name}] object has a total of {approp_childs_l} attributes {name!r}")
            return approp_childs[number]
        raise AttributeError(f"Node[{self.name}] object has no childs. Use 'Node::value'")


def dump_ast(ast: Node, format: Literal["txt", "json"]="txt", dump_image:str|None=""):
    def build_tree(node, parent=None):
        if iterable(node.value):
            tree_node = TreeNode(node.name, parent=parent)
            for child in node.value:
                build_tree(child, tree_node)
            return tree_node
        else:
            TreeNode(f"{node.name}[{node.value}]", parent=parent)
    tree = build_tree(ast)

    if pydot is not None:
        if dump_image:
            dot_str = "\n".join(UniqueDotExporter(tree))
            graph = pydot.graph_from_dot_data(dot_str)[0]
            try:
                graph.write_png(dump_image)
            except Exception as e:
                print(e)
                print("Install Graphviz and specify 'dot' executable in your PATH")
    else:
        print("'pydot' not found. Try 'pip install pydot'")

    if format == "txt":
        output = ""
        for pre, _, node in RenderTree(tree):
            output += f"{pre}{node.name}\n"
        return output
    elif format == "json":
        exporter = JsonExporter(indent=2, sort_keys=False)
        return exporter.export(tree)


##########################
#####     PARSER     #####
##########################
class LParser(Parser):
    tokens = LLexer.tokens

    precedence = (
        ("nonassoc", "IFX"),
        ("nonassoc", "ELSE"),
        ("right",    "OR"),
        ("right",    "AND"),
        ("right",    "NOT"),
        ("nonassoc", "EQU", "NEQ", "LEQ", "LES", "GEQ", "GRT"),
        ("left",     "ADD", "SUB"),
        ("left",     "MUL", "DIV"),
        ("right",    "NEG"),
        ("right",    "POW"),
    )

    def __init__(self, text):
        self.warns = []
        self.text = text

    @_("program")
    def main_test(self, p):
        main_node = next((node for node in p[0].value if node.FNAME.value == "main"), None)
        if main_node is None:
            self.warns.append("main function is not defined")
        return p[0]

    #===== ROOT RULE =====#
    @_("definition def_list")
    def program(self, p):
        if p.def_list:
            return Node("PROG", (p.definition, *p.def_list))
        else:
            return Node("PROG", p.definition)

    #===== Sequence of definitions =====#
    @_("definition def_list")
    def def_list(self, p):
        if p.def_list:
            return p.definition, *p.def_list
        else:
            return p.definition,
    
    @_("")
    def def_list(self, p):
        pass

    #===== Only functions can be defined globally =====# 
    @_("fdef")
    def definition(self, p):
        return p[0]

    #===== Function represented as header and statement =====#
    @_("f_head statement")
    def fdef(self, p):
        return Node("FDEF", (*p.f_head, Node("FBODY", p.statement)))

    #===== Header is key-token, function name =====#
    #===== and arg list in parentheses        =====#
    @_("FUNC IDENT LPAREN arg_list RPAREN")
    def f_head(self, p):
        return Node("FNAME", p[1]), Node("FARGS", p.arg_list)

    #===== Header is key-token, function name =====#
    #===== and empty parentheses (no args)    =====#
    @_("FUNC IDENT LPAREN RPAREN")
    def f_head(self, p):
        return Node("FNAME", p[1]),

    #===== Arg list is list of decalrations =====#
    @_("decl")
    def arg_list(self, p):
        return p.decl,

    @_("decl COMMA arg_list")
    def arg_list(self, p):
        return p.decl, *p.arg_list

    @_("IDENT")
    def decl(self, p):
        return Node("FARG", p[0])

    #===== Statement is single operation ended with  =====#
    #===== semicolon, or comples block of operations =====#
    @_("operation SEMICOLON", "block")
    def statement(self, p):
        return p[0]

    #===== Block is list of statements inside curly brackets =====#
    @_("LCURLY stm_list RCURLY")
    def block(self, p):
        return p.stm_list

    @_("statement stm_list")
    def stm_list(self, p):
        if p.stm_list:
            if iterable(p.statement):
                return (*p.statement, *p.stm_list)
            else:
                return  p.statement, *p.stm_list
        else:
            return p.statement,

    @_("")
    def stm_list(self, p):
        pass

    #===== If statement =====#
    @_("IF LPAREN condition RPAREN statement %prec IFX")
    def statement(self, p):
        return Node("IF", (
            Node("COND", p.condition),
            Node("BRANCH", p.statement)
        ))

    #===== If else statement =====# 
    @_("IF LPAREN condition RPAREN statement ELSE statement")
    def statement(self, p):
        return Node("IF", (
            Node("COND", p.condition),
            Node("BRANCH", p.statement0),
            Node("BRANCH", p.statement1)
        ))

    #===== While statement =====#
    @_("WHILE LPAREN condition RPAREN statement")
    def statement(self, p):
        return Node("WHILE", (
            Node("COND", p.condition),
            Node("BRANCH", p.statement)
        ))

    #===== operation can be just a variable declaration =====#
    @_("LET IDENT")
    def operation(self, p): # declaration
        return Node("VARDECL", Node("NAME", p[1]))

    #===== operation can be a variable assignment =====#
    @_("IDENT ASSIGN expression")
    def operation(self, p): # assignment
        return Node("VARASGN", (Node("VAR", p[0]), p[2]))

    #===== operation can be a variable declare assignment =====#
    @_("LET IDENT ASSIGN expression")
    def operation(self, p): # assignment
        return (
            Node("VARDECL", Node("NAME", p[1])),
            Node("VARASGN", (Node("VAR", p[1]), p[3]))
        )

    #===== Operation can be read statement =====#
    @_("READ LPAREN IDENT RPAREN")
    def operation(self, p):
        return Node("READ", Node("VAR", p[2]))

    @_("WRITE LPAREN expression RPAREN",
       "WRITE LPAREN condition  RPAREN")
    def operation(self, p):
        return Node("WRITE", p[2])

    #===== Operation can be return statement =====#
    @_("RETURN expression")
    def operation(self, p):
        return Node("RETURN", p.expression)

    #===== Operation can be an expression =====#
    @_("expression")
    def operation(self, p): # expression
        return p.expression
    
    #===== Operation can be a condition =====#
    @_("condition")
    def operation(self, p): # expression
        return p.condition

    #===== Expression can be binary operation =====#
    #===== with two expressions               =====#
    @_("expression ADD expression")
    def expression(self, p):
        return Node("ADD", (p.expression0, p.expression1))
    
    @_("expression SUB expression")
    def expression(self, p):
        return Node("SUB", (p.expression0, p.expression1))
    
    @_("expression MUL expression")
    def expression(self, p):
        return Node("MUL", (p.expression0, p.expression1))
    
    @_("expression DIV expression")
    def expression(self, p):
        return Node("DIV", (p.expression0, p.expression1))
    
    @_("expression POW expression")
    def expression(self, p):
        return Node("POW", (p.expression0, p.expression1))
    
    #===== Expression can be unary minus operation =====#
    #===== with expression                         =====#
    @_("SUB expression %prec NEG")
    def expression(self, p):
        return Node("NEG", p.expression)

    #===== Function call with args (a.k.a. expresion list) =====#
    @_("IDENT LPAREN exp_list RPAREN")
    def expression(self, p):
        return Node("FCALL", (Node("FNAME", p[0]), *p.exp_list))

    #===== Function call without args =====#
    @_("IDENT LPAREN RPAREN")
    def expression(self, p):
        return Node("FCALL", Node("FNAME", p[0]))

    #===== Expression list can be a single expression =====#
    @_("expression")
    def exp_list(self, p):
        return p.expression,

    #===== Expression list can be expression and =====#
    #===== expression list separated with comma  =====#
    @_("expression COMMA exp_list")
    def exp_list(self, p):
        return p.expression, *p.exp_list

    #===== Expression parentheses =====#
    @_("LPAREN expression RPAREN")
    def expression(self, p):
        return p.expression

    #===== Bool operation with conditions =====#
    @_("condition AND condition")
    def condition(self, p):
        return Node("AND", (p.condition0, p.condition1))

    @_("condition OR condition")
    def condition(self, p):
        return Node("OR", (p.condition0, p.condition1))

    @_("NOT condition")
    def condition(self, p):
        return Node("NOT", p.condition)

    @_("LPAREN condition RPAREN")
    def condition(self, p):
        return p.condition

    #===== Expression comparisons operators =====#
    @_("expression EQU expression")
    def condition(self, p):
        return Node("EQU", (p.expression0, p.expression1))
    
    @_("expression NEQ expression")
    def condition(self, p):
        return Node("NEQ", (p.expression0, p.expression1))
    
    @_("expression LEQ expression")
    def condition(self, p):
        return Node("LEQ", (p.expression0, p.expression1))
    
    @_("expression LES expression")
    def condition(self, p):
        return Node("LES", (p.expression0, p.expression1))
    
    @_("expression GEQ expression")
    def condition(self, p):
        return Node("GEQ", (p.expression0, p.expression1))
    
    @_("expression GRT expression")
    def condition(self, p):
        return Node("GRT", (p.expression0, p.expression1))

    #===== Expression can be a variable =====#
    @_("IDENT")
    def expression(self, p):
        return Node("VAR", p[0])

    #===== Expression can be a number =====#
    @_("number")
    def expression(self, p):
        return p[0]

    #===== Number can be integer or float =====#
    @_("INT")
    def number(self, p):
        return Node("INT", p[0])

    @_("FLOAT")
    def number(self, p):
        return Node("FLOAT", p[0])

    def error(self, p):
        if p:
            row = p.lineno
            col = find_column(self.text, p)

            if p.type == "ERROR":
                msg = f"Unknown literal {p.value[0]!r} at {row}:{col}"
            else:
                msg = f"Syntax error. Unexpected token {p.type}[{p.value!r}] at {row}:{col}"
        else:
            msg = "Syntax error at EOF."
        raise YaccError(msg)

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
        'fileformat': None,
        'outputimagefile': None
    }
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            print_help()
            exit(0)
        elif opt in ["-f", "--format"]:
            if options['fileformat']:
                print(f"Format already set as {options['fileformat']!r} before.")
                print(f"Remove redundant '-f' or '--format' flags")
                exit(1)
            if opt == "-f" and arg == "ormat":
                print("Unknown format 'ormat'. You probably meant to use the '--format' (doubledashed).")
                exit(1)
            if arg == "":
                print("Format can't be empty")
                exit(1)
            if arg not in ["txt", "json"]:
                print(f"Unknown format {arg!r}. Only 'txt' or 'json' are allowed.")
                exit(1)
            options['fileformat'] = arg
    if not options['fileformat']:
        options['fileformat'] = "txt"
    for opt, arg in opts:
        if opt in ["-o", "--output"]:
            if options['outputfile']:
                print(f"Format already set as {options['outputfile']!r} before.")
                print(f"Remove redundant '-f' or '--format' flags")
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
            options['outputfile'] = f"{arg}"
        if opt in ["-i", "--image-output"]:
            if options['outputimagefile']:
                print(f"Image output file already set as {options['outputimagefile']!r} before.")
                print(f"Remove redundant '-i' or '--image-output' flags")
                exit(1)
            if opt == "-i" and arg == "mage-output":
                print(f"Image output file is 'mage-output.png'. You probably meant to use the '--image-output' (doubledashed)")
                accept = input(f"Use 'mage-output.png' as image output file? (y/n): ")
                while(accept != "y"):
                    if accept == "n":
                        exit(1)
                    else:
                        print(f"Unknown answer {accept!r}")
                        accept = input(f"Use 'mage-output.png' as image output file? (y/n): ")
            elif arg == "":
                print("Image output file can't be empty")
                exit(1)
            options['outputimagefile'] = f"{arg}.png"
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
        print("Input file not specified. Use 'LParser.py -h' for help")
        exit(1)

    return options

def print_help():
    print("NAME:")
    print("\tLParser - parser for non-exsitend L lang")
    
    print("SYNOPSIS:")
    print("\tLParser [options]... input_file")
    
    print("DESCRIPTION")
    print("\tWrite arguments to the standard output.\n")
    print("\tOptions:")
    print("\t  -h,    --help\t\t\tDisplay info about program.")
    print("\t  -f[=], --format[=]\t\tOutput text format. \"txt\" (default) and \"json\" are allowed.")
    print("\t  -o[=], --output[=]\t\tOutput file. If not specified, printed into stdout.")
    print("\t  -i[=], --image-output[=]\tImage output file. If not specified, image not generated.\n")

    print("\tArguments:")
    print("\t  input_file\t\t\tRequired. File with L lang source to be parsed.\n")


##########################
####### MAIN FRAME #######
##########################
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

        try:
            ast = parser.parse(lexer.tokenize(text))
        except YaccError as error:
            print(error)
            exit(0)

        if anytree is not None:
            output_string = dump_ast(ast, format=options['fileformat'], dump_image=options['outputimagefile'])
        else:
            print("'anytree' not found. Try 'pip install anytree'.")
            print("simple representation will be printed in txt")
            options["fileformat"] = "txt"
            output_string = str(ast)

        if options['outputfile']:
            try:
                output_fp = open(f"{options['outputfile']}.{options['fileformat']}", "x", encoding="utf-8")
            except FileExistsError:
                print(f"'{options['outputfile']}.{options['fileformat']}' alreasy exist")
                while((answer:=input("Rewrite file? (y/n): ")) != "y"):
                    if answer == "n":
                        print("Output printed into stdout")
                        print(output_string)
                        output_fp = None
                        break
                    else:
                        print(f"Unknown answer {answer!r}")
                else:
                    output_fp = open(f"{options['outputfile']}.{options['fileformat']}", "w", encoding="utf-8")
            except IOError as error:
                print(error)
                exit(0)

            if output_fp:
                with output_fp:
                    output_fp.write(output_string)
                    print(f"Abstract Syntax Tree printed into {os.getcwd()}{os.path.sep}{options['outputfile']}.{options['fileformat']}")
        else:
            print(output_string)

        if parser.warns:
            for warn in parser.warns:
                print(f"WARNING::{warn}")
