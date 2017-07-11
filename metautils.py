#encoding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import binascii

cats = {
    u'影视': u'影视',
    u'图像': u'图像',
    u'文档书籍': u'文档书籍',
    u'音乐': u'音乐',
    u'压缩文件': u'压缩文件',
    u'安装包': u'安装包',
}

def get_label(name):
    if name in cats:
        return cats[name]
    return u'其他'

def get_label_by_crc32(n):
    for k in cats:
        if binascii.crc32(k)&0xFFFFFFFFL == n:
            return k
    return u'其他'

def get_extension(name):
    return os.path.splitext(name)[1]

def get_category(ext):
    ext = ext + '.'
    cats = {
        u'影视': '.avi.mp4.rmvb.m2ts.wmv.mkv.flv.qmv.rm.mov.vob.asf.3gp.mpg.mpeg.m4v.f4v.',
        u'图像': '.jpg.bmp.jpeg.png.gif.tiff.',
        u'文档书籍': '.pdf.isz.chm.txt.epub.bc!.doc.ppt.',
        u'音乐': '.mp3.ape.wav.dts.mdf.flac.',
        u'压缩文件': '.zip.rar.7z.tar.gz.iso.dmg.pkg.',
        u'安装包': '.exe.app.msi.apk.'
    }
    for k, v in cats.iteritems():
        if ext in v:
            return k
    return u'其他'

def get_detail(y):
    if y.get('files'):
        y['files'] = [z for z in y['files'] if not z['path'].startswith('_')]
    else:
        y['files'] = [{'path': y['name'], 'length': y['length']}]
    y['files'].sort(key=lambda z:z['length'], reverse=True)
    bigfname = y['files'][0]['path']
    ext = get_extension(bigfname).lower()
    y['category'] = get_category(ext)
    y['extension'] = ext


