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
    let a = 10.7;
    let b = 0.92;
    let c;
    read(c);
    write(foo(a, b, c) - bar(a, b, c));
}