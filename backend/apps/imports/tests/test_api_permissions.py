from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.imports.services.import_service import import_report

from .helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class ImportApiPermissionTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()
        self.scan_import = import_report(
            assessment=self.assessment_a,
            actor=self.consultant_a,
            tool="nmap",
            filename="sample.xml",
            content=self.sample_content(),
        )
        self.observation = self.scan_import.import_observations.first().scanner_observation

    def results(self, response):
        return response.json()["results"]

    def test_unauthenticated_api_requests_are_denied(self):
        response = self.api.get(reverse("scanimport-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assigned_consultant_can_list_and_retrieve_imports_and_observations(self):
        self.api.force_authenticate(self.consultant_a)

        imports_response = self.api.get(reverse("scanimport-list"))
        observations_response = self.api.get(reverse("scannerobservation-list"))
        detail_response = self.api.get(reverse("scanimport-detail", args=[self.scan_import.id]))
        import_observations_response = self.api.get(
            reverse("scanimport-observations", args=[self.scan_import.id])
        )

        self.assertEqual(imports_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in self.results(imports_response)], [self.scan_import.id])
        self.assertEqual(observations_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.results(observations_response)), 3)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(import_observations_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.results(import_observations_response)), 3)

    def test_unassigned_consultant_cannot_list_or_retrieve_other_client_import_data(self):
        self.api.force_authenticate(self.consultant_b)

        imports_response = self.api.get(reverse("scanimport-list"))
        observations_response = self.api.get(reverse("scannerobservation-list"))
        import_detail_response = self.api.get(reverse("scanimport-detail", args=[self.scan_import.id]))
        observation_detail_response = self.api.get(
            reverse("scannerobservation-detail", args=[self.observation.id])
        )

        self.assertEqual(self.results(imports_response), [])
        self.assertEqual(self.results(observations_response), [])
        self.assertEqual(import_detail_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(observation_detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_read_assigned_imports_and_observations(self):
        self.api.force_authenticate(self.manager_a)

        imports_response = self.api.get(reverse("scanimport-list"))
        observations_response = self.api.get(reverse("scannerobservation-list"))

        self.assertEqual([item["id"] for item in self.results(imports_response)], [self.scan_import.id])
        self.assertEqual(len(self.results(observations_response)), 3)

    def test_client_user_cannot_read_raw_imports_or_observations(self):
        self.api.force_authenticate(self.client_user_a)

        imports_response = self.api.get(reverse("scanimport-list"))
        observations_response = self.api.get(reverse("scannerobservation-list"))
        detail_response = self.api.get(reverse("scanimport-detail", args=[self.scan_import.id]))

        self.assertEqual(imports_response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.results(imports_response), [])
        self.assertEqual(self.results(observations_response), [])
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)
