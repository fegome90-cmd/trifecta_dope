## Error Card Extraction

The harness automatically extracts Error Cards from stderr by looking for:

1. **Error Code**: `TRIFECTA_ERROR_CODE: <code>`
2. **Class**: `CLASS: <class>`
3. **Cause**: Text between `CAUSE:` and `NEXT STEPS:`
