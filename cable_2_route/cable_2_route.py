import cloudshell.api.cloudshell_api as cs_api
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from json import loads as json_loads
from base64 import b64decode
from time import strftime


class ConvertCableToRoute(object):

    def __init__(self):
        self.json_file_path = './configs.json'  # manually set this
        self.configs = json_loads(open(self.json_file_path).read())
        self.cs_session = self._start_cloudshell_session()

        if self.cs_session:
            self.w2output = self.cs_session.WriteMessageToReservationOutput

    def _start_cloudshell_session(self):
        try:
            return cs_api.CloudShellAPISession(self.configs['cs_host'],
                                               username=self.configs['cs_user'],
                                               password=b64decode(self.configs['cs_pwrd']),
                                               domain=self.configs['cs_domain'])
        except CloudShellAPIError as e:
            print 'Unable to Connect to CloudShell!'
            print ' {}'.format(e.message)
            return None

    def check_id(self, id):
        """
        verifies that a ID is a valid Sandbox
        :param id:
        :return:
        """
        sandbox_detail = None

        try:
            sandbox_detail = self.cs_session.GetReservationDetails(id).ReservationDescription
        except CloudShellAPIError as err:
            print err.message

        if sandbox_detail.ActualEndTime == '':
            return True
        else:
            return False

    def convert_cable_to_route(self, id):
        """

        :param str id: Unique ID for a CloudShell Sandbox (Active Reservation)
        :return:
        """
        full_route_details = self.cs_session.GetReservationDetails(id).ReservationDescription.RequestedRoutesInfo

        con_list = []
        for route in full_route_details:
            if route.RouteType == 'cable':
                con_list.append(route)

        if len(con_list) > 0:
            for each in con_list:
                try:
                    self.cs_session.RemoveRoutesFromReservation(reservationId=id,
                                                                endpoints=[each.Source, each.Target],
                                                                mappingType='bi')

                    self.cs_session.UpdatePhysicalConnection(resourceAFullPath=each.Source,
                                                             resourceBFullPath=each.Target,
                                                             overrideExistingConnections=True)

                    self.cs_session.AddRoutesToReservation(reservationId=id,
                                                           sourceResourcesFullPath=[each.Source],
                                                           targetResourcesFullPath=[each.Target],
                                                           mappingType='bi')

                    self.cs_session.ConnectRoutesInReservation(reservationId=id,
                                                               endpoints=[each.Source, each.Target],
                                                               mappingType='bi')

                    print 'Converted Cable to Route:'
                    print '  {} <---> {}'.format(each.Source, each.Target)

                    self.w2output(reservationId=id, message='----------')
                    self.w2output(reservationId=id, message=strftime('%Y-%m-%d %H:%M:%S'))
                    self.w2output(reservationId=id, message='Converted Cable to Route')
                    self.w2output(reservationId=id, message='  {} <---> {}'.format(each.Source, each.Target))
                    self.w2output(reservationId=id, message='----------')

                except CloudShellAPIError as err:
                    print 'Unable to Complete Requested Connection'
                    print '{} <--> {}'.format(each.Source, each.Target)
                    print err.message
        else:
            print 'No Cables to Convert - Please check your ID or validate on the Canvas'


def main():
    local = ConvertCableToRoute()

    stop = False

    if local.cs_session:
        print 'Connected to CloudShell'

        while not stop:
            print "\nPlease Enter Sandbox/Reservation ID, or 'exit' to end"
            user_input = raw_input('ID: ')

            if user_input.upper() == 'EXIT' or user_input == '0':
                stop = True
            else:
                id_check = local.check_id(user_input.strip())

                if id_check:
                    local.convert_cable_to_route(user_input.strip())
                else:
                    print 'Invalid ID'

        print '-- Ending'


main()
