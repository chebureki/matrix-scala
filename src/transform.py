#transform swagger-data into easily-to-generate codegen-data
import dataclasses
import re
from functools import reduce

import codegen
import swagger
from dataclasses import dataclass
from codegen import ApiModule,ModelModule, ArgumentType, Argument, Model,NamespacePath, InnerArgumentType
from swagger import SwaggerData,Reference, Swagger, Schema, PathItem, Parameter, Response
from enum import Enum
from typing import Optional, TypeVar
import os

# technically, items and schema should be two distinct things,
# but they are used interchangebly with minimal differences
# which will be handles as plain edge cases
Items = Schema

#should it be escaped?
#https://www.scala-lang.org/files/archive/spec/2.11/01-lexical-syntax.html#identifiers
def is_scala_identifier(ident: str)->bool:
    reserved_words = [
        "abstract", "case", "catch", "class", "def",
        "do", "else", "extends", "false", "final",
        "finally", "for", "forSome", "if", "implicit",
        "import", "lazy", "macro", "match", "new",
        "null", "object", "override", "package", "private",
        "protected", "return", "sealed", "super", "this",
        "throw", "trait", "try", "true", "type",
        "val", "var", "while", "with", "yield",
        "_", ":", "=", "=>", "<-", "<:", "<%", ">:", "#", "@",
        "⇒", "←"
    ]

    # this is _technically_ incorrect
    # python's implementation obviously differs
    # but eh, good enough init?
    return (ident not in reserved_words) and ident.isidentifier()


class ScalaBaseType(str, Enum):
    Int = "Int"
    Double = "Double"
    String = "String"
    Boolean = "Boolean"
    Seq = "Seq"
    Nothing = "Nothing"
    Any = "Any"# last resort :o

# for simple primitives
type_mapping: dict[str,ArgumentType] = {
    "string": ArgumentType(type=ScalaBaseType.String),
    "integer": ArgumentType(type=ScalaBaseType.Int),
    "boolean": ArgumentType(type=ScalaBaseType.Boolean),
    "number": ArgumentType(type=ScalaBaseType.Double),
}


def determine_allof_inner_types(schemas: list[Schema|Reference[Schema]], base_name: str, path: Optional[NamespacePath])->list[ArgumentType]:
    #base_name: Foo, i=0 => FooA
    def gen_alt_name(i: int)->str:
        assert 25>=i
        return f"{base_name}{chr(ord('A')+i)}"
    return list(
        map(
            lambda t: determine_schema_type(t[1],gen_alt_name(t[0]),path),
            enumerate(schemas)
        )
    )

def build_union_type(types: list[ArgumentType])->ArgumentType:
    le = len(types)

    #UnionN where N is the num of fields
    union_name = f"Union{le}"

    def build_link(i:int)->Optional[InnerArgumentType]:
        next_link = None if i<=1 else build_link(i-1)
        return None if i <= 0 else InnerArgumentType(
            value = types[le-i],
            next = next_link,
            has_next = next_link != None,
        )

    link = build_link(le)
    return ArgumentType(
        type=union_name,
        inner=link,
        has_inner=link != None,
    )


# with a fs read
def attempt_to_get_ref_title(ref: Reference)->Optional[str]:
    #raise NotImplemented
    #TODO: fix the references with a base path
    return None# TMP!


# try to come up with a title from it's file name
# i.e definitions/request_token_response.yaml => RequestTokenResponse
def synthesize_ref_title(path: str) -> str:
    full_file_name = os.path.basename(path)
    file_name = full_file_name.removesuffix(".yaml")
    return to_model_name(file_name)


def determine_reference_type(ref: Reference)->ArgumentType:
    str_type = attempt_to_get_ref_title(ref) or synthesize_ref_title(ref.ref)
    return ArgumentType(to_model_name(str_type))


def determine_items_type(items: Items | Reference, possible_model_name: str, path: NamespacePath)->ArgumentType:
    inner_type = determine_schema_type(items,possible_model_name,path)
    assert inner_type.type != ScalaBaseType.Any
    return ArgumentType(
        has_inner=True,inner=InnerArgumentType(inner_type),type=ScalaBaseType.Seq
    )

def determine_parameter_type(param: Parameter, possible_model_name: str, path: NamespacePath) -> ArgumentType:
    if param.type in type_mapping:
        return type_mapping[param.type]
    if param.items:
        return determine_items_type(param.items, possible_model_name, path)
    return ArgumentType(ScalaBaseType.Any)

def transform_parameter(param: Parameter)->Argument:
    return Argument(
        name=param.name,
        escape=not is_scala_identifier(param.name),
        #TODO:  this is quite the code stink, this parameter _should_ not exist!!!
        #       if everything goes right, the model-name will never be used!
        type=determine_parameter_type(param,"FAILURE", None)
    )

#"Some cool name" => "SomeCoolName"
def to_model_name(s: str)->str:
    delimiters="\s|-|_"
    #fooBarBar => FooBarBar
    #as opposed to pythons: fooBarBar => Foobarbar
    def capitalize_first_char(s: str)->str:
        return s[0].capitalize() + s[1:]
    return "".join(
        map(
            capitalize_first_char, re.split(delimiters,s)
        )
    )

#def attempt_model_name_from_schema(schema: Schema, field_name: Optional[str]=None)->Optional[str]:
#if field_name:
    #    return to_model_name(field_name)
    #raise Exception(f"unable to determine model-name for schema: {schema}")

def attempt_model_name_from_schema(schema: Schema) -> Optional[str]:
    if schema.title:
        return to_model_name(schema.title)

    return None


#def extract_definitions(swagger: Swagger)->list[DefinitionModel]:
#    raise NotImplemented

# a hacky extraction form swagger.info.title
# a possible alternative could be an extraction from a path's tag
def extract_module_name(swagger: Swagger)->str:
    assert swagger.info
    assert swagger.info.title
    info_title = swagger.info.title

    PREFIX="Matrix Client-Server "
    assert info_title.startswith(PREFIX)
    return to_model_name(info_title[len(PREFIX):])

# returns a list of (http_method, Operation)
def get_defined_operations(pi: PathItem) -> list[tuple[str, swagger.Operation]]:
    # this is terrible code
    # it returns a (Index, Value) tuple from a dataclass
    # where the value is not None
    # in this case to get a tuple of the http-method and operations
    # mypy fails here, don't believe a single word
    return list(filter(lambda t: t[1]!=None,pi.__dict__.items()))


def transform_path(endpoint: str, pi: PathItem)->list[codegen.Operation]:
    defined_tups: list[tuple[str,swagger.Operation]] = get_defined_operations(pi)
    return list(
        map(
            lambda t: transform_operation(t[0], endpoint, t[1]),
            defined_tups
        )
    )

def get_operation_default_http_response_code(sop: swagger.Operation)->int:
    # TODO: the _first_ response in the spec is obviously not the default
    return 200 if 200 in sop.responses else (list(sop.responses.keys())[0])

def response_model_alt_name(http_code: int)->str:
    return f"Response{http_code}"

def transform_operation(http_method: str, endpoint: str, sop: swagger.Operation)->codegen.Operation:
    assert sop.operationId
    def extract_and_transform_params_from(from_: str)->list[Argument]:
        return list(map(transform_parameter,extract_params_from_in(from_, sop.parameters or [])))

    # returns (code, type)
    def extract_default_response_type(namespace: NamespacePath)->tuple[int,ArgumentType]:
        resp_code = get_operation_default_http_response_code(sop)
        response = sop.responses[resp_code]
        if response.schema:
            if isinstance(response.schema, Schema):
                name = attempt_model_name_from_schema(response.schema) or response_model_alt_name(resp_code)
                return (resp_code,ArgumentType(name,path=namespace))
            else:
                #otherwise a reference
                return (resp_code, determine_reference_type(response.schema))
        else:
            return (resp_code, ArgumentType(ScalaBaseType.Nothing))
    def attempt_extract_body(namespace: NamespacePath)->Optional[ArgumentType]:
        body_args = extract_params_from_in("body", sop.parameters or []) #there should really only be 0..1 of those
        body_arg = body_args[0] if len(body_args) > 0 else None
        if not body_arg:
            return None #no defined bodys
        else:
            if body_arg.schema:
                # NOTE:  this requires a separate namespace, due to collisions
                #        here, it's namespaced with companion objects
                name = attempt_model_name_from_schema(body_arg.schema) or "Body"
                # body of "getFoo" will be pathed as: GetFoo.Body
                return ArgumentType(name,path=namespace)
            else:
                # TODO: log this fallback
                return ArgumentType(ScalaBaseType.Any)


    #TODO: this line is too long
    (path_args,query_args,header_args) = (extract_and_transform_params_from("path"),extract_and_transform_params_from("query"),extract_and_transform_params_from("header")) if sop.parameters else ([],[],[])
    #print(path_args,query_args,header_args)
    namespace = NamespacePath(to_model_name(sop.operationId))
    (default_code, response_type) = extract_default_response_type(namespace)
    body_type = attempt_extract_body(namespace)
    return codegen.Operation(
        operation_id=sop.operationId,
        endpoint=endpoint,
        http_method=http_method.upper(), #TODO: weird place to transform it, but okay
        default_code=default_code,

        #TODO: I heavily dislike this approach, as it requires a logical sync in the model extraction
        body_type=body_type,
        has_body=body_type!=None,
        path_args=path_args,
        query_args=query_args,
        header_args=header_args,
        response_type=response_type,
    )

def extract_schema_inner_models(schema: Schema) -> list[Model]:
    # TODO: this shouldn't be handled here!
    # only tmp!!!
    if not schema.properties:
        return []
    models: list[Model] = []

    # TODO: does this have ever have depth greater than one?
    def get_items_inner_most(items: Items)->Items:
        # quite the mouthful
        return get_items_inner_most(items.items) if items.items else items

    #TODO: this is very very ugly
    def append_schema(field_name: str, schema: Schema):
        name = attempt_model_name_from_schema(schema) or to_model_name(field_name)
        models.append(transform_schema(schema, name))
    # assert schema.properties
    for field_name, field_schema in schema.properties.items():
        if isinstance(field_schema,Schema):
            if field_schema.type == "object":
                append_schema(field_name,field_schema)
            if field_schema.items and isinstance(field_schema.items,Items):
                inner_most = get_items_inner_most(field_schema.items)
                if inner_most.type == "object":
                    append_schema(field_name, inner_most)

    #if len(models)>0:
    #    print(models)
    return models

# parameter and schema are decoupled.
# shame on you swagger v2
def determine_schema_type(schema: Schema | Reference, possible_model_name:str, path:Optional[NamespacePath]) -> ArgumentType:
    if isinstance(schema,Reference):
        return determine_reference_type(schema)
    #schema is array
    if schema.items:
        return determine_items_type(schema.items, possible_model_name, path)

    if schema.allOf:
        return build_union_type(determine_allof_inner_types(schema.allOf, possible_model_name,path))

    #TODO: actually support enums
    if schema.enum:
        return ArgumentType(ScalaBaseType.String)

    #TODO: this is an ugly ugly side-case
    # it allows for a String to be null
    # we will only consider the first primitive element for sake of simplicity
    if isinstance(schema.type,list):
        for t in schema.type:
            if t in type_mapping:
                return type_mapping[t]
        assert False

    if isinstance(schema.type, str):
        if schema.type in type_mapping:
            return type_mapping[schema.type]
        elif schema.type == "object": #TODO: ENUM!!!
            return ArgumentType(attempt_model_name_from_schema(schema) or possible_model_name,path=path)

    assert False

def extract_schema_fields(schema: Schema, namespace: NamespacePath) -> list[Argument]:
    #TODO: this shouldn't be handled here!
    # only tmp!!!
    if not schema.properties:
        return []
    fields: list[Argument] = []

    #assert schema.properties
    for field_name, field_schema in schema.properties.items():
        #TODO: this line is wayyy to long
        field_type = determine_reference_type(field_schema) if isinstance(field_schema,Reference) else (determine_schema_type(field_schema, attempt_model_name_from_schema(field_schema) or to_model_name(field_name),namespace))
        fields.append(
            Argument(
                name=field_name,
                escape=not is_scala_identifier(field_name),
                type=field_type,
            )
        )

    return fields

#def is_schema_blank()

# tuple: (Model, inner_imports)
def transform_schema(schema: Schema, name: str)->Model:
    inner_models = extract_schema_inner_models(schema)
    #print(inner_models)
    namespace = NamespacePath(name)
    fields = extract_schema_fields(schema, namespace)
    return Model(
        name=name,
        inner_models=inner_models,
        has_inner_models=len(inner_models) > 0,
        has_fields=True,
        fields=fields,
    )

T = TypeVar("T")
def flatten_2d(outer: list[list[T]])->list[T]:
    return [item for sublist in outer for item in sublist]

def extract_api(swagger: Swagger)->ApiModule:
    paths_ops = list(
        map(lambda t: transform_path(t[0], t[1]), swagger.paths.items())
    )
    # flatten it, like a good ol blin from babushka
    flattened = flatten_2d(paths_ops)
    return ApiModule(
        module_name=extract_module_name(swagger),
        imports=[],
        operations=flattened,
    )

    #TODO: perhaps make Operation.in a enum?
def extract_params_from_in(from_: str, params: list[Parameter])->list[Parameter]:
    return list(filter(lambda p: p._in == from_, params))


def extract_operation_model(op: swagger.Operation) -> Model:
    assert op.operationId
    model_name = to_model_name(op.operationId)
    #namespace = NamespacePath(model_name)

    def get_body_model() -> Optional[Model]:
        body_args = extract_params_from_in("body", op.parameters or [])
        body_arg = body_args[0] if len(body_args) > 0 else None
        if body_arg and body_arg.schema:
            name = attempt_model_name_from_schema(body_arg.schema) or "Body"
            model = transform_schema(body_arg.schema, name)
            return dataclasses.replace(model,is_body=True)
        else:
            return None

    def get_op_models() -> list[Model]:
        models = []
        for code, resp in op.responses.items():
            if resp.schema and isinstance(resp.schema, Schema):
                name = attempt_model_name_from_schema(resp.schema) or response_model_alt_name(code)
                models.append(transform_schema(resp.schema,name))
            # Refs don't need an entry, they're imported from Definitions
        return models

    opt_body_model = get_body_model()
    return Model(
        name=model_name,
        inner_models= get_op_models() + ([opt_body_model] if opt_body_model else []),
        has_inner_models=True,
        has_fields=False,
        fields=[]# TODO: this will create a dummy case class
    )

def extract_models(swagger:Swagger)->ModelModule:
    models = list(
        map(
            extract_operation_model,
            map(
                lambda t: t[1],
                flatten_2d(
                    list(
                        map(
                            get_defined_operations,
                            swagger.paths.values()
                        )
                    )
                )
            )
        )
    )

    return ModelModule(
        module_name=extract_module_name(swagger),
        imports=[],
        models=models,
    )

def transform_swagger(swagger: Swagger)->tuple[ModelModule,ApiModule]:
    return (
        extract_models(swagger),
        extract_api(swagger),
    )

def transform_definition(def_schema: Schema, path: str)->Model:
    #TODO: now this is plain garbage
    type = determine_reference_type(Reference(path))
    return transform_schema(def_schema,type.type)

@dataclass
class TransformationResult:
    apis: list[ApiModule]
    models: list[ModelModule]
    definitions: list[Model]

def transform_swaggers_for_codegen(data: SwaggerData) -> TransformationResult:
    (api, model) = reduce(
        # concat results
        lambda a, b: (a[0]+[b[0]],a[1]+[b[1]]),
        map(
            transform_swagger,
            data.swaggers
        ),
        (
            list[ModelModule](),
            list[ApiModule](),
        )
    )

    definitions = list(
        map(
            lambda t:transform_definition(t[1],t[0]),
            data.ref_path_lookup.items()
        )
    )
    return TransformationResult(model,api, definitions)
