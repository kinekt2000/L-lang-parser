# L-lang-parser
Lexer and parser for non-existent lang

Made via `sly` python package

## Pre-requirements
Package dependencies:
* sly
* anytree
* pydot

To be able to plot a tree, Graphviz software is required. `dot` executable must be in the PATH.

## Usage
### Lexer
Run lexer with specified input file to get tokens of file
```console
~$ python LLexer <input_file> 
```
To get more info about lexer usage, run 
```console
~$ python LLexer -h
```

### Parser
Run parser with specified input to get abstract syntax tree
```console
~$ python LParser <input_file> 
```
To get more info about parser usage, run 
```console
~$ python LParser -h
```

## Example
Only a sequence of functions can be defined in program global scope
```js
function foo(){
    return 0;
}

function bar(a, b){
    return a + b;
}

function main(){
    return 0;
}
```

A function consists of the keyword "_function_", a "_function name_", a "_list of arguments_", and a "_body_". To return value, `return` statement should be used.
```js
   function main(a, b, c) return 0;
// \  ^   / \^ / \  ^  /  \   ^   /
//    |      |      |         |
//  keyword  |      |         |
//    function name |         |
//             argument list  |
//                          body
```
"body" can be represented as a single statement with semicolon at the end, or as a list of statements enclosed in curly braces.
```js
// single statement
function main(a, b, c) write(a + b + c);

// list of statements
function main(a, b, c) {
    let d = a + b + c;
    write(d);
}
```
Simple conditional statements are available. They can also accept either a single statement or a statement list enclosed in curly braces.
```js
function main() {
    let a = 0

    // if statement ("else" statement can be ommited)
    if (a < 5) a = a + 1;
    else a = a - 1;

    // while loop statement
    while (a < 5) {
        a = a + 1;
        write(a);
    }
}
```
The variable declaration operator already shown earlier. A variable can be simply declared, or it can also be assigned. Integer and floating point variables available.
```js
function main() {
    let a;
    a = 10;
    let b = 10.5 - 6;
}
```
Functions and variable assignments take an expression
```js
function foo(a, b) return a / b;
function main() {
    let a = foo(12 / 8, 3.2 ^ 0.9) - 15.9 * (2 + 6.4);
}
```
Condition used for conditional statements. && (AND), || (OR), ! (NOT) operators are avalable for conditions. To get a condition, you need to compare two expressions with any of next operators "==", "!=", "<=", "<", ">=", ">".
```js
function main() {
    if (!5 - 3 > 9 && 7 / 2 == 3.5 || 1 != 2) return 0;
    return 1;
}
```
To manipulate the I/O stream, operators `read` and `write` can be used. `read` takes a variable, `write` takes an expression or condition.
```js
function main() {
    let a;
    read(a);
    write(a * 2);
}
```

## Manual
### Lexer
```
NAME:
        LParser - parser for non-exsitend L lang
SYNOPSIS:
        LParser [options]... input_file
DESCRIPTION
        Write arguments to the standard output.

        Options:
          -h,    --help                 Display info about program.
          -f[=], --format[=]            Output text format. "txt" (default) and "json" are allowed.
          -o[=], --output[=]            Output file. If not specified, printed into stdout.

        Arguments:
          input_file                    Required. File with L lang source to be tokenized.
```

### Parser
```
NAME:
        LParser - parser for non-exsitend L lang
SYNOPSIS:
        LParser [options]... input_file
DESCRIPTION
        Write arguments to the standard output.

        Options:
          -h,    --help                 Display info about program.
          -f[=], --format[=]            Output text format. "txt" (default) and "json" are allowed.
          -o[=], --output[=]            Output file. If not specified, printed into stdout.
          -i[=], --image-output[=]      Image output file. If not specified, image not generated.

        Arguments:
          input_file                    Required. File with L lang source to be parsed.
```