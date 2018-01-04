from cable_2_route import ConvertCableToRoute

unit = ConvertCableToRoute()
test_id = '10fd2bd9-0c53-49ba-9967-ea889bef36bb'

if unit.cs_session:
    if unit.check_id(test_id):
        unit.convert_cable_to_route(test_id)
    else:
        print 'Invalid ID'
else:
    'No valid session to CloudShell -- Exit'
