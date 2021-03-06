# -*- coding: utf-8 -*-
import os
import json
import asyncio

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop, TestClient

from app import app

from configs.db import DB

os.environ['IS_TEST'] = 'True'
os.environ['MONGODB_DB_NAME'] = 'async_chat_test'


class TestChatApi(AioHTTPTestCase):
    data = {}
    headers = {}

    first_headers = None
    second_headers = None

    first_token = None
    second_token = None

    first_client = {}
    second_client = {}

    client_in_request = None

    def get_app(self, loop):
        server = app(
            loop=loop
        )

        server['db'] = self.database(
            loop=loop
        )

        return server

    def setUp(self):
        self.load_data()

        self.database = DB()
        self.loop = asyncio.new_event_loop()
        # self.loop.set_debug(False)
        self.app = self.get_app(
            self.loop
        )

        self.client = TestClient(
            self.app,
        )

        self.loop.run_until_complete(self.install_client())

        self.loop.run_until_complete(self.auth_client())

        self.first_headers = {
            'Authorization': self.first_token,
            'Content-Type': 'application/json',
        }

        self.second_headers = {
            'Authorization': self.second_token,
            'Content-Type': 'application/json',
        }

        self.loop.run_until_complete(self.install_chat())

    def load_data(self):
        with open('ws_chat_fixtures.json') as data:
            self.data = json.load(data)

    def install_client(self):
        #   Grab data for create users
        first_client = self.data.get('clients').get('first')
        second_client = self.data.get('clients').get('second')

        #   Create request for create first client
        first_client_auth_request = yield from self.client.post(
            path="/client/create/",
            data=json.dumps(first_client)
        )

        # Create request for create second client
        second_client_auth_request = yield from self.client.post(
            path="/client/create/",
            data=json.dumps(second_client)
        )

        yield

    def auth_client(self):
        first_client = self.data.get('clients').get('first')
        second_client = self.data.get('clients').get('second')

        #   auth  and get token for first client
        first_client_request = yield from self.client.post(
            path="/client/auth/",
            data=json.dumps(first_client)
        )

        self.first_client = yield from first_client_request.json()
        self.first_token = self.first_client.get('token')

        #   auth  and get token for second client
        second_client_request = yield from self.client.post(
            path="/client/auth/",
            data=json.dumps(second_client)
        )

        self.second_client = yield from second_client_request.json()

        self.second_token = self.second_client.get('token')

    def install_chat(self):
        request = yield from self.client.post(
            path='/chat/create/',
            headers=self.first_headers
        )

        result = yield from request.json()
        os.environ['TEST_CHAT_PK'] = result.get('chat')

    def delete_test_chat(self):
        chat = os.environ['TEST_CHAT_PK']

        data = json.dumps({
            'id': chat
        })

        request = yield from self.client.post(
            path='/chat/delete/',
            headers=self.first_headers,
            data=data
        )

        result = yield from request.json()

    def tearDown(self):
        self.delete_test_chat()
        super(TestChatApi, self).tearDown()

    @property
    def chat_path(self):
        chat = os.environ['TEST_CHAT_PK']
        path = "/chat/ws/{}/{}/".format(chat, self.first_client.get('client_id'))
        return path

    @property
    def second_path(self):
        chat = os.environ['TEST_CHAT_PK']
        path = "/chat/ws/{}/{}/".format(chat, self.second_client.get('client_id'))
        return path

    @unittest_run_loop
    async def test_open_ws_connect(self):
        print("========================")
        print("test_open_ws_connect")

        request = await self.client.ws_connect(
            path=self.chat_path,
            headers=self.first_headers
        )

        assert request.closed is False

        msg = await request.receive()
        print(msg)

        request.send_str(data='{"msg": "Hello"}')

    # @unittest_run_loop
    # async def test_send_message(self):
    #     print("========================")
    #     print("test_send_message")
    #
    #     request = await self.client.ws_connect(
    #         path=self.chat_path,
    #         headers=self.first_headers
    #     )
    #     request.send_str("{'msg': 'Hello'}")

    # @unittest_run_loop
    # async def test_chat_btw_users(self):
    #     print("========================")
    #     print("test_chat_btw_users")
    #
    #     first_client = await self.client.ws_connect(
    #         path=self.chat_path,
    #         headers=self.first_headers
    #     )
    #
    #     second_client = await self.client.ws_connect(
    #         path=self.second_path,
    #         headers=self.second_headers
    #     )
    #
    #     msgs = ["Hello second client ", "How are you"]
    #
    #     for item in msgs:
    #         msg = '{"msg": "%s"}' % item
    #         first_client.send_str(msg)

        # msg = await second_client.receive()
        # print("Second client receive messages")
        # print(msg)

        # await first_client.close()
        # await second_client.close()
