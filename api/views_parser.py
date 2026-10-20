import time
import traceback
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.parser.product_parser import parse_product_page

@api_view(["POST"])
def parse_product_view(request):

    request_id = str(
        uuid.uuid4()
    )[:8]

    print(
        "\n" + "=" * 80
    )

    print(
        "PARSE PRODUCT REQUEST"
    )

    print(
        "REQUEST ID:",
        request_id
    )

    print(
        "TIME:",
        time.time()
    )

    print(
        "METHOD:",
        request.method
    )

    print(
        "URL:",
        request.data.get("url")
    )

    print(
        "REFERER:",
        request.META.get("HTTP_REFERER")
    )

    print(
        "USER AGENT:",
        request.META.get("HTTP_USER_AGENT")
    )

    print(
        "=" * 80
    )

    url = request.data.get(
        "url",
        ""
    ).strip()

    if not url:

        return Response(
            {
                "error":
                    "URL не указан"
            },
            status=400
        )

    try:

        result = parse_product_page(
            url
        )

        print(
            f"[{request_id}] END parse_product_page"
        )

        return Response(
            result
        )

    except Exception as e:

        traceback.print_exc()

        return Response(
            {
                "error":
                    str(e)
            },
            status=500
        )