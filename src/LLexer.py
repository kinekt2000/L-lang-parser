import sys, getopt, os, json
from sly import Lexer

if sys.version_info < (3, 9):
    print("Please upgrade your Python version to 3.9 or higher")
    exit()

##########################
#####     LEXER      #####
##########################
class LLexer(Lexer):
    tokens = {
        IDENT, FUNC,
        INT, BININT, FLOAT,
        IF, ELSE, WHILE,
        READ, WRITE, RETURN, ASSIGN,
        POW, MUL, DIV, ADD, SUB,
        EQU, NEQ, LEQ, LES, GEQ, GRT,
        NOT, AND, OR,
        LCURLY, RCURLY, LPAREN, RPAREN,
        SEMICOLON, COMMA
    }
    ignore = '\t '

    @_(r"//.*")
    def COMMENT(self, t):
        pass

    # assign tokens
    FUNC   = r"function"
    IF     = r"if"
    ELSE   = r"else"
    WHILE  = r"while"
    READ   = r"read"
    WRITE  = r"write"
    RETURN = r"return"

    POW = r"\^"
    MUL = r"\*"
    DIV = r"/"
    ADD = r"\+"
    SUB = r"-"

    EQU = r"=="
    NEQ = r"!="
    LEQ = r"<="
    LES = r"<"
    GEQ = r">="
    GRT = r">"
    
    ASSIGN = r"="

    NOT = r"!"
    AND = r"&&"
    OR  = r"\|\|"

    LCURLY    = r"\{"
    RCURLY    = r"\}"
    LPAREN    = r"\("
    RPAREN    = r"\)"

    SEMICOLON = r";"
    COMMA     = r","

    @_(r"[0-9]*[.][0-9]+")
    def FLOAT(self, t):
        t.value = float(t.value)
        return t

    @_(r"0[bB][01]+")
    def BININT(self, t):
        t.value = int(t.value[2:], 2)
        return t

    @_(r"\d+")
    def INT(self, t):
        t.value = int(t.value)
        return t

    IDENT = r"[a-zA-Z_][a-zA-Z0-9_]*"

    @_(r"\n+")
    def newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        self.index += 1
        return t


##########################
##### UTIL FUNCTIONS #####
##########################
def find_column(text, token):
    last_cr = text.rfind('\n', 0, token.index)
    if last_cr < 0:
        last_cr = 0
    column = (token.index - last_cr)
    return column

def dump_tokens(tokens, format="txt"):
    if format == "txt":
        return '\n'.join(map(lambda token: str(token), tokens))
    elif format == "json":
        return json.dumps(list(map(lambda token: {
            "type":   token.type,
            "value":  token.value,
            "lineno": token.lineno,
            "index":  token.index,
        }, tokens)), indent=2)
    else:
        raise ValueError(f"Unknown format {format!r}. 'txt' and 'json' are allowed")


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
        if opt in ["-h", "--help"]:
            pass
        elif opt in ["-o", "--output"]:
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
            options['outputfile'] = f"{arg}"
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
    print("\tLLexer - lexer for non-exsitend L lang")
    
    print("SYNOPSIS:")
    print("\tLLexer [options]... input_file")
    
    print("DESCRIPTION:")
    print("\tWrite arguments to the standard output.\n")
    print("\tOptions:")
    print("\t  -h,    --help\t\t\tDisplay info about program.")
    print("\t  -f[=], --format[=]\t\tOutput text format. \"txt\" (default) and \"json\" are allowed.")
    print("\t  -o[=], --output[=]\t\tOutput file. If not specified, printed into stdout.\n")

    print("\tArguments:")
    print("\t  input_file\t\t\tRequired. File with L lang source to be tokenized.\n")

##########################
####### MAIN FRAME #######
##########################
if __name__ == "__main__":
    try:
        opts, args = parse_cliargs("hf:o:", ["help", "format=", "output="])
    except getopt.GetoptError as e:
        print(e)
        print("use 'LParser -h' for help")

    options = make_options(opts, args)

    lexer = LLexer()

    try:
        input_fp = open(options['inputfile'], "r")
    except IOError as error:
        print(e)
        exit(0)

    with input_fp:
        text = "".join(input_fp.readlines())
        lex = lexer.tokenize(text)
        errors = []
        tokens = []
        for token in lex:
            if token.type == "ERROR":
                errors.append(token)
            tokens.append(token)

        output_string = dump_tokens(tokens, options['fileformat'])

        if options['outputfile']:
            os.makedirs(os.path.dirname(f"{options['outputfile']}.{options['fileformat']}"), exist_ok=True)
            try:
                output_fp = open(f"{options['outputfile']}.{options['fileformat']}", "x")
            except FileExistsError:
                print(f"'{options['outputfile']}.{options['fileformat']}' alreasy exist")
                while((answer:=input(f"Rewrite '{options['outputfile']}.{options['fileformat']}'? (y/n): ")) != "y"):
                    if answer == "n":
                        print("Output printed into stdout")
                        print(output_string)
                        output_fp = None
                        break
                    else:
                        print(f"Unknown answer {answer!r}")
                else:
                    output_fp = open(f"{options['outputfile']}.{options['fileformat']}", "w")
            except IOError as error:
                print(error)
                exit(0)

            if output_fp:
                with output_fp:
                    output_fp.write(output_string)
                    print(f"Token List printed into {os.path.abspath(output_fp.name)}")
        else:
            print(output_string)
        
        if errors:
            print("\n===========ERRORS===========")
            for bad_token in errors:
                row = bad_token.lineno
                col = find_column(text, bad_token)
                print(f"ERROR::Unknown Literal {bad_token.value[0]!r}. At {row}:{col}")
