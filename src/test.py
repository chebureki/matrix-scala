#TODO: this file should be removed
import sys
import swagger
import codegen
import transform
from codegen import *
import yaml


if __name__ == "__main__":
    path = "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/"
    config_path = "/home/cheb/dev/matrix-scala/build_config.yaml"
    output_path = "/home/cheb/dev/matrix-scala/build/matrix-scala"
    templates_path = "/home/cheb/dev/matrix-scala/templates"
    swagger_data = swagger.load_swaggers_from_path(path)
    tr = transform.transform_swaggers_for_codegen(swagger_data)
    codegen_data = CodegenData(
        load_build_config(config_path),
        tr.apis, tr.models, tr.definitions
    )

    generate_project(
        codegen_data,
        output_path,
        templates_path
    )

# if __name__ == "__main__":
#     #paths=  ["/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/users.yaml"]
#     paths = ["/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/account-data.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/administrative_contact.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/admin.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/appservice_room_directory.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/banning.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/capabilities.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/content-repo.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/create_room.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/cross_signing.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/device_management.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/directory.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/event_context.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/filter.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/inviting.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/joining.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/key_backup.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/keys.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/kicking.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/knocking.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/leaving.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/list_joined_rooms.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/list_public_rooms.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/login.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/logout.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/message_pagination.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/notifications.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/old_sync.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/openid.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/peeking_events.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/presence.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/profile.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/pusher.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/pushrules.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/read_markers.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/receipts.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/redaction.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/refresh.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/registration_tokens.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/registration.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/relations.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/report_content.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/room_initial_sync.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/room_send.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/room_state.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/rooms.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/room_upgrades.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/search.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/space_hierarchy.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/sso_login_redirect.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/sync.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/tags.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/third_party_lookup.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/third_party_membership.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/threads_list.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/to_device.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/typing.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/users.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/versions.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/voip.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/wellknown.yaml", "/home/cheb/dev/matrix-scala/build/matrix-spec/data/api/client-server/whoami.yaml"]
#
#     def b():
#         swaggers = []
#         for v in paths:
#             try:
#                 file = open(v, "r")
#                 data = yaml.load(file, Loader=yaml.CLoader)
#                 file.close()
#                 swagger_data = swagger.load_swagger(data,v)  # dacite.from_dict(data_class=swagger.Swagger,data=data)
#                 swaggers.append(swagger_data)
#                 #print(f"P: {v}")
#             except:
#                 print(f"F: {v}")
#         codegen_data = CodegenData(
#             load_build_config("/home/cheb/dev/matrix-scala/build_config.yaml"),
#             *transform.transform_swaggers_for_codegen(swaggers)
#         )
#
#         #print(codegen_data)
#         generate_project(
#             codegen_data,
#             "/home/cheb/dev/matrix-scala/build/matrix-scala",
#             "/home/cheb/dev/matrix-scala/templates"
#         )
#
#
#     b()
#
#     def c():
#         cp = "/home/cheb/dev/matrix-scala/build_config.yaml"
#         tp = "/home/cheb/dev/matrix-scala/templates"
#         op = "/home/cheb/dev/matrix-scala/build/matrix-scala"
#         """
#         codegen.generate_project(
#             codegen.CodegenData(
#                 codegen.load_build_config(cp),[
#                     codegen.ApiModule("SomeModule",["Foo","Bar"],[codegen.Operation("getBitches","/getBitches","GET",200,"Bitch",
#                                                                                     [codegen.Argument("peter",codegen.ArgumentType(True,codegen.ArgumentType(True,codegen.ArgumentType(False,None,"String"),None),None))]
#                                                                                     ,[],[],False,"")])
#                 ],[], []
#             ),
#             op,tp
#         )
#         """
#         generate_project(
#             CodegenData(
#                 config=load_build_config(cp),
#                 api_modules=[ApiModule(
#                     "Test",
#                     [],
#                     [Operation(
#                         "getBitches",
#                         "get/Bitch/es",
#                         "GET",
#                         200,
#                         ArgumentType(
#                             True,
#                             ArgumentType(
#                                 False,
#                                 None,
#                                 "Bitch"
#                             ),
#                             "Seq",
#                         ),
#                         [],[],[],
#                         False,
#                         None,
#
#                     )]
#                 )],
#                 model_modules=[
#                     ModelModule(
#                         "Test",
#                         [],
#                         [
#                             Model(
#                                 True,
#                                 [
#                                     Model(
#                                         False,[],
#                                         "InnerBitch",
#                                         [
#                                             Argument(
#                                                 "a",
#                                                 ArgumentType(
#                                                     False,
#                                                     None,
#                                                     "Str"
#                                                 )
#                                             )
#                                         ]
#                                     )
#                                 ],
#                                 "Bitch",
#                                 [
#                                     Argument(
#                                         "inner",
#                                         ArgumentType(
#                                             False,
#                                             None,
#                                             "InnerBitch",
#                                             NamespacePath(
#                                                 "Bitch"
#                                             )
#                                         )
#                                     )
#                                 ]
#                             )
#                         ]
#                     )
#                 ],
#                 definition_models=[],
#             ),
#             op,tp
#         )
#         #codegen.generate(tp,op,)
