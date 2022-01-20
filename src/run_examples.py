import os

for i in range(1, 6):
    print(f"================= RUN EXAMPLE {i} =================")
    d = os.path.sep
    parser_exe = f".{d}src{d}LParser.py"
    lexer_exe = f".{d}src{d}LLexer.py"
    
    input = f".{d}examples{d}exmp{i}.l"
    output_txt = f".{d}examples{d}parser_output{d}txt{d}exmp{i}"
    output_png = f".{d}examples{d}parser_output{d}png{d}exmp{i}"
    output_lex = f".{d}examples{d}lexer_output{d}txt{d}exmp{i}"

    parser_cmd = f"python {parser_exe} {input} -o {output_txt} -i {output_png}"
    lexer_cmd = f"python {lexer_exe} {input} -o {output_lex}"
    
    os.system(parser_cmd)
    os.system(lexer_cmd)

    print("=================================================")
    print()

