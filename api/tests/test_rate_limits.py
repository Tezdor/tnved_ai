from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django.db import close_old_connections, connections

from rest_framework.test import APIRequestFactory, force_authenticate

from api.models import RateLimitBucket
from api.core.rate_limit import check_rate_limit, get_client_ip
from api.views.analysis import generate_questions_view, analyze_product_view

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier



class RateLimitTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="rate-limit-test")

    def test_counter_blocks_after_limit(self):
        results = [
            check_rate_limit(
                scope="test",
                identity="client",
                limit=2,
                period_seconds=60
            )
            for _ in range(3)
        ]

        self.assertEqual(results[:2], [0, 0])
        self.assertGreater(results[2], 0)
        self.assertEqual(
            RateLimitBucket.objects.get().request_count,
            2
        )

    def test_counter_resets_after_period(self):
        check_rate_limit(
            scope="test",
            identity="client",
            limit=1,
            period_seconds=60
        )

        RateLimitBucket.objects.update(
            window_started_at=timezone.now() - timedelta(seconds=61)
        )

        result = check_rate_limit(
            scope="test",
            identity="client",
            limit=1,
            period_seconds=60
        )

        self.assertEqual(result, 0)
        self.assertEqual(
            RateLimitBucket.objects.get().request_count,
            1
        )

    def test_clients_have_separate_limits(self):
        for identity in ("first", "second"):
            result = check_rate_limit(
                scope="test",
                identity=identity,
                limit=1,
                period_seconds=60
            )
            self.assertEqual(result, 0)

        self.assertEqual(RateLimitBucket.objects.count(), 2)

    @override_settings(TRUST_NGINX_CLIENT_IP=False)
    def test_direct_connection_ignores_ip_header(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_REAL_IP="192.0.2.10"
        )

        self.assertEqual(get_client_ip(request), "127.0.0.1")

    @override_settings(TRUST_NGINX_CLIENT_IP=True)
    def test_trusted_proxy_uses_real_ip(self):
        request = self.factory.get(
            "/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_REAL_IP="192.0.2.10"
        )

        self.assertEqual(get_client_ip(request), "192.0.2.10")

    def test_questions_limit_blocks_before_model_call(self):
        for _ in range(10):
            self.assertEqual(
                check_rate_limit(
                    scope="generate_questions",
                    identity=f"user:{self.user.pk}",
                    limit=10,
                    period_seconds=60
                ),
                0
            )

        request = self.factory.post(
            "/api/generate-questions/",
            {"description": "Тестовый товар"},
            format="json"
        )
        force_authenticate(request, user=self.user)

        with patch(
            "api.views.analysis.generate_questions"
        ) as model_call:
            response = generate_questions_view(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data["code"], "RATE_LIMIT_EXCEEDED")
        self.assertGreater(int(response["Retry-After"]), 0)
        model_call.assert_not_called()

    def test_analysis_limit_blocks_before_analysis_starts(self):
        for _ in range(5):
            self.assertEqual(
                check_rate_limit(
                    scope="analyze_product",
                    identity=f"user:{self.user.pk}",
                    limit=5,
                    period_seconds=60
                ),
                0
            )

        request = self.factory.post(
            "/api/analyze-product/",
            {"request_id": 123, "description": "Тестовый товар"},
            format="json"
        )
        force_authenticate(request, user=self.user)

        with patch(
            "api.services.analysis.pipeline.ThreadPoolExecutor"
        ) as executor:
            response = analyze_product_view(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data["code"], "RATE_LIMIT_EXCEEDED")
        self.assertGreater(int(response["Retry-After"]), 0)
        executor.assert_not_called()

class ConcurrentRateLimitTests(TransactionTestCase):
    def run_parallel_checks(self):
        barrier = Barrier(6)

        def check():
            close_old_connections()

            try:
                barrier.wait(timeout=10)

                return check_rate_limit(
                    scope="concurrent-test",
                    identity="same-client",
                    limit=2,
                    period_seconds=60
                )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(check)
                for _ in range(6)
            ]

            results = [
                future.result(timeout=30)
                for future in futures
            ]

        self.assertEqual(results.count(0), 2)
        self.assertEqual(
            sum(result > 0 for result in results),
            4
        )
        self.assertEqual(RateLimitBucket.objects.count(), 1)
        self.assertEqual(
            RateLimitBucket.objects.get().request_count,
            2
        )

    def test_concurrent_creation(self):
        self.run_parallel_checks()

    def test_concurrent_existing_bucket(self):
        check_rate_limit(
            scope="concurrent-test",
            identity="same-client",
            limit=2,
            period_seconds=60
        )

        RateLimitBucket.objects.update(request_count=0)

        self.run_parallel_checks()