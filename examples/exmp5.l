function fib(n) {
    if (n <= 1)
        return n;
    return fib(n-1)+fib(n-2);
}

function main(){
    let n;
    read(n);
    print(fib(n));
    return 0;
}