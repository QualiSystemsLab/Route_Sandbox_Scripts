import cloudshell.helpers.scripts.cloudshell_scripts_helpers as cs_helper
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

bi_dir = []
uni_dir = []

res_id = cs_helper.get_reservation_context_details().id
route_details = cs_helper.get_api_session().GetReservationDetails(res_id).ReservationDescription.TopologiesRouteInfo
w2output = cs_helper.get_api_session().WriteMessageToReservationOutput

# build route lists
# route lists used by the Route API are just are endpoints paired in an open list:
# ['source1', 'target1', 'source2', 'target2', ... 'sourceN', 'targetN']
for route in route_details:
    for r in route.Routes:
        if r.RouteType == 'bi':
            bi_dir.append(r.Source)
            bi_dir.append(r.Target)
        if r.RouteType == 'uni':
            uni_dir.append(r.Source)
            uni_dir.append(r.Target)

# execute routes
if len(bi_dir) > 0:
    try:
        w2output(reservationId=res_id,
                 message='Queuing {} Bi-Dir routes for connection'.format(len(bi_dir)/2))
        cs_helper.get_api_session().ConnectRoutesInReservation(reservationId=res_id, endpoints=bi_dir,
                                                               mappingType='bi')
    except CloudShellAPIError as err:
        w2output(reservationId=res_id, message=err.message)

if len(uni_dir) > 0:
    try:
        w2output(reservationId=res_id,
                 message='Queuing {} Uni-Dir routes for connection'.format(len(uni_dir)/2))
        cs_helper.get_api_session().ConnectRoutesInReservation(reservationId=res_id, endpoints=uni_dir,
                                                               mappingType='uni')
    except CloudShellAPIError as err:
        w2output(reservationId=res_id, message=err.message)