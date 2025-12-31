# Aquí añadirías 'naming-convention' y 'function-style'
                
        except yaml.YAMLError as e:
            print(f"Error parseando bloque YAML: {e}")

    return {'rules': compiled_rules}

if __name__ == "__main__":
