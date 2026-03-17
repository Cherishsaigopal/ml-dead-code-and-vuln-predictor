#include <iostream>
#include <cstring>
using namespace std;

int helper(int x) {
    int y = x * 2;
    if (x < 0) {
        return -1;
    }
    return y;
}

void risky_copy(char *input) {
    char buffer[10];
    strcpy(buffer, input); // intentionally unsafe
    cout << buffer << endl;
}

int main() {
    char data[] = "hello";
    risky_copy(data);

    int result = helper(5);
    cout << "Result: " << result << endl;

    return 0;
}