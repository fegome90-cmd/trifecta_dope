### 4. NL Normalization with Bigrams

**New Method**: `_normalize_nl(task: str) -> list[str]`

```python
def _normalize_nl(self, task: str) -> list[str]:
    """Normalize NL query for L2 direct trigger matching.

    Rules (T9.3.2):
    - Lowercase
    - Strip punctuation
    - Collapse whitespace
    - Generate bigrams (2-token sequences)

    Returns:
        List of normalized unigrams and bigrams
    """
    # Lowercase
    normalized = task.lower()

    # Strip punctuation
    normalized = normalized.translate(str.maketrans("", "", string.punctuation))

    # Collapse whitespace
    normalized = " ".join(normalized.split())

    # Generate unigrams and bigrams
    tokens = normalized.split()
    unigrams = tokens
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]

    return unigrams + bigrams
```

**Example**:
- Input: `"can you show me the token counting logic"`
- Unigrams: `["can", "you", "show", "me", "the", "token", "counting", "logic"]`
- Bigrams: `["can you", "you show", "show me", "me the", "the token", "token counting", "counting logic"]`
- Match: `"token counting"` → `token_estimation`
