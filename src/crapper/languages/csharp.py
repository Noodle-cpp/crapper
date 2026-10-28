"""C# methods and cyclomatic complexity, aligned with crap4java and TypeScript nullish rules.

Constructors, property accessors, and methods inside lambdas or local functions
are ignored as entries. Nested types use `Ns.Outer.Inner` in snapshots and
`Ns.Outer+Inner` in coverage reports (Coverlet/Cobertura). Expression-bodied
methods and switch expressions are scored when they have a body clause.
"""

from crapper.languages.treesitter import (
    binary_logic,
    child_of_type,
    complexity,
    end_line,
    node_text,
    parse,
    start_line,
)
from crapper.model import Function

_NESTED_TYPES = {
    "class_declaration",
    "struct_declaration",
    "record_declaration",
    "interface_declaration",
    "enum_declaration",
}
_DECISIONS = {
    "if_statement",
    "for_statement",
    "foreach_statement",
    "while_statement",
    "do_statement",
    "catch_clause",
    "conditional_expression",
    "switch_section",
    "switch_expression_arm",
}
_SKIP_COMPLEXITY = _NESTED_TYPES | {
    "class_body",
    "local_function_statement",
    "lambda_expression",
    "anonymous_function_expression",
}
_EXECUTABLE = {
    "method_declaration",
    "constructor_declaration",
    "local_function_statement",
    "lambda_expression",
    "anonymous_function_expression",
}


def _is_decision(node) -> bool:
    if node.type in _DECISIONS or binary_logic(node):
        return True
    if node.type == "binary_expression" and any(child.type == "??" for child in node.children):
        return True
    if node.type == "conditional_access_expression":
        return True
    return node.type == "?." and (
        node.parent is None or node.parent.type != "conditional_access_expression"
    )


def _skip(node) -> bool:
    return node.type in _SKIP_COMPLEXITY


def _inside_executable(node) -> bool:
    current = node.parent
    while current is not None:
        if current.type in _EXECUTABLE:
            return True
        current = current.parent
    return False


def _namespace_name(data: bytes, root) -> str | None:
    for child in root.children:
        if child.type not in {"namespace_declaration", "file_scoped_namespace_declaration"}:
            continue
        name = child_of_type(child, "qualified_name")
        if name is not None:
            return node_text(data, name)
        ident = child_of_type(child, "identifier")
        if ident is not None:
            return node_text(data, ident)
    return None


def _type_identifier(data: bytes, node) -> str | None:
    name = child_of_type(node, "identifier")
    if name is not None:
        return node_text(data, name)
    generic = child_of_type(node, "generic_name")
    if generic is not None:
        inner = child_of_type(generic, "identifier")
        if inner is not None:
            return node_text(data, inner)
    return None


def _type_chain(data: bytes, node) -> list[str]:
    names: list[str] = []
    current = node.parent
    while current is not None:
        if current.type in _NESTED_TYPES:
            ident = _type_identifier(data, current)
            if ident is not None:
                names.append(ident)
        current = current.parent
    names.reverse()
    return names


def _qualify(namespace: str | None, names: list[str], nested: str) -> str:
    body = nested.join(names)
    if namespace:
        return f"{namespace}.{body}" if body else namespace
    return body


def _has_body(node) -> bool:
    return (
        child_of_type(node, "block") is not None
        or child_of_type(node, "arrow_expression_clause") is not None
    )


def _method_name(data: bytes, node) -> str | None:
    ident = child_of_type(node, "identifier")
    if ident is not None:
        return node_text(data, ident)
    return None


def functions_in_source(
    source: str, path: str, project_root: str | None = None
) -> list[Function]:
    del project_root
    data, tree = parse(source, "csharp")
    namespace = _namespace_name(data, tree.root_node)
    found: list[Function] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == "method_declaration" and not _inside_executable(node):
            if not _has_body(node):
                continue
            name = _method_name(data, node)
            names = _type_chain(data, node)
            if name is not None and names:
                found.append(
                    Function(
                        name=name,
                        namespace=_qualify(namespace, names, "."),
                        complexity=complexity(node, _is_decision, _skip),
                        start_line=start_line(node),
                        end_line=end_line(node),
                        path=path,
                        language="csharp",
                        jacoco_class=_qualify(namespace, names, "+"),
                        start_byte=node.start_byte,
                        end_byte=node.end_byte,
                    )
                )
            continue
        stack.extend(reversed(node.children))
    return found
