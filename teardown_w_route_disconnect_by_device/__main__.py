from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from sandbox_orch_plugins import ServiceCommandHelper, ResourceCommandHelper, RouteCommandHelper, SandboxOrchPlugins
from collections import OrderedDict


def main():
    sandbox = Sandbox()
    DefaultSetupWorkflow().register(sandbox)
    w2output = sandbox.automation_api.WriteMessageToReservationOutput

    model_list = ['Arista EOS Router']

    for model in model_list:
        route_helper = RouteCommandHelper(device_model=model)
        w2output(sandbox.id, 'Queueing Route Disconnection for {}'.format(model))
        sandbox.workflow.add_to_teardown(function=SandboxOrchPlugins().disconnect_routes_by_device_type(),
                                         components=route_helper)

    sandbox.execute_setup()

main()
