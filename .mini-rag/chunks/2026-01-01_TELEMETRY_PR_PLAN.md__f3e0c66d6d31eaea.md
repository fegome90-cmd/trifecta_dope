# Import tree-sitter on first use
            from tree_sitter import Language, Parser

            PYTHON_LANGUAGE = Language("tree-sitter-python")
            parser = Parser()
            parser.set_language(PYTHON_LANGUAGE)

            tree = parser.parse(code.encode('utf-8'))
            functions, classes, imports = self._extract_structure(tree)

            skeleton = SkeletonMap(
                functions=functions,
                classes=classes,
                imports=imports,
                file_path=file_path
            )

            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)

            skeleton_bytes = len(json.dumps(skeleton.__dict__, default=str))
            reduction_ratio = skeleton_bytes / max(len(code), 1)

            # Emit event with monotonic timing
            self.telemetry.event(
                "ast.parse",
                {"file": self._relative_path(file_path)},
                {
                    "functions": len(functions),
                    "classes": len(classes),
                    "status": "ok"
                },
                elapsed_ms,
                skeleton_bytes=skeleton_bytes,
                reduction_ratio=round(reduction_ratio, 4),
            )

            # Increment counter
            self.telemetry.incr("ast_parse_count")

            return skeleto
