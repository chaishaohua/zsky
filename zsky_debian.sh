#!/bin/sh
#By 我本戏子 2017.7
if [ $(id -u) != "0" ]; then
    echo "当前非root用户登录系统， 请使用root用户运行此脚本!"
    exit 1
fi
grep SwapTotal /proc/meminfo
if [ $? -ne 0 ]
then
	echo "主机没有swap, 将自动创建swap"
	fallocate -l 1G /swapfile
	chmod 600 /swapfile
	mkswap /swapfile
	swapon /swapfile
	echo '/swapfile   swap    swap    sw  0   0' >> /etc/fstab
fi
\cp -rpf /usr/share/zoneinfo/Asia/Chongqing /etc/localtime
systemctl stop firewalld.service  
systemctl disable firewalld.service   
systemctl stop iptables.service  
systemctl disable iptables.service  
setenforce 0  
sed -i s/"SELINUX=enforcing"/"SELINUX=disabled"/g  /etc/selinux/config
cat << EOF > /etc/sysctl.conf
net.ipv4.tcp_syn_retries = 1
net.ipv4.tcp_synack_retries = 1
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl =15
net.ipv4.tcp_retries2 = 5
net.ipv4.tcp_fin_timeout = 2
net.ipv4.tcp_max_tw_buckets = 36000
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_orphans = 32768
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 16384
net.ipv4.tcp_wmem = 8192 131072 16777216
net.ipv4.tcp_rmem = 32768 131072 16777216
net.ipv4.tcp_mem = 786432 1048576 1572864
net.ipv4.ip_local_port_range = 1024 65000
net.ipv4.ip_conntrack_max = 65536
net.ipv4.netfilter.ip_conntrack_max=65536
net.ipv4.netfilter.ip_conntrack_tcp_timeout_established=180
net.core.somaxconn = 16384
net.core.netdev_max_backlog = 16384
vm.overcommit_memory = 1
net.core.somaxconn = 511
EOF
/sbin/sysctl -p /etc/sysctl.conf
/sbin/sysctl -w net.ipv4.route.flush=1
echo ulimit -HSn 65536 >> /etc/rc.local
echo ulimit -HSn 65536 >>/root/.bash_profile
ulimit -HSn 65536
apt-get update
apt-get -y install wget gcc build-essential libsnmp-dev libcurl4-gnutls-dev libxml2-dev  mariadb-server mariadb-client  
apt-get -y install psmisc net-tools lsof python-dev python-pip libevent-dev python-setuptools python-requests python-gevent python-flask
apt-get -y install git libmysqlclient-dev
apt-get -y install python-pip
apt-get -y install redis-server
pip install -r requirements.txt
cd /root/zsky
mkdir /root/zsky/uploads
\cp -rpf systemctl/indexer.service  systemctl/searchd.service /etc/systemd/system
\cp -rpf systemctl/gunicorn_debian.service  /etc/systemd/system/gunicorn.service
systemctl daemon-reload	
\cp my_debian.cnf /etc/mysql/my.cnf
mysql_secure_installation
systemctl start  mysql.service 
systemctl enable mysql.service
systemctl start redis-server.service
systemctl enable redis-server.service
mysql -uroot -p -e"create database zsky default character set utf8mb4;set global interactive_timeout=31536000;set global wait_timeout=31536000;set global max_allowed_packet = 64*1024*1024;set global max_connections = 10000;"  
#建表
python manage.py init_db
#按照提示输入管理员用户名、密码、邮箱
python manage.py create_user
#杀死占用80端口的进程
kill -9 $(lsof -i:80|tail -1|awk '"$1"!=""{print $2}')
#配置前端nginx
apt-get -y install nginx
systemctl start  nginx.service
systemctl enable  nginx.service
\cp -rpf /root/zsky/nginx.conf  /etc/nginx/nginx.conf 
nginx -s reload
cd /root/zsky
#启动后端gunicorn+gevent,开启日志并在后台运行
systemctl start gunicorn
systemctl enable gunicorn
#启动爬虫,开启日志并在后台运行
nohup python simdht_worker.py >/root/zsky/spider.log 2>&1& 
#编译sphinx,启动索引,启动搜索进程
apt-get -y install git gcc cmake automake g++ mysql-devel
git clone https://github.com/wenguonideshou/sphinx-jieba.git
cd sphinx-jieba
git clone https://github.com/wenguonideshou/cppjieba.git
./configure --prefix=/usr/local/sphinx-jieba 
\cp -r cppjieba/include/cppjieba src/ 
\cp -r cppjieba/deps/limonp src/ 
make install
\cp -r cppjieba/dict/* /usr/local/sphinx-jieba/etc/ 
cd /usr/local/sphinx-jieba/
\cp etc/jieba.dict.utf8 etc/xdictjieba.dict.utf8
\cp etc/user.dict.utf8 etc/xdictuser.dict.utf8
\cp etc/hmm_model.utf8 etc/xdicthmm_model.utf8
\cp etc/idf.utf8 etc/xdictidf.utf8
\cp etc/stop_words.utf8 etc/xdictstop_words.utf8
systemctl start indexer	
systemctl enable indexer
systemctl start searchd	
systemctl enable searchd
#开机自启动
chmod +x /etc/rc.local
echo "systemctl start  mysql.service" >> /etc/rc.local
echo "systemctl start  redis.service" >> /etc/rc.local
echo "systemctl start  nginx.service" >> /etc/rc.local
echo "systemctl start  gunicorn.service" >> /etc/rc.local
echo "systemctl start  indexer.service" >> /etc/rc.local
echo "systemctl start  searchd.service" >> /etc/rc.local
echo "cd /root/zsky" >> /etc/rc.local
echo "nohup python simdht_worker.py>/root/zsky/spider.log 2>&1&" >> /etc/rc.local
echo "echo never > /sys/kernel/mm/transparent_hugepage/enabled" >> /etc/rc.local
#设置计划任务,每天早上5点进行主索引
apt-get -y install  cron
systemctl start cron.service
systemctl enable cron.service
crontab -l > /tmp/crontab.bak
echo '0 5 * * * /usr/local/sphinx-jieba/bin/indexer -c /root/zsky/sphinx.conf film --rotate&&/usr/local/sphinx-jieba/bin/searchd --config ~/zsky/sphinx.conf' >> /tmp/crontab.bak
crontab /tmp/crontab.bak
echo '当前进程运行状态:'
pgrep -l nginx
pgrep -l searchd
pgrep -l gunicorn
