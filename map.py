#coding:utf-8
import datetime
import pymysql
import os

DB_HOST='127.0.0.1'
DB_NAME_MYSQL='zsky'
DB_PORT_MYSQL=3306
DB_NAME_SPHINX='film'
DB_PORT_SPHINX=9306
DB_USER='root'
DB_PASS=''
DB_CHARSET='utf8mb4'
domain="http://www.0276789.com/"

if not os.path.exists('map'):
    os.mkdir('map')
    print "成功创建map文件夹"
conn = pymysql.connect(host=DB_HOST,port=DB_PORT_MYSQL,user=DB_USER,password=DB_PASS,db=DB_NAME_MYSQL,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
curr = conn.cursor()
totalsql='select count(*) from search_hash'
curr.execute(totalsql)
totalcounts=curr.fetchall()
total=int(totalcounts[0]['count(*)'])
pages=(total+4999)/5000
print "将在map目录生成{}个文件".format(pages+1)
mtime = datetime.datetime.now().strftime('%Y-%m-%d')
sitemaplist=[]
for i in range(1,pages+1):
   sitemap = domain+'map/sitemap{}.xml'.format(i)
   sitemap_xml = '<sitemap><loc>{}</loc><lastmod>{}</lastmod></sitemap>'.format(sitemap, mtime)
   sitemaplist.append(sitemap_xml)
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{}</sitemapindex>'.format("".join(x for x in sitemaplist))
with open('map/sitemap.xml', 'wb') as f:
   f.write(sitemap_content)
   f.close()
   print "成功创建sitemap.xml"
for i in range(1,pages+1):
   urlsql='SELECT info_hash FROM search_hash order by id desc limit %s,5000'
   curr.execute(urlsql,(i-1)*5000)
   urlhash=curr.fetchall()
   url="".join(['<url><loc>{}hash/{}.html</loc><lastmod>{}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>'.format(domain,info_hash['info_hash'], mtime) for info_hash in urlhash ])
   urlset = '<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{}</urlset>'.format(url)
   with open('map/sitemap{}.xml'.format(i), 'wb') as f_urlset:
       f_urlset.write(urlset)
       f_urlset.close()
       print "成功创建sitemap{}.xml".format(i)
curr.close()
conn.close()
