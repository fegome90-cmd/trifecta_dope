import tree_sitter_python
from tree_sitter import Language, Parser

print(f"Language Ptr: {tree_sitter_python.language()}")
try:
    py_lang = Language(tree_sitter_python.language())
    parser = Parser(py_lang)
    print("Parser initialized successfully")
except Exception as e:
    print(f"Error: {e}")
