# SPDX-FileCopyrightText: 2018-2020 Magenta ApS
# SPDX-License-Identifier: MPL-2.0

import copy

import freezegun

import mora.async_util
import tests.cases
from mora import lora


class Tests(tests.cases.LoRATestCase):
    @freezegun.freeze_time('2000-12-01')
    def test_terminate_employee(self):
        self.load_sample_structures()

        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"

        payload = {
            "vacate": True,
            "validity": {
                "to": "2000-12-01"
            }
        }

        # None of these should be activate at this point in time,
        # and should therefore remain unaffected by the termination request

        engagement_uuid = 'd000591f-8705-4324-897a-075e3623f37b'
        association_uuid = 'c2153d5d-4a2b-492d-a18c-c498f7bb6221'
        role_uuid = '1b20d0b9-96a0-42a6-b196-293bb86e62e8'
        leave_uuid = 'b807628c-030c-4f5f-a438-de41c1f26ba5'
        manager_uuid = '05609702-977f-4869-9fb4-50ad74c6999a'

        async def get_expected(id, is_vacant=False):
            o = await c.organisationfunktion.get(id)

            o.update(
                livscykluskode='Rettet',
                note='Afsluttet',
            )

            if is_vacant:
                del o['relationer']['tilknyttedebrugere'][0]['uuid']
            else:
                v = o['tilstande']['organisationfunktiongyldighed']
                v[0]['gyldighed'] = 'Inaktiv'

            return o

        expected_engagement = mora.async_util.async_to_sync(get_expected)(
            engagement_uuid)
        expected_association = mora.async_util.async_to_sync(get_expected)(
            association_uuid, True)
        expected_role = mora.async_util.async_to_sync(get_expected)(role_uuid)
        expected_leave = mora.async_util.async_to_sync(get_expected)(leave_uuid)
        expected_manager = mora.async_util.async_to_sync(get_expected)(manager_uuid,
                                                                       True)

        self.assertRequestResponse(
            '/service/e/{}/terminate'.format(userid),
            userid,
            json=payload,
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.engagement.delete': 1,
                'employee.employee.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        actual_engagement = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            engagement_uuid)
        actual_association = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            association_uuid)
        actual_role = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            role_uuid)
        actual_leave = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            leave_uuid)
        actual_manager = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            manager_uuid)

        with self.subTest('engagement'):
            self.assertRegistrationsEqual(expected_engagement,
                                          actual_engagement)

        with self.subTest('association'):
            self.assertRegistrationsEqual(expected_association,
                                          actual_association)

        with self.subTest('role'):
            self.assertRegistrationsEqual(expected_role,
                                          actual_role)

        with self.subTest('leave'):
            self.assertRegistrationsEqual(expected_leave,
                                          actual_leave)

        with self.subTest('manager'):
            self.assertRegistrationsEqual(expected_manager,
                                          actual_manager)

    @freezegun.freeze_time('2000-12-01')
    def test_terminate_employee_vacatables_full(self):
        """
        Ensure that organisationfunktions that can be vacated are
        terminated as well, when run with 'full'
        """
        self.load_sample_structures()

        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"

        payload = {
            "validity": {
                "to": "2000-12-01"
            },
            "vacate": False,
        }

        manager_uuid = '05609702-977f-4869-9fb4-50ad74c6999a'
        association_uuid = 'c2153d5d-4a2b-492d-a18c-c498f7bb6221'

        def get_expected(id):
            o = mora.async_util.async_to_sync(c.organisationfunktion.get)(id)

            o.update(
                livscykluskode='Rettet',
                note='Afsluttet',
            )

            v = o['tilstande']['organisationfunktiongyldighed']
            v[0]['gyldighed'] = 'Inaktiv'

            return o

        expected_manager = get_expected(manager_uuid)
        expected_association = get_expected(association_uuid)

        self.assertRequestResponse(
            '/service/e/{}/terminate'.format(userid),
            userid,
            json=payload,
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        actual_manager = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            manager_uuid)

        self.assertRegistrationsEqual(expected_manager,
                                      actual_manager)

        actual_association = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            association_uuid)

        self.assertRegistrationsEqual(expected_association,
                                      actual_association)

    @freezegun.freeze_time('2018-01-01')
    def test_validation_missing_validity(self):
        self.load_sample_structures()

        manager_uuid = '05609702-977f-4869-9fb4-50ad74c6999a'

        for req in (
            {
                "type": "manager",
                "uuid": manager_uuid,
            },
            {
                "type": "manager",
                "uuid": manager_uuid,
                "validity": {},
            },
            {
                "type": "manager",
                "uuid": manager_uuid,
                "validity": {
                    "from": "2000-12-01",
                },
            },
        ):
            with self.subTest(req):
                self.assertRequestResponse(
                    '/service/details/terminate',
                    {
                        'description': 'Missing validity',
                        'error': True,
                        'error_key': 'V_MISSING_REQUIRED_VALUE',
                        'key': 'validity',
                        'obj': req,
                        'status': 400,
                    },
                    status_code=400,
                    json=req,
                )

        with self.subTest('invalid type'):
            self.assertRequestFails(
                '/service/details/terminate',
                404,
                json={
                    "type": "association",
                    "uuid": manager_uuid,
                    "validity": {
                        "to": "2018-01-01",
                    },
                },
            )

    @freezegun.freeze_time('2017-01-01', tz_offset=1)
    def test_terminate_manager_via_user(self):
        self.load_sample_structures()

        # Check the POST request
        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"
        manager_uuid = '05609702-977f-4869-9fb4-50ad74c6999a'

        payload = {
            "vacate": True,
            "validity": {
                "to": "2017-11-30"
            }
        }
        self.assertRequestResponse(
            '/service/e/{}/terminate'.format(userid),
            userid,
            json=payload,
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.engagement.delete': 1,
                'employee.employee.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        expected_manager = {
            **(mora.async_util.async_to_sync(c.organisationfunktion.get)(manager_uuid)),

            "note": "Afsluttet",
            "livscykluskode": "Rettet",
        }

        expected_manager['relationer']['tilknyttedebrugere'] = [
            {
                "uuid": "53181ed2-f1de-4c4a-a8fd-ab358c2c454a",
                "virkning": {
                    "from_included": True,
                    "to_included": False,
                    "from": "2017-01-01 00:00:00+01",
                    "to": "2017-12-01 00:00:00+01"
                }
            },
            {
                "virkning": {
                    "from_included": True,
                    "to_included": False,
                    "from": "2017-12-01 00:00:00+01",
                    "to": "infinity"
                }
            }
        ]

        actual_manager = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            manager_uuid)

        self.assertRegistrationsEqual(expected_manager, actual_manager)

        expected = {
            'manager_level': {
                'uuid': 'ca76a441-6226-404f-88a9-31e02e420e52',
            },
            'manager_type': {
                'uuid': '32547559-cfc1-4d97-94c6-70b192eff825',
            },
            'org_unit': {
                'uuid': '9d07123e-47ac-4a9a-88c8-da82e3a4bc9e',
            },
            'person': {
                'uuid': '53181ed2-f1de-4c4a-a8fd-ab358c2c454a',
            },
            'responsibility': [{
                'uuid': '4311e351-6a3c-4e7e-ae60-8a3b2938fbd6',
            }],
            'uuid': '05609702-977f-4869-9fb4-50ad74c6999a',
            'user_key': 'be736ee5-5c44-4ed9-b4a4-15ffa19e2848',
            'validity': {
                'from': '2017-01-01',
                'to': '2017-11-30',
            },
        }

        self.assertRequestResponse(
            '/service/e/{}/details/manager?only_primary_uuid=1'.format(userid),
            [expected],
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        self.assertRequestResponse(
            '/service/e/{}/details/manager'
            '?validity=future&only_primary_uuid=1'.format(userid),
            [{
                **expected,
                'person': None,
                'validity': {'from': '2017-12-01', 'to': None},
            }],
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

    @freezegun.freeze_time('2017-01-01', tz_offset=1)
    def test_terminate_association_via_user(self):
        self.load_sample_structures()

        # Check the POST request
        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"
        association_uuid = 'c2153d5d-4a2b-492d-a18c-c498f7bb6221'

        payload = {
            "vacate": True,
            "validity": {
                "to": "2017-11-30"
            }
        }
        self.assertRequestResponse(
            '/service/e/{}/terminate'.format(userid),
            userid,
            json=payload,
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.engagement.delete': 1,
                'employee.employee.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        expected_tilknyttedebrugere = [
            {
                "uuid": "53181ed2-f1de-4c4a-a8fd-ab358c2c454a",
                "virkning": {
                    "from_included": True,
                    "to_included": False,
                    "from": "2017-01-01 00:00:00+01",
                    "to": "2017-12-01 00:00:00+01"
                }
            },
            {
                "virkning": {
                    "from_included": True,
                    "to_included": False,
                    "from": "2017-12-01 00:00:00+01",
                    "to": "infinity"
                }
            }
        ]

        expected_association = {
            **(mora.async_util.async_to_sync(c.organisationfunktion.get)(
                association_uuid)),

            "note": "Afsluttet",
            "livscykluskode": "Rettet",
        }

        expected_association['relationer'][
            'tilknyttedebrugere'] = expected_tilknyttedebrugere

        actual_association = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            association_uuid)

        self.assertRegistrationsEqual(expected_association, actual_association)

        expected = {
            'association_type': {'uuid': '32547559-cfc1-4d97-94c6-70b192eff825'},
            'dynamic_classes': [],
            'org_unit': {'uuid': '9d07123e-47ac-4a9a-88c8-da82e3a4bc9e'},
            'person': {'uuid': '53181ed2-f1de-4c4a-a8fd-ab358c2c454a'},
            'primary': None,
            'substitute': None,
            'user_key': 'bvn',
            'uuid': 'c2153d5d-4a2b-492d-a18c-c498f7bb6221',
            'validity': {'from': '2017-01-01', 'to': '2017-11-30'}
        }

        self.assertRequestResponse(
            '/service/e/{}/details/association?only_primary_uuid=1'.format(userid),
            [expected],
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        self.assertRequestResponse(
            '/service/e/{}/details/association'
            '?validity=future&only_primary_uuid=1'.format(userid),
            [{
                **expected,
                'person': None,
                'validity': {'from': '2017-12-01', 'to': None},
            }],
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

    @freezegun.freeze_time('2017-01-01', tz_offset=1)
    def test_terminate_manager_properly_via_user(self):
        self.load_sample_structures()

        # Check the POST request
        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"
        manager_uuid = '05609702-977f-4869-9fb4-50ad74c6999a'

        payload = {
            "vacate": False,
            "validity": {
                "to": "2017-11-30"
            }
        }

        self.assertRequestResponse(
            '/service/e/{}/terminate'.format(userid),
            userid,
            json=payload,
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        expected_manager = {
            **(mora.async_util.async_to_sync(c.organisationfunktion.get)(manager_uuid)),

            "note": "Afsluttet",
            "livscykluskode": "Rettet",
            "tilstande": {
                "organisationfunktiongyldighed": [
                    {
                        "gyldighed": "Aktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-01-01 00:00:00+01",
                            "to": "2017-12-01 00:00:00+01"
                        }
                    },
                    {
                        "gyldighed": "Inaktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-12-01 00:00:00+01",
                            "to": "infinity"
                        }
                    },
                ]
            },

        }

        actual_manager = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            manager_uuid)

        self.assertRegistrationsEqual(expected_manager, actual_manager)

    @freezegun.freeze_time('2017-01-01', tz_offset=1)
    def test_terminate_association_properly_via_user(self):
        self.load_sample_structures()

        # Check the POST request
        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"
        association_uuid = 'c2153d5d-4a2b-492d-a18c-c498f7bb6221'

        payload = {
            "vacate": False,
            "validity": {
                "to": "2017-11-30"
            }
        }

        self.assertRequestResponse(
            '/service/e/{}/terminate'.format(userid),
            userid,
            json=payload,
            amqp_topics={
                'employee.address.delete': 1,
                'employee.association.delete': 1,
                'employee.employee.delete': 1,
                'employee.engagement.delete': 1,
                'employee.leave.delete': 1,
                'employee.manager.delete': 1,
                'employee.it.delete': 1,
                'employee.role.delete': 1,
                'org_unit.association.delete': 1,
                'org_unit.engagement.delete': 1,
                'org_unit.manager.delete': 1,
                'org_unit.role.delete': 1,
            },
        )

        expected_association = {
            **(mora.async_util.async_to_sync(c.organisationfunktion.get)(
                association_uuid)),

            "note": "Afsluttet",
            "livscykluskode": "Rettet",
            "tilstande": {
                "organisationfunktiongyldighed": [
                    {
                        "gyldighed": "Aktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-01-01 00:00:00+01",
                            "to": "2017-12-01 00:00:00+01"
                        }
                    },
                    {
                        "gyldighed": "Inaktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-12-01 00:00:00+01",
                            "to": "infinity"
                        }
                    },
                ]
            },

        }

        actual_association = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            association_uuid)

        self.assertRegistrationsEqual(expected_association, actual_association)

    @freezegun.freeze_time('2017-01-01', tz_offset=1)
    def test_terminate_manager_directly(self):
        self.load_sample_structures()

        # Check the POST request
        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"
        manager_uuid = '05609702-977f-4869-9fb4-50ad74c6999a'

        original_manager = self.assertRequest(
            '/service/e/{}/details/manager'.format(userid),
        )

        original = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            manager_uuid)

        self.assertRequestResponse(
            '/service/details/terminate',
            manager_uuid,
            json={
                "type": "manager",
                "uuid": manager_uuid,
                "validity": {
                    "to": "2017-11-30"
                }
            },
            amqp_topics={
                'employee.manager.delete': 1,
                'org_unit.manager.delete': 1,
            },
        )

        expected = copy.deepcopy(original)
        expected.update(
            livscykluskode="Rettet",
            note="Afsluttet",
            tilstande={
                "organisationfunktiongyldighed": [
                    {
                        "gyldighed": "Aktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-01-01 00:00:00+01",
                            "to": "2017-12-01 00:00:00+01"
                        }
                    },
                    {
                        "gyldighed": "Inaktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-12-01 00:00:00+01",
                            "to": "infinity"
                        }
                    },
                ]
            },
        )

        actual = mora.async_util.async_to_sync(c.organisationfunktion.get)(manager_uuid)

        self.assertRegistrationsEqual(expected, actual)

        with self.subTest('current'):
            current = copy.deepcopy(original_manager)
            current[0]['validity']['to'] = '2017-11-30'

            self.assertRequestResponse(
                '/service/e/{}/details/manager'.format(userid),
                current,
                amqp_topics={
                    'employee.manager.delete': 1,
                    'org_unit.manager.delete': 1,
                },
            )

        with self.subTest('future'):
            self.assertRequestResponse(
                '/service/e/{}/details/manager'
                '?validity=future'.format(userid),
                [],
                amqp_topics={
                    'employee.manager.delete': 1,
                    'org_unit.manager.delete': 1,
                },
            )

    @freezegun.freeze_time('2017-01-01', tz_offset=1)
    def test_terminate_association_directly(self):
        self.load_sample_structures()

        # Check the POST request
        c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')

        userid = "53181ed2-f1de-4c4a-a8fd-ab358c2c454a"
        association_uuid = 'c2153d5d-4a2b-492d-a18c-c498f7bb6221'

        original_association = self.assertRequest(
            '/service/e/{}/details/association'.format(userid),
        )

        original = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            association_uuid)

        self.assertRequestResponse(
            '/service/details/terminate',
            association_uuid,
            json={
                "type": "association",
                "uuid": association_uuid,
                "validity": {
                    "to": "2017-11-30"
                }
            },
            amqp_topics={
                'employee.association.delete': 1,
                'org_unit.association.delete': 1,
            },
        )

        expected = copy.deepcopy(original)
        expected.update(
            livscykluskode="Rettet",
            note="Afsluttet",
            tilstande={
                "organisationfunktiongyldighed": [
                    {
                        "gyldighed": "Aktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-01-01 00:00:00+01",
                            "to": "2017-12-01 00:00:00+01"
                        }
                    },
                    {
                        "gyldighed": "Inaktiv",
                        "virkning": {
                            "from_included": True,
                            "to_included": False,
                            "from": "2017-12-01 00:00:00+01",
                            "to": "infinity"
                        }
                    },
                ]
            },
        )

        actual = mora.async_util.async_to_sync(c.organisationfunktion.get)(
            association_uuid)

        self.assertRegistrationsEqual(expected, actual)

        with self.subTest('current'):
            current = copy.deepcopy(original_association)
            current[0]['validity']['to'] = '2017-11-30'

            self.assertRequestResponse(
                '/service/e/{}/details/association'.format(userid),
                current,
                amqp_topics={
                    'employee.association.delete': 1,
                    'org_unit.association.delete': 1,
                },
            )

        with self.subTest('future'):
            self.assertRequestResponse(
                '/service/e/{}/details/association'
                '?validity=future'.format(userid),
                [],
                amqp_topics={
                    'employee.association.delete': 1,
                    'org_unit.association.delete': 1,
                },
            )
