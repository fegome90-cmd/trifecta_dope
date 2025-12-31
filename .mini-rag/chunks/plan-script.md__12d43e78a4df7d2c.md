# split oversized sections by paragraphs
        if len(txt) > max_chars:
            parts = re.split(r"\n\s*\n", txt)
            acc = []
            acc_len = 0
            part_i = 0
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if acc and acc_len + len(p) + 2 > max_chars:
                    i += 1
                    cid = f"{doc_id}:{i:04d}"
                    chunks.append({"id": cid, "doc": doc_id, "title": f"{t} (part {part_i})", "level": lvl, "text": "\n\n".join(acc)})
                    acc, acc_len = [], 0
                    part_i += 1
                acc.append(p)
                acc_len += len(p) + 2
            if acc:
                i += 1
                cid = f"{doc_id}:{i:04d}"
                chunks.append({"id": cid, "doc": doc_id, "title": f"{t} (part {part_i})", "level": lvl, "text": "\n\n".join(acc)})
        else:
            i += 1
            cid = f"{doc_id}:{i:04d}"
            chunks.append({"id": cid, "doc": doc_id, "title": t, "level": lvl, "text": txt})
    return chunks

def preview(txt: str, max_chars: int = 180) -> str:
    one = re.sub(r"\s+", " ", txt.strip())
    return one[:max_chars] + ("…" if len(one) > max_chars else "")
