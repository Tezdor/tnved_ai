from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from xml.sax.saxutils import escape

from io import BytesIO

import os
from pathlib import Path

def register_pdf_fonts():
    if os.name == "nt":
        fonts_dir = Path(
            os.environ.get("WINDIR", "C:/Windows")
        ) / "Fonts"

        regular_path = fonts_dir / "arial.ttf"
        bold_path = fonts_dir / "arialbd.ttf"
    else:
        fonts_dir = Path("/usr/share/fonts/truetype/dejavu")

        regular_path = fonts_dir / "DejaVuSans.ttf"
        bold_path = fonts_dir / "DejaVuSans-Bold.ttf"

    for font_path in (regular_path, bold_path):
        if not font_path.is_file():
            raise FileNotFoundError(
                f"Не найден шрифт для PDF: {font_path}"
            )

    pdfmetrics.registerFont(
        TTFont("PDFRegular", str(regular_path))
    )
    pdfmetrics.registerFont(
        TTFont("PDFBold", str(bold_path))
    )

    pdfmetrics.registerFontFamily(
        "PDFRegular",
        normal="PDFRegular",
        bold="PDFBold",
        italic="PDFRegular",
        boldItalic="PDFBold"
    )


def generate_pdf(results):

    pdf_buffer = BytesIO()

    register_pdf_fonts()

    doc = SimpleDocTemplate(pdf_buffer)

    styles = getSampleStyleSheet()

    style = styles['BodyText']

    style.fontName = "PDFRegular"

    elements = []

    title = Paragraph(
        "<font size=18><b>Результаты анализа ТН ВЭД</b></font>",
        style
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    # OpenAI

    openai_text = f"""
    <b>OpenAI GPT</b><br/><br/>

    <b>Код ТН ВЭД:</b>
    {results['openai']['tnved_code']}<br/><br/>

    <b>Категория:</b>
    {results['openai']['title']}<br/><br/>

    <b>Уверенность:</b>
    {results['openai']['confidence']}<br/><br/>

    <b>Обоснование:</b><br/>
    {results['openai']['reasoning']}
    """

    elements.append(
        Paragraph(openai_text, style)
    )

    elements.append(Spacer(1, 30))

    # DeepSeek

    deepseek_text = f"""
    <b>DeepSeek</b><br/><br/>

    <b>Код ТН ВЭД:</b>
    {results['deepseek']['tnved_code']}<br/><br/>

    <b>Категория:</b>
    {results['deepseek']['title']}<br/><br/>

    <b>Уверенность:</b>
    {results['deepseek']['confidence']}<br/><br/>

    <b>Обоснование:</b><br/>
    {results['deepseek']['reasoning']}
    """

    elements.append(
        Paragraph(deepseek_text, style)
    )
    # GigaChat

    elements.append(Spacer(1, 30))

    gigachat_text = f"""
    <b>GigaChat</b><br/><br/>

    <b>Код ТН ВЭД:</b>
    {results.get('gigachat', {}).get('tnved_code', '-')}<br/><br/>

    <b>Категория:</b>
    {results.get('gigachat', {}).get('title', '-')}<br/><br/>

    <b>Уверенность:</b>
    {results.get('gigachat', {}).get('confidence', '-')}<br/><br/>

    <b>Обоснование:</b><br/>
    {results.get('gigachat', {}).get('reasoning', '-')}
    """

    elements.append(
        Paragraph(gigachat_text, style)
    )
    
    yandex_text = f"""
    <b>YandexGPT</b><br/><br/>

    <b>Код ТН ВЭД:</b>
    {results['yandex']['tnved_code']}<br/><br/>

    <b>Категория:</b>
    {results['yandex']['title']}<br/><br/>

    <b>Уверенность:</b>
    {results['yandex']['confidence']}<br/><br/>

    <b>Обоснование:</b><br/>
    {results['yandex']['reasoning']}
    """

    elements.append(
        Paragraph(yandex_text, style)
    )
    final = results.get("final") or {}

    def pdf_text(value):
        if value is None or value == "":
            return "-"
        return escape(str(value)).replace("\n", "<br/>")

    supported_by = ", ".join(
        str(name) for name in (final.get("supported_by") or [])
    )

    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            "<font size=16><b>Итоговая рекомендация</b></font>",
            style
        )
    )

    elements.append(Spacer(1, 15))

    final_fields = [
        ("Код ТН ВЭД", final.get("recommended_code")),
        ("Уверенность, %", final.get("confidence")),
        ("НДС", final.get("vat")),
        ("Импортная пошлина", final.get("duty")),
        ("Поддерживается моделями", supported_by),
        (
            "Обоснование НДС и пошлины",
            final.get("customs_reasoning")
        ),
        ("Обоснование решения", final.get("reasoning")),
    ]

    for label, value in final_fields:
        elements.append(
            Paragraph(
                f"<b>{label}:</b><br/>{pdf_text(value)}",
                style
            )
        )
        elements.append(Spacer(1, 10))

    doc.build(elements)

    pdf_buffer.seek(0)

    return pdf_buffer