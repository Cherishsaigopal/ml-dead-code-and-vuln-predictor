#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Test Case 1: Dead Code (unused variable)
void test1() {
    int x = 10; // unused → dead code
}

// Test Case 2: No Dead Code
void test2() {
    int a = 5;
    printf("%d", a); // used → no dead code
}

// Test Case 3: Vulnerability (unsafe strcpy)
void test3(char *input) {
    char dest[10];
    strcpy(dest, input); // vulnerable
}

// Test Case 4: Safe code (no vulnerability)
void test4() {
    char buffer[10];
    fgets(buffer, sizeof(buffer), stdin); // safe
}

// Test Case 5: Mixed (dead code + vulnerability)
void test5(char *input) {
    int unused = 20; // dead code
    char dest[10];
    strcpy(dest, input); // vulnerable
}

int main() {
    char input[20] = "hello";

    test1();
    test2();
    test3(input);
    test4();
    test5(input);

    return 0;
}