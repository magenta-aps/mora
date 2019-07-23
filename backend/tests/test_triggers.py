
#
# Copyright (c) Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

from . import util
from mora.triggers import Trigger
from mora.mapping import (
    ON_BEFORE,
    ON_AFTER,
)

from mora.service.handlers import (
    RequestType,
    RequestHandler,
)


class MockHandler(RequestHandler):
    role_type = "mock"

    def prepare_edit(self, req):
        self.uuid = "edit"

    def prepare_create(self, req):
        self.uuid = "create"

    def prepare_terminate(self, req):
        self.uuid = "terminate"

    def submit(self):
        super().submit(result="okidoki")


class Tests(util.TestCase):
    maxDiff = None
    Trigger.registry = {}

    def setUp(self):
        super().setUp()
        self.trigger_called = False

    def test_handler_trigger_before_edit(self):
        @Trigger.on("mock", RequestType.EDIT, ON_BEFORE)
        def trigger(trigger_dict):
            self.trigger_called = True
            self.assertEqual({
                'event_type': ON_BEFORE,
                'request': {},
                'request_type': RequestType.EDIT,
                'uuid': 'edit'
            }, trigger_dict)
        MockHandler({}, RequestType.EDIT)
        self.assertTrue(self.trigger_called)

    def test_handler_trigger_after_edit(self):
        @Trigger.on("mock", RequestType.EDIT, ON_AFTER)
        def trigger(trigger_dict):
            self.trigger_called = True
            self.assertEqual({
                'event_type': ON_AFTER,
                'request': {},
                'request_type': RequestType.EDIT,
                'uuid': 'edit',
                'result': 'okidoki'
            }, trigger_dict)
        MockHandler({}, RequestType.EDIT).submit()
        self.assertTrue(self.trigger_called)

    def test_handler_trigger_before_create(self):
        @Trigger.on("mock", RequestType.CREATE, ON_BEFORE)
        def trigger(trigger_dict):
            self.trigger_called = True
            self.assertEqual({
                'event_type': ON_BEFORE,
                'request': {},
                'request_type': RequestType.CREATE,
                'uuid': 'create'
            }, trigger_dict)
        MockHandler({}, RequestType.CREATE)
        self.assertTrue(self.trigger_called)

    def test_handler_trigger_after_create(self):
        @Trigger.on("mock", RequestType.CREATE, ON_AFTER)
        def trigger(trigger_dict):
            self.trigger_called = True
            self.assertEqual({
                'event_type': ON_AFTER,
                'request': {},
                'request_type': RequestType.CREATE,
                'uuid': 'create',
                'result': 'okidoki'
            }, trigger_dict)
        MockHandler({}, RequestType.CREATE).submit()
        self.assertTrue(self.trigger_called)

    def test_handler_trigger_before_terminate(self):
        @Trigger.on("mock", RequestType.TERMINATE, ON_BEFORE)
        def trigger(trigger_dict):
            self.trigger_called = True
            self.assertEqual({
                'event_type': ON_BEFORE,
                'request': {},
                'request_type': RequestType.TERMINATE,
                'uuid': 'terminate'
            }, trigger_dict)
        MockHandler({}, RequestType.TERMINATE)
        self.assertTrue(self.trigger_called)

    def test_handler_trigger_after_terminate(self):
        @Trigger.on("mock", RequestType.TERMINATE, ON_AFTER)
        def trigger(trigger_dict):
            self.trigger_called = True
            self.assertEqual({
                'event_type': ON_AFTER,
                'request': {},
                'request_type': RequestType.TERMINATE,
                'uuid': 'terminate',
                'result': 'okidoki'
            }, trigger_dict)
        MockHandler({}, RequestType.TERMINATE).submit()
        self.assertTrue(self.trigger_called)
