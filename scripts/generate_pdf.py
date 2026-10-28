"""Genera el documento de entrega con ReportLab (dependencia de documentacion)."""
import json
import re
import sys
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfgen import canvas as pdfcanvas
from pypdf import PdfReader, PdfWriter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_project import TABLES

BLUE=colors.HexColor('#173854')
TEAL=colors.HexColor('#087e8b')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Subtitle',fontName='Helvetica-Bold',fontSize=11,leading=16,textColor=TEAL))
styles.add(ParagraphStyle(name='BodyCustom',fontName='Helvetica',fontSize=10,leading=15,spaceAfter=8,textColor=colors.HexColor('#253444')))
styles.add(ParagraphStyle(name='SmallCustom',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=5))
styles.add(ParagraphStyle(name='TableHeader',parent=styles['SmallCustom'],textColor=colors.white))
styles['Title'].textColor=BLUE
styles['Heading1'].textColor=BLUE
styles['Heading1'].spaceBefore=16
styles['Heading1'].spaceAfter=10
styles['Heading2'].textColor=TEAL
styles['Heading2'].spaceBefore=12
styles['Heading2'].spaceAfter=8
styles['Heading1'].keepWithNext=True
styles['Heading2'].keepWithNext=True

def para(text,style='BodyCustom'):
    value=escape(text)
    value=re.sub(r'(https://[^\s<]+)',r'<link href="\1" color="#087e8b">\1</link>',value)
    return Paragraph(value,styles[style])

def footer(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setStrokeColor(TEAL)
    canvas.line(1.8*cm,1.55*cm,w-1.8*cm,1.55*cm)
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(BLUE)
    canvas.drawString(1.8*cm,1.1*cm,'Inventario y ventas | Bases de Datos I')
    canvas.drawRightString(w-1.8*cm,1.1*cm,str(doc.page))
    canvas.restoreState()

def main():
    source=(ROOT/'docs/analisis.md').read_text(encoding='utf-8')
    # Markdown companion is intentionally kept alongside the canonical Mermaid source.
    er=(ROOT/'docs/diagrama_er.mmd').read_text(encoding='utf-8')
    (ROOT/'docs/diagrama_er.md').write_text('# Diagrama entidad-relacion\n\n![Modelo ER completo](diagrama_er.svg)\n\n[Descargar PNG](diagrama_er.png) | [Fuente Mermaid](diagrama_er.mmd)\n\n<details>\n<summary>Codigo Mermaid editable</summary>\n\n```mermaid\n'+er+'```\n\n</details>\n',encoding='utf-8')
    story=[Spacer(1,2.2*cm),para('PROYECTO FINAL','Subtitle'),Spacer(1,.5*cm),para('Inventario y ventas multisucursal','Title'),Spacer(1,.7*cm),para('Diseno de base de datos relacional y API REST','Heading2'),Spacer(1,.7*cm),para('SQL Server + FastAPI | 24 tablas relacionadas | 3FN'),para('27 de octubre de 2026'),Spacer(1,1*cm),para('Repositorio de entrega','Heading2'),para('https://github.com/BansheeUmg/Proyecto_Final_BD_API'),Spacer(1,1*cm),para('Documento de analisis, reglas, modelo, dependencias funcionales, arquitectura y validacion. El codigo, los scripts y el diagrama ER completo se incluyen en el repositorio.'),PageBreak()]
    lines=source.splitlines()
    index=0
    while index<len(lines):
        line=lines[index]
        if not line.strip(): index+=1; continue
        if line.startswith('# '): index+=1; continue
        if line.startswith('|'):
            data=[]
            while index<len(lines) and lines[index].startswith('|'):
                row=lines[index]
                if not re.match(r'^\|[-| ]+\|$',row):
                    data.append([para(x.strip(),'TableHeader' if not data else 'SmallCustom') for x in row.strip('|').split('|')])
                index+=1
            table=Table(data,colWidths=[4.3*cm,13.1*cm],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f5f8'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([table,Spacer(1,10)])
            continue
        if line.startswith('### '): story.append(para(line[4:],'Heading2'))
        elif line.startswith('## '): story.append(para(line[3:],'Heading1'))
        else:
            paragraph=line
            while index+1<len(lines) and lines[index+1].strip() and not lines[index+1].startswith(('#','|','- ')) and not re.match(r'^\d+\.',lines[index+1]):
                index+=1; paragraph+=' '+lines[index]
            story.append(para(paragraph))
        index+=1
    story.extend([PageBreak(),para('Anexo A. Diccionario de datos','Heading1'),para('PK: id INT IDENTITY en cada tabla. Las FK son obligatorias salvo venta_id y compra_id de MovimientosInventario. Los atributos y las restricciones se reproducen del catalogo fuente; el script SQL es la definicion ejecutable.')])
    for name,(fields,extra,_) in TABLES.items():
        cells=[para(name,'Heading2'),para('id INT IDENTITY PRIMARY KEY; '+fields+('; '+extra if extra else ''),'SmallCustom')]
        story.append(KeepTogether(cells))
    story.extend([PageBreak(),para('Anexo B. Relaciones del modelo ER','Heading1'),para('El archivo Mermaid contiene la representacion grafica con todos los atributos. Esta matriz proporciona una vista legible de cada relacion. 1:N permite cero o mas hijos; 1:0..1 es una extension opcional.')])
    rows=[[para('Padre','SmallCustom'),para('Hijo / FK','SmallCustom'),para('Cardinalidad','SmallCustom')]]
    for name,(fields,_,_) in TABLES.items():
        for col in re.split(r',\s*(?![^()]*\))',fields):
            fk=re.search(r'REFERENCES (\w+)\(id\)',col)
            if fk: rows.append([para(fk[1],'SmallCustom'),para(name+'.'+col.split()[0],'SmallCustom'),para('1:0..1' if 'UNIQUE' in col else '1:N','SmallCustom')])
    matrix=Table(rows,colWidths=[4.5*cm,10.2*cm,2.7*cm],repeatRows=1)
    matrix.setStyle(TableStyle([('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#edf3f6'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(matrix)
    story.extend([Spacer(1,12),para('La tabla MovimientosInventario restringe con CHECK el origen exclusivo: venta o compra. Las asociaciones EmpleadoRoles, ProductoProveedores y Existencias resuelven N:M mediante dos relaciones 1:N y una clave compuesta UNIQUE.'),PageBreak(),para('Anexo C. Evidencia de validacion','Heading1')])
    for line in (ROOT/'docs/validacion.md').read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.startswith('#'): story.append(para(line))
    output=ROOT/'docs/Proyecto_Final.pdf'
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=1.8*cm,leftMargin=1.8*cm,topMargin=1.7*cm,bottomMargin=2*cm,title='Inventario y ventas - Proyecto Final BD',author='Proyecto Final BD',pageCompression=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    # Lamina amplia para que las 24 entidades y sus atributos puedan ampliarse al leer.
    graph=ROOT/'docs/diagrama_er.png'
    if graph.exists():
        buffer=BytesIO()
        c=pdfcanvas.Canvas(buffer,pagesize=(1500,1230))
        c.setFont('Helvetica-Bold',24)
        c.setFillColor(BLUE)
        c.drawString(40,1180,'Anexo D. Diagrama entidad-relacion completo')
        c.setFont('Helvetica',13)
        c.drawString(40,1150,'24 entidades | PK y FK | relaciones 1:0..1 y 1:N | asociaciones N:M resueltas')
        c.drawImage(str(graph),40,40,width=1420,height=1090,preserveAspectRatio=True,anchor='c')
        c.showPage();c.save();buffer.seek(0)
        writer=PdfWriter()
        writer.append(PdfReader(str(output)))
        writer.append(PdfReader(buffer))
        writer.add_metadata({'/Title':'Inventario y ventas - Proyecto Final BD'})
        with output.open('wb') as stream: writer.write(stream)
    print(output)

if __name__=='__main__': main()
