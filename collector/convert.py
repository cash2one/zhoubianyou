# -*- encoding=utf8 -*-
import os
import sqlite3
import xlwt
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def set_style(name,height,bold=False):
    style = xlwt.XFStyle()  # 初始化样式

    font = xlwt.Font()  # 为样式创建字体
    font.name = name # 'Times New Roman'
    font.bold = bold
    font.color_index = 4
    font.height = height

    # borders= xlwt.Borders()
    # borders.left= 6
    # borders.right= 6
    # borders.top= 6
    # borders.bottom= 6

    style.font = font
    # style.borders = borders

    return style

if __name__ == '__main__':
    conn = sqlite3.connect('result.db')
    cur = conn.cursor()
    res = cur.execute('''
        select url, result 
        from resultdb_comment_fetcher
    ''')
        # url:0, comment_txt:1, create_time:2, location:3, shop_id:4, shop_name:5, user_name:6, user_rate:7
    header = [u'评论内容', u'创建时间', u'用户名称', u'评级', u'图片标记']
    xls_dict = {}
    header_style = set_style('Times New Roman',220,True)
    item_style = set_style('Arial',220,True)
    for row in res:
        pic_token = row[0]
        result_dict = json.loads(row[1])
        shop_id = result_dict['shop_id']
        shop_name = result_dict['shop_name']
        create_time = result_dict['create_time']
        location = result_dict['location']
        user_name = result_dict['user_name']
        user_rate = result_dict['user_rate']
        comment_txt = result_dict['comment_txt']
        if shop_id not in xls_dict:
            xls_dict[shop_id] = {'hd': xlwt.Workbook(), 'idx': 1, 'name': shop_name}
            xls_dict[shop_id]['sheet'] = xls_dict[shop_id]['hd'].add_sheet(u'comments', cell_overwrite_ok=True)
            for idx, item in enumerate(header):
                xls_dict[shop_id]['sheet'].write(0, idx, item, header_style)
        items = [comment_txt, create_time, user_name, user_rate, pic_token]
        sheet = xls_dict[shop_id]['sheet']
        for idx, item in enumerate(items):
            sheet.write(xls_dict[shop_id]['idx'], idx, item, item_style)
        xls_dict[shop_id]['idx'] += 1

    for shop_id, fd in xls_dict.iteritems():
        fd['hd'].save(os.path.join(u'guangzhou', str(shop_id).decode('utf-8') + '_'+str(fd['name']).decode('utf-8') + '_' + str(fd['idx']-1).decode('utf-8') + u'.xls'))

