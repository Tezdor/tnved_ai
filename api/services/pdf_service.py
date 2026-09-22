from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from django.conf import settings

import os


def generate_pdf(results):

    pdf_path = os.path.join(
        settings.BASE_DIR,
        'api',
        'pdfs',
        'tnved_result.pdf'
    )

    # Регистрируем шрифт с поддержкой русского

    font_path = "C:/Windows/Fonts/arial.ttf"

    pdfmetrics.registerFont(
        TTFont('Arial', font_path)
    )

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    style = styles['BodyText']

    style.fontName = 'Arial'

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
    doc.build(elements)

    return pdf_path