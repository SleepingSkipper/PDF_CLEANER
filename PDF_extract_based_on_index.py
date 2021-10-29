from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import re
import io
import glob
import os
import pandas as pd
from PDF_CLEANER import extract_only_texts

class PDFProcessor:
    def __init__(self, input_file:str, leader_list:list, re_list:list):
        self.input_file = input_file
        self.leader_list = leader_list
        self.re_list = re_list
        self.mokuji=[]
        self.mokuji_page_number = None
        
        self.first_index = None
        self.second_index = None
        
        self.extract_area = range(3,20) # Noneだと、全ページを抽出する
#         self.extract_titles = []
    
    #  re_listで定義した正規表現に一致するものを目次データとして抜き出す関数
    def parse_outline(self):
        rsrcmgr = PDFResourceManager()
        mokuji_page = False
        with open(self.input_file, "rb") as fp:
            mokuji_page = False
            for pidx, page in enumerate(PDFPage.get_pages(fp)):
                out_fp = io.StringIO()
                device = TextConverter(
                    rsrcmgr,
                    out_fp,
                    laparams=LAParams(),
                    imagewriter=None
                )
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                interpreter.process_page(page)
                out_fp.seek(0)
                page_str = out_fp.read()
                
                if mokuji_page:
                    break

                for leader in self.leader_list:
                    # Find a page which contains 目次
                    if leader in page_str:
                        print("yes",leader)
                        mokuji_page = True
                        self.mokuji_page_number = pidx
                        for ln in page_str.split('\n'):
                            for re_expression in self.re_list:
                                m = re.match(re_expression, ln)
                                if m != None:
                                    full_title = m.groups()[0]
                                    title_num = m.groups()[1]
                                    title = m.groups()[2]
                                    page_number = m.groups()[-1]
                                else:
                                    continue
                                self.mokuji.append([full_title,title_num,title,page_number])
                                break
                    elif mokuji_page:
                        break
        return self.mokuji,self.mokuji_page_number
    
        
    # 目次の情報をもとに、取り出すページ範囲を決定する
    def define_extract_range(self):
        # 目次ページが不明、または目次内容が読み取れなかった場合は全ページから文章を抜き出す。
        if self.mokuji_page_number == None or self.mokuji==[]:
            print("Mokuji page was not detected. We'll extract whole PDF file. We'll extract p3-20 from PDF file.")
            return self.extract_area
        # 目次情報が取れた場合
        else:
            for i,item in enumerate(self.mokuji):
                if item[1] == "1" or item[1] == "１":
                    self.first_index =  item[-1]

                if item[1] == "2" or item[1] == "２":
                    self.second_index = item[-1]

            # インデックス１とインデックス２どちらかが見つからなかった場合
            if self.first_index == None or self.second_index ==None:
                print("Either Index 1 or Index 2 was not detected.")
                # インデックス１だけ見つかった場合　⇨ インデックス１〜最終ページ
                if self.first_index != None:
                    print("Only Index 1 was detected. We'll extract Index 1 to p20 of PDF file).")
                    self.extract_area = [i for i in range(mokuji_page_number-1+int(self.first_index), 20)]
                    return self.extract_area
                # インデックス2だけ見つかった場合　⇨ 目次ページ+1 ~ インデックス２のページ
                elif self.second_index != None:
                    print("Only Index 2 was detected. We'll extract first page to Index 2 of PDF file.")
                    self.extract_area = [i for i in range(self.mokuji_page_number+1,self.mokuji_page_number+int(self.second_index))]
                    return self.extract_area 
                # インデックス１もインデックス２も見つからなかった場合。pdfの目次ページのレイアウトがおかしい場合は対応不可なので、全ページを対象にする
                else:
                    print("Index was not properly detected from Mokuji page. We'll extract p3-20 from PDF file.")
                    return self.extract_area
                    
            # インデックスが１、２とも見つかった場合
            else:
                #　２nd index pageまで念の為抽出する。
                print("Both Index1 and 2 were detected.")
                self.extract_area = [i for i in range(self.mokuji_page_number-1+int(self.first_index),self.mokuji_page_number+int(self.second_index))]
#                 self.extract_area = [i+1 for i in range(self.mokuji_page_number-1+int(self.first_index),self.mokuji_page_number+int(self.second_index))]
                return self.extract_area
#                 extract_titles = [re.match("(.+?)(?=…)",j).group() for j in [i[0] for i in mokuji[first_index:second_index]]]

    def extract_text(self):  
        pages = [i+1 for i in self.extract_area]
#         print(self.extract_area)
#         print(pages)
        result = extract_only_texts(self.input_file, pages)
#         result = extract_text(self.input_file, page_numbers=self.extract_area, codec='utf-8')
#         print(result)
#         result_buffer =re.sub("\n","",result)
#         result_buffer = re.split("(?<=。(?!）))",result_buffer)
#         result_list = [re.sub("\u3000*\d*(.+?)\s*\((\d{4}\))*\s*(.+?)[期|年度]\s*\u3000*決算短信"," ",i) for i in result_buffer]
#         result_list = [re.sub("\u3000*\d*(.+?)\s*\d{4}\s*(.+?)[期|年度][\u3000|\s]*決算短信"," ",i) for i in result_buffer]
        print("ページレンジ：　",pages[0], " to ", pages[-1])
        print("総行数：　",len(result))
        return result

# if __name__ == "__main__":
#     pp.parse_outline()
#     pp.define_extract_range()
#     target_texts = pp.extract_text()
