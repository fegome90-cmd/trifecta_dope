# Lógica: Si estoy en 'target', NO puedo tener 'import' de 'disallow'
    disallowed_patterns = "|".join([p.replace("**/*.ts", "") for p in rule.get('disallow', [])])

    return {
        'id': rule['id'],
        'message': rule['description'],
        'severity': rule['severity'],
        'language': 'TypeScript',
        'rule': {
            'pattern': 'import $IMPORTS from "$SOURCE"',
            'all': [
                {
                    'inside': {
                        'subdir': rule['target'].replace('**/*.ts', '')
                    }
                },
                {
                    'has': {
                        'field': 'source',
                        'regex': disallowed_patterns
                    }
                }
            ]
        }
    }

def compile_security_rule(rule):
    """
    Convierte 'security-guard' a regla de ast-grep
    """
    pattern_map = {
        'eval': 'eval($$$ARGS)',
        'dangerouslySetInnerHTML': 'dangerouslySetInnerHTML={$$$PROPS}',
        'process-env': 'process.env.$VAR'
    }

    return {
        'id': rule['id'],
        'message': rule['description'],
        'severity': rule['severity'],
        'language': 'TypeScript',
        'rule': {
            'pattern': pattern_map.get(rule['disallow'], rule.get('pattern', 'TODO'))
        }
    }
