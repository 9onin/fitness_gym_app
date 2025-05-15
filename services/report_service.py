import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import xlsxwriter

# Регистрируем шрифт Times New Roman для поддержки кириллицы
font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'timesnewromanpsmt.ttf')
pdfmetrics.registerFont(TTFont('TimesNewRoman', font_path))

def generate_pdf_report(title, data, start_date, end_date):
    """
    Генерирует отчет в формате PDF
    
    Args:
        title (str): Заголовок отчета
        data (dict): Данные отчета в формате {'headers': [...], 'rows': [...], 'summary': "..."}
        start_date (datetime): Начальная дата периода отчета
        end_date (datetime): Конечная дата периода отчета
        
    Returns:
        bytes: PDF данные
    """
    buffer = io.BytesIO()
    
    # Определяем ориентацию страницы в зависимости от количества колонок
    # Если колонок больше 5, используем альбомную ориентацию
    page_size = landscape(letter) if len(data['headers']) > 5 else letter
    
    # Создаем документ
    doc = SimpleDocTemplate(buffer, pagesize=page_size, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    # Создаем кастомные стили с шрифтом Times New Roman
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName='TimesNewRoman',
        fontSize=16
    )
    
    subtitle_style = ParagraphStyle(
        name='CustomSubtitle',
        parent=styles['Heading2'],
        fontName='TimesNewRoman',
        fontSize=14
    )
    
    normal_style = ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontName='TimesNewRoman',
        fontSize=12
    )
    
    summary_style = ParagraphStyle(
        name='CustomSummary',
        parent=styles['Normal'],
        fontName='TimesNewRoman',
        fontSize=12,
        textColor=colors.darkblue,
        alignment=1  # По центру
    )
    
    # Заголовок отчета
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Период отчета
    period_text = f"Период: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}"
    elements.append(Paragraph(period_text, subtitle_style))
    elements.append(Spacer(1, 12))
    
    # Дата создания отчета
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    elements.append(Paragraph(f"Дата создания: {now}", normal_style))
    elements.append(Spacer(1, 24))
    
    # Добавляем текст сводки, если он есть
    if 'summary' in data and data['summary']:
        elements.append(Paragraph(data['summary'], summary_style))
        elements.append(Spacer(1, 12))
    
    # Данные таблицы
    table_data = [data['headers']]
    table_data.extend(data['rows'])
    
    # Создаем таблицу с автоматической шириной колонок
    # Рассчитываем ширину колонок в зависимости от количества колонок
    available_width = doc.width
    col_count = len(data['headers'])
    
    # Определяем ширину для каждой колонки
    # Если много колонок, уменьшаем размер шрифта
    font_size = 10 if col_count <= 5 else 8
    col_widths = [available_width / col_count] * col_count
    
    # Делаем первую колонку (дата) немного уже, если много колонок
    if col_count > 5 and col_count <= 7:
        col_widths[0] = col_widths[0] * 0.8  # Дата
        for i in range(1, col_count):
            col_widths[i] = col_widths[i] * 1.04  # Компенсируем остальные
    
    # Создаем таблицу с заданной шириной колонок
    table = Table(table_data, colWidths=col_widths)
    
    # Стиль таблицы с использованием Times New Roman
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'TimesNewRoman'),
        ('FONTSIZE', (0, 0), (-1, 0), font_size + 1),  # Заголовок чуть больше
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'TimesNewRoman'),
        ('FONTSIZE', (0, 1), (-1, -1), font_size),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('WORDWRAP', (0, 0), (-1, -1), True),  # Разрешаем перенос текста
    ])
    
    # Добавляем зебру (чередующийся цвет строк)
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
    
    # Выделяем строку ИТОГО, если она есть
    if len(table_data) > 1 and "ИТОГО" in str(table_data[-1][0]):
        table_style.add('BACKGROUND', (0, -1), (-1, -1), colors.lightblue)
        table_style.add('FONTNAME', (0, -1), (-1, -1), 'TimesNewRoman')
        table_style.add('FONTSIZE', (0, -1), (-1, -1), font_size + 1)
        table_style.add('TEXTCOLOR', (0, -1), (-1, -1), colors.navy)
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Сноска
    elements.append(Spacer(1, 36))
    elements.append(Paragraph("* Отчет создан автоматически", normal_style))
    
    # Строим документ
    doc.build(elements)
    
    # Получаем данные и возвращаем
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def generate_excel_report(title, data, start_date, end_date):
    """
    Генерирует отчет в формате Excel
    
    Args:
        title (str): Заголовок отчета
        data (dict): Данные отчета в формате {'headers': [...], 'rows': [...], 'summary': "..."}
        start_date (datetime): Начальная дата периода отчета
        end_date (datetime): Конечная дата периода отчета
        
    Returns:
        bytes: Excel данные
    """
    buffer = io.BytesIO()
    
    # Создаем файл Excel
    workbook = xlsxwriter.Workbook(buffer)
    worksheet = workbook.add_worksheet('Отчет')
    
    # Определяем количество колонок для объединения ячеек
    col_count = len(data['headers']) if data['headers'] else 5
    merge_range = f'A1:{chr(64 + min(col_count, 26))}1'  # A1:E1 или другой диапазон
    
    # Форматы
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    subtitle_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#CCCCCC',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    alt_row_format = workbook.add_format({
        'border': 1,
        'bg_color': '#F5F5F5',
        'align': 'center',
        'valign': 'vcenter'
    })
    
    date_format = workbook.add_format({
        'align': 'right',
        'font_size': 10
    })
    
    total_row_format = workbook.add_format({
        'bold': True,
        'bg_color': '#B8CCE4',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_color': '#0F243E'
    })
    
    summary_format = workbook.add_format({
        'align': 'center',
        'font_size': 11,
        'font_color': 'blue',
        'italic': True
    })
    
    # Заголовок отчета
    worksheet.merge_range(merge_range, title, title_format)
    
    # Период отчета
    period_text = f"Период: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}"
    worksheet.merge_range(f'A2:{chr(64 + min(col_count, 26))}2', period_text, subtitle_format)
    
    # Дата создания отчета
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    worksheet.merge_range(f'A3:{chr(64 + min(col_count, 26))}3', f"Дата создания: {now}", date_format)
    
    # Добавляем строку для вывода сводной информации
    current_row = 4
    if 'summary' in data and data['summary']:
        worksheet.merge_range(f'A{current_row}:{chr(64 + min(col_count, 26))}{current_row}', data['summary'], summary_format)
        current_row += 1
    
    # Заголовки таблицы
    for col, header in enumerate(data['headers']):
        worksheet.write(current_row, col, header, header_format)
        # Автоподбор ширины колонок для заголовков
        width = max(len(str(header)) * 1.2, 10)
        worksheet.set_column(col, col, width)
    
    # Данные таблицы
    for row_idx, row_data in enumerate(data['rows']):
        # Определяем, является ли строка итоговой
        is_total_row = "ИТОГО" in str(row_data[0]) if row_data else False
        
        for col_idx, cell_data in enumerate(row_data):
            # Выбираем формат в зависимости от типа строки
            if is_total_row:
                format_to_use = total_row_format
            else:
                format_to_use = alt_row_format if row_idx % 2 == 0 else cell_format
                
            worksheet.write(row_idx + current_row + 1, col_idx, cell_data, format_to_use)
    
    # Сноска
    footnote_row = len(data['rows']) + current_row + 2
    worksheet.merge_range(f'A{footnote_row}:{chr(64 + min(col_count, 26))}{footnote_row}', "* Отчет создан автоматически")
    
    # Автоподбор ширины колонок на основе данных
    for i in range(len(data['headers'])):
        header_width = len(str(data['headers'][i])) * 1.2
        data_width = max([len(str(row[i])) for row in data['rows']]) * 1.2 if data['rows'] else 0
        column_width = max(header_width, data_width, 10)  # Минимум 10
        # Ограничиваем максимальную ширину колонки
        column_width = min(column_width, 30)
        worksheet.set_column(i, i, column_width)
    
    # Сохраняем и закрываем
    workbook.close()
    
    # Получаем данные и возвращаем
    excel_data = buffer.getvalue()
    buffer.close()
    
    return excel_data 