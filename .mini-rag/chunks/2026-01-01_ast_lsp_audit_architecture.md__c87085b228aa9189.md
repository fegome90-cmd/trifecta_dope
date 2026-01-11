### 3.1 Grammar (EBNF)
```ebnf
URI         = "sym://" Language "/" Kind "/" Path ("#" Member)?
Language    = "python"
Kind        = "mod" | "type"
Path        = Identifier ("/" Identifier)*
Member      = Identifier ("." Identifier)*
Identifier  = [a-zA-Z_][a-zA-Z0-9_]*
```
