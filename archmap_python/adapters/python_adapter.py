import ast
import os
from archmap_python.core.model import Entity, Relation

class PythonParser:
    def __init__(self, repo_path: str, model):
        self.repo_path = repo_path
        self.model = model

        self.current_module = None
        self.current_class = None
        self.current_function = None

        # NEW: track import aliases
        self.import_aliases = {}

    # ----------------------------
    # PUBLIC
    # ----------------------------
    def parse_file(self, file_path: str):
        if any(part in {"venv", ".venv", "env", ".env"} for part in file_path.split(os.sep)):
            return

        with open(file_path, "r", encoding="utf-8") as f:
            print(f"Parsing {file_path}...")
            source = f.read()

        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            print(f"Skipping {file_path} due to syntax error: {e}")
            return

        module_name = os.path.relpath(file_path, self.repo_path) \
            .replace(os.sep, ".") \
            .replace(".py", "")

        self.current_module = module_name
        module_id = f"module:{module_name}"

        # Ensure module entity exists
        self._ensure_entity(module_id, "module", module_name, file_path)

        for node in tree.body:

            # -------- Imports --------
            if isinstance(node, ast.Import):
                for alias in node.names:
                    real_name = alias.name
                    alias_name = alias.asname or alias.name

                    self.import_aliases[alias_name] = real_name
                    self._add_import(module_id, real_name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        alias_name = alias.asname or alias.name
                        full_name = f"{node.module}.{alias.name}"
                        self.import_aliases[alias_name] = full_name

                    self._add_import(module_id, node.module)

            # -------- Classes --------
            elif isinstance(node, ast.ClassDef):
                self._handle_class(node, module_id, module_name, file_path)

            # -------- Top-level Functions --------
            elif isinstance(node, ast.FunctionDef):
                self._handle_function(
                    node, module_id, module_name, file_path, parent_class=None
                )

    # ----------------------------
    # ENTITY HELPERS
    # ----------------------------
    def _ensure_entity(self, entity_id, entity_type, name, file):
        if entity_id not in self.model.entities:
            self.model.add_entity(Entity(
                id=entity_id,
                type=entity_type,
                name=name,
                file=file
            ))

    def _ensure_external_entity(self, entity_id):
        if entity_id not in self.model.entities:
            self.model.add_entity(Entity(
                id=entity_id,
                type="external",
                name=entity_id.split(":", 1)[-1],
                file="external"
            ))

    def _add_relation(self, src, dst, rel_type):
        self._ensure_external_entity(dst)

        self.model.add_relation(Relation(
            src=src,
            dst=dst,
            type=rel_type
        ))

    # ----------------------------
    # IMPORTS
    # ----------------------------
    def _add_import(self, module_id: str, imported_module: str):
        target_id = f"module:{imported_module}"
        self._add_relation(module_id, target_id, "imports")

    # ----------------------------
    # CLASS HANDLER
    # ----------------------------
    def _handle_class(self, node, module_id, module_name, file_path):
        class_name = node.name
        qualname = f"{module_name}.{class_name}"
        class_id = f"class:{qualname}"

        self._ensure_entity(class_id, "class", qualname, file_path)

        self._add_relation(module_id, class_id, "contains")

        # -------- Inheritance --------
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_id = f"class:{base.id}"
                self._add_relation(class_id, base_id, "inherits")

        prev_class = self.current_class
        self.current_class = class_name

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._handle_function(
                    item, module_id, module_name, file_path, parent_class=class_name
                )

        self.current_class = prev_class

    # ----------------------------
    # FUNCTION / METHOD HANDLER
    # ----------------------------
    def _handle_function(self, node, module_id, module_name, file_path, parent_class):
        func_name = node.name

        if parent_class:
            qualname = f"{module_name}.{parent_class}.{func_name}"
            func_id = f"function:{qualname}"
            parent_id = f"class:{module_name}.{parent_class}"
            entity_type = "method"
        else:
            qualname = f"{module_name}.{func_name}"
            func_id = f"function:{qualname}"
            parent_id = module_id
            entity_type = "function"

        self._ensure_entity(func_id, entity_type, qualname, file_path)

        self._add_relation(parent_id, func_id, "contains")

        # -------- Calls --------
        prev_function = self.current_function
        self.current_function = func_id

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                called_name = self._resolve_call(child.func)
                if called_name:
                    target_id = f"function:{called_name}"
                    self._add_relation(func_id, target_id, "calls")

        self.current_function = prev_function

    # ----------------------------
    # CALL RESOLUTION (IMPROVED)
    # ----------------------------
    def _resolve_call(self, node):
        # foo()
        if isinstance(node, ast.Name):
            return self._resolve_alias(node.id)

        # obj.method()
        elif isinstance(node, ast.Attribute):
            parts = []
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value

            if isinstance(node, ast.Name):
                base = self._resolve_alias(node.id)
                parts.append(base)

            return ".".join(reversed(parts))

        return None

    def _resolve_alias(self, name):
        return self.import_aliases.get(name, name)