import pdfplumber
import re
import glob
import os

# 見出し直後以外の改行を削除する関数。
def cleaner(sentence):
    new=[]
    sentence_list = sentence.split("\n")
    for b in sentence_list:
        # ページ下部のページ番号が存在する場合は削除
        b = re.sub(r"―\s?[0-9０-９]\s?―\n?","",b)
        # 決算短信のヘッダーは無視
        if re.search(r"決算短信$",b):
            continue
        m = re.search(r"(\([0-9０-９]\)|（[0-9０-９]）|[0-9０-９]|[①-⑨]).+(に関する|等の|の).*(見通し|情報|概況|概要)",b)
        if m:
            new.append(b+"\n")
        else:
            new.append(b)
        
    return "".join(new)

# 表を無視し、テキストのみ抽出する。
def extract_only_texts(PDF:str, pages:list):
    def not_within_bboxes(obj):
        """Check if the object is in any of the table's bbox."""
        def obj_in_bbox(_bbox):
            """See https://github.com/jsvine/pdfplumber/blob/stable/pdfplumber/table.py#L404"""
            v_mid = (obj["top"] + obj["bottom"]) / 2
            h_mid = (obj["x0"] + obj["x1"]) / 2
            x0, top, x1, bottom = _bbox
            return (h_mid >= x0) and (h_mid < x1) and (v_mid >= top) and (v_mid < bottom)

        return not any(obj_in_bbox(__bbox) for __bbox in bboxes)
    
    sentences = []
    cleaned_sentences = []
    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages:

            page_number = page.page_number
            if page_number in pages:

    #         # Get the bounding boxes of the tables on the page.
                edges = page.curves+page.edges
                if len(edges)  >=1 :
                    bboxes = [
                        table.bbox for table in page.find_tables(
                            table_settings={
                                "vertical_strategy": "explicit",
                                "horizontal_strategy": "explicit",
                                "explicit_vertical_lines": edges,
                                "explicit_horizontal_lines": edges,
                                }
                            )
                        ]
                else:
                    bboxes = [
                        table.bbox for table in page.find_tables(
                            table_settings={
                                "vertical_strategy": "lines",
                                "horizontal_strategy": "lines",
                                }
                            )
                        ]
                    
                content = page.filter(not_within_bboxes).extract_text()
                content = re.sub("\xa0","\n",content)
                content = re.sub("\u3000","\n",content)
                sentences.append(content)
# 全ページぶん纏めたものを一旦、句読点で区切り直す
    whole_sentences = "\n".join(sentences)
    buffer = re.split("(?<=。(?!）))",whole_sentences)
    # buffer= re.split('(?<=。)',whole_sentences)
#  不自然な改行を削除し、改行によって離れている文同士は繋げる
    for b in buffer:
        b = cleaner(b).strip()
        if b.isdigit():
            continue
        else:
            cleaned_sentences.append(b)
    return cleaned_sentences
    
    # for b in buffer:
    #     cleaned_sentences.append(cleaner(b).strip())
    # return cleaned_sentences

    