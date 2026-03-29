from pathlib import Path
from src.Parser.clang_parser import ClangFunctionExtractor
from src.cfg.builder import build_cfg

def print_ast(node, indent=0):
    """Recursively print AST structure"""
    prefix = "  " * indent
    print(f"{prefix}{node.kind}: {repr(node.text[:50] if node.text else 'None')}")
    
    if node.children:
        for child in node.children:
            print_ast(child, indent + 1)

# Parse test.cpp
extractor = ClangFunctionExtractor()
functions = extractor.parse_file(Path("test.cpp"))

# Just look at test3 which has strcpy
test3 = [f for f in functions if f.name == "test3"][0]

print("="*80)
print(f"AST for test3() - Should contain strcpy call")
print("="*80)
print_ast(test3.body)