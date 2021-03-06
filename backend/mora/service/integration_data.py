# SPDX-FileCopyrightText: 2018-2020 Magenta ApS
# SPDX-License-Identifier: MPL-2.0

'''
Integration data
----------------

This module handles reading of integration data

Integration data is typically key-value pairs tieing an entity in OS2mo/LoRa to
an entity in another IT-system. This way previously transferred data can be
identified, be it an employee in a salary-system or an organisational unit in
an ERP-system.

Inserting/editing integration data is done using the endpoints for
inserting/updating organisational units and employees

'''
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter

from . import employee
from . import orgunit
from .. import common
from .. import exceptions
from .. import mapping

router = APIRouter()


@router.get('/ou/{unitid}/integration-data')
# @util.restrictargs('at')
async def get_org_unit_integration_data(
    unitid: UUID,
    only_primary_uuid: Optional[bool] = None
):
    """Get organisational unit with integration data

    .. :quickref: Unit ; integration data

    :param uuid unitid: UUID of the unit to retrieve.

    :queryparam date at: Show the unit at this point in time,
        in ISO-8601 format.

    :statuscode 200: Integration data (json) retrieved
    :statuscode 404: No such unit found.


    :returns: organisational unit with integration data as json

    **Example Response**:

    .. sourcecode:: json

        {
          "integration_data": {},
          "name": "Ballerup Bibliotekasdfasdf",
          "user_key": "BIBLIOTEK",
          "uuid": "921e44d3-2ec0-4c16-9935-2ec7976566dc",
          "validity": {
            "from": "1993-01-01",
            "to": null
          }
        }

    """
    unitid = str(unitid)
    c = common.get_connector()

    r = await orgunit.get_one_orgunit(c, unitid,
                                      details=orgunit.UnitDetails.INTEGRATION,
                                      only_primary_uuid=only_primary_uuid)

    if not r:
        exceptions.ErrorCodes.E_ORG_UNIT_NOT_FOUND(org_unit_uuid=unitid)

    if r[mapping.INTEGRATION_DATA]:
        r[mapping.INTEGRATION_DATA] = json.loads(r[mapping.INTEGRATION_DATA])
    else:
        r[mapping.INTEGRATION_DATA] = {}

    return r


@router.get('/e/{employeeid}/integration-data')
# @util.restrictargs('at')
async def get_employee_integration_data(
    employeeid: UUID,
    only_primary_uuid: Optional[bool] = None
):
    """Get employee with integration data

    .. :quickref: Employee; integration data

    :param uuid employeeid: UUID of the employee to retrieve.

    :queryparam date at: Show the employee at this point in time,
        in ISO-8601 format.

    :statuscode 200: Integration data (json) retrieved
    :statuscode 404: No such employee found.

    :returns: employee with integration data as json

    **Example Response**:

    .. sourcecode:: json

        {
          "integration_data": {},
          "name": "Sanne Sch\u00e4ff",
          "uuid": "1ce40e25-6238-4202-9e93-526b348ec745"
        }

    """
    employeeid = str(employeeid)
    c = common.get_connector()

    r = await employee.get_one_employee(c, employeeid,
                                        details=employee.EmployeeDetails.INTEGRATION,
                                        only_primary_uuid=only_primary_uuid)

    if not r:
        exceptions.ErrorCodes.E_USER_NOT_FOUND(employee_uuid=employeeid)

    if r[mapping.INTEGRATION_DATA]:
        r[mapping.INTEGRATION_DATA] = json.loads(r[mapping.INTEGRATION_DATA])
    else:
        r[mapping.INTEGRATION_DATA] = {}

    return r
