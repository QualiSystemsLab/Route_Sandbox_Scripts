from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.api.cloudshell_api import InputNameValue, ResourceCommandListInfo
from collections import OrderedDict


class ResourceCommandHelper(object):
    def __init__(self, command_name='', device_name='', device_family='', device_model='', run_type='enqueue',
                 inputs={}):
        """

        :param string command_name: Name of the Command on the Resource to Run
        :param string device_family: The Name of the Device Family for lookup to run against (validation)
        :param string device_model: The Name of the Device Model for lookup to run against (validation)
        :param string device_name: The Name of the Exact Device to run against (validation)
        :param string run_type: enqueue or execute - how to run the command (fire & forget vs wait to complete)
                                *Connected Commands can only Execute
        :param OrderedDict inputs: Key == Input Name, Value == Input Value
        """
        self.command_name = command_name
        self.device_name = device_name.upper()
        self.family_name = device_family.upper()
        self.model_name = device_model.upper()
        self.run_type = run_type.upper()
        self.parameters = inputs


class ServiceCommandHelper(object):
    def __init__(self, command_name='', service_name='', run_type='enqueue', inputs={}):
        """

        :param string command_name: Name of the Command on the Service to Run
        :param string service_name: Name of the Service to Use
        :param string run_type: Enqueue or Execute this command (fire and forget vs wait to complete)
        :param OrderedDict inputs: Key == Input Name, Value == Input Value
        """
        self.command_name = command_name
        self.service_name = service_name.upper()
        self.run_type = run_type.upper()
        self.parameters = inputs


class RouteCommandHelper(object):
    def __init__(self, device_name='', device_family='', device_model='', route_type='', evaluate_connection_by='Either'):
        """
        Designed to allow qualifiers to be used with determining which routes to activate or deactivate
        :param device_name: Name of the Exact Device to use
        :param device_family: Name of the Device Family
        :param device_model:
        :param route_type:
        :param str evaluate_connection_by:  Judge Route by 'Source', 'Target' or 'Either'
        """
        self.device_name = device_name.upper()
        self.device_family = device_family.upper()
        self.device_model = device_model.upper()
        self.route_type = route_type.upper()
        self.evaluate_by = evaluate_connection_by.upper()


class SandboxOrchPlugins(object):
    def __init__(self):
        pass

    def _build_cmd_list_from_cmdlistinfo(self, command_list):
        """
        builds
        :param list ResourceCommandListInfo command_list:
        :return: list commands:
        """
        commands = []
        for each in command_list:
            commands.append(each.Name)

        return commands

    def _build_resource_command_lists(self, sandbox, device_name):
        """

        :param Sandbox sandbox:
        :param str device_name:
        :return: list str reg_commands, con_commands:  Returns two lists, Regular Commands & Connected Commands
        """
        reg_commands = self._build_cmd_list_from_cmdlistinfo(
            sandbox.automation_api.GetResourceCommands(device_name).Commands)

        con_commands = self._build_cmd_list_from_cmdlistinfo(
            sandbox.automation_api.GetResourceConnectedCommands(device_name).Commands)

        return reg_commands, con_commands

    def _build_command_params(self, param_dict):
        """

        :param dict param_dict:
        :return: list str out: list of inputs with value [input1, value1, input2, value2, ... inputN, valueN]
        """
        out = []
        for key in param_dict.keys():
            out.append(InputNameValue(key, param_dict[key]))

        return out

    def connect_all_routes(self, sandbox, components):
        """
        examines the routes listed for the sandbox being activated, and creates two lists of routes to be created
        (bi & uni-directional).  Lists passed into the ConnectRoutesInReservation are just paired endpoints
        in an open list:
        ['source1', 'target1', 'source2', 'target2', ... 'sourceN', 'targetN']
        :param Sandbox sandbox: Sandbox context obj
        :param TopologiesRouteInfo components:  List of Route Objects found in the reservation being used
        :return: Bool result: If Command Called
        """
        result = False
        w2output = sandbox.automation_api.WriteMessageToReservationOutput
        bi_routes = []
        uni_routes = []
        for route in components:
            for r in route:
                if r.RouteType == 'bi':
                    bi_routes.append(r.Source)
                    bi_routes.append(r.Target)
                elif r.RouteType == 'uni':
                    uni_routes.append(r.Source)
                    uni_routes.append(r.Target)

        # set Bi-Dir Routes:
        if len(bi_routes) > 0:
            try:
                w2output(sandbox.id,
                         'Queueing {} Bi-Dir Routes for Connection'.format(len(bi_routes) / 2))
                sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id,
                                                                  endpoints=bi_routes,
                                                                  mappingType='bi')
                result = True
            except Exception as err:
                w2output(sandbox.id, err.message)

        if len(uni_routes) > 0:
            try:
                w2output(sandbox.id,
                         'Queueing {} Uni-Dir Routes for Connection'.format(len(uni_routes) / 2))
                sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id,
                                                                  endpoints=uni_routes,
                                                                  mappingType='uni')
                result = True
            except Exception as err:
                w2output(sandbox.id, err.message)

        return result

    def disconnect_all_routes(self, sandbox, components):
        """
        examines the all routes listed in the sandbox being, and creates a list of routes to be disconnected
        Lists passed into the ConnectRoutesInReservation are just paired endpoints
        in an open list:
        ['source1', 'target1', 'source2', 'target2', ... 'sourceN', 'targetN']
        :param Sandbox sandbox: Sandbox context obj
        :param TopologiesRouteInfo components:  List of Route Objects found in the reservation being used
        :return: Bool result: If Command Called
        """
        result = False
        w2output = sandbox.automation_api.WriteMessageToReservationOutput
        routes = []
        for route in components:
            for r in route:
                routes.append(r.Source)
                routes.append(r.Target)

        if len(routes) > 0:
            try:
                w2output(sandbox.id,
                         'Queueing {} Routes for disconnection'.format(len(routes) / 2))
                sandbox.automation_api.DisconnectRoutesInReservation(reservationId=sandbox.id,
                                                                     endpoints=routes)
                result = True
            except Exception as err:
                w2output(reservationId=sandbox.id, message=err.message)

        return result

    def connect_select_routes_by_type(self, sandbox, components):
        """
        Connect Routes if they are ["Bi" or "Uni"]
        :param Sandbox sandbox:
        :param RouteCommandHelper components:
        :return:
        """
        result = False
        if components.route_type != '':
            w2output = sandbox.automation_api.WriteMessageToReservationOutput
            tar_routes = []
            routes = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.TopologiesRouteInfo
            for route in routes:
                for r in route:
                    if r.RouteType.upper() == components.route_type:
                        tar_routes.append(r.Source)
                        tar_routes.append(r.Target)
            try:
                w2output(sandbox.id, 'Queuing Connection of {} {} Routes'.format(len(tar_routes)/2,
                                                                                 components.route_type)
                         )
                sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id, endpoints=tar_routes,
                                                                  mappingType=components.route_type.lower())
                result = True
            except Exception as err:
                w2output(reservationId=sandbox.id, message=err.message)

        return result

    def disconnect_select_routes_by_type(self, sandbox, components):
        """
        Connect Routes if they are ["Bi" or "Uni"]
        :param Sandbox sandbox:
        :param RouteCommandHelper components:
        :return:
        """
        result = False
        if components.route_type != '':
            w2output = sandbox.automation_api.WriteMessageToReservationOutput
            tar_routes = []
            routes = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.TopologiesRouteInfo
            for route in routes:
                for r in route:
                    if r.RouteType.upper() == components.route_type:
                        tar_routes.append(r.Source)
                        tar_routes.append(r.Target)
            try:
                w2output(sandbox.id, 'Queuing Connection of {} {} Routes'.format(len(tar_routes)/2,
                                                                                 components.route_type)
                         )
                sandbox.automation_api.DisconnectRoutesInReservation(reservationId=sandbox.id, endpoints=tar_routes,
                                                                     mappingType=components.route_type.lower())
                result = True
            except Exception as err:
                w2output(reservationId=sandbox.id, message=err.message)

        return result

    def connect_routes_by_device_type(self, sandbox, components):
        """
        Connect Routes if they are ["Bi" or "Uni"]
        :param Sandbox sandbox:
        :param RouteCommandHelper components:
        :return:
        """
        result = False
        if components.route_type != '':
            w2output = sandbox.automation_api.WriteMessageToReservationOutput
            bi_routes = []
            uni_routes = []
            devices = sandbox.components.resources
            matching_devices = []
            for device in devices:
                family = sandbox.automation_api.GetResourceDetails(device).ResourceFamilyName
                model = sandbox.automation_api.GetResourceDetails(device).ResourceModelName
                if components.device_family == family:
                    matching_devices.append(device)
                elif components.device_model == model:
                    matching_devices.append(device)
                elif components.device_name.upper() in device.upper():
                    matching_devices.append(device)
            routes = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.TopologiesRouteInfo
            for route in routes:
                for r in route:
                    base_target = r.Target.split('/')[0]
                    base_source = r.Source.split('/')[0]
                    if base_source in matching_devices or base_target in matching_devices:
                        if r.RouteType.upper() == 'BI':
                            bi_routes.append(r.Source)
                            bi_routes.append(r.Target)
                        if r.RouteType.upper() == 'UNI':
                            uni_routes.append(r.Source)
                            uni_routes.append(r.Target)
            try:
                # Bi-Routes
                w2output(sandbox.id, 'Queuing Connection of {} {} Routes'.format(len(bi_routes) / 2, 'Bi-Directional'))
                sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id, endpoints=bi_routes,
                                                                  mappingType=components.route_type.lower())
                # Uni-Routes
                w2output(sandbox.id, 'Queuing Connection of {} {} Routes'.format(len(uni_routes) / 2, 'Uni'))
                sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id, endpoints=uni_routes,
                                                                  mappingType=components.route_type.lower())
                result = True
            except Exception as err:
                w2output(reservationId=sandbox.id, message=err.message)

        return result

    def disconnect_routes_by_device_type(self, sandbox, components):
        """
        :param Sandbox sandbox:
        :param RouteCommandHelper components:
        :return: Boolean:  If it did something w/out error - no route changes will still return false
        """
        result = False
        if components.route_type != '':
            w2output = sandbox.automation_api.WriteMessageToReservationOutput
            tar_routes = []
            devices = sandbox.components.resources
            matching_devices = []
            for device in devices:
                family = sandbox.automation_api.GetResourceDetails(device).ResourceFamilyName
                model = sandbox.automation_api.GetResourceDetails(device).ResourceModelName
                if components.device_family == family:
                    matching_devices.append(device)
                elif components.device_model == model:
                    matching_devices.append(device)
                elif components.device_name.upper() in device.upper():
                    matching_devices.append(device)
            routes = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.TopologiesRouteInfo
            for route in routes:
                for r in route:
                    base_target = r.Target.split('/')[0]
                    base_source = r.Source.split('/')[0]
                    if base_target in matching_devices or base_source in matching_devices:
                        tar_routes.append(r.Target)
                        tar_routes.append(r.Source)

            try:
                w2output(sandbox.id, 'Queuing Connection of {} {} Routes'.format(len(tar_routes)/2,
                                                                                 components.route_type)
                         )
                sandbox.automation_api.DisconnectRoutesInReservation(reservationId=sandbox.id, endpoints=tar_routes)
                result = True
            except Exception as err:
                w2output(reservationId=sandbox.id, message=err.message)

        return result

    def run_resource_command_on_all(self, sandbox, components):
        """
        designed to call a singular command on all devices, such as a Power Up.
        Verifies first that the command exists, and then launches it.
        Execute vs. Enqueue - Execute waits for it to complete
        :param Sandbox sandbox:
        :param ResourceCommandHelper components: Use the CommandHelper (ignores Family & Model)
        :return: Bool result: If command was called
        """
        result = False

        if components.command_name == '':  # if the command is blank, stop here
            return result

        devices = sandbox.components.resources
        for device in devices:
            reg_cmd_check = False

            reg_commands, con_commands = self._build_resource_command_lists(sandbox, device)

            if len(reg_commands) > 0:
                if components.command_name in reg_commands:
                    reg_cmd_check = True
                    params = self._build_command_params(components.parameters)

                    try:
                        if components.run_type == 'EXECUTE':
                            sandbox.automation_api.ExecuteCommand(reservationId=sandbox.id,
                                                                  targetName=device,
                                                                  targetType='Resource',
                                                                  commandName=components.command_name,
                                                                  commandInputs=params)
                            result = True
                        elif components.run_type == 'ENQUEUE':
                            sandbox.automation_api.EnqueueCommand(reservationId=sandbox.id,
                                                                  targetName=device,
                                                                  targetType='Resource',
                                                                  commandName=components.command_name,
                                                                  commandInputs=params)
                            result = True
                    except Exception as err:
                        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                               message=err.message)

            if len(con_commands) > 0 and not reg_cmd_check:
                if components.command_name in con_commands:
                    try:
                        params = self._build_command_params(components.parameters)
                        sandbox.automation_api.ExecuteResourceConnectedCommand(reservationId=sandbox.id,
                                                                               resourceFullPath=device,
                                                                               commandName=components.command_name,
                                                                               parameterValues=params)
                        result = True
                    except Exception as err:
                        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                               message=err.message)

        return result

    def run_resource_command_on_select(self, sandbox, components):
        """

        :param Sandbox sandbox:
        :param ResourceCommandHelper components:
        :return: Bool result: If a command was called
        """
        result = False

        if components.command_name == '':  # if the command is blank, stop here
            return result

        devices = sandbox.components.resources

        for device in devices:
            reg_commands = []  # commands as part of the Shell/Driver
            con_commands = []  # commands inherited via connection (Power)
            reg_cmd_check = False
            resource = sandbox.automation_api.GetResourceDetails(device)

            # build commands lists on the device is conditions are meet
            # - A specific device name is meet
            # - Matches Specific Family / Model combo
            # - Matches Specific Model Name, no Family Name specified (as Model Names a unique, this is an edge case)
            # - Matches Specific Family Name, no Model Name specified
            if components.device_name == device.upper():

                reg_commands, con_commands = self._build_resource_command_lists(sandbox, device)

            elif components.family_name == resource.ResourceFamilyName.upper() and \
                    components.model_name == resource.ResourceModelName.upper() and components.device_name == '':

                reg_commands, con_commands = self._build_resource_command_lists(sandbox, device)

            elif components.model_name == resource.ResourceModelName.upper() and \
                    components.family_name == '' and components.device_name == '':

                reg_commands, con_commands = self._build_resource_command_lists(sandbox, device)

            elif components.family_name == resource.ResourceFamilyName.upper() and \
                    components.model_name == '' and components.device_name == '':

                reg_commands, con_commands = self._build_resource_command_lists(sandbox, device)

            if len(reg_commands) > 0:
                if components.command_name in reg_commands:
                    reg_cmd_check = True
                    params = self._build_command_params(components.parameters)

                    try:
                        if components.run_type == 'EXECUTE':
                            sandbox.automation_api.ExecuteCommand(reservationId=sandbox.id,
                                                                  targetName=device,
                                                                  targetType='Resource',
                                                                  commandName=components.command_name,
                                                                  commandInputs=params)
                            result = True
                        elif components.run_type == 'ENQUEUE':
                            sandbox.automation_api.EnqueueCommand(reservationId=sandbox.id,
                                                                  targetName=device,
                                                                  targetType='Resource',
                                                                  commandName=components.command_name,
                                                                  commandInputs=params)
                            result = True
                    except Exception as err:
                        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                               message=err.message)

            if len(con_commands) > 0 and not reg_cmd_check:
                if components.command_name in con_commands:
                    try:
                        params = self._build_command_params(components.parameters)

                        sandbox.automation_api.ExecuteResourceConnectedCommand(reservationId=sandbox.id,
                                                                               resourceFullPath=device,
                                                                               commandName=components.command_name,
                                                                               parameterValues=params)
                        result = True
                    except Exception as err:
                        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                               message=err.message)

        return result

    def run_service_command(self, sandbox, components):
        """

        :param Sandbox sandbox:
        :param ServiceCommandHelper components:
        :return: bool result:
        """
        result = False
        command_list = []
        cmds = sandbox.automation_api.GetServiceCommands(components.service_name)
        for cmd in cmds:
            command_list.append(cmd.Name)

        services = sandbox.components.services
        for each in services:
            # is this the service (droid) we're looking for?
            if each.ServiceName == components.service_name:
                # verify command is present
                if components.command_name in command_list:
                    params = self._build_command_params(components.parameters)

                    try:
                        if components.run_type == 'EXECUTE':
                            sandbox.automation_api.ExecuteCommand(reservationId=sandbox.id,
                                                                  targetName=components.service_name,
                                                                  targetType='Service',
                                                                  commandName=components.command_name,
                                                                  commandInputs=params)
                            result = True
                        if components.run_type == 'ENQUEUE':
                            sandbox.automation_api.EnqueueCommand(reservationId=sandbox.id,
                                                                  targetName=components.command_name,
                                                                  targetType='Service',
                                                                  commandName=components.command_name,
                                                                  commandInputs=params)
                            result = True
                    except Exception as err:
                        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                               message=err.message)

        return result
