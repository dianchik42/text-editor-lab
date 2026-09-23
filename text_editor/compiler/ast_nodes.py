"""Компактное AST: знаки пунктуации и служебные правила в дерево не входят."""
from dataclasses import dataclass, field
import json


@dataclass
class AstNode:
    kind: str
    line: int = 1
    col: int = 1
    attributes: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def to_dict(self):
        return {"node": self.kind, "position": {"line": self.line, "column": self.col},
                "attributes": self.attributes,
                "children": [child.to_dict() for child in self.children]}

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, allow_nan=False)


class ProgramNode(AstNode):
    def __init__(self):
        super().__init__("ProgramNode")


class VariableDeclNode(AstNode):
    def __init__(self, name_token, type_token, initializer):
        super().__init__("VariableDeclNode", name_token.line, name_token.start,
                         {"name": name_token.lexeme, "type": type_token.lexeme, "modifiers": []},
                         [AstNode("TypeNode", type_token.line, type_token.start,
                                  {"name": type_token.lexeme}), initializer])


def make_expression(token, sign=None):
    if token.type == "SCIENTIFIC":
        kind, attributes = "ScientificLiteralNode", {"type": "double", "lexeme": token.lexeme}
    elif token.type == "STRING":
        kind, attributes = "StringLiteralNode", {"type": "String", "lexeme": token.lexeme}
    elif token.lexeme in ("true", "false"):
        kind, attributes = "BooleanLiteralNode", {"type": "boolean", "lexeme": token.lexeme, "value": token.lexeme == "true"}
    else:
        kind, attributes = "IdentifierNode", {"name": token.lexeme}
    node = AstNode(kind, token.line, token.start, attributes)
    if sign:
        node = AstNode("UnaryOpNode", sign.line, sign.start, {"operator": sign.lexeme}, [node])
    return node
