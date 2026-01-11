import copy
from src.domain.anchor_extractor import extract_anchors

def classify_query(query: str, anchors_cfg: dict, aliases_cfg: dict) -> dict:
    """
    Clasifica una query en vague/semi/guided basándose en anchors y tokens.
    Función pura.
    """
    extraction = extract_anchors(query, anchors_cfg, aliases_cfg)
    
    tokens = extraction["tokens"]
    strong = extraction["strong"]
    weak = extraction["weak"]
    aliases_matched = extraction["aliases_matched"]
    
    token_count = len(tokens)
    strong_count = len(strong)
    total_anchor_count = strong_count + len(weak) + len(aliases_matched)
    
    # Reglas de clasificación v1 (determinista)
    if token_count >= 5 and (strong_count >= 1 or total_anchor_count >= 2):
        q_class = "guided"
    elif token_count < 3 or total_anchor_count == 0:
        q_class = "vague"
    else:
        q_class = "semi"
        
    return {
        "query_class": q_class,
        "token_count": token_count,
        "anchors": {
            "strong": strong,
            "weak": weak,
            "aliases_matched": aliases_matched
        }
    }

def expand_query(query: str, analysis: dict, anchors_cfg: dict) -> dict:
    """
    Expande una query VAGUE de forma determinista.
    Función pura.
    """
    if analysis["query_class"] != "vague":
        return {
            "expanded_query": query,
            "added_strong": [],
            "added_weak": [],
            "reasons": []
        }
        
    added_strong: list[str] = []
    added_weak: list[str] = []
    reasons: list[str] = []
    
    # Helper para cargar config safe
    strong_cfg = anchors_cfg.get("anchors", {}).get("strong", {})
    # weak_cfg = anchors_cfg.get("anchors", {}).get("weak", {}) # Unused for now
    
    # Detección de intención documental en tokens existentes
    # Usamos los weak anchors detectados en analysis
    existing_weak = analysis["anchors"]["weak"]
    existing_strong = analysis["anchors"]["strong"]
    
    is_doc_intent = any(t in existing_weak for t in ["doc", "docs", "documentación", "guía", "manual", "uso", "cómo", "how", "howto"])
    
    # Regla: preferir strong.dirs + strong.exts cuando el usuario pida documentación
    if is_doc_intent:
        # Intentar añadir docs/ y readme.md si no están presentes
        candidates = ["docs/", "readme.md"]
        for cand in candidates:
            if cand not in existing_strong and cand not in added_strong and len(added_strong) < 2:
                added_strong.append(cand)
                reasons.append("doc_intent_boost")
                
    # Si aun tenemos espacio para strong anchors y no hay intención documental clara,
    # podríamos añadir "agent.md" o "prime.md" como entrypoints por defecto para queries muy vagas
    # pero el mandato dice "limitado".
    if len(added_strong) < 2:
        defaults = ["agent.md", "prime.md"]
        for cand in defaults:
            if cand not in existing_strong and cand not in added_strong and len(added_strong) < 2:
                # Solo añadir si la query es REALMENTE vaga (token count muy bajo)
                if analysis["token_count"] <= 2:
                    added_strong.append(cand)
                    reasons.append("vague_default_boost")

    # Construir query expandida
    # Simplemente concatenamos los términos únicos
    terms = query.split()
    for s in added_strong:
        if s not in terms: # Check simple string presence
             terms.append(s)
    
    # Weak expansion: no especificada logicamente en "reglas" salvo "limitado".
    # Mandato: "agregar máximo 2 weak intent/doc terms".
    # Si la query no tiene NINGUN weak term, podríamos inyectar uno genérico como "context"?
    # Por ahora dejémoslo conservador: solo strong boost.
    
    expanded_query_str = " ".join(terms)
    
    return {
        "expanded_query": expanded_query_str,
        "added_strong": added_strong,
        "added_weak": added_weak,
        "reasons": reasons
    }

def lint_query(query: str, anchors_cfg: dict, aliases_cfg: dict) -> dict:
    """
    Orquesta clasificación y expansión para producir un plan auditable.
    """
    analysis = classify_query(query, anchors_cfg, aliases_cfg)
    
    q_class = analysis["query_class"]
    
    if q_class == "vague":
        expansion = expand_query(query, analysis, anchors_cfg)
        expanded_query = expansion["expanded_query"]
        changed = expanded_query != query
        changes = {
            "added_strong": expansion["added_strong"],
            "added_weak": expansion["added_weak"],
            "reasons": expansion["reasons"]
        }
    else:
        expanded_query = query
        changed = False
        changes = {
            "added_strong": [],
            "added_weak": [],
            "reasons": []
        }
        
    return {
        "original_query": query,
        "query_class": q_class,
        "token_count": analysis["token_count"],
        "anchors_detected": analysis["anchors"],
        "expanded_query": expanded_query,
        "changed": changed,
        "changes": changes
    }
