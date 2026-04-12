#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>

// 1. Perfectly Safe: Normal logic, variables used, safe APIs
void test_safe_simple(int a, int b) {
    int sum = a + b;
    printf("Sum is: %d\n", sum);
}

// 2. Dead Code: Unused Variable (Tests your new Regex logic)
void test_unused_variable() {
    int unused_val = 100; // Will trigger unused variable detection
    printf("Hello World\n");
}

// 3. Dead Code: Unreachable Code (Tests CFG structural logic)
void test_unreachable_code() {
    printf("Before return\n");
    return;
    printf("After return"); // Will trigger structural unreachable block
}

// 4. Vulnerability: Command Injection (High Risk)
void test_vuln_system(char* user_input) {
    char command[256];
    // 'sprintf' and 'system' are both highly sensitive APIs
    sprintf(command, "ping %s", user_input); 
    system(command);
}

// 5. Vulnerability: Buffer Overflow
void test_vuln_buffer_overflow() {
    char buffer[50];
    printf("Enter name: ");
    gets(buffer); // Extremely high-risk API
}

// 6. Mixed: Vulnerability AND Dead Code
void test_mixed_vuln_and_dead_code(char* src) {
    float unused_float = 3.14; // Dead code (unused var)
    char dest[20];
    strcpy(dest, src); // Vulnerability
    return;
    strcpy(dest, "unreachable"); // Dead code (unreachable block)
}

// 7. High Complexity but Safe: Deep nesting, multiple branches/loops
// Tests that high cyclomatic complexity doesn't cause a false positive Vuln alert
void test_high_complexity_safe(int limit) {
    int total = 0;
    for (int i = 0; i < limit; i++) {
        if (i % 2 == 0) {
            for (int j = 0; j < 5; j++) {
                if (j == 3) {
                    total += (i * j);
                } else {
                    total -= j;
                }
            }
        }
    }
    printf("Complex total: %d\n", total);
}

// 8. Safe String Handling: Using secure alternatives
// Tests that the model doesn't flag 'strncpy' or 'snprintf' by mistake
void test_safe_string_handling(const char* input) {
    char safe_buffer[100];
    strncpy(safe_buffer, input, sizeof(safe_buffer) - 1);
    safe_buffer[sizeof(safe_buffer) - 1] = '\0';
    
    char out_msg[150];
    snprintf(out_msg, sizeof(out_msg), "Safe output: %s", safe_buffer);
    printf("%s\n", out_msg);
}

int main() {
    char sample_input[] = "127.0.0.1";
    
    test_safe_simple(5, 10);
    test_unused_variable();
    test_unreachable_code();
    test_vuln_system(sample_input);
    test_vuln_buffer_overflow();
    test_mixed_vuln_and_dead_code(sample_input);
    test_high_complexity_safe(10);
    test_safe_string_handling("test data");
    
    return 0;
}