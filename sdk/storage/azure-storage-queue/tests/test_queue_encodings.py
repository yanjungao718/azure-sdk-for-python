# coding: utf-8

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import unittest
import sys
import pytest
from azure.core.exceptions import HttpResponseError, DecodeError, ResourceExistsError
from azure.storage.queue import (
    QueueClient,
    QueueServiceClient,
    TextBase64EncodePolicy,
    TextBase64DecodePolicy,
    BinaryBase64EncodePolicy,
    BinaryBase64DecodePolicy
)
from azure.storage.queue._message_encoding import NoEncodePolicy, NoDecodePolicy
from settings.testcase import QueuePreparer

from devtools_testutils.storage import StorageTestCase

# ------------------------------------------------------------------------------
TEST_QUEUE_PREFIX = 'mytestqueue'


# ------------------------------------------------------------------------------

class StorageQueueEncodingTest(StorageTestCase):
    # --Helpers-----------------------------------------------------------------
    def _get_queue_reference(self, qsc, prefix=TEST_QUEUE_PREFIX):
        queue_name = self.get_resource_name(prefix)
        queue = qsc.get_queue_client(queue_name)
        return queue

    def _create_queue(self, qsc, prefix=TEST_QUEUE_PREFIX):
        queue = self._get_queue_reference(qsc, prefix)
        try:
            created = queue.create_queue()
        except ResourceExistsError:
            pass
        return queue

    def _validate_encoding(self, queue, message):
        # Arrange
        try:
            created = queue.create_queue()
        except ResourceExistsError:
            pass

        # Action.
        queue.send_message(message)

        # Asserts
        dequeued = next(queue.receive_messages())
        self.assertEqual(message, dequeued.content)

    # --------------------------------------------------------------------------

    @QueuePreparer()
    def test_message_text_xml(self, storage_account_name, storage_account_key):
        # Arrange.
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        message = '<message1>'
        queue = qsc.get_queue_client(self.get_resource_name(TEST_QUEUE_PREFIX))

        # Asserts
        assert isinstance(queue._config.message_encode_policy, NoEncodePolicy)
        assert isinstance(queue._config.message_decode_policy, NoDecodePolicy)
        self._validate_encoding(queue, message)

    @QueuePreparer()
    def test_message_text_xml_whitespace(self, storage_account_name, storage_account_key):
        # Arrange.
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        message = '  mess\t age1\n'
        queue = qsc.get_queue_client(self.get_resource_name(TEST_QUEUE_PREFIX))

        # Asserts
        self._validate_encoding(queue, message)

    @QueuePreparer()
    def test_message_text_xml_invalid_chars(self, storage_account_name, storage_account_key):
        # Action.
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        queue = self._get_queue_reference(qsc)
        message = '\u0001'

        # Asserts
        with self.assertRaises(HttpResponseError):
            queue.send_message(message)

    @QueuePreparer()
    def test_message_text_base64(self, storage_account_name, storage_account_key):
        # Arrange.
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        queue = QueueClient(
            account_url=self.account_url(storage_account_name, "queue"),
            queue_name=self.get_resource_name(TEST_QUEUE_PREFIX),
            credential=storage_account_key,
            message_encode_policy=TextBase64EncodePolicy(),
            message_decode_policy=TextBase64DecodePolicy())

        message = '\u0001'

        # Asserts
        self._validate_encoding(queue, message)

    @QueuePreparer()
    def test_message_bytes_base64(self, storage_account_name, storage_account_key):
        # Arrange.
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        queue = QueueClient(
            account_url=self.account_url(storage_account_name, "queue"),
            queue_name=self.get_resource_name(TEST_QUEUE_PREFIX),
            credential=storage_account_key,
            message_encode_policy=BinaryBase64EncodePolicy(),
            message_decode_policy=BinaryBase64DecodePolicy())

        message = b'xyz'

        # Asserts
        self._validate_encoding(queue, message)

    @QueuePreparer()
    def test_message_bytes_fails(self, storage_account_name, storage_account_key):
        # Arrange
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        queue = qsc.get_queue_client(self.get_resource_name(TEST_QUEUE_PREFIX))
        queue.create_queue()


        # Action.
        with self.assertRaises(TypeError) as e:
            message = b'xyz'
            queue.send_message(message)

            # Asserts
            self.assertTrue(str(e.exception).startswith(
                'Message content must not be bytes. '
                'Use the BinaryBase64EncodePolicy to send bytes.'))

    @QueuePreparer()
    def test_message_text_fails(self, storage_account_name, storage_account_key):
        # Arrange
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        queue = QueueClient(
            account_url=self.account_url(storage_account_name, "queue"),
            queue_name=self.get_resource_name(TEST_QUEUE_PREFIX),
            credential=storage_account_key,
            message_encode_policy=BinaryBase64EncodePolicy(),
            message_decode_policy=BinaryBase64DecodePolicy())

        # Action.
        with self.assertRaises(TypeError) as e:
            message = 'xyz'
            queue.send_message(message)

        # Asserts
        self.assertTrue(str(e.exception).startswith('Message content must be bytes'))

    @QueuePreparer()
    def test_message_base64_decode_fails(self, storage_account_name, storage_account_key):
        # Arrange
        qsc = QueueServiceClient(self.account_url(storage_account_name, "queue"), storage_account_key)
        queue = QueueClient(
            account_url=self.account_url(storage_account_name, "queue"),
            queue_name=self.get_resource_name(TEST_QUEUE_PREFIX),
            credential=storage_account_key,
            message_encode_policy=None,
            message_decode_policy=BinaryBase64DecodePolicy())
        try:
            queue.create_queue()
        except ResourceExistsError:
            pass
        message = 'xyz'
        queue.send_message(message)

        # Action.
        with self.assertRaises(DecodeError) as e:
            queue.peek_messages()

        # Asserts
        self.assertNotEqual(-1, str(e.exception).find('Message content is not valid base 64'))

    def test_message_no_encoding(self):
        # Arrange
        queue = QueueClient(
            account_url="https://account.queue.core.windows.net",
            queue_name="queue",
            credential="account_key",
            message_encode_policy=None,
            message_decode_policy=None)

        # Asserts
        assert isinstance(queue._config.message_encode_policy, NoEncodePolicy)
        assert isinstance(queue._config.message_decode_policy, NoDecodePolicy)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
