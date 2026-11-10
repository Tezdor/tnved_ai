from .account import account_page
from .analysis import generate_questions_view, analyze_product_view
from .auth import register_view, login_view, logout_view
from .history import history_view
from .images import image_preview_view, process_image_view, wb_image_proxy
from .pages import index, history_page
from .parser import parse_product_view
from .pdf import download_pdf_view