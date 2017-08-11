使用说明
---
>此一键包只在centos7系统有效
```Bash
yum -y install git 

git  clone https://github.com/wenguonideshou/zsky.git

cd zsky&&sh zsky.sh
```

>此一键包只在Debian8+系统有效，注意：提示输入数据库密码的时候直接回车
```Bash
apt-get -y install git 

git  clone https://github.com/wenguonideshou/zsky.git

cd zsky&&sh zsky_debian.sh
```


>安装过程中会提示输入管理员用户名、密码、邮箱，输入后耐心等待即可访问 http://IP 

>后台地址 http://IP/admin 



**Q：如何给首页的推荐影片添加图片、评分？**

A：后台-文件管理-上传图片（图片名不能重复）,后台-首页推荐-新建，
    在“图片”选项中输入/uploads/图片地址 ， 以及片名、评分、显示顺序 , 
    在templates/index.html里调用{{k.pic}}代表图片地址,{{k.score}}代表影片评分


**Q：怎么限制/提高爬取速度？**

A：修改simdht_worker.py里的max_node_qsize=后面的数字，越大爬取越快，越小爬取越慢

**Q：觉得数据库空密码不安全，怎么修改数据库密码？**

A：执行mysqladmin -uroot -p password 123456!@#$%^      //将提示输入当前密码，直接回车即可，123456!@#$%^是新密码

**Q：修改数据库密码后怎么修改程序里的配置？**

A：修改manage.py里的mysql+pymysql://root:密码@127.0.0.1、修改manage.py里的DB_PASS、修改simdht_worker.py里的DB_PASS、修改sphinx.conf里的sql_pass

**Q：怎么确定爬虫是在正常运行？**

A：2个方法，1.查看后台首页爬虫日志  2.执行 ps -ef|grep -v grep|grep simdht 如果有结果说明爬虫正在运行

**Q：更新版本/模板后怎么立即生效？**

A：执行 systemctl restart gunicorn 重启gunicorn

**Q：为什么首页统计的数据远远小于后台的数据？**

A：在数据量变大后，索引将占用CPU 100%，非常影响用户访问网站，为了最小程度减小此影响 默认设置为每天早上5点更新索引，你想现在更新爬取结果的话，手动执行索引 systemctl restart indexer ，需要注意的是，数据量越大 索引所耗费时间越长

**Q：如何查看索引是否成功？**

A：执行 systemctl status indexer 可以看到索引记录

**Q：觉得索引速度有点慢，怎么加快？**

A：修改sphinx.conf里面的mem_limit = 512M ，根据你的主机的内存使用情况来修改，越大索引越快

**Q：想确定搜索进程是否正常运行**

A：执行 systemctl status searchd ，如果是绿色的running说明搜索进程完全正常

**Q：发现又升级了，想重装，直接安装新版本，如何备份数据库？**

A：执行 mysqldump -uroot -p zsky>/root/zsky.sql  导出数据库  //将提示输入当前密码，直接回车即可，数据库导出后存在/root/zsky.sql

**Q：数据库备份后，现在重新安装了程序，如何导入旧数据？**

A：执行 mysql -uroot -p zsky</root/zsky.sql       //假设你的旧数据库文件是/root/zsky.sql，将提示输入当前密码，直接回车即可

**Q：怎么修改搜索结果数量，默认1000条太少了**

A：修改manage.py里的max_matches=1000

**Q：sitemap数量默认是100太少了，怎么修改？**

A：修改manage.py里的sql语句 'SELECT info_hash,create_time FROM film order by create_time desc limit 100' 里的数量

**Q：我以前使用的搜片大师/手撕包菜，可以迁移过来吗？**

A：程序在开发之初就已经考虑到从这些程序迁移过来的问题，所以你不用担心，完全可以无缝迁移。如果有需求，请联系作者QQ 153329152 付费为你提供服务

**Q：网站经常收到版权投诉，有没有好的解决办法？**

A：除了删除投诉的影片数据外，你可以使用前端Nginx、后端gunicorn+爬虫+数据库+索引在不同主机上的模式，甚至多前端模式，这样 即使前端被主机商强行封机，也能保证后端数据的安全。如果有需求，请联系作者QQ 153329152 付费为你提供服务

**Q：我觉得这程序非常垃圾，怎么卸载？**

A：执行 mysql -uroot -p 将提示输入密码，输入密码后进入mysql管理界面，执行 drop database zsky;  （注意必须带分号)这样就删除了数据库，然后执行yum -y remove nginx mariadb mariadb-devel mariadb-server redis&&rm -rf /root/zsky 就成功卸载此程序了

*如果还有疑问 加入QQ群：253524174 获取解决办法*

