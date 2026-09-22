from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    index,
    generate_questions_view,
    analyze_product_view,
    download_pdf_view,
    history_view,
    history_page,
    image_preview_view,
    process_image_view,
    parse_product_view,
    wb_image_proxy,
)

urlpatterns = [

    path('', index),
    path('generate-questions/', generate_questions_view),
    path('analyze-product/', analyze_product_view),
    path('download-pdf/', download_pdf_view),
    path('history-page/', history_page, name='history_page'),
    path('history/', history_view, name='history_api'), 
    path ("image-preview/", image_preview_view),
    path( "process-image/", process_image_view),
    path("parse_product/", parse_product_view),
    path('wb-image-proxy/', wb_image_proxy, name='wb_image_proxy'),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)