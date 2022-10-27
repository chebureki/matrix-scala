# NOTE:
# this swagger parser does NOT try to be a full implementation
# it ONLY implements features used by the matrix-spec, so a few shortcuts are made
# it also mostly implements spec-features which are relevant to code execution
# checkout out the swagger spec: https://swagger.io/specification/v2
from __future__ import annotations # for recursive type annotations
import dacite
import os
import yaml
from glob import glob
from dataclasses import dataclass
from functools import reduce
from operator import or_ as set_combine # | operator
from collections import namedtuple

from typing import Optional, Dict, Union, TypeVar, Generic,Any, Type

T = TypeVar("T")
@dataclass
class Reference(Generic[T]):
    ref: str


# Generics sadly break dacite. Uncomment line below for testing purposes
# enable the debug flag so dadict can parse the generic type, but be careful, this disables typechecking
#RefOrT = Union[Reference[T],T]
RefOrT = Union[Reference,T]
SWAGGER_DEBUG=True

#http://json-schema.org/
@dataclass
class Schema:
    title: Optional[str]
    description: Optional[str]
    type: Optional[Union[str,list[str]]]  # "string", "number", "integer", "boolean", or "array"
    format: Optional[str]
    items: Optional[RefOrT[Schema]]

    allOf: Optional[list[RefOrT[Schema]]] # never references

    additionalProperties: Optional[Union[Schema,bool]]
    default: Optional[Any]
    maximum: Optional[float]
    exclusiveMaximum: Optional[bool]
    minimum: Optional[float]
    exclusiveMinimum: Optional[bool]
    maxLength: Optional[int]
    minLength: Optional[int]
    pattern: Optional[str]
    maxItems: Optional[int]
    minItems: Optional[int]
    uniqueItems: Optional[bool]
    properties: Optional[dict[str,RefOrT[Schema]]]

    enum: Optional[list[Any]]
    multipleOf: Optional[float]
    # extensions ignored

Example = Dict[str, Any]# mime-type to example, incomplete for now!


@dataclass
class Header:
    description: Optional[str]
    type: str# "string", "number", "integer", "boolean", or "array"
    format: Optional[str]
    #items: Optional[RefOrT[Items]] # never used
    collectionFormat: Optional[str]# "string", "number", "integer", "boolean", or "array"
    default: Optional[Any]
    maximum: Optional[float]
    exclusiveMaximum: Optional[bool]
    minimum: Optional[float]
    exclusiveMinimum: Optional[bool]
    maxLength: Optional[int]
    minLength: Optional[int]
    pattern: Optional[str]
    maxItems: Optional[int]
    minItems: Optional[int]
    uniqueItems: Optional[bool]
    enum: Optional[list[Any]]
    multipleOf: Optional[float]
    # extensions ignored


Headers = Dict[str, Header]

@dataclass
class Response:
    description: str
    schema: Optional[RefOrT[Schema]]
    headers: Optional[Headers]
    examples: Optional[Example]

# TODO: does matrix ever use the default field?
# responses are never a reference in the matrix doc
Responses = Dict[int, Response]

@dataclass
class Operation:
    tags: Optional[list[str]]
    summary: Optional[str]
    description: Optional[str]
    externalDocs: Optional[ExternalDocumentation]
    operationId: Optional[str]
    consumes: Optional[list[str]]# overrides the global definition
    produces: Optional[list[str]]# overrides the global definition
    parameters: Optional[list[Parameter]]
    responses: Responses
    schemes: Optional[list[str]]# overrides the global definition
    deprecated: Optional[bool]
    security: Optional[list[SecurityRequirement]]

@dataclass
class PathItem:
    get: Optional[Operation]
    put: Optional[Operation]
    post: Optional[Operation]
    delete: Optional[Operation]
    options: Optional[Operation]
    head: Optional[Operation]
    patch: Optional[Operation]
    #parameters: Optional[list[Parameter]]# never a ref
    #parameters: Optional[list[RefOrT[Parameter]]]

# PathItems are never a reference in matrix spec
Paths = dict[str, PathItem]

##now, technically items and schema are distinct, but matrix uses them interchangeably
#@dataclass
#class Items:
#    type: Optional[Union[str, list[str]]] # "string", "number", "integer", "boolean", or "array"
#    format: Optional[str]
#    items: Optional[RefOrT[Items]]
#    #properties: Optional[dict[str, RefOrT[Schema]]]
#    collectionFormat: Optional[str]# how arrays are seperated, one of: csv, ssv, tsv, pipes
#    default: Optional[Any]
#    maximum: Optional[float]
#    exclusiveMaximum: Optional[bool]
#    minimum: Optional[float]
#    exclusiveMinimum: Optional[bool]
#    maxLength: Optional[int]
#    minLength: Optional[int]
#    pattern: Optional[str]
#    maxItems: Optional[int]
#    minItems: Optional[int]
#    uniqueItems: Optional[bool]
#    enum: Optional[list[Any]]
#    multipleOf: Optional[float]
#    #extensions ignored


# TODO: this should really be at least two classes, one of which being BodyParameter
@dataclass
class Parameter:
    name: str
    _in: str # "query", "header", "path", "formData" or "body"
    description: Optional[str]
    required: Optional[bool] # if _in==path => **must be true**, else optional and default is false
    schema: Optional[Schema]# _should_ hold a value if _in==body

    #if _in is NOT body
    type: Optional[str] # technically _not_ Optional, but whatever
    format: Optional[str] # "string", "number", "integer", "boolean", "array" or "file"
    allowEmptyValues: Optional[bool]

    items: Optional[Schema] # never a ref
    #items: Optional[RefOrT[Items]] # used if type is array


ParametersDefinitions = Dict[str,Parameter]

@dataclass
class SecurityScheme:
    type: str #"basic", "apiKey" or "oauth2"
    description: Optional[str]
    name: str
    in_: str #"query" or "header"
    #extensions ignored

    #TODO: oauth2 is NOT supported for now
    #flow: str #"implicit", "password", "application" or "accessCode"
    #authorizationUrl: str
    #tokenUrl: str
    #scope: Scopes


Definitions = Dict[str,Schema]
ResponsesDefinitions = Dict[str,Response]
SecurityRequirement = Dict[str,list[str]]
SecurityDefinitions = Dict[str, SecurityScheme]

@dataclass
class ExternalDocumentation:
    description: Optional[str]
    url: str
    # extensions ignored

@dataclass
class Contact:
    name: Optional[str]
    url: Optional[str]
    email: Optional[str]
    #extensions ignored

@dataclass
class License:
    name: str
    url: Optional[str]

@dataclass
class Info:
    title: str
    description: Optional[str]
    termsOfService: Optional[str]
    contact: Optional[Contact]
    license: Optional[License]
    version: str

@dataclass
class Tag:
    name: str
    description: Optional[str]
    externalDocs: Optional[ExternalDocumentation]

@dataclass
class Swagger:
    swagger: str #TODO: always 2.0?
    info: Info
    host: Optional[str]
    basePath: Optional[str]
    schemes: Optional[list[str]] #limited to "http", "https", "ws", "wss"
    consumes: Optional[list[str]]
    produces: Optional[list[str]]
    paths: Paths
    #not used: definitions: Optional[Definitions]
    parameters: Optional[ParametersDefinitions]
    responses: Optional[ResponsesDefinitions]
    securityDefinitions: Optional[Reference]
    security: Optional[list[SecurityRequirement]]
    tag: Optional[list[Tag]]
    externalDocs: Optional[ExternalDocumentation]
    # extensions ignored


#TODO: _almost all_ references point to a schema, except security-definitions that it :/
RefPathLookup = Dict[str, Schema]

@dataclass
class SwaggerData:
    swaggers: list[Swagger]
    ref_path_lookup: RefPathLookup

ident_replace_lookup: dict[str,str] = {
    "$ref": "ref",
    "in": "_in", #keyword :/
}

# replace any keys that can't be a python identifier
def dict_replace_keys(d: dict, lookup: dict[str,str])->dict:
    def replace(d: dict):
        for k in lookup.keys():
            if k in d:
                d[lookup[k]] = d.pop(k)
        for v in d.values():
            if isinstance(v,dict):
                replace(v)# recursion goes brrr
            if isinstance(v,list):
                for c in v:
                    if isinstance(c,dict):
                        replace(c)# recursion goes brrr
    copy = d.copy()
    replace(copy)
    return copy


def load_swagger_dict(path: str)->dict:
    with open(path, "r") as file:
        dict_data = data = yaml.load(file, Loader=yaml.CLoader)
        sanitised = dict_replace_keys(data, lookup=ident_replace_lookup)
        return sanitised

T = TypeVar("T")
def flatten_2d(outer: list[list[T]])->list[T]:
    return [item for sublist in outer for item in sublist]


# find all references within a swagger, but do not open references
def flat_extract_refs(swagger_dict: dict[str,any]) -> set[str]:
    def filter_dict(l:iter)->list:
        return list(filter(lambda t: isinstance(t, dict),l))
    ref: set[str] = {swagger_dict["ref"]} if "ref" in swagger_dict else set()
    dict_children = filter_dict(swagger_dict.values())
    array_children = filter_dict(flatten_2d(list(filter(lambda t: isinstance(t, list), swagger_dict.values()))))

    return set_combine(
        ref,
        reduce(
            set_combine,
            map(
                flat_extract_refs,
                dict_children + array_children,
            ),
            set[str]()
        )
    )


def load_swaggers_from_path(base_path: str)->SwaggerData:
    # base_path is just for reading, our lookup will only utilize relative_path
    RefWithPath = namedtuple("RefWithTuple",["base_path","relative_path"])
    def load_definition(base_path: str, ref_path: str) -> Schema:
        data = load_swagger_dict(os.path.join(base_path, ref_path))
        return dacite.from_dict(data_class=Schema, data=data, config=dacite.Config(check_types=not SWAGGER_DEBUG))

    # this implementation causes a swagger to be read multiple times, if referenced a lot
    def rec_inner_refs(inner: RefWithPath, visited: set[RefWithPath])->set[RefWithPath]:
        inner_dict = load_swagger_dict(os.path.join(inner.base_path, inner.relative_path))

        extracted_refs = flat_extract_refs(inner_dict)
        inner_refs = set(
            map(
                lambda p: RefWithPath(
                    os.path.join(inner.base_path,os.path.dirname(inner.relative_path)),
                    p
                ),
                flat_extract_refs(inner_dict)
            )
        )
        diff = inner_refs - visited
        if len(diff) == 0:
            return visited.union({inner})
        now_visited = visited.union(diff).union({inner})
        return reduce(
            set_combine,
            map(
                lambda i: rec_inner_refs(i, now_visited),
                diff
            ),
            now_visited
        )

    swagger_paths = glob(os.path.join(base_path, "*.yaml"))
    swagger_dicts = list(map(load_swagger_dict, swagger_paths))
    swaggers = list(
        map(
            lambda dict_data: dacite.from_dict(data_class=Swagger, data=dict_data,
                                               config=dacite.Config(check_types=not SWAGGER_DEBUG)),
            swagger_dicts
        )
    )

    flat_refs: set[RefWithPath] = set(
        map(
            lambda p: RefWithPath(base_path,p),
            reduce(
                set_combine,
                map(
                    flat_extract_refs,
                    swagger_dicts
                )
            )
        )
    )

    recursive_refs = reduce(
        set_combine,
        map(
            lambda inner: rec_inner_refs(inner, set()),
            flat_refs
        ),
        set()
    )

    ref_path_lookup: dict[str, Schema] = dict(
        map(
            lambda refWithTuple: (refWithTuple.relative_path,load_definition(refWithTuple.base_path,refWithTuple.relative_path)),
            recursive_refs
        )
    )


    return SwaggerData(
        swaggers,
        ref_path_lookup,
    )