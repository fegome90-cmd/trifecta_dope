# Busca ```yaml ... ```
    yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
    
    compiled_rules = []
    
    for block in yaml_blocks:
        try:
            rules_list = yaml.safe_load(block)
            if not isinstance(rules_list, list): continue # Ignorar configs que no son listas de reglas
            
            for rule in rules_list:
                if rule['rule'] == 'architectural-boundary':
                    compiled_rules.append(compile_boundary_rule(rule))
                elif rule['rule'] == 'security-guard':
                    compiled_rules.append(compile_security_rule(rule))
