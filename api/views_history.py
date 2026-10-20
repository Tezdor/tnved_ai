from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import ProductRequest

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history_view(request):

    requests = (
        ProductRequest.objects.filter(
            user=request.user,
            final__isnull=False
        )
        .select_related('final')
        .prefetch_related('results')
        .order_by('-created_at')
    )

    data = []

    for req in requests:

        data.append({

            "id":
                req.id,

            "description":
                req.description,

            "image":
                req.image.url
                if req.image
                else None,

            "image_url":
                req.image_url,

            "created_at":
                req.created_at,

            "results": [

                {
                    "model":
                        r.model_name,

                    "tnved_code":
                        r.tnved_code,

                    "title":
                        r.title,

                    "confidence":
                        r.confidence,

                    "reasoning":
                        r.reasoning,
                }

                for r in req.results.all()

            ],

            "final": (

                {
                    "recommended_code":
                        req.final.recommended_code,

                    "confidence":
                        req.final.confidence,

                    "supported_by":
                        req.final.supported_by,

                    "reasoning":
                        req.final.reasoning,

                    "vat":
                        req.final.vat,

                    "duty":
                        req.final.duty,
                }

                if hasattr(
                    req,
                    "final"
                )
                and req.final

                else None
            )
        })

    return Response(
        data
    )
