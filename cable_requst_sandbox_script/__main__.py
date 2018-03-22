from cloudshell.helpers.scripts import cloudshell_dev_helpers as dev_helper
from cloudshell.workflow.orchestration.sandbox import Sandbox
from base64 import b64decode
import smtplib
from email.mime.text import MIMEText
from cloudshell.core.logger import qs_logger
from time import strftime

SMTP_USER = 'no-reply@acmeco.com'
SMTP_MAIL_LIST = 'user1@acmeco.com;user2@acmeco.com'
SMTP_SERVER = 'mail-relay.acmeco.com'
SMTP_PORT = 25
HTTP_PREFIX = 'cloudshell.lab.acmeco.com:8080/RM/Diagram/Index/'  # portal address
HTTP_SECURE = False


def send_email(subject='', message=''):

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = SMTP_MAIL_LIST

    try:
        s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        s.sendmail(SMTP_USER, SMTP_MAIL_LIST, msg.as_string())
        s.quit()
    except Exception as e:
        logger = qs_logger.get_qs_logger()
        logger.warning('Unable to send email message')
        logger.warning(e.message)
        logger.warning(message)


def main():
    # Debugging Only:
    _d_user = 'admin'
    _d_pwrd = b64decode('')
    _d_host = 'localhost'
    _d_domain = 'Global'
    _d_id = '8cd7c1d7-b6ac-4b6e-a972-2cebb3a6a2a8'
    dev_helper.attach_to_cloudshell_as(_d_user, _d_pwrd, _d_domain, _d_id, server_address=_d_host)
    # end Debug section
    sandbox = Sandbox()
    cable_req = []
    routes = sandbox.automation_api.GetReservationDetails(sandbox.id).ReservationDescription.RequestedRoutesInfo
    for route in routes:
        if route.RouteType == 'cable':
            cable_req.append(route)

    if len(cable_req) > 0:
        owner = sandbox.reservationContextDetails.owner_user
        email = sandbox.automation_api.GetUserDetails(username=owner).Email
        subj = 'CloudShell Cable Request from {}'.format(owner)
        count = 0

        if HTTP_SECURE:
            wedge = 'https://{}'.format(HTTP_PREFIX)
        else:
            wedge = 'http://{}'.format(HTTP_PREFIX)

        wedge += sandbox.id
        link = '<a href="{}">{}</a>'.format(wedge, sandbox.id)

        msg = str()
        msg += 'CloudShell Request for Cabling\n'
        msg += '{}\n'.format(strftime('%Y-%m-%d %H:%M:%S'))
        msg += 'From User: {} ( {} )\n'.format(owner, email)
        msg += 'Sandbox Id: {}\n'.format(link)
        msg += 'Link: {}\n'.format(wedge)
        msg += '\n'
        msg += 'Requests:\n'

        for cable in cable_req:
            count += 1
            r_txt = str()
            r_txt += '  Cable # {}\n'.format(count)
            r_txt += '   > From: {}\n'.format(cable.Source)
            r_txt += '   >   To: {}\n'.format(cable.Target)
            r_txt += '\n'
            msg += r_txt

        msg += '-- End of Requests'

        # print msg
        send_email(subject=subj, message=msg)
        sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                               message='\nRequest for {} Cable(s) made'.format(count))
        for each in cable_req:
            sandbox.automation_api.WriteMessageToReservationOutput(reservationId=sandbox.id,
                                                                   message=' {} <---> {}'.format(each.Source,
                                                                                                 each.Target))
# end main


main()
