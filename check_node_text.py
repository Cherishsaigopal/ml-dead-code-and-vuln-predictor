from pathlib import Path
from src.Parser.clang_parser import ClangFunctionExtractor

def walk_tree(node):
    """Walk tree and print all nodes with text"""
    nodes_with_text = []
    
    def recurse(n):
        if hasattr(n, 'text') and n.text and len(n.text) > 5:
            nodes_with_text.append((n.kind, n.text[:60]))
        if hasattr(n, 'children') and n.children:
            for child in n.children:
                recurse(child)
    
    recurse(node)
    return nodes_with_text

# Parse
extractor = ClangFunctionExtractor()
functions = extractor.parse_file(Path("test.cpp"))

test3 = [f for f in functions if f.name == "test3"][0]

print("All nodes with text content in test3:")
nodes = walk_tree(test3.body)
for kind, text in nodes:
    print(f"  {kind}: {repr(text)}")

if not nodes:
    print("  ❌ NO NODES WITH TEXT FOUND!")
    print("\nChecking node structure:")
    
    def check_structure(n, indent=0):
        prefix = "  " * indent
        has_text = hasattr(n, 'text') and n.text
        has_children = hasattr(n, 'children') and n.children
        print(f"{prefix}{n.kind} (has_text={has_text}, has_children={has_children})")
        if has_children and indent < 3:
            for child in n.children[:2]:
                check_structure(child, indent+1)
    
    check_structure(test3.body)