from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow


def main():
    sandbox = Sandbox()
    DefaultSetupWorkflow().register(sandbox)

    route_details = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.TopologiesRouteInfo

    # stage hooks:
    sandbox.workflow.add_to_connectivity(function=do_route_connections, components=route_details)
    sandbox.execute_setup()


def do_route_connections(sandbox, components):
    """
    examines the routes listed for the sandbox being activated, and creates two lists of routes to be created
    (bi & uni-directional).  Lists passed into the ConnectRoutesInReservation are just paired endpoints
    in an open list:
    ['source1', 'target1', 'source2', 'target2', ... 'sourceN', 'targetN']
    :param Sandbox sandbox: Sandbox context obj
    :param TopologiesRouteInfo components:  List of Route Objects found in the reservation being used
    :return: None
    """
    bi_direction = []
    uni_direction = []
    for route in components:
        for r in route:
            if r.RouteType == 'bi':
                bi_direction.append(r.Source)
                bi_direction.append(r.Target)
            elif r.RouteType == 'uni':
                uni_direction.append(r.Source)
                uni_direction.append(r.Target)

    # set bi-directional routes
    if len(bi_direction) > 0:
        try:
            sandbox.automation_api.WriteMessageToReservationOutput(
                'Queuing {} Bi-Dir routes for connection'.format(len(bi_direction) / 2))

            sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id,
                                                              endpoints=bi_direction, mappingType='bi')
        except Exception as err:
            sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id, message=err.message)

    # set uni-directional routes
    if len(uni_direction) > 0:
        try:
            sandbox.automation_api.WriteMessageToReservationOutput(
                'Queuing {} Uni-Dir routes for connection'.format(len(uni_direction) / 2))

            sandbox.automation_api.ConnectRoutesInReservation(reservationId=sandbox.id,
                                                              endpoints=uni_direction, mappingType='uni')
        except Exception as err:
            sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id, message=err.message)


main()
