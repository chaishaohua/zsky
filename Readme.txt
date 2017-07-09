说明：
程序基于本人修复的手撕包菜爬虫，python实现的磁力搜索网站，代码比较烂，请轻喷！
少数功能未完成：搜索排行榜、浏览排行榜、浏览热度、DMCA投诉
没有使用sphinx进行索引，而是用redis缓存访问页面，以后可能会做调整
模板引擎是jinja2，编写自己的专属模板非常方便，中文版文档 http://docs.jinkan.org/docs/jinja2/

实验环境：centos7 python2.7

安装：
tar zxvf zsky.tar.gz
systemctl stop firewalld.service  
systemctl disable firewalld.service   
systemctl stop iptables.service  
systemctl disable iptables.service  
setenforce 0  
sed -i s/"SELINUX=enforcing"/"SELINUX=disabled"/g  /etc/selinux/config
cd zsky
yum -y install wget gcc gcc-c++ python-devel mariadb mariadb-devel mariadb-server
yum -y install epel-release python-pip redis
pip install -r requirements.txt
systemctl start  mariadb.service 
systemctl enable mariadb.service
systemctl start redis.service
systemctl enable redis.service
mysql -uroot  -e"create database zsky default character set utf8mb4;" 
python manage.py init_db
#建表
python manage.py create_user
#按照提示属于用户名、密码、邮箱
nohup gunicorn -k gevent mange:app -b 0.0.0.0:80 --reload>/dev/zero 2>&1&  
nohup python simdht_worker.py >/dev/zero 2>&1&
现在访问http://IP 网站能够正常运行，解析域名即可完成部署

后台地址http://IP/admin

