## Parsing Rules

1. **Order-Independent**: Key order is **NOT guaranteed**. Parsers **MUST** be order-insensitive
2. **Ignore Unknown Keys**: Parsers **MUST** ignore unknown keys for forward compatibility
3. **Key-Value Format**: Each pair is `<key>=<value>` separated by spaces
4. **No Escaping**: Values do not contain spaces or special characters (design constraint)
