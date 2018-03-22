from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from sandbox_orch_plugins import ServiceCommandHelper, ResourceCommandHelper, SandboxOrchPlugins
from collections import OrderedDict


def main():
    sandbox = Sandbox()
    DefaultSetupWorkflow().register(sandbox)

    bark_inputs = OrderedDict()
    bark_inputs['Times'] = '3'

    cmd_helper = ResourceCommandHelper(command_name='bark', inputs=bark_inputs)

    # stage hooks:
    sandbox.workflow.add_to_configuration(function=SandboxOrchPlugins().run_resource_command_on_all,
                                          components=cmd_helper)

    sandbox.execute_setup()

main()
