使用说明

yum -y install git 

git  clone https://github.com/wenguonideshou/zsky.git

cd zsky

sh zsky.sh

此一键包只在centos7系统有效

安装过程中会提示输入管理员用户名、密码、邮箱，输入后耐心等待即可访问http://IP

后台地址http://IP/admin

Q：如何限制爬取速度？

A：修改simdht_worker.py里的max_node_qsize=后面的数字

Q：修改数据库密码后怎么修改程序里的配置？

A：修改manage.py里的mysql+pymysql://root:后面的内容、修改simdht_worker.py里的DB_PASS、修改sphinx.conf里的sql_pass

如果还有疑问 加入QQ群：253524174 获取解决办法
