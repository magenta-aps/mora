#
# Copyright (c) 2017, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import collections
import copy
import datetime
import functools
import uuid
from typing import List

from . import meta
from .. import exceptions, lora, util


def _set_virkning(lora_obj: dict, virkning: dict, overwrite=False) -> dict:
    """
    Adds virkning to the "leafs" of the given LoRa JSON (tree) object.

    :param lora_obj: A LoRa object with or without virkning.
    :param virkning: The virkning to set in the LoRa object
    :param overwrite: Whether any original virknings should be overwritten
    :return: The LoRa object with the new virkning

    """
    for k, v in lora_obj.items():
        if isinstance(v, dict):
            _set_virkning(v, virkning, overwrite)
        elif isinstance(v, list):
            for d in v:
                if overwrite:
                    d['virkning'] = virkning.copy()
                else:
                    d.setdefault('virkning', virkning.copy())
    return lora_obj


def _create_virkning(From: str, to: str, from_included=True,
                     to_included=False) -> dict:
    """
    Create virkning from frontend request.

    :param From: The "from" date.
    :param to: The "to" date.
    :param from_included: Specify if the from-date should be included or not.
    :param to_included: Specify if the to-date should be included or not.
    :return: The virkning object.
    """
    return {
        'from': util.to_lora_time(From),
        'to': util.to_lora_time(to),
        'from_included': from_included if not From == '-infinity' else False,
        'to_included': to_included if not to == 'infinity' else False
    }


def create_org_unit(req: dict) -> dict:
    """
    Create org unit data to send to LoRa.

    :param req: Dictionary representation of JSON request from the frontend.
    :return: Dictionary representation of the org unit JSON object to send to
        LoRa.
    """

    # Create virkning

    # NOTE: 'to' date is always infinity here but if the 'valid-to' is set in
    # the frontend request, the org unit end-date will be changed below
    virkning = _create_virkning(req.get('valid-from'),
                                req.get('valid-to', 'infinity'))

    # Create the organisation unit object
    org_unit = {
        'note': 'Oprettet i MO',
        'attributter': {
            'organisationenhedegenskaber': [
                {
                    'enhedsnavn': req['name'],
                    'brugervendtnoegle': req['name'].replace(' ', ''),
                    # TODO: make a proper function to set the bvn
                },
            ],
        },
        'tilstande': {
            'organisationenhedgyldighed': [
                {
                    'gyldighed': 'Aktiv',
                },
            ],
        },
        'relationer': {
            'adresser': [
                {
                    'uuid': location['location'][
                        'UUID_EnhedsAdresse'],
                    'objekttype': str(meta.Address.fromdict(location)),
                    'virkning': virkning,
                }

                # TODO: will we ever have more than one location?
                # (multiple locations not tested) (however,
                # multiple contact channels are tested)

                for location in req.get('locations', [])
            ] + [
                {
                    'urn': 'urn:magenta.dk:telefon:{}'.format(
                        channel['contact-info'],
                    ),
                    'objekttype': str(meta.PhoneNumber(
                        location=location['location']
                        ['UUID_EnhedsAdresse'],
                        visibility=channel['visibility']['user-key'],
                    )),
                    'virkning': virkning,
                }
                for location in req.get('locations', [])
                for channel in location.get('contact-channels', [])
            ],
            # TODO: what happens if we have neither locations nor addresses?
            # (no test for this yet...)
            'tilhoerer': [
                {
                    'uuid': req['org'],
                }
            ],
            'enhedstype': [
                {
                    'uuid': req['type']['uuid'],
                }
            ],
            'overordnet': [
                {
                    'uuid': req['parent'],
                }
            ],
        }
    }

    org_unit = _set_virkning(org_unit, virkning)

    return org_unit


def create_org_funktion(req: dict) -> dict:
    virkning = _create_virkning(req.get('valid-from'),
                                req.get('valid-to', 'infinity'))

    funktionstype_name = req.get('job-title').get('name')
    funktionstype_uuid = req.get('job-title').get('uuid')
    engagementstype_uuid = req.get('type').get('uuid')
    bruger_uuid = req.get('person')
    org_enhed_uuid = req.get('org-unit').get('uuid')
    org_uuid = req.get('org-unit').get('org')

    org_funk = {
        'note': 'Oprettet i MO',
        'attributter': {
            'organisationfunktionegenskaber': [
                {
                    'funktionsnavn': "{} {}".format(funktionstype_name,
                                                    org_enhed_uuid),
                    'brugervendtnoegle': "{} {}".format(bruger_uuid,
                                                        org_enhed_uuid)
                },
            ],
        },
        'tilstande': {
            'organisationfunktiongyldighed': [
                {
                    'gyldighed': 'Aktiv',
                },
            ],
        },
        'relationer': {
            'organisatoriskfunktionstype': [
                {
                    'uuid': engagementstype_uuid
                }
            ],
            'tilknyttedebrugere': [
                {
                    'uuid': bruger_uuid
                }
            ],
            'tilknyttedeorganisationer': [
                {
                    'uuid': org_uuid
                }
            ],
            'tilknyttedeenheder': [
                {
                    'uuid': org_enhed_uuid
                }
            ],
            'opgaver': [
                {
                    'uuid': funktionstype_uuid
                }
            ]
        }
    }

    org_funk = _set_virkning(org_funk, virkning)

    return org_funk


def update_org_funktion_payload(from_time, to_time, note, fields, original,
                                payload):
    for field in fields:
        payload = _create_payload(
            from_time, to_time,
            field[0],
            field[1],
            note,
            payload,
            original)

    paths = [field[0] for field in fields]

    payload = _ensure_object_effect_bounds(
        from_time, to_time,
        original, payload,
        get_remaining_org_funk_fields(paths)
    )

    return payload


def get_remaining_org_funk_fields(obj_paths: List[List[str]]):
    # TODO: Maybe fetch this information dynamically from LoRa?
    fields = {
        ('attributter', 'organisationfunktionegenskaber'),
        ('tilstande', 'organisationfunktiongyldighed'),
        ('relationer', 'organisatoriskfunktionstype'),
        ('relationer', 'opgaver'),
        ('relationer', 'tilknyttedebrugere'),
        ('relationer', 'tilknyttedeenheder'),
        ('relationer', 'tilknyttedeorganisationer'),
    }

    tupled_set = {tuple(x) for x in obj_paths}
    diff = fields.difference(tupled_set)

    return [list(x) for x in diff]


def move_org_funktion_payload(move_date, from_time, to_time,
                              overwrite, org_unit_uuid, orgfunk):
    note = "Flyt engagement"
    fields = [(
        ['relationer', 'tilknyttedeenheder'],
        {'uuid': org_unit_uuid}
    )]

    payload = {}

    if overwrite:
        return update_org_funktion_payload(move_date, to_time, note, fields,
                                           orgfunk, payload)
    else:
        return update_org_funktion_payload(move_date, from_time, note, fields,
                                           orgfunk, payload)


def inactivate_org_funktion(startdate, enddate):
    obj_path = ['tilstande', 'organisationfunktiongyldighed']
    props_active = {'gyldighed': 'Aktiv'}
    props_inactive = {'gyldighed': 'Inaktiv'}

    payload = _create_payload(startdate, enddate, obj_path, props_active,
                              'Afslut funktion')
    payload = _create_payload(enddate, 'infinity', obj_path, props_inactive,
                              'Afslut funktion', payload)

    return payload


def inactivate_org_unit(startdate: str, enddate: str) -> dict:
    """
    Inactivate an org unit.

    :param startend: The date from which the org unit is active.
    :param enddate: The date to inactivate the org unit from.
    :return: The payload JSON used to update LoRa.
    """

    obj_path = ['tilstande', 'organisationenhedgyldighed']
    props_active = {'gyldighed': 'Aktiv'}
    props_inactive = {'gyldighed': 'Inaktiv'}

    payload = _create_payload(startdate, enddate, obj_path, props_active,
                              'Afslut enhed')
    payload = _create_payload(enddate, 'infinity', obj_path, props_inactive,
                              'Afslut enhed', payload)

    return payload


def move_org_unit(req: dict) -> dict:
    """
    Move an org unit to a new parent unit.

    :param req: The JSON reqeust from the frontend.
    :return: The payload JSON used to update LoRa.
    """

    date = req['moveDate']
    obj_path = ['relationer', 'overordnet']
    props = {'uuid': req['newParentOrgUnitUUID']}

    return _create_payload(date, 'infinity', obj_path, props,
                           'Flyt enhed')


def rename_org_unit(req: dict) -> dict:
    """
    Rename an org unit.

    :param req: The JSON request sent from the frontend.
    :return: The payload JSON used to update LoRa.
    """

    From = req['valid-from']
    to = req.get('valid-to', 'infinity')
    obj_path = ['attributter', 'organisationenhedegenskaber']
    props = {'enhedsnavn': req['name']}

    return _create_payload(From, to, obj_path, props,
                           'Omdøb enhed')


# TODO: rename this function...
def retype_org_unit(req: dict) -> dict:
    """
    Change the type or start-date of the org unit.

    :param req: The JSON request sent from the frontend.
    :return: The payload JSON used to update LoRa.
    """

    payload = None

    if 'type-updated' in req.keys():
        # Update the org unit type
        From = datetime.datetime.today()
        obj_path = ['relationer', 'enhedstype']
        props = {'uuid': req['type']['uuid']}
        to = req['valid-to']
        payload = _create_payload(From, to, obj_path, props, 'Ret enhedstype')

    if 'valid-from-updated' in req.keys():
        # Update the org unit start-date
        From = req['valid-from']
        obj_path = ['tilstande', 'organisationenhedgyldighed']
        props = {'gyldighed': 'Aktiv'}
        to = req['valid-to']
        payload = _create_payload(From, to, obj_path, props,
                                  'Ret enhedstype og start dato'
                                  if payload else 'Ret start dato', payload)

    return payload


def _zero_to_many_rels() -> List[str]:
    # TODO: Load and cache from LoRa
    return [
        "adresser",
        "opgaver",
        "tilknyttedebrugere",
        "tilknyttedeenheder",
        "tilknyttedeorganisationer",
        "tilknyttedeitsystemer",
        "tilknyttedeinteressefaellesskaber",
        "tilknyttedepersoner"
    ]


def _create_payload(From: str, to: str, obj_path: list,
                    props: dict, note: str, payload: dict = None,
                    original: dict = None) -> dict:
    """
    Generate payload to send to LoRa when updating or writing new data. See
    the example below.

    :param From: The "from" date.
    :param to: The "to" date.
    :param obj_path: List with "path" to object to add.
    :param props: Properties to add.
    :param note: Note to add to the payload.
    :param payload: An already existing payload that should have extra
        properties added.
    :param original: An optional, existing object containing properties on
        "obj_path" which should be merged with props, in case of adding props
        to a zero-to-many relation.
    :return: The resulting payload (see example below).

    :Example:

    >>> _create_payload(
            '01-01-2017', '01-01-2018',
            ['tilstande', 'organisationenhedgyldighed'],
            {'gyldighed': 'Aktiv'}, 'Ret gyldighed'
        )
        {
            'tilstande': {
                'organisationenhedgyldighed': [
                    {
                        'gyldighed': 'Aktiv',
                        'virkning': {
                            'to': '2018-01-01T00:00:00+01:00',
                            'from_included': True,
                            'from': '2017-01-01T00:00:00+01:00',
                            'to_included': False
                        }
                    }
                ]
            },
            'note': 'Ret gyldighed'
        }
    """

    obj_path_copy = obj_path.copy()
    props_copy = props.copy()

    if payload:
        payload['note'] = note
    else:
        payload = {
            'note': note,
        }

    current_value = payload
    while obj_path_copy:
        key = obj_path_copy.pop(0)
        if obj_path_copy:
            if key not in current_value.keys():
                current_value[key] = {}
            current_value = current_value[key]
        else:
            props_copy['virkning'] = _create_virkning(From, to)
            if key in _zero_to_many_rels() and original:
                if key in current_value.keys():
                    merge_obj = payload
                else:
                    merge_obj = original
                orig_list = functools.reduce(lambda x, y: x.get(y),
                                             obj_path, merge_obj)
                current_value[key] = _merge_obj_effects(orig_list, props_copy)
            elif key in current_value.keys():
                current_value[key].append(props_copy)
            else:
                current_value[key] = [props_copy]

    return payload


def _ensure_object_effect_bounds(lower_bound: str, upper_bound: str,
                                 original: dict, payload: dict,
                                 paths: List[List[str]]) -> dict:
    """
    Given an original object and a set of time bounds from a prospective
    update, ensure that ranges on object validities are sane, when the
    update is performed. Operates under the assumption that we do not have
    any overlapping intervals in validity ranges

    :param lower_bound: The lower bound, in ISO-8601
    :param upper_bound: The upper bound, in ISO-8601
    :param original: The original object, as it exists in LoRa
    :param payload: An existing payload to add the updates to
    :param paths: A list of paths to be checked on the original object
    :return: The payload with the additional updates applied, if relevant
    """

    note = payload.get('note')

    for path in paths:
        # Get list of original relevant properties, sorted by start_date
        orig_list = functools.reduce(lambda x, y: x.get(y, {}), path, original)
        if not orig_list:
            continue
        sorted_rel = sorted(orig_list, key=lambda x: x['virkning']['from'])
        first = sorted_rel[0]
        last = sorted_rel[-1]

        # Handle lower bound
        if lower_bound < first['virkning']['from']:
            props = copy.deepcopy(first)
            del props['virkning']
            payload = _create_payload(
                lower_bound,
                first['virkning']['to'],
                path,
                props,
                note,
                payload,
                original
            )

        # Handle upper bound
        if last['virkning']['to'] < upper_bound:
            props = copy.deepcopy(last)
            del props['virkning']
            payload = _create_payload(
                last['virkning']['from'],
                upper_bound,
                path,
                props,
                note,
                payload,
                original
            )

    return payload


def _merge_obj_effects(orig_objs: List[dict], new: dict) -> List[dict]:
    """
    Performs LoRa-like merging of a relation object, with a current list of
    relation objects, with regards to virkningstider,
    producing a merged list of relation to be inserted into LoRa, similar to
    how LoRa performs merging of zero-to-one relations.

    We assume that the list of objects satisfy the same contraints as a list
    of objects from a zero-to-one relation, i.e. no overlapping time periods

    :param orig_objs: A list of objects with virkningstider
    :param new: A new object with virkningstid, to be merged
                into the original list.
    :return: A list of merged objects
    """
    # TODO: Implement merging of two lists?

    sorted_orig = sorted(orig_objs, key=lambda x: x['virkning']['from'])

    result = [new]
    new_from = util.parsedatetime(new['virkning']['from'])
    new_to = util.parsedatetime(new['virkning']['to'])

    for orig in sorted_orig:
        orig_from = util.parsedatetime(orig['virkning']['from'])
        orig_to = util.parsedatetime(orig['virkning']['to'])

        if new_to <= orig_from or orig_to <= new_from:
            # Not affected, add orig as-is
            result.append(orig)
            continue

        if new_from <= orig_from:
            if orig_to <= new_to:
                # Orig is completely contained in new, ignore
                continue
            else:
                # New end overlaps orig beginning
                new_rel = copy.deepcopy(orig)
                new_rel['virkning']['from'] = util.to_lora_time(new_to)
                result.append(new_rel)
        elif new_from < orig_to:
            # New beginning overlaps with orig end
            new_obj_before = copy.deepcopy(orig)
            new_obj_before['virkning']['to'] = util.to_lora_time(new_from)
            result.append(new_obj_before)
            if new_to < orig_to:
                # New is contained in orig
                new_obj_after = copy.deepcopy(orig)
                new_obj_after['virkning']['from'] = util.to_lora_time(new_to)
                result.append(new_obj_after)

    return sorted(result, key=lambda x: x['virkning']['from'])


def _inactivate_old_interval(old_from: str, old_to: str, new_from: str,
                             new_to: str, payload: dict,
                             path: List[str]) -> dict:
    """
    Create 'inactivation' updates based on two sets of from/to dates
    :param old_from: The old 'from' time, in ISO-8601
    :param old_to: The old 'to' time, in ISO-8601
    :param new_from: The new 'from' time, in ISO-8601
    :param new_to: The new 'to' time, in ISO-8601
    :param payload: An existing payload to add the updates to
    :param path: The path to where the object's 'gyldighed' is located
    :return: The payload with the inactivation updates added, if relevant
    """
    if old_from < new_from:
        payload = _create_payload(
            old_from,
            new_from,
            path,
            {
                'gyldighed': "Inaktiv"
            },
            payload.get('note'),
            payload
        )
    if new_to < old_to:
        payload = _create_payload(
            new_to,
            old_to,
            path,
            {
                'gyldighed': "Inaktiv"
            },
            payload.get('note'),
            payload
        )
    return payload

# ---------------------------- Updating addresses -------------------------- #

# ---- Handling of role types: contact-channel, location and None ---- #


def _add_contact_channels(obj: dict, *, location: dict=None,
                          contact_channels: list=None) -> dict:
    """
    Adds new contact channels to the address list.

    :param obj: The org unit to update.
    :param location: The location to attach the contact channel to.
    :param contact_channels: List of contact channels to add.
    :return: The updated list of addresses.
    """
    addresses = obj['relationer'].get('adresser', []).copy()

    if contact_channels:
        addresses.extend([
            {
                'urn': (
                    (info.get('type') or info['phone-type'])['prefix'] +
                    info['contact-info']
                ),
                'objekttype': str(meta.PhoneNumber(
                    location=location and location['uuid'],
                    visibility=(
                        (info.get('visibility') or info['properties'])
                        ['user-key']
                    ),
                )),
                'virkning': _create_virkning(
                    info['valid-from'],
                    info.get('valid-to', 'infinity'),
                ),
            }
            for info in contact_channels
        ])

    return addresses


# Role type location
def _update_existing_address(org_unit: dict,
                             address_uuid: str,
                             location: dict,
                             From: str,
                             to: str, **kwargs) -> list:
    """
    Used to update an already existing address.

    :param org_unit: The org unit to update.
    :param address_uuid: The address UUID to update.
    :param location: Location JSON given by the frontend.
    :param From: The start date.
    :param to: The end date.
    :return: The updated list of addresses.
    """

    # Note: the frontend makes a call for each location it wants to update

    assert location

    addresses = [
        address if address.get('uuid') != address_uuid else {
            'uuid': (location.get('UUID_EnhedsAdresse') or
                     location['uuid']),
            'objekttype': str(meta.Address(**kwargs)),
            'virkning': _create_virkning(From, to),
        }
        for address in org_unit['relationer']['adresser']
    ]

    return addresses


# Role type not set in payload JSON
def _add_location(org_unit: dict, location: dict, From: str, to: str,
                  **kwargs: dict) -> dict:
    """
    Adds a new location the the existing list of addresses.

    :param org_unit: The org unit to update.
    :param location: The new location to add.
    :param From: The start date of the address.
    :param to: The end date of the address.
    :param kwargs: The necessary data from the frontend request.
    :return: The updated list of addresses.
    """

    # Note: the frontend makes a call for each location it wants to update

    assert location

    new_addr = {
        'uuid': location['UUID_EnhedsAdresse'],
        'objekttype': str(meta.Address(**kwargs)),
        'virkning': _create_virkning(From, to),
    }

    addresses = org_unit['relationer'].get('adresser', []).copy()
    addresses.append(new_addr)

    return addresses


def _check_arguments(mandatory_args: collections.abc.Iterable,
                     args_to_check: collections.abc.Iterable):
    """
    Check that the mandatory arguments are present when updating or adding new
    locations to an org unit.

    :param mandatory_args: List of mandatory arguments.
    :param args_to_check: List of arguments to check.
    :raises: IllegalArgumentException if the argument list does not contain all
        the mandatory arguments.
    """
    for arg in mandatory_args:
        if arg not in args_to_check:
            raise exceptions.IllegalArgumentException('%s missing' % arg)


def create_update_kwargs(req: dict) -> dict:
    """
    Pick out the necessary data from the frontend request depending on
    the roletype - the frontend handles location updates in a very funny
    way...

    :param req: The frontend request.
    :return: The necessary data depending on the roletype.
    """

    roletype = req.get('role-type')

    if roletype == 'contact-channel':
        if 'location' in req:
            kwargs = {
                'contact_channels': req['contact-channels'],
                'roletype': roletype,
                'location': req['location'],
            }
        else:
            kwargs = {
                'roletype': roletype,
            }
    # NB: consistency - employees use contact, not contact-channe
    elif roletype == 'contact':
        kwargs = {
            'contact_channels': [req],
            'roletype': roletype,
            'emplid': req['person'],
            'location': None,
        }
    elif roletype == 'location':
        kwargs = {
            'roletype': roletype,
            'address_uuid': req['uuid'],
            'location': req['location'],
            'From': req['valid-from'],
            'to': req['valid-to'],
            'name': req['name'],
            'primary': req.get('primaer', False),
        }
    elif roletype:
        raise NotImplementedError(roletype)
    else:
        kwargs = {
            'roletype': roletype,
            'location': req['location'],
            'From': req['valid-from'],
            'to': req['valid-to'],
            'name': req['name'],
            'primary': req.get('primaer', False),
        }

    return kwargs


def update_employee_addresses(emplid: str, roletype: str, **kwargs):
    assert roletype == 'contact', roletype

    c = lora.Connector()
    employee = c.bruger.get(emplid)

    if roletype == 'contact':
        if 'contact_channels' in kwargs:
            # Adding contact channels
            note = 'Tilføj kontaktkanal'
            updated_addresses = _add_contact_channels(
                employee, **kwargs)
        else:
            # Contact channel already exists
            note = 'Tilføj eksisterende kontaktkanal'
            updated_addresses = []
    else:
        raise NotImplementedError(roletype)

    payload = {
        'note': note,
        'relationer': {
            'adresser': updated_addresses
        }
    }

    return payload


def update_org_unit_addresses(unitid: str, roletype: str, **kwargs):
    """
    Update or add an org unit address or contact channel.

    :param unitid: The org unit UUID.
    :param roletype: The roletype (contact-channel, location, None) to use -
      this is handled in a funny way by the frontend!?
    :param kwargs: The required data from the frontend request.
    :return: The payload to send (PUT) to LoRa.
    """

    assert roletype in ['contact-channel', 'location', None]

    org_unit = lora.organisationenhed(
        uuid=unitid, virkningfra='-infinity', virkningtil='infinity')[0][
        'registreringer'][-1]

    if roletype == 'contact-channel':
        if 'contact_channels' in kwargs:
            # Adding contact channels
            note = 'Tilføj kontaktkanal'
            updated_addresses = _add_contact_channels(
                org_unit, **kwargs)
        else:
            # Contact channel already exists
            note = 'Tilføj eksisterende kontaktkanal'
            updated_addresses = []
    elif roletype == 'contact':
        # Adding contact channels
        note = 'Tilføj kontaktoplysninger'
        updated_addresses = _add_contact_channels(
            org_unit, **kwargs)
    elif roletype == 'location':
        # Updating an existing address
        _check_arguments(['address_uuid', 'location', 'From', 'to',
                          'name', 'primary'],
                         kwargs)
        note = 'Ret adresse'
        updated_addresses = _update_existing_address(org_unit, **kwargs)
    else:
        # Roletype is None - adding new location
        _check_arguments(['location', 'From', 'to', 'name', 'primary'],
                         kwargs)
        note = 'Tilføj addresse'
        updated_addresses = _add_location(org_unit, **kwargs)

    payload = {
        'note': note,
        'relationer': {
            'adresser': updated_addresses
        }
    }

    return payload


# Engagements
def move_engagements(move_date, overwrite, engagements, org_unit_uuid):
    """
    Move a list of engagements to the given org unit on the given date

    :param move_date: The date of the move
    :param overwrite: Whether the move should overwrite the existing engagement
    :param engagements: A list of engagements on the form:
                        {'uuid': <UUID>, 'from': <date>, 'to': <date>}
    :param org_unit_uuid: A UUID of the org unit to move to
    """
    c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')
    for engagement in engagements:
        engagement_uuid = engagement.get('uuid')
        from_time = engagement.get('from')
        to_time = engagement.get('to')

        # Fetch current orgfunk
        orgfunk = c.organisationfunktion.get(engagement_uuid)

        # Create new orgfunk active from the move date, with new org unit
        payload = move_org_funktion_payload(move_date, from_time, to_time,
                                            overwrite, org_unit_uuid, orgfunk)

        c.organisationfunktion.update(payload, engagement_uuid)


def edit_engagement(req, employee_uuid, engagement_uuid):
    # Get the current org-funktion which the user wants to change
    c = lora.Connector(virkningfra='-infinity', virkningtil='infinity')
    original = c.organisationfunktion.get(uuid=engagement_uuid)
    payload = update_engagement_payload(req, original)
    c.organisationfunktion.update(payload, engagement_uuid)


def update_engagement_payload(req, original):
    # TODO: New API
    old_from = req.get('oldvalidfrom')
    old_to = req.get('oldvalidto')
    new_from = req.get('newvalidfrom')
    new_to = req.get('newvalidto')

    note = 'Rediger engagement'

    fields = [
        (['relationer', 'opgaver'],
         {'uuid': req.get('jobtitle')}),

        (['relationer', 'organisatoriskfunktionstype'],
         {'uuid': req.get('type')}),

        (['tilstande', 'organisationfunktiongyldighed'],
         {'gyldighed': "Aktiv"}),
    ]

    payload = {}
    payload = _inactivate_old_interval(
        old_from, old_to, new_from, new_to, payload,
        ['tilstande', 'organisationfunktiongyldighed']
    )

    payload = update_org_funktion_payload(new_from, new_to, note,
                                          fields, original, payload)

    return payload


def terminate_engagement(engagement_uuid, enddate):
    """
    Terminate the given engagement at the given date

    :param engagement_uuid: An engagement UUID
    :param enddate: The date of termination
    """
    c = lora.Connector(effective_date=enddate)

    orgfunk = c.organisationfunktion.get(engagement_uuid)

    # Create inactivation object
    startdate = [
        g['virkning']['from'] for g in
        orgfunk['tilstande']['organisationfunktiongyldighed']
        if g['gyldighed'] == 'Aktiv'
    ][0]

    payload = inactivate_org_funktion(startdate, enddate)
    c.organisationfunktion.update(payload, engagement_uuid)


def create_engagement(req):
    # TODO: Validation
    engagement = create_org_funktion(req)
    lora.Connector().organisationfunktion.create(engagement)


def create_contact(req):
    # TODO: Validation
    kwargs = create_update_kwargs(req)

    payload = update_employee_addresses(**kwargs)

    if payload['relationer']['adresser']:
        lora.update('organisation/bruger/%s' % req['person'], payload)
