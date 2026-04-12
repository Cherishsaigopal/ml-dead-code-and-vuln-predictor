#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>

// 1. Safe: Standard math operations and loops
void safe_calculate_average(int* data, int size) {
    if (size <= 0) return;
    int sum = 0;
    for(int i = 0; i < size; i++) {
        sum += data[i];
    }
    printf("Average: %d\n", sum / size);
}

// 2. Dead Code: Unused Array
void dead_code_unused_array() {
    char unused_buffer[256]; // Dead code: declared but never read/written
    int active_val = 42;
    printf("Active value: %d\n", active_val);
}

// 3. Dead Code: Unreachable after 'break'
void dead_code_unreachable_break(int index) {
    while(true) {
        if (index < 0) {
            break;
            index = 0; // Dead code: unreachable after break
        }
        printf("Index is valid\n");
        return;
    }
}

// 4. Vulnerability: Insecure memory copy (memcpy)
void vuln_memory_copy(char* source) {
    char destination[10];
    // 'memcpy' is in your SENSITIVE_APIS list
    memcpy(destination, source, 100); 
    printf("Copied data\n");
}

// 5. Vulnerability: Insecure string parsing (sscanf)
void vuln_string_parsing(const char* input_string) {
    char parsed_word[20];
    // 'sscanf' is highly susceptible to buffer overflows
    sscanf(input_string, "%s", parsed_word);
    printf("Parsed: %s\n", parsed_word);
}

// 6. Mixed: Vulnerability (popen) + Dead Code (unused var & unreachable)
void mixed_vuln_and_dead_code(const char* command) {
    float unused_float = 9.99; // Dead code
    
    // 'popen' is a command injection risk
    FILE* fp = popen(command, "r"); 
    if (!fp) return;
    
    pclose(fp);
    return;
    printf("Finished execution\n"); // Dead code: unreachable
}

// 7. High Complexity but Safe: Bubble Sort
// Verifies that heavily nested loops don't cause false positive vulnerabilities
void safe_complex_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

// 8. Safe: Manual array copy (No sensitive APIs)
// Verifies the model correctly identifies safe data movement
void safe_manual_copy(const char* src) {
    char dest[50];
    int i = 0;
    while(src[i] != '\0' && i < 49) {
        dest[i] = src[i];
        i++;
    }
    dest[i] = '\0';
    printf("Safely copied: %s\n", dest);
}

int main() {
    int data[] = {1, 2, 3, 4, 5};
    char sample_text[] = "malicious_input_string";
    
    safe_calculate_average(data, 5);
    dead_code_unused_array();
    dead_code_unreachable_break(-1);
    vuln_memory_copy(sample_text);
    vuln_string_parsing(sample_text);
    mixed_vuln_and_dead_code("ls -la");
    safe_complex_sort(data, 5);
    safe_manual_copy(sample_text);
    
    return 0;
}