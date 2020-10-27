import json
from unittest import TestCase

import optuna
from optuna_dashboard.app import create_app
from .wsgi_utils import send_request


class APITestCase(TestCase):
    def test_get_study_summaries(self) -> None:
        storage = optuna.storages.InMemoryStorage()
        storage.create_new_study("foo1")
        storage.create_new_study("foo2")

        app = create_app(storage)
        status, _, body = send_request(
            app,
            "/api/studies/",
            "GET",
            content_type="application/json",
        )
        self.assertEqual(status, "200 OK")
        study_summaries = json.loads(body)["study_summaries"]
        self.assertEqual(len(study_summaries), 2)

    def test_create_study(self) -> None:
        storage = optuna.storages.InMemoryStorage()
        self.assertEqual(len(storage.get_all_study_summaries()), 0)

        app = create_app(storage)
        request_body = {
            "study_name": "foo",
            "direction": "minimize",
        }
        status, _, _ = send_request(
            app,
            "/api/studies",
            "POST",
            content_type="application/json",
            body=json.dumps(request_body),
        )
        self.assertEqual(status, "201 Created")
        self.assertEqual(len(storage.get_all_study_summaries()), 1)

    def test_create_study_duplicated(self) -> None:
        storage = optuna.storages.InMemoryStorage()
        storage.create_new_study("foo")
        self.assertEqual(len(storage.get_all_study_summaries()), 1)

        app = create_app(storage)
        request_body = {
            "study_name": "foo",
            "direction": "minimize",
        }
        status, _, _ = send_request(
            app,
            "/api/studies",
            "POST",
            content_type="application/json",
            body=json.dumps(request_body),
        )
        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(len(storage.get_all_study_summaries()), 1)

    def test_delete_study(self) -> None:
        storage = optuna.storages.InMemoryStorage()
        storage.create_new_study("foo1")
        storage.create_new_study("foo2")
        self.assertEqual(len(storage.get_all_study_summaries()), 2)

        app = create_app(storage)
        status, _, _ = send_request(
            app,
            "/api/studies/1",
            "DELETE",
            content_type="application/json",
        )
        self.assertEqual(status, "204 No Content")
        self.assertEqual(len(storage.get_all_study_summaries()), 1)

    def test_delete_study_not_found(self) -> None:
        storage = optuna.storages.InMemoryStorage()
        app = create_app(storage)
        status, _, _ = send_request(
            app,
            "/api/studies/1",
            "DELETE",
            content_type="application/json",
        )
        self.assertEqual(status, "404 Not Found")
