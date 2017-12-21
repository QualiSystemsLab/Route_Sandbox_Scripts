import cloudshell.helpers.scripts.cloudshell_scripts_helpers as cs_helper
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

route_list = []

res_id = cs_helper.get_reservation_context_details().id
route_details = cs_helper.get_api_session().GetReservationDetails(res_id).ReservationDescription.TopologiesRouteInfo
w2output = cs_helper.get_api_session().WriteMessageToReservationOutput

# build route lists
# route lists used by the Route API are just are endpoints paired in an open list:
# ['source1', 'target1', 'source2', 'target2', ... 'sourceN', 'targetN']
for route in route_details:
    for r in route.Routes:
        route_list.append(r.Source)
        route_list.append(r.Target)


# execute routes
if len(route_list) > 0:
    try:
        w2output('Queuing {} routes for disconnection'.format(len(route_list)/2))
        cs_helper.get_api_session().DisconnectRoutesInReservation(reservationId=res_id, endpoints=route_list)
    except CloudShellAPIError as err:
        w2output(reservationId=res_id, message=err.message)
