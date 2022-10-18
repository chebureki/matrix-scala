from __future__ import annotations # for recursive type annotations

import dataclasses
from dataclasses import dataclass
import dataclasses
from typing import Optional, TypeVar, Callable
import dacite
import chevron
import os
import yaml


#NamespacePath("Foo",NP("Bar",NP("Data",None))) => Foo.Bar.Data
@dataclass
class NamespacePath:
    entry: str
    next: Optional[NamespacePath] = None

#@dataclass
#class ScalaUnion:
#    all_of: list[]


# the whole point of this class is so it can easily be comma separated in mustache lol
@dataclass
class InnerArgumentType:
    value: ArgumentType
    has_next: bool = False
    next: Optional[InnerArgumentType] = None

@dataclass
class ArgumentType:
    type: str
    inner: Optional[InnerArgumentType] = None
    has_inner: bool = False
    path: Optional[NamespacePath] = None

    #is_union: bool
    #union_types: Optional[list[ArgumentType]]

@dataclass
class Argument:
    name: str
    type: ArgumentType
    escape: bool
    #required: bool #should the transformer, or the template make this into an Option??

@dataclass
class Operation:
    operation_id: str
    endpoint: str
    http_method: str
    default_code: int
    response_type: ArgumentType
    path_args: list[Argument]
    query_args: list[Argument]
    header_args: list[Argument]
    has_body: bool
    body_type: Optional[ArgumentType]

@dataclass
class Model:
    has_inner_models: bool # => create a  companion object
    inner_models: list[Model]
    name: str
    #num_fields: int # for JsonWriter
    #has_extra_fields: bool # allow JsObject
    #is_empty: bool # => alias to EmptyBody
    has_fields: bool # just a namespace if false
    fields: Optional[list[Argument]]

    is_body: bool = False# just so the ApiRequestBody trait is extended

@dataclass
class ApiModule:
    module_name: str
    imports: list[str]
    operations: list[Operation]

@dataclass
class ModelModule:
    module_name: str
    imports: list[str]
    models: list[Model]


@dataclass
class BuildConfig:
    version: str
    project_name: str
    package_base: str
    author: str
    group_id: str
    scala_version: str
    akka_http_version: str
    akka_version: str
    spray_json_version: str

@dataclass
class CodegenData:
    config: BuildConfig
    apis: list[ApiModule]
    models: list[ModelModule]
    definitions: list[Model]

def load_build_config(path: str)->BuildConfig:
    with open(path, "r") as file:
        data = yaml.load(file, Loader=yaml.CLoader)
        return dacite.from_dict(data_class=BuildConfig, data=data)

T = TypeVar('T')
def generate(template_path: str, base_path: str, data_entries: list[T], file_name: Callable[[T],str], env: dict, partials: dict[str,str]):
    with open(template_path, 'r') as tf:
        template_str = tf.read()
        for data_entry in data_entries:
            data_dict = dataclasses.asdict(data_entry) | env
            rendered = chevron.render(template_str, data_dict, partials_dict=partials, warn=True)
            with open(os.path.join(base_path,file_name(data_entry)),"w") as of:
                of.write(rendered)
                of.flush()

#kinda ugly, that these are hard-coded, but optimization is for another time
def load_partials(tp: str)->dict[str,str]:
    def load(p: str)->str:
        with open(p,"r") as f:
            return f.read()
    return {
        "operation": load(os.path.join(tp, "operation.mustache")),
        "header": load(os.path.join(tp, "header.mustache")),
        "model": load(os.path.join(tp, "model.mustache")),
        "argument": load(os.path.join(tp, "argument.mustache")),
        "argument_type": load(os.path.join(tp, "argument_type.mustache")),
        "ns_path": load(os.path.join(tp, "ns_path.mustache")),
        "argument_name": load(os.path.join(tp, "argument_name.mustache")),
        "inner_argument_type": load(os.path.join(tp, "inner_argument_type.mustache"))
    }

#com.foo.bar.api => [com, foo, bar, api]
def split_package(pkg: str)-> list[str]:
    return pkg.split('.')

def generate_project(data: CodegenData, out_path: str, template_path: str):
    def const_path(name: str):
        return lambda _: name

    pkg_dot_components = split_package(data.config.package_base)
    src_path = os.path.join(out_path, "src", "main", "scala", *pkg_dot_components)
    model_path = os.path.join(src_path, "model")
    api_path = os.path.join(src_path, "api")
    core_path = os.path.join(src_path, "core")
    definitions_path = os.path.join(model_path,"definitions")

    #create dirs
    for path in [src_path,model_path,api_path,core_path,definitions_path]:
        os.makedirs(path,exist_ok=True)

    partials = load_partials(template_path)
    env = dataclasses.asdict(data.config)

    generate(os.path.join(template_path, "README.md.mustache"), out_path, [data],const_path("README.md"),env,partials)
    generate(os.path.join(template_path, "pom.xml.mustache"), out_path, [data], const_path("pom.xml"), env,partials)
    generate(os.path.join(template_path, "build.sbt.mustache"), out_path, [data], const_path("build.sbt"), env,partials)
    generate(os.path.join(template_path, "api_core.mustache"), out_path, [data], const_path(os.path.join(core_path,"ApiCore.scala")), env,partials)

    generate(os.path.join(template_path, "models_module.mustache"), model_path, data.models, lambda m: f"{m.module_name}.scala", env,partials)
    generate(os.path.join(template_path, "api_module.mustache"), api_path, data.apis,lambda m: f"{m.module_name}.scala", env,partials)
    generate(os.path.join(template_path, "definition_model.mustache"), definitions_path, data.definitions, lambda m: f"{m.name}.scala", env,partials)