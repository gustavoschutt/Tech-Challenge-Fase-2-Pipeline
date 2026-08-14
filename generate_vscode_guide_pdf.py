"""
Script para geração do Guia Passo a Passo de Execução no VS Code em PDF.
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

PDF_FILENAME = "guia_execucao_vscode.pdf"


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
        self.drawString(54, 11 * 72 - 36, "Tech Challenge – Fase 2 | Guia de Execução no VS Code")
        self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "PosTech FIAP")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer
        self.line(54, 45, 8.5 * 72 - 54, 45)
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(8.5 * 72 - 54, 32, page_text)
        self.drawString(54, 32, "Manual de Desenvolvimento e Execução Local")
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

    primary_color = colors.HexColor("#1e3a8a")     # Deep Blue
    secondary_color = colors.HexColor("#0f766e")   # Teal
    dark_neutral = colors.HexColor("#1e293b")      # Slate 800
    code_bg = colors.HexColor("#f1f5f9")

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
        fontSize=11.5,
        leading=15,
        textColor=primary_color,
        spaceBefore=11,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=dark_neutral,
    )

    body_bold = ParagraphStyle(
        "Body_Bold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    code_block_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # Title & Subtitle
    story.append(Spacer(1, 6))
    story.append(Paragraph("Guia Passo a Passo: Execução no VS Code", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Tech Challenge – Fase 2 | PosTech FIAP · Pipeline Híbrida de Alfabetização", subtitle_style))
    story.append(Spacer(1, 8))

    meta_data = [
        [
            Paragraph("<b>Projeto:</b> <code>Tech-Challenge-Fase-2-Pipeline</code>", body_style),
            Paragraph("<b>Ambiente Python:</b> Python 3.13.5 (Anaconda)", body_style),
        ],
        [
            Paragraph("<b>GitHub:</b> <code>gustavoschutt/Tech-Challenge-Fase-2-Pipeline</code>", body_style),
            Paragraph("<b>Suíte de Testes:</b> 49 Testes (pytest) – 100% Aprovados", body_style),
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
    story.append(Spacer(1, 8))

    # Passo 1: Abrir no VS Code
    story.append(Paragraph("Passo 1: Abertura do Projeto no Visual Studio Code", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=4))
    p1_desc = (
        "Abra o terminal e acerte o diretório do projeto ou execute o comando abaixo:<br/>"
        "<code>code /home/gusvato/FIAP_postech/Fase_2/tech_challenge/Tech-Challenge-Fase-2-Pipeline</code><br/>"
        "<i>Alternativamente, acesse no menu superior: <b>File &gt; Open Folder...</b> e selecione a pasta do projeto.</i>"
    )
    story.append(Paragraph(p1_desc, body_style))
    story.append(Spacer(1, 6))

    # Passo 2: Selecionar o Interpretador
    story.append(Paragraph("Passo 2: Seleção do Interpretador Python", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=4))
    p2_desc = (
        "1. Pressione o atalho <b><code>Ctrl + Shift + P</code></b> (ou <code>F1</code>) para abrir a Paleta de Comandos.<br/>"
        "2. Digite e selecione: <b><code>Python: Select Interpreter</code></b>.<br/>"
        "3. Escolha o ambiente Anaconda configurado: <b><code>Python 3.13.5 ('base': conda) /home/gusvato/anaconda3/bin/python</code></b>.<br/>"
        "<i>O VS Code integrará automaticamente as bibliotecas do Google Cloud SDK, Pandas, PyArrow e PyTest.</i>"
    )
    story.append(Paragraph(p2_desc, body_style))
    story.append(Spacer(1, 6))

    # Passo 3: Executar os Testes Automatizados (pytest)
    story.append(Paragraph("Passo 3: Execução da Suíte de Testes Automatizados (49 Testes)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=4))
    p3_desc = (
        "<b>• Pela Interface Visual (Aba Testing):</b> Clique no ícone do <b>Frasco de Ensaio (🧪)</b> na barra lateral esquerda. "
        "Você verá os 5 módulos organizados (<code>test_bronze.py</code>, <code>test_silver.py</code>, <code>test_gold.py</code>, "
        "<code>test_streaming.py</code>, <code>test_quality.py</code>). Clique no botão <b>Play ▶️</b> no topo para rodar tudo.<br/>"
        "<b>• Pelo Terminal Integrado:</b> Pressione <b><code>Ctrl + `</code></b> e digite: <code>pytest tests/ -v</code>"
    )
    story.append(Paragraph(p3_desc, body_style))
    story.append(Spacer(1, 6))

    # Passo 4: Menu Run & Debug (F5)
    story.append(Paragraph("Passo 4: Execução e Debug pelo Menu 'Run and Debug' (F5)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=4))
    p4_intro = (
        "O arquivo <code>.vscode/launch.json</code> foi configurado com 5 perfis prontos de execução. "
        "Acesse a aba <b>Run and Debug</b> (<code>Ctrl + Shift + D</code>) e escolha no menu superior:"
    )
    story.append(Paragraph(p4_intro, body_style))
    story.append(Spacer(1, 4))

    launch_data = [
        [
            Paragraph("<b>Perfil no Menu</b>", body_bold),
            Paragraph("<b>Arquivo / Módulo Executado</b>", body_bold),
            Paragraph("<b>Descrição / Objetivo</b>", body_bold)
        ],
        [
            Paragraph("<code>🚀 1. Orquestrador - Pipeline Completo</code>", body_style),
            Paragraph("<code>orchestrator.py --stage full</code>", code_block_style),
            Paragraph("Executa o ciclo E2E com health checks pré/pós e audit log", body_style)
        ],
        [
            Paragraph("<code>ℹ️ 2. Orquestrador - Help / Args</code>", body_style),
            Paragraph("<code>orchestrator.py --help</code>", code_block_style),
            Paragraph("Exibe parâmetros CLI e documentação dos estágios", body_style)
        ],
        [
            Paragraph("<code>⚡ 3. Simulação Streaming (Pub/Sub)</code>", body_style),
            Paragraph("<code>streaming/streaming_pipeline.py simulate</code>", code_block_style),
            Paragraph("Simula produção e validação de 30 eventos em tempo real", body_style)
        ],
        [
            Paragraph("<code>🧪 4. Executar Testes (pytest)</code>", body_style),
            Paragraph("<code>pytest tests/ -v</code>", code_block_style),
            Paragraph("Roda a suíte completa de 49 testes com mocks offline", body_style)
        ],
        [
            Paragraph("<code>📄 5. Gerar Relatório PDF</code>", body_style),
            Paragraph("<code>generate_pdf_report.py</code>", code_block_style),
            Paragraph("Compila e atualiza o arquivo <code>checklist_verificacao.pdf</code>", body_style)
        ]
    ]

    launch_table = Table(launch_data, colWidths=[160, 150, 194])
    launch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(launch_table)
    story.append(Spacer(1, 8))

    # Passo 5: Comandos no Terminal Integrado
    story.append(Paragraph("Passo 5: Comandos Úteis para o Terminal Integrado (Ctrl + `)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=4))

    cmd_data = [
        [
            Paragraph("<b>Finalidade</b>", body_bold),
            Paragraph("<b>Comando no Terminal</b>", body_bold)
        ],
        [
            Paragraph("Ajuda e opções do Orquestrador", body_style),
            Paragraph("<code>python orchestrator.py --help</code>", code_block_style)
        ],
        [
            Paragraph("Executar apenas estágio Bronze (Ingestão)", body_style),
            Paragraph("<code>python orchestrator.py --stage bronze</code>", code_block_style)
        ],
        [
            Paragraph("Executar apenas estágio Silver (Transformação)", body_style),
            Paragraph("<code>python orchestrator.py --stage silver</code>", code_block_style)
        ],
        [
            Paragraph("Executar apenas estágio Gold (Analytics)", body_style),
            Paragraph("<code>python orchestrator.py --stage gold</code>", code_block_style)
        ],
        [
            Paragraph("Executar apenas Quality Checks", body_style),
            Paragraph("<code>python orchestrator.py --stage quality</code>", code_block_style)
        ],
        [
            Paragraph("Simulação do Streaming contínuo", body_style),
            Paragraph("<code>python streaming/streaming_pipeline.py simulate</code>", code_block_style)
        ],
        [
            Paragraph("Atualizar relatório PDF do checklist", body_style),
            Paragraph("<code>python generate_pdf_report.py</code>", code_block_style)
        ]
    ]

    cmd_table = Table(cmd_data, colWidths=[180, 324])
    cmd_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(cmd_table)
    story.append(Spacer(1, 8))

    # Seção 6: Vídeo de Apresentação
    story.append(Paragraph("Passo 6: Vídeo de Apresentação Otimizado (Item 14)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=4))
    v_desc = (
        "• <b>Arquivo:</b> <code>/home/gusvato/FIAP_postech/Fase_2/tech_challenge/video_TC_2_editado.mp4</code><br/>"
        "• <b>Duração:</b> <b>04 minutos e 55 segundos</b> (em total conformidade com o limite máximo de 04m 58s).<br/>"
        "• <b>Qualidade:</b> Full HD 1080p, áudio estéreo AAC 48kHz e tamanho compacto de 13 MB."
    )
    story.append(Paragraph(v_desc, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF do Guia VS Code gerado com sucesso: {PDF_FILENAME}")


if __name__ == "__main__":
    build_pdf()
