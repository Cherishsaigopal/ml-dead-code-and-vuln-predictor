from clang import cindex

code = r"""
int add(int a, int b) {
    if (a > 0) return a + b;
    else return b;
}
"""

index = cindex.Index.create()
tu = index.parse(
    path="tmp.c",
    args=["-x", "c", "-std=c11"],
    unsaved_files=[("tmp.c", code)],
)

print("Translation Unit parsed OK")

for c in tu.cursor.get_children():
    if c.kind.name == "FUNCTION_DECL":
        print("Found function:", c.spelling)
