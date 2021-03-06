# SPDX-FileCopyrightText: 2019-2020 Magenta ApS
# SPDX-License-Identifier: MPL-2.0

import logging
from typing import Any, Dict

from .. import reading
from ... import common
from ... import exceptions
from ... import mapping
from ... import util
from ...lora import Connector
from ...request_scoped.query_args import current_query
from ...service import employee

ROLE_TYPE = "employee"

logger = logging.getLogger(__name__)


@reading.register(ROLE_TYPE)
class EmployeeReader(reading.ReadingHandler):
    @classmethod
    async def get(cls, c: Connector, search_fields: Dict[Any, Any]):
        object_tuples = await c.bruger.get_all(**search_fields)
        return await cls._get_obj_effects(c, object_tuples)

    @classmethod
    async def get_from_type(cls, c: Connector, type: str, objid):
        if type != "e":
            exceptions.ErrorCodes.E_INVALID_ROLE_TYPE()

        object_tuples = await c.bruger.get_all_by_uuid(uuids=[objid])
        return await cls._get_obj_effects(c, object_tuples)

    @classmethod
    async def _get_effects(cls, c, obj, **params):
        relevant = {
            "attributter": ("brugeregenskaber", "brugerudvidelser"),
            "relationer": ("tilknyttedepersoner", "tilhoerer"),
            "tilstande": ("brugergyldighed",),
        }

        return await c.bruger.get_effects(obj, relevant, {}, **params)

    @classmethod
    async def _get_mo_object_from_effect(cls, effect, start, end, obj_id):
        c = common.get_connector()
        only_primary_uuid = current_query.args.get('only_primary_uuid')

        employee_object = await employee.get_one_employee(
            c,
            obj_id,
            effect,
            details=employee.EmployeeDetails.FULL,
            only_primary_uuid=only_primary_uuid
        )

        employee_object["validity"] = {
            mapping.FROM: util.to_iso_date(start),
            mapping.TO: util.to_iso_date(end, is_end=True),
        }

        return employee_object
