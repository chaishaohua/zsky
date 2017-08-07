使用说明

yum -y install git 

git  clone https://github.com/wenguonideshou/zsky.git

cd zsky

sh zsky.sh

此一键包只在centos7系统有效

安装过程中会提示输入管理员用户名、密码、邮箱，输入后耐心等待即可访问 http://IP

后台地址 http://IP/admin


Q：怎么限制/提高爬取速度？

A：修改simdht_worker.py里的max_node_qsize=后面的数字，越大爬取越快，越小爬取越慢

Q：修改数据库密码后怎么修改程序里的配置？

A：修改manage.py里的mysql+pymysql://root:密码@127.0.0.1、修改manage.py里的DB_PASS、修改simdht_worker.py里的DB_PASS、修改sphinx.conf里的sql_pass

Q：怎么确定爬虫是在正常运行？

A：2个方法，1.查看后台首页爬虫日志  2.执行 ps -ef|grep -v grep|grep simdht 如果有结果说明爬虫正在运行

Q：更新版本/模板后怎么立即生效？

A：执行 systemctl restart gunicorn 重启gunicorn

Q：为什么首页统计的数据远远小于后台的数据？

A：在数据量变大后，索引将占用CPU 100%，非常影响用户访问网站，为了最小程度减小此影响，你想现在更新爬取结果的话，手动执行索引 systemctl restart indexer ，需要注意的是，数据量越大 索引所耗费时间越长

Q：如何查看索引是否成功？

A：执行 systemstl status indexer 可以看到索引记录

Q：想确定搜索进程是否正常运行

A：执行 systemctl status searchd ，如果是绿色的running说明搜索进程完全正常

Q：我以前使用的搜片大师/手撕包菜，可以迁移过来吗？

A：程序在开发之初就已经考虑到从这些程序迁移过来的问题，所以你不用担心，完全可以无缝迁移。如果有需要，请联系作者QQ 153329152 付费为你提供服务

Q：网站经常收到版权投诉，有没有好的解决办法？

A：除了删除投诉的影片数据外，你可以使用前段Nginx、后端gunicorn+爬虫+数据库+索引的模式，甚至多前端模式。如果有需要，请联系作者QQ 153329152 付费为你提供服务

如果还有疑问 加入QQ群：253524174 获取解决办法
