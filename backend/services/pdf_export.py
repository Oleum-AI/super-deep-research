import io
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
import markdown
from bs4 import BeautifulSoup
import re
from datetime import datetime

class PDFExporter:
    """Export markdown reports to PDF format"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._customize_styles()
    
    def _customize_styles(self):
        """Customize PDF styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a202c'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Heading styles
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=10,
            spaceBefore=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#718096'),
            spaceAfter=8,
            spaceBefore=8
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=16
        ))
        
        # Quote style
        self.styles.add(ParagraphStyle(
            name='CustomQuote',
            parent=self.styles['Italic'],
            fontSize=10,
            textColor=colors.HexColor('#718096'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            spaceBefore=12,
            borderColor=colors.HexColor('#e2e8f0'),
            borderWidth=1,
            borderPadding=10,
            borderRadius=2
        ))
    
    async def export_to_pdf(self, markdown_content: str, title: str = "Research Report") -> bytes:
        """Convert markdown content to PDF and return as bytes"""
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'tables', 'toc', 'fenced_code']
        )
        
        # Parse HTML and convert to reportlab elements
        elements = []
        
        # Add title page
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Generated on: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}",
            self.styles['Normal']
        ))
        elements.append(PageBreak())
        
        # Parse and convert content
        soup = BeautifulSoup(html_content, 'html.parser')
        elements.extend(self._convert_html_to_pdf_elements(soup))
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _convert_html_to_pdf_elements(self, soup):
        """Convert BeautifulSoup elements to reportlab elements"""
        elements = []
        
        for element in soup.children:
            if element.name == 'h1':
                elements.append(Paragraph(element.text, self.styles['CustomHeading1']))
            elif element.name == 'h2':
                elements.append(Paragraph(element.text, self.styles['CustomHeading2']))
            elif element.name == 'h3':
                elements.append(Paragraph(element.text, self.styles['CustomHeading3']))
            elif element.name == 'p':
                # Handle nested elements like strong, em, code
                text = self._process_inline_elements(element)
                elements.append(Paragraph(text, self.styles['CustomBodyText']))
            elif element.name == 'blockquote':
                text = element.text.strip()
                elements.append(Paragraph(text, self.styles['CustomQuote']))
            elif element.name == 'ul':
                elements.extend(self._process_list(element, ordered=False))
            elif element.name == 'ol':
                elements.extend(self._process_list(element, ordered=True))
            elif element.name == 'table':
                table_element = self._process_table(element)
                if table_element:
                    elements.append(table_element)
            elif element.name == 'hr':
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph('<para><b>_' * 50 + '</b></para>', self.styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
            elif element.name == 'pre':
                # Code block
                code_text = element.text.strip()
                code_text = self._escape_xml(code_text)
                elements.append(Paragraph(
                    f'<font name="Courier" size="9">{code_text}</font>',
                    self.styles['Code']
                ))
                elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _process_inline_elements(self, element):
        """Process inline HTML elements like strong, em, code"""
        text = ""
        for child in element.children:
            if hasattr(child, 'name'):
                if child.name == 'strong' or child.name == 'b':
                    text += f'<b>{self._escape_xml(child.text)}</b>'
                elif child.name == 'em' or child.name == 'i':
                    text += f'<i>{self._escape_xml(child.text)}</i>'
                elif child.name == 'code':
                    text += f'<font name="Courier">{self._escape_xml(child.text)}</font>'
                else:
                    text += self._escape_xml(child.text)
            else:
                text += self._escape_xml(str(child))
        return text
    
    def _process_list(self, list_element, ordered=False):
        """Process HTML list elements"""
        elements = []
        items = list_element.find_all('li')
        
        for i, item in enumerate(items):
            if ordered:
                prefix = f"{i + 1}. "
            else:
                prefix = "• "
            
            text = prefix + self._escape_xml(item.text.strip())
            elements.append(Paragraph(text, self.styles['CustomBodyText']))
        
        return elements
    
    def _process_table(self, table_element):
        """Process HTML table elements"""
        rows = []
        
        # Process header
        header = table_element.find('thead')
        if header:
            header_row = []
            for th in header.find_all('th'):
                header_row.append(Paragraph(f'<b>{self._escape_xml(th.text)}</b>', self.styles['Normal']))
            if header_row:
                rows.append(header_row)
        
        # Process body
        tbody = table_element.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                row = []
                for td in tr.find_all('td'):
                    row.append(Paragraph(self._escape_xml(td.text), self.styles['Normal']))
                if row:
                    rows.append(row)
        
        if not rows:
            return None
        
        # Create table
        table = Table(rows)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _escape_xml(self, text):
        """Escape XML special characters"""
        if not text:
            return ""
        
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
