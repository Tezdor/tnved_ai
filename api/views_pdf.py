from django.http import FileResponse

from rest_framework.decorators import api_view

from .services.pdf_service import generate_pdf


@api_view(['POST'])
def download_pdf_view(request):
    pdf_buffer = generate_pdf(request.data)

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename='tnved_result.pdf'
    )