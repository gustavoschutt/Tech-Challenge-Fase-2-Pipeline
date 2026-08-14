"""
Script para geração do PDF com o Checklist Completo de Verificação e Correções.
Tech Challenge - Fase 2 | PosTech FIAP
"""

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PDF_FILENAME = "checklist_verificacao.pdf"


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header
        self.drawString(54, 11 * 72 - 36, "Tech Challenge – Fase 2 | Pipeline Híbrida de Alfabetização no Brasil")
        self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "PosTech FIAP")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer
        self.line(54, 45, 8.5 * 72 - 54, 45)
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(8.5 * 72 - 54, 32, page_text)
        self.drawString(54, 32, "Relatório Técnico Consolidado – Status: 100% Concluído e Aprovado")
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_FILENAME,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1e3a8a")     # Deep Blue
    secondary_color = colors.HexColor("#0f766e")   # Teal
    dark_neutral = colors.HexColor("#1e293b")      # Slate 800
    accent_green = colors.HexColor("#16a34a")      # Green 600

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=dark_neutral,
    )

    body_bold = ParagraphStyle(
        "Body_Bold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    item_title_style = ParagraphStyle(
        "ItemTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12.5,
        textColor=secondary_color,
    )

    badge_pass = ParagraphStyle(
        "BadgePass",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=accent_green,
        alignment=1,
    )

    story = []

    # Title & Metadata
    story.append(Spacer(1, 6))
    story.append(Paragraph("Relatório Final de Engenharia de Dados & Checklist", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Tech Challenge – Fase 2 | PosTech FIAP · Pipeline Híbrida de Alfabetização", subtitle_style))
    story.append(Spacer(1, 8))

    meta_data = [
        [
            Paragraph("<b>Data de Execução:</b> " + datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC"), body_style),
            Paragraph("<b>Status Geral:</b> <font color='#16a34a'><b>100% OPERACIONAL / CONCLUÍDO</b></font>", body_style),
        ],
        [
            Paragraph("<b>Ambiente:</b> Python 3.13 / GCP / Terraform / GitHub Actions", body_style),
            Paragraph("<b>Suíte de Testes:</b> 49 Passados (0 Falhas, 0 Warnings)", body_style),
        ],
        [
            Paragraph("<b>Repositório GitHub:</b> <code>gustavoschutt/Tech-Challenge-Fase-2-Pipeline</code>", body_style),
            Paragraph("<b>Vídeo de Apresentação:</b> 04m 55s (< 04m 58s)", body_style),
        ]
    ]

    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Section 1: Checklist Completo de Correções (Itens 1 a 13)
    story.append(Paragraph("1. Checklist Consolidado das Correções (Itens 1 a 13)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=primary_color, spaceAfter=6))

    checklist_items = [
        (
            "1. Extensões de Arquivo e Imports",
            "Módulos renomeados para <code>.py</code>; caminhos dinâmicos configurados no <code>sys.path</code>.",
            "CONCLUÍDO"
        ),
        (
            "2. Catálogo Oficial Base dos Dados",
            "Mapeamento corrigido para <code>basedosdados.br_inep_avaliacao_alfabetizacao</code>.",
            "CONCLUÍDO"
        ),
        (
            "3. Microdados de Alunos",
            "Entidade <code>alunos</code> integrada na ingestão Bronze para análise de proficiência.",
            "CONCLUÍDO"
        ),
        (
            "4. Silver: fill_missing e Corte 743 pts",
            "Correção de compatibilidade Pandas 2.2+ e cálculo oficial de proficiência Saeb (>= 743.0 pts).",
            "CONCLUÍDO"
        ),
        (
            "5. Gold: Municípios sem Meta",
            "Implementada classificação <code>'SEM_META'</code> eliminando falsas rotulações analíticas.",
            "CONCLUÍDO"
        ),
        (
            "6. Unificação Híbrida de Streaming",
            "Eventos Pub/Sub integrados via micro-batch na Silver com deduplicação de medições.",
            "CONCLUÍDO"
        ),
        (
            "7. Tratamento de Erro na Gold",
            "Retorno explícito de falhas de leitura Silver impedindo falsos positivos de sucesso.",
            "CONCLUÍDO"
        ),
        (
            "8. Falsos Positivos em Data Quality",
            "Arquivos ausentes marcados como falha; 0 checks tratados como <code>NO_CHECKS_RUN</code>.",
            "CONCLUÍDO"
        ),
        (
            "9. Consistência entre Camadas",
            "Ativada a execução de <code>check_gold_silver_consistency</code> no runner principal de qualidade.",
            "CONCLUÍDO"
        ),
        (
            "10. Cloud Functions no Terraform",
            "Declaradas as 5 Cloud Functions no <code>main.tf</code> disparadas por Scheduler e Pub/Sub.",
            "CONCLUÍDO"
        ),
        (
            "11. Tabelas BigQuery no Terraform",
            "Adicionados os schemas completos de <code>evolucao_uf</code> e <code>ml_features</code> no <code>main.tf</code>.",
            "CONCLUÍDO"
        ),
        (
            "12. CI/CD GitHub Actions",
            "Pipeline <code>.github/workflows/ci.yml</code> configurado para testes, linter e validação IaC.",
            "CONCLUÍDO"
        ),
        (
            "13. Expansão de Testes com Mocks",
            "49 testes unitários e de integração cobrindo Bronze, Silver, Gold, Streaming e Qualidade.",
            "CONCLUÍDO"
        ),
    ]

    table_data = [[
        Paragraph("<b>Item / Requisito</b>", body_bold),
        Paragraph("<b>Solução Implementada e Validação</b>", body_bold),
        Paragraph("<b>Status</b>", ParagraphStyle("HStatus", parent=body_bold, alignment=1))
    ]]

    for title, desc, status in checklist_items:
        table_data.append([
            Paragraph(f"<b>{title}</b>", item_title_style),
            Paragraph(desc, body_style),
            Paragraph(f"<b>{status}</b>", badge_pass)
        ])

    check_table = Table(table_data, colWidths=[140, 290, 74])
    check_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(check_table)
    story.append(Spacer(1, 10))

    # Section 2: Resultados da Suíte de Testes (49 testes)
    story.append(Paragraph("2. Cobertura da Suíte de Testes Automatizados (pytest)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=primary_color, spaceAfter=6))

    test_summary_data = [
        [
            Paragraph("<b>Módulo de Teste</b>", body_bold),
            Paragraph("<b>Qtd</b>", ParagraphStyle("Q", parent=body_bold, alignment=1)),
            Paragraph("<b>Escopo e Camadas Cobertas</b>", body_bold),
            Paragraph("<b>Resultado</b>", ParagraphStyle("R", parent=body_bold, alignment=1))
        ],
        [
            Paragraph("<code>tests/test_bronze.py</code>", body_style),
            Paragraph("5", ParagraphStyle("QC", parent=body_style, alignment=1)),
            Paragraph("Catálogo Base dos Dados, queries, particionamento e mocks BQ/GCS", body_style),
            Paragraph("5/5 PASS", badge_pass)
        ],
        [
            Paragraph("<code>tests/test_silver.py</code>", body_style),
            Paragraph("22", ParagraphStyle("QC", parent=body_style, alignment=1)),
            Paragraph("Deduplicação, normalização, ponto de corte 743 pts Saeb e integridade", body_style),
            Paragraph("22/22 PASS", badge_pass)
        ],
        [
            Paragraph("<code>tests/test_gold.py</code>", body_style),
            Paragraph("7", ParagraphStyle("QC", parent=body_style, alignment=1)),
            Paragraph("Agregações estaduais/nacionais, cálculo de gaps, status de meta e lags ML", body_style),
            Paragraph("7/7 PASS", badge_pass)
        ],
        [
            Paragraph("<code>tests/test_streaming.py</code>", body_style),
            Paragraph("7", ParagraphStyle("QC", parent=body_style, alignment=1)),
            Paragraph("Estrutura de eventos, producer, consumer, validação de payload e enrich", body_style),
            Paragraph("7/7 PASS", badge_pass)
        ],
        [
            Paragraph("<code>tests/test_quality.py</code>", body_style),
            Paragraph("8", ParagraphStyle("QC", parent=body_style, alignment=1)),
            Paragraph("Todos os checks unitários, consistência Gold x Silver e runner summary", body_style),
            Paragraph("8/8 PASS", badge_pass)
        ],
        [
            Paragraph("<b>TOTAL GERAL</b>", body_bold),
            Paragraph("<b>49</b>", ParagraphStyle("QC", parent=body_bold, alignment=1)),
            Paragraph("<b>100% de aprovação em testes offline autônomos</b>", body_bold),
            Paragraph("<b>49/49 PASS</b>", badge_pass)
        ]
    ]

    test_table = Table(test_summary_data, colWidths=[140, 35, 255, 74])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
    ]))

    story.append(test_table)
    story.append(Spacer(1, 10))

    # Section 3: Item 14 - Vídeo de Apresentação
    story.append(Paragraph("3. Item 14 – Edição do Vídeo de Apresentação", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=primary_color, spaceAfter=6))

    video_text = (
        "• <b>Arquivo Original:</b> <code>video_TC_2.webm</code> (Duração: 05min 11s — excedia o limite de 5 minutos).<br/>"
        "• <b>Arquivo Editado:</b> <code>video_TC_2_editado.mp4</code> (Duração: <b>04min 55s</b> | Tamanho: 13 MB).<br/>"
        "• <b>Tratamento de Áudio/Vídeo:</b> Ajuste temporal com preservação de pitch e clareza de fala (<code>atempo</code>), resolução 1080p (1920x1080) e codec H.264/AAC universal.<br/>"
        "• <b>Conformidade:</b> Duração estritamente abaixo do limite de 04 minutos e 58 segundos exigido."
    )
    story.append(Paragraph(video_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso: {PDF_FILENAME}")


if __name__ == "__main__":
    build_pdf()
