# etiquetas.py
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import black
from reportlab.graphics.barcode import code128
from reportlab.pdfbase.pdfmetrics import stringWidth
import textwrap
from datetime import datetime
import os

from config import *

def gerar_etiquetas(lista_produtos, caminho_pdf):
    """
    Gera PDF com etiquetas de preço
    
    Args:
        lista_produtos: Lista de tuplas (descricao, preco, ean)
        caminho_pdf: Caminho para salvar o PDF
    """
    print(f"\n📄 Criando etiquetas no arquivo: {caminho_pdf}")
    print(f"   Total de produtos: {len(lista_produtos)}")
    
    # Configurações da página
    largura = ETIQUETA_LARGURA_CM * cm
    altura = ETIQUETA_ALTURA_CM * cm
    margem_esq = 0.5 * cm
    margem_dir = 0.5 * cm
    
    c = canvas.Canvas(caminho_pdf, pagesize=(largura, altura))
    
    for idx, (descricao, preco, ean) in enumerate(lista_produtos, start=1):
        # Debug
        print(f"      Produto {idx}: {descricao[:30]}... | R$ {preco} | EAN: {ean}")
        
        # Prepara dados
        descricao = str(descricao).upper().strip()
        preco_txt = f"R$ {float(preco):.2f}".replace(".", ",")
        
        # Desenha descrição (centralizada, máximo 2 linhas)
        desenhar_descricao(c, descricao, largura, margem_esq, margem_dir)
        
        # Desenha preço (grande à esquerda)
        c.setFont("Helvetica-Bold", 31.5)
        c.drawString(margem_esq, 0.9 * cm, preco_txt)
        
        # Desenha código de barras e EAN (centralizado à direita)
        if ean and len(ean) > 5:
            desenhar_codigo_barras(c, ean, largura)
        
        # Moldura da etiqueta (opcional)
        c.setStrokeColor(black)
        c.rect(0, 0, largura, altura, stroke=1, fill=0)
        c.showPage()
    
    c.save()
    print(f"✅ Etiquetas geradas com sucesso: {caminho_pdf}")

def desenhar_descricao(c, descricao, largura, margem_esq, margem_dir):
    """Desenha a descrição do produto no topo da etiqueta"""
    fonte_base = 10
    largura_max = largura - margem_esq - margem_dir
    
    # Ajusta fonte para caber no espaço
    while fonte_base >= 6:
        c.setFont("Helvetica-Bold", fonte_base)
        linhas = textwrap.wrap(descricao, width=40)
        
        # Garante exatamente 2 linhas
        if len(linhas) == 1:
            linhas.append("")
        elif len(linhas) > 2:
            linhas = [linhas[0], " ".join(linhas[1:])]
        
        # Verifica se cabe na largura
        larguras = [stringWidth(l, "Helvetica-Bold", fonte_base) for l in linhas]
        if all(w <= largura_max for w in larguras):
            break
        fonte_base -= 1
    
    # Desenha as linhas
    c.setFont("Helvetica-Bold", fonte_base)
    if linhas[1] == "":
        c.drawCentredString(largura / 2, 2.4 * cm, linhas[0])
    else:
        c.drawCentredString(largura / 2, 2.5 * cm, linhas[0])
        c.drawCentredString(largura / 2, 2.1 * cm, linhas[1])

def desenhar_codigo_barras(c, ean, largura):
    """Desenha código de barras e número EAN"""
    try:
        # Código de barras
        barcode = code128.Code128(ean, barHeight=7 * mm, barWidth=0.52)
        barcode_x = largura - 3.5 * cm
        barcode_y = 1.1 * cm
        barcode.drawOn(c, barcode_x, barcode_y)
        
        # Número EAN abaixo do código
        c.setFont("Helvetica", 9)
        c.drawCentredString(barcode_x + 1.75 * cm, barcode_y - 10, ean)
    except Exception as e:
        print(f"⚠️ Erro ao gerar código de barras {ean}: {e}")

def gerar_etiquetas_por_filial(df_produtos, df_estoque, saida_dir):
    """
    Gera etiquetas separadas por filial baseado no estoque
    
    Returns:
        dict: {filial: caminho_pdf}
    """
    print("\n🏷️ Gerando etiquetas por filial...")
    
    # Processa estoque por filial
    filiais_dict = processar_estoque_por_filial(df_estoque)
    
    print(f"\nTotal de filiais encontradas: {len(filiais_dict)}")
    for filial, codigos in filiais_dict.items():
        print(f"Filial {filial} → {len(codigos)} códigos no estoque")
    
    arquivos_etiquetas = {}
    
    for filial, codigos in filiais_dict.items():
        print(f"\n➡️ Processando filial {filial}")
        print(f"   Total de códigos no estoque: {len(codigos)}")
        
        # Filtra produtos alterados que existem nesta filial
        df_filial = df_produtos[df_produtos["Código"].astype(int).isin(codigos)]
        
        print(f"   Produtos alterados nesta filial: {len(df_filial)}")
        if df_filial.empty:
            print("   ⚠️ Nenhum produto alterado nesta filial — pulando.")
            continue
        
        # Gera etiquetas
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        caminho_pdf = os.path.join(saida_dir, f"etiquetas_F{filial:02d}_{timestamp}.pdf")
        
        lista_produtos = list(zip(
            df_filial["Descrição Completa"], 
            df_filial["Preço"], 
            df_filial["EAN"]
        ))
        
        gerar_etiquetas(lista_produtos, caminho_pdf)
        arquivos_etiquetas[filial] = caminho_pdf
    
    return arquivos_etiquetas

def processar_estoque_por_filial(df_estoque):
    """
    Processa relatório de estoque para extrair códigos por filial
    """
    # Encontra coluna 'Cód.'
    col_cod = None
    for c in df_estoque.columns:
        if str(c).strip() == "Cód.":
            col_cod = c
            break
    
    if col_cod is None:
        raise Exception("❌ Coluna 'Cód.' não encontrada no relatório de estoque.")
    
    idx_cod = df_estoque.columns.get_loc(col_cod)
    filiais_dict = {}
    filial_atual = None
    coletando_produtos = False
    
    # Percorre linhas
    for idx, row in df_estoque.iterrows():
        valor_cod = str(row[col_cod]).strip()
        
        # Encontrou início de uma filial
        if valor_cod == "Filial:":
            nome_filial_raw = str(row.iloc[idx_cod + 2]).strip()
            try:
                filial_num = int(nome_filial_raw.split()[0].replace("F", ""))
            except:
                continue
            
            filiais_dict[filial_num] = []
            filial_atual = filial_num
            coletando_produtos = True
            continue
        
        # Coletando códigos da filial atual
        if coletando_produtos and filial_atual is not None:
            if valor_cod == "" or valor_cod.lower() == "nan":
                coletando_produtos = False
                continue
            
            try:
                codigo_prod = int(float(valor_cod))
                filiais_dict[filial_atual].append(codigo_prod)
            except:
                pass
    
    return filiais_dict
