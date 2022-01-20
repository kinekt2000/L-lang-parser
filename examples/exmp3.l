function foo(a, b, c){
    write(a);
    write(b);
    write(c);
    return a + b + c;
}

function bar(a, b, c){
    return a * b / c;
}

function main() {
    a = 10.7;
    b = 0.92;
    c = read();
    write(foo(a, b, c) - bar(a, b, c));
}