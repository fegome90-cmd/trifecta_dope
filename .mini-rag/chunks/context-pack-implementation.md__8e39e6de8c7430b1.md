_RE.match(line)
        if heading_match and not in_fence:
            flush(i)  # Guardar chunk anterior

            # Iniciar nuevo chunk
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            title_path = title_path[:level - 1] + [title]
            start_line = i
            buf = [line]
        else:
            buf.append(line)

    flush(len(lines))  # Flush final chunk

    # ... (handle oversized chunks with paragraph fallback)

    return final_chunks
```
