import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from graphql import print_schema, build_client_schema

from krakql.entities import GraphQLPrimitive
from krakql.entities.context import log
from krakql.entities.primitives import GraphQLKind

class TypeRef:
    def __init__(
        self,
        name: str,
        kind: str,
        is_list: bool = False,
        non_null_item: bool = False,
        non_null: bool = False,
    ) -> None:
        if not is_list and non_null_item:
            raise ValueError("Elements can't be NON_NULL if TypeRef is not LIST")

        self.name = name
        self.kind = kind
        self.is_list = is_list
        self.non_null = non_null
        self.list = self.is_list
        self.non_null_item = non_null_item

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TypeRef):
            for key, attr in self.__dict__.items():
                if attr != other.__dict__[key]:
                    return False
            return True
        return False

    def __str__(self) -> str:
        return str(self.__dict__)

    def to_json(self) -> Dict[str, Any]:
        j: Dict[str, Any] = {"kind": self.kind, "name": self.name, "ofType": None}

        if self.non_null_item:
            j = {"kind": GraphQLKind.NON_NULL, "name": None, "ofType": j}

        if self.list:
            j = {"kind": GraphQLKind.LIST, "name": None, "ofType": j}

        if self.non_null:
            j = {"kind": GraphQLKind.NON_NULL, "name": None, "ofType": j}

        return j


class InputValue:
    def __init__(
        self,
        name: str,
        typ: TypeRef,
    ) -> None:
        self.name = name
        self.type = typ

    def __str__(self) -> str:
        return f"{{ 'name': {self.name}, 'type': {str(self.type)} }}"

    def to_json(self) -> dict:
        return {
            "defaultValue": None,
            "description": None,
            "name": self.name,
            "type": self.type.to_json(),
        }

    @classmethod
    def from_json(
        cls,
        _json: Dict[str, Any],
    ) -> "InputValue":
        name = _json["name"]
        typ = field_or_arg_type_from_json(_json["type"])
        return cls(
            name=name,
            typ=typ,
        )

class Field:
    def __init__(
        self,
        name: str,
        typeref: Optional[TypeRef],
        args: Optional[List[InputValue]] = None,
        novelty_score: float = 1.0
    ):
        if not typeref:
            raise ValueError(f"Can't create {name} Field from {typeref} TypeRef.")

        self.name = name
        self.type = typeref
        self.args = args or []
        self.novelty_score = novelty_score

    def to_json(self) -> dict:
        return {
            "args": [a.to_json() for a in self.args],
            "deprecationReason": None,
            "description": None,
            "isDeprecated": False,
            "name": self.name,
            "type": self.type.to_json(),
        }

    def has_argument(self, arg_name: str) -> bool:
        """Checks if an argument is in the field."""
        if self.args is None:
            return False
        return any(a.name == arg_name for a in self.args)

    def reduce_novelty(self, step: float) -> None:
        self.novelty_score = max(0.0, self.novelty_score - step)

    def increase_novelty(self, step: float) -> None:
        self.novelty_score = min(1.0, self.novelty_score + step)
    
    def add_arg(self, arg: InputValue) -> bool:
        """Adds an argument to the field."""
        if arg not in self.args:
            self.args.append(arg)
            return True
        return False
    
    @classmethod
    def from_json(cls, _json: Dict[str, Any]) -> "Field":
        name = _json["name"]
        typ = field_or_arg_type_from_json(_json["type"])

        args = []
        for a in _json["args"]:
            args.append(InputValue.from_json(a))
        novelty_score = 1.0

        return cls(name, typ, args, novelty_score)
    

class Type:
    def __init__(
        self,
        name: str = "",
        kind: str = "",
        fields: Optional[List[Field]] = None,
        novelty_score: float = 1.0
    ):
        self.name = name
        self.kind = kind
        self.fields: List[Field] = fields or []
        self.novelty_score = novelty_score
        
    def reduce_novelty(self, step: float) -> None:
        self.novelty_score = max(0.0, self.novelty_score - step)

    def increase_novelty(self, step: float) -> None:
        self.novelty_score = min(1.0, self.novelty_score + step)
        
    def get_next_field_by_novelty(self) -> Optional[Field]:
        """Gets the field with the maximum novelty score."""
        if not self.fields:
            return None
        return max(
            (f for f in self.fields if f.novelty_score > 0 and f.type.name not in GraphQLPrimitive),
            key=lambda f: f.novelty_score,
            default=None
        )

    def add_field(self, field: Field) -> bool:
        """Adds a field to the type."""
        if self.fields is None:
            self.fields = []

        if field not in self.fields:
            self.fields.append(field)
            field.parent_type = self
            return True
        return False

    def has_field(self, field_name: str) -> bool:
        """Checks if a field is in the type."""
        if self.fields is None:
            return False
        return any(f.name == field_name for f in self.fields)

    def to_json(self) -> Dict[str, Any]:
        output: Dict[str, Any] = {
            "description": None,
            "enumValues": None,
            "interfaces": [],
            "kind": self.kind,
            "name": self.name,
            "possibleTypes": None,
        }

        if self.kind in [GraphQLKind.OBJECT, GraphQLKind.INTERFACE]:
            output["fields"] = [f.to_json() for f in (self.fields or [Field("dummy", TypeRef(name=GraphQLPrimitive.STRING, kind=GraphQLKind.SCALAR))])]
            output["inputFields"] = None
        elif self.kind == GraphQLKind.INPUT_OBJECT:
            output["fields"] = None
            output["inputFields"] = [f.to_json() for f in self.fields]

        return output

    @classmethod
    def from_json(
        cls,
        _json: Dict[str, Any],
    ) -> "Type":
        name = _json["name"]
        kind = _json["kind"]
        fields = []
        novelty_score = 1.0

        if kind in [
            GraphQLKind.OBJECT,
            GraphQLKind.INTERFACE,
            GraphQLKind.INPUT_OBJECT,
        ]:
            fields_field = ""
            if kind in [GraphQLKind.OBJECT, GraphQLKind.INTERFACE]:
                fields_field = "fields"
            elif kind == GraphQLKind.INPUT_OBJECT:
                fields_field = "inputFields"

            for f in _json[fields_field]:
                # Don't add dummy fields!
                if f["name"] == "dummy":
                    continue
                fields.append(Field.from_json(f))

        new_type = cls(
            name=name,
            kind=kind,
            fields=fields,
            novelty_score=novelty_score
        )
        
        # Set the parent for all fields after the type is created
        for field in new_type.fields:
            field.parent_type = new_type

        return new_type

class Schema:
    """Host of the introspection data."""

    def __init__(
        self,
        query_type: Optional[str] = None,
        mutation_type: Optional[str] = None,
        subscription_type: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ):
        if schema:
            self._schema = {
                "directives": schema["data"]["__schema"]["directives"],
                "mutationType": schema["data"]["__schema"]["mutationType"],
                "queryType": schema["data"]["__schema"]["queryType"],
                "subscriptionType": schema["data"]["__schema"]["subscriptionType"],
                "types": [],
            }
            self.types = {}
            for t in schema["data"]["__schema"]["types"]:
                typ = Type.from_json(t)
                self.types[typ.name] = typ
        else:
            self.query_type = {"name": query_type} if query_type else None
            self.mutation_type = {"name": mutation_type} if mutation_type else None
            self.subscription_type = (
                {"name": subscription_type} if subscription_type else None
            )
            self._schema = {
                "directives": [],
                "queryType": self.query_type,
                "mutationType": self.mutation_type,
                "subscriptionType": self.subscription_type,
                "types": [],
            }
            self.types = {
                GraphQLPrimitive.STRING: Type(
                    name=GraphQLPrimitive.STRING,
                    kind=GraphQLKind.SCALAR,
                    novelty_score=0.0,
                ),
                GraphQLPrimitive.ID: Type(
                    name=GraphQLPrimitive.ID,
                    kind=GraphQLKind.SCALAR,
                    novelty_score=0.0,
                ),
            }
            if query_type:
                self.add_type(query_type, "OBJECT")
            if mutation_type:
                self.add_type(mutation_type, "OBJECT")
            if subscription_type:
                self.add_type(subscription_type, "OBJECT")

    # Adds type to schema if it's not exists already, return False if it was already present
    def add_type(
        self,
        name: str,
        kind: str,
    ) -> bool:
        """Adds type to schema if it's not exists already."""

        if name not in self.types:
            typ = Type(name=name, kind=kind)
            self.types[name] = typ
            return True
        return False

    def __repr__(self) -> str:
        """String representation of the schema."""

        schema = {"data": {"__schema": self._schema}}

        for t in self.types.values():
            schema["data"]["__schema"]["types"].append(t.to_json())

        output = json.dumps(schema, indent=4, sort_keys=True)
        return output
    
    def sdl_representation(self) -> str:
        """Returns SDL representation of the schema."""
        # get the json representation first
        schema = {"data": {"__schema": self._schema}}

        for t in self.types.values():
            schema["data"]["__schema"]["types"].append(t.to_json())
        
        log().debug(f"Schema JSON: {schema}")
        schema = build_client_schema(schema["data"], assume_valid=True)
        output = print_schema(schema)
        return output

    def get_path_from_root(
        self,
        name: str,
    ) -> List[str]:
        """Getting path starting from root.

        The algorigthm explores the schema in a DFS manner. It uses a set to keep track of visited nodes, and a list to keep track of the path. Keeping track of
        the visited nodes is necessary to avoid infinite loops (ie. recursions in the schema). If a full iteration over the types is made without finding a
        match, it means that the schema is not connected, and the path cannot be found.
        """

        log().debug(f"Entered get_path_from_root({name})")
        path_from_root: List[str] = []

        if name not in self.types:
            raise ValueError(f"Type '{name}' not in schema!")

        roots = [
            self._schema["queryType"]["name"] if self._schema["queryType"] else "",
            (
                self._schema["mutationType"]["name"]
                if self._schema["mutationType"]
                else ""
            ),
            (
                self._schema["subscriptionType"]["name"]
                if self._schema["subscriptionType"]
                else ""
            ),
        ]
        roots = [r for r in roots if r]

        visited = set()
        initial_name = name
        while name not in roots:
            found = False
            for t in self.types.values():
                for f in t.fields:
                    key = f"{t.name}.{f.name}"
                    if key in visited:
                        continue
                    if f.type.name == name:
                        path_from_root.insert(0, f.name)
                        visited.add(key)
                        name = t.name
                        found = True
                        break
                if found:
                    break
            if not found:
                log().debug(
                    "get_path_from_root: Ran an iteration with no matches found"
                )
                raise ValueError(
                    f"Could not find path from root to '{initial_name}' \nCurrent path: {path_from_root}"
                )

        # Prepend queryType or mutationType
        path_from_root.insert(0, name)

        return path_from_root

    def get_next_type_by_novelty(
        self,
    ) -> Optional[Type]:
        """Gets the type with the maximum novelty score, which is not 0 and not INPUT_OBJECT or SCALAR"""

        return max(
            (t for t in self.types.values() if t.novelty_score > 0 and t.kind != GraphQLKind.INPUT_OBJECT and t.kind != GraphQLKind.SCALAR),
            key=lambda t: t.novelty_score,
            default=None,
        )
    
    def get_by_novelty(self) -> Optional[Tuple[Union[Type, Field], str]]:
        """
        Inspects the schema and selects the Type or Field with the highest novelty score.
        
        Returns a tuple containing the object (Type or Field) and its kind ('type' or 'field'),
        or None if no novel items are found.
        """
        best_type = self.get_next_type_by_novelty()

        # For each type, let's get the the next_field_by_novelty
        possible_fields = [type_obj.get_next_field_by_novelty() for type_obj in self.types.values()]

        # Find the field with the maximum novelty score
        best_field = max(possible_fields, key=lambda f: f.novelty_score if f else 0, default=None)

        # Determine which object has a higher novelty score
        if not best_type and not best_field:
            return None

        if best_type and not best_field:
            return best_type, "type"

        if best_field and not best_type:
            return best_field, "field"

        # If both exist, compare their scores
        if best_type.novelty_score >= best_field.novelty_score:
            return best_type, "type"
        else:
            return best_field, "field"

    def convert_path_to_document(
        self,
        path: List[str],
    ) -> str:
        """Converts a path to document."""

        log().debug(f"Entered convert_path_to_document({path})")
        doc = "FUZZ"

        while len(path) > 1:
            doc = f"{path.pop()} {{ {doc} }}"

        if self._schema["queryType"] and path[0] == self._schema["queryType"]["name"]:
            doc = f"query {{ {doc} }}"
        elif (
            self._schema["mutationType"]
            and path[0] == self._schema["mutationType"]["name"]
        ):
            doc = f"mutation {{ {doc} }}"
        elif (
            self._schema["subscriptionType"]
            and path[0] == self._schema["subscriptionType"]["name"]
        ):
            doc = f"subscription {{ {doc} }}"
        else:
            raise ValueError("Unknown operation type")

        return doc


def field_or_arg_type_from_json(_json: Dict[str, Any]) -> "TypeRef":
    typ = None

    if _json["kind"] not in [GraphQLKind.NON_NULL, GraphQLKind.LIST]:
        typ = TypeRef(
            name=_json["name"],
            kind=_json["kind"],
        )
    elif not _json["ofType"]["ofType"]:
        actual_type = _json["ofType"]

        if _json["kind"] == GraphQLKind.NON_NULL:
            typ = TypeRef(
                name=actual_type["name"],
                kind=actual_type["kind"],
                non_null=True,
            )
        elif _json["kind"] == GraphQLKind.LIST:
            typ = TypeRef(
                name=actual_type["name"],
                kind=actual_type["kind"],
                is_list=True,
            )
        else:
            raise ValueError(f'Unexpected type.kind: {_json["kind"]}')
    elif not _json["ofType"]["ofType"]["ofType"]:
        actual_type = _json["ofType"]["ofType"]

        if _json["kind"] == GraphQLKind.NON_NULL:
            typ = TypeRef(
                actual_type["name"],
                actual_type["kind"],
                True,
                False,
                True,
            )
        elif _json["kind"] == GraphQLKind.LIST:
            typ = TypeRef(
                name=actual_type["name"],
                kind=actual_type["kind"],
                is_list=True,
                non_null_item=True,
            )
        else:
            raise ValueError(f'Unexpected type.kind: {_json["kind"]}')
    elif not _json["ofType"]["ofType"]["ofType"]["ofType"]:
        actual_type = _json["ofType"]["ofType"]["ofType"]
        typ = TypeRef(
            name=actual_type["name"],
            kind=actual_type["kind"],
            is_list=True,
            non_null_item=True,
            non_null=True,
        )
    else:
        raise ValueError("Invalid field or arg (too many 'ofType')")

    return typ