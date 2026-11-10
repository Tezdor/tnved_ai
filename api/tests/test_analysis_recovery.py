import uuid

from contextlib import ExitStack
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIRequestFactory, force_authenticate

from api.models import ProductRequest, ModelResult, FinalResult
from api.views.analysis import analyze_product_view


class AnalysisRecoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="recovery-test")
        self.product = ProductRequest.objects.create(
            user=self.user,
            description="Тестовый товар"
        )
        self.factory = APIRequestFactory()

        self.patches = ExitStack()
        self.addCleanup(self.patches.close)

        model_result = {
            "tnved_code": "1234567890",
            "title": "Тест",
            "confidence": 80,
            "reasoning": "Тестовое обоснование"
        }

        self.model_mocks = []

        for name in (
            "analyze_tnved",
            "ask_deepseek",
            "ask_gigachat",
            "ask_yandex_gpt",
        ):
            mocked = self.patches.enter_context(
                patch(
                    f"api.services.analysis.pipeline.{name}",
                    side_effect=lambda *args, **kwargs: model_result.copy()
                )
            )
            self.model_mocks.append(mocked)

        self.final_data = {
            "recommended_code": "1234567890",
            "confidence": 80,
            "supported_by": ["openai"],
            "reasoning": "Тестовый итог"
        }

        self.final_mock = self.patches.enter_context(
            patch(
                "api.services.analysis.pipeline.make_final_decision",
                side_effect=lambda *args, **kwargs: self.final_data.copy()
            )
        )

    def analyze(self):
        request = self.factory.post(
            "/api/analyze-product/",
            {
                "request_id": self.product.id,
                "description": "Тестовый товар",
                "answers": [],
                "vision_data": None
            },
            format="json"
        )
        force_authenticate(request, user=self.user)
        return analyze_product_view(request)

    def lock(self, minutes):
        self.product.analysis_in_progress = True
        self.product.analysis_started_at = (
            timezone.now() - timedelta(minutes=minutes)
        )
        self.product.analysis_run_id = uuid.uuid4()
        self.product.save()

    def test_new_analysis(self):
        response = self.analyze()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.results.count(), 4)
        self.assertTrue(
            FinalResult.objects.filter(request=self.product).exists()
        )

        self.product.refresh_from_db()
        self.assertFalse(self.product.analysis_in_progress)
        self.assertIsNone(self.product.analysis_started_at)
        self.assertIsNone(self.product.analysis_run_id)

    def test_active_analysis_is_rejected(self):
        self.lock(minutes=1)
        previous_run_id = self.product.analysis_run_id

        response = self.analyze()

        self.assertEqual(response.status_code, 409)

        for mocked in self.model_mocks:
            mocked.assert_not_called()

        self.product.refresh_from_db()
        self.assertTrue(self.product.analysis_in_progress)
        self.assertEqual(self.product.analysis_run_id, previous_run_id)

    def test_expired_analysis_can_restart(self):
        self.lock(minutes=20)

        ModelResult.objects.create(
            request=self.product,
            model_name="old",
            tnved_code="-",
            title="Частичный ответ",
            confidence=0,
            reasoning=""
        )

        response = self.analyze()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.product.results.count(), 4)
        self.assertFalse(
            self.product.results.filter(model_name="old").exists()
        )

    def test_old_attempt_cannot_save_or_unlock_new_attempt(self):
        new_run_id = uuid.uuid4()

        def replace_attempt(*args, **kwargs):
            ProductRequest.objects.filter(id=self.product.id).update(
                analysis_run_id=new_run_id,
                analysis_started_at=timezone.now(),
                analysis_in_progress=True
            )
            return self.final_data.copy()

        self.final_mock.side_effect = replace_attempt

        response = self.analyze()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.product.results.count(), 0)
        self.assertFalse(
            FinalResult.objects.filter(request=self.product).exists()
        )

        self.product.refresh_from_db()
        self.assertTrue(self.product.analysis_in_progress)
        self.assertEqual(self.product.analysis_run_id, new_run_id)

    def test_failed_save_rolls_back_model_results(self):
        with patch(
            "api.services.analysis.pipeline.FinalResult.objects.create",
            side_effect=RuntimeError("Тестовая ошибка сохранения")
        ):
            response = self.analyze()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.product.results.count(), 0)

        self.product.refresh_from_db()
        self.assertFalse(self.product.analysis_in_progress)