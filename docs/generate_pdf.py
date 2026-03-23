from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

OUTPUT_PATH = 'E:/bisai/docs/Neural Mesh Generator 开发文档.pdf'

def create_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=HexColor('#2C3E50')
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseSubtitle',
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=HexColor('#7F8C8D')
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseH1',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=24,
        spaceBefore=20,
        spaceAfter=12,
        textColor=HexColor('#2980B9')
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseH2',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        spaceBefore=15,
        spaceAfter=8,
        textColor=HexColor('#34495E')
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseH3',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor=HexColor('#2C3E50')
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseBody',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        firstLineIndent=20
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseBodyNoIndent',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    ))
    
    styles.add(ParagraphStyle(
        name='CodeStyle',
        fontName='Courier',
        fontSize=8,
        leading=10,
        spaceAfter=8,
        backColor=HexColor('#F8F9FA'),
    ))
    
    return styles

def create_cover_page(styles):
    elements = []
    elements.append(Spacer(1, 4*cm))
    elements.append(Paragraph('Neural Mesh Generator', styles['ChineseTitle']))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph('开发文档', styles['ChineseTitle']))
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph('基于深度学习的三维网格生成系统', styles['ChineseSubtitle']))
    elements.append(Paragraph('Development Documentation', styles['ChineseSubtitle']))
    elements.append(Spacer(1, 3*cm))
    
    info_data = [
        ['版本', 'V1.0.0'],
        ['文档状态', '正式发布'],
        ['编写日期', '2026年3月'],
        ['技术栈', 'Python 3.12 / PyQt6 / ComfyUI']
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#7F8C8D')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#2C3E50')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*cm))
    elements.append(Paragraph('CONFIDENTIAL - FOR COMPETITION USE', styles['ChineseSubtitle']))
    elements.append(PageBreak())
    return elements

def create_toc(styles):
    elements = []
    elements.append(Paragraph('目录', styles['ChineseH1']))
    elements.append(Spacer(1, 0.5*cm))
    
    toc_items = [
        '1. 项目概述',
        '   1.1 项目背景',
        '   1.2 项目目标',
        '   1.3 创新点',
        '2. 系统架构',
        '   2.1 整体架构设计',
        '   2.2 模块划分',
        '3. 技术栈',
        '4. 核心模块设计',
        '5. 工作流配置',
        '6. API接口设计',
        '7. 模型集成',
        '8. 部署与配置',
        '附录',
    ]
    
    for item in toc_items:
        elements.append(Paragraph(item, styles['ChineseBodyNoIndent']))
    
    elements.append(PageBreak())
    return elements

def create_chapter1(styles):
    elements = []
    elements.append(Paragraph('1. 项目概述', styles['ChineseH1']))
    
    elements.append(Paragraph('1.1 项目背景', styles['ChineseH2']))
    elements.append(Paragraph(
        '随着人工智能技术的快速发展，生成式AI在图像、文本等领域取得了突破性进展。然而，在3D内容创作领域，'
        '传统建模方式仍然需要专业的技能和大量的时间投入。Neural Mesh Generator 项目旨在利用最新的深度学习技术，'
        '实现从文本描述或2D图像自动生成高质量3D模型，降低3D内容创作的门槛，提高生产效率。',
        styles['ChineseBody']
    ))
    
    elements.append(Paragraph('1.2 项目目标', styles['ChineseH2']))
    goals = [
        '提供直观易用的图形用户界面，支持三种3D生成模式',
        '实现高质量的3D模型生成，支持纹理贴图和UV展开',
        '支持实时预览和进度显示，提升用户体验',
        '提供灵活的配置选项，支持快速模式和高质量模式',
        '输出标准格式的3D模型文件(.glb)，便于后续使用'
    ]
    for goal in goals:
        elements.append(Paragraph(f'- {goal}', styles['ChineseBodyNoIndent']))
    
    elements.append(Paragraph('1.3 创新点', styles['ChineseH2']))
    innovations = [
        ('多模态输入支持', '同时支持文本、单图、双图三种输入方式'),
        ('实时进度反馈', '通过WebSocket实现实时进度推送'),
        ('多视图预览', '同时展示2D、UV、法线贴图和3D模型'),
        ('质量/速度权衡', '提供4B快速模式和9B高质量模式'),
    ]
    for title, desc in innovations:
        elements.append(Paragraph(f'<b>{title}</b>: {desc}', styles['ChineseBody']))
    
    elements.append(PageBreak())
    return elements

def create_chapter2(styles):
    elements = []
    elements.append(Paragraph('2. 系统架构', styles['ChineseH1']))
    
    elements.append(Paragraph('2.1 整体架构设计', styles['ChineseH2']))
    elements.append(Paragraph(
        'Neural Mesh Generator 采用分层架构设计，主要分为四层：用户界面层、API客户端层、推理引擎层和AI模型层。',
        styles['ChineseBody']
    ))
    
    elements.append(Paragraph('2.2 模块划分', styles['ChineseH2']))
    modules = [
        ('用户界面层', '负责用户交互，基于PyQt6框架开发'),
        ('API客户端层', '负责与ComfyUI后端通信'),
        ('推理引擎层', 'ComfyUI作为推理引擎，负责节点调度'),
        ('AI模型层', '包含FLUX.2、Hunyuan3D等核心模型'),
    ]
    for name, desc in modules:
        elements.append(Paragraph(f'<b>{name}</b>: {desc}', styles['ChineseBody']))
    
    elements.append(PageBreak())
    return elements

def create_chapter3(styles):
    elements = []
    elements.append(Paragraph('3. 技术栈', styles['ChineseH1']))
    
    frontend_tech = [
        ['技术', '版本', '用途'],
        ['Python', '3.12', '主要开发语言'],
        ['PyQt6', '6.10+', 'GUI框架'],
        ['PyVista', '0.47+', '3D可视化'],
        ['Pillow', '12.0', '图像处理'],
    ]
    
    table = Table(frontend_tech, colWidths=[4*cm, 3*cm, 8*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F8F9FA')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    
    elements.append(PageBreak())
    return elements

def create_chapter4(styles):
    elements = []
    elements.append(Paragraph('4. 核心模块设计', styles['ChineseH1']))
    
    elements.append(Paragraph('4.1 GUI模块', styles['ChineseH2']))
    elements.append(Paragraph(
        'GUI模块是用户与系统交互的主要入口，基于PyQt6框架开发。主要包含MainWindow、Worker、LogWindow三个核心类。',
        styles['ChineseBody']
    ))
    
    elements.append(Paragraph('4.2 API客户端模块', styles['ChineseH2']))
    elements.append(Paragraph(
        'API客户端模块(api_client.py)负责与ComfyUI后端的所有通信。主要函数包括：upload_image()、queue_prompt()、run_pipeline()等。',
        styles['ChineseBody']
    ))
    
    elements.append(Paragraph('4.3 启动器模块', styles['ChineseH2']))
    elements.append(Paragraph(
        '启动器模块(launcher.py)负责系统的启动流程，包括检测ComfyUI服务、自动启动后端、启动GUI等。',
        styles['ChineseBody']
    ))
    
    elements.append(PageBreak())
    return elements

def create_chapter5(styles):
    elements = []
    elements.append(Paragraph('5. 工作流配置', styles['ChineseH1']))
    
    elements.append(Paragraph(
        '系统采用ComfyUI的工作流JSON格式定义生成流程。三种模式对应三个工作流文件。',
        styles['ChineseBody']
    ))
    
    workflow_files = [
        ['模式', '文件路径'],
        ['文生3D', 'backend/文生图片生模型.json'],
        ['图生3D', 'backend/图片生模型.json'],
        ['双图融合', 'backend/双图生图生模型.json'],
    ]
    
    table = Table(workflow_files, colWidths=[5*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#9B59B6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F8F9FA')]),
    ]))
    elements.append(table)
    
    elements.append(PageBreak())
    return elements

def create_chapter6(styles):
    elements = []
    elements.append(Paragraph('6. API接口设计', styles['ChineseH1']))
    
    apis = [
        ['接口', '方法', '功能'],
        ['/upload/image', 'POST', '上传图片文件'],
        ['/prompt', 'POST', '提交工作流'],
        ['/history/{id}', 'GET', '查询执行历史'],
        ['/ws', 'WebSocket', '实时消息推送'],
    ]
    
    table = Table(apis, colWidths=[4*cm, 3*cm, 7*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E74C3C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    elements.append(table)
    
    elements.append(PageBreak())
    return elements

def create_chapter7(styles):
    elements = []
    elements.append(Paragraph('7. 模型集成', styles['ChineseH1']))
    
    elements.append(Paragraph('7.1 FLUX.2集成', styles['ChineseH2']))
    elements.append(Paragraph(
        'FLUX.2是Black Forest Labs开发的先进文生图模型。支持4B快速模式和9B高质量模式。',
        styles['ChineseBody']
    ))
    
    elements.append(Paragraph('7.2 Hunyuan3D集成', styles['ChineseH2']))
    elements.append(Paragraph(
        'Hunyuan3D是腾讯开发的开源3D生成模型，支持从单张图片生成高质量的3D模型。',
        styles['ChineseBody']
    ))
    
    elements.append(PageBreak())
    return elements

def create_chapter8(styles):
    elements = []
    elements.append(Paragraph('8. 部署与配置', styles['ChineseH1']))
    
    requirements = [
        ['项目', '最低配置', '推荐配置'],
        ['操作系统', 'Windows 10', 'Windows 11'],
        ['CPU', 'Intel i5', 'Intel i7'],
        ['内存', '16 GB', '32 GB'],
        ['GPU', 'RTX 3060', 'RTX 4080'],
    ]
    
    table = Table(requirements, colWidths=[4*cm, 5*cm, 5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1ABC9C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    elements.append(table)
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph('安装步骤：', styles['ChineseH2']))
    steps = [
        '1. 创建虚拟环境: python -m venv .venv',
        '2. 激活虚拟环境: .venv\\Scripts\\activate',
        '3. 安装依赖: pip install -r requirements.txt',
        '4. 下载模型文件到models/unet/目录',
        '5. 启动ComfyUI后端服务',
        '6. 运行launcher.py启动应用'
    ]
    for step in steps:
        elements.append(Paragraph(step, styles['ChineseBodyNoIndent']))
    
    elements.append(PageBreak())
    return elements

def create_appendix(styles):
    elements = []
    elements.append(Paragraph('附录: 依赖清单', styles['ChineseH1']))
    
    deps = [
        'PyQt6>=6.10',
        'pyvista>=0.47',
        'pyvistaqt>=0.11',
        'websocket-client>=1.8',
        'requests>=2.32',
        'Pillow>=12.0',
        'trimesh>=4.11',
        'torch>=2.6.0+cu126',
        'diffusers>=0.37',
        'transformers>=5.3',
    ]
    
    for dep in deps:
        elements.append(Paragraph(dep, styles['CodeStyle']))
    
    return elements

def main():
    os.makedirs('E:/bisai/docs', exist_ok=True)
    
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = create_styles()
    elements = []
    
    elements.extend(create_cover_page(styles))
    elements.extend(create_toc(styles))
    elements.extend(create_chapter1(styles))
    elements.extend(create_chapter2(styles))
    elements.extend(create_chapter3(styles))
    elements.extend(create_chapter4(styles))
    elements.extend(create_chapter5(styles))
    elements.extend(create_chapter6(styles))
    elements.extend(create_chapter7(styles))
    elements.extend(create_chapter8(styles))
    elements.extend(create_appendix(styles))
    
    doc.build(elements)
    print(f'PDF created: {OUTPUT_PATH}')

if __name__ == '__main__':
    main()