#先修改manage.py里的mysql+pymysql://root:密码@127.0.0.1、修改manage.py里的DB_PASS、修改simdht_worker.py里的DB_PASS、修改sphinx.conf里的sql_pass
#再执行下面的命令
#设置时区
\cp -rpf /usr/share/zoneinfo/Asia/Chongqing /etc/localtime
#关闭防火墙
systemctl stop firewalld.service  
systemctl disable firewalld.service   
systemctl stop iptables.service  
systemctl disable iptables.service  
#关闭SELinux
setenforce 0  
sed -i s/"SELINUX=enforcing"/"SELINUX=disabled"/g  /etc/selinux/config
#优化内和参数
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
#安装必须组件和库
yum -y install wget gcc gcc-c++ python-devel mariadb mariadb-devel mariadb-server
yum -y install psmisc net-tools lsof epel-release
yum -y install python-pip
yum -y install redis
pip install -r requirements.txt
#如果提示没有pip命令,或者你使用linode的主机,请取消下面4行的注释
#wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
#wget -qO /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
#yum clean metadata
#yum makecache
cd /root/zsky
#创建女优、番号文件夹
mkdir -p /root/zsky/uploads  /root/zsky/uploads/nvyou  /root/zsky/uploads/fanhao
#注册为服务
\cp -rpf systemctl/gunicorn.service  systemctl/indexer.service  systemctl/searchd.service /etc/systemd/system
systemctl daemon-reload	
\cp -rpf /root/zsky/my.cnf  /etc/my.cnf 
#设置数据库密码
mysqladmin -uroot password 新密码
#启动mariadb
systemctl start  mariadb.service 
systemctl enable mariadb.service
#启动redis
systemctl start redis.service
systemctl enable redis.service
#密码是上面设置的数据库密码
mysql  -uroot -p密码 -e "create database IF NOT EXISTS zsky default character set utf8mb4;set global max_allowed_packet = 64*1024*1024;set global max_connections = 100000;" 
#建表
python manage.py init_db
#按照提示输入管理员用户名、密码、邮箱
python manage.py create_user
#配置前端nginx
yum -y install nginx
systemctl start  nginx.service
systemctl enable  nginx.service
#修改/etc/nginx/nginx.conf里面绑定的域名再执行下面的拷贝
\cp -rpf /root/zsky/nginx.conf  /etc/nginx/nginx.conf 
nginx -s reload
#启动后端gunicorn+gevent,开启日志并在后台运行
systemctl start gunicorn
systemctl enable gunicorn
#启动爬虫,开启日志并在后台运行
nohup python /root/zsky/simdht_worker.py >/root/zsky/spider.log 2>&1& 
#编译sphinx,启动索引,启动搜索进程
yum -y install git gcc cmake automake g++ mysql-devel
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
#开机自启动, 优化redis参数
chmod +x /etc/rc.local
echo "systemctl start  mariadb.service" >> /etc/rc.local
echo "systemctl start  redis.service" >> /etc/rc.local
echo "systemctl start  nginx.service" >> /etc/rc.local
echo "systemctl start  gunicorn.service" >> /etc/rc.local
echo "systemctl start  indexer.service" >> /etc/rc.local
echo "systemctl start  searchd.service" >> /etc/rc.local
echo "nohup python /root/zsky/simdht_worker.py>/root/zsky/spider.log 2>&1&" >> /etc/rc.local
echo "echo never > /sys/kernel/mm/transparent_hugepage/enabled" >> /etc/rc.local
#设置计划任务,每天早上5点进行主索引
#每分钟索引一次女优、番号、搜索记录的表
yum -y install  vixie-cron crontabs
systemctl start crond.service
systemctl enable crond.service
crontab -l > /tmp/crontab.bak
echo '*/1 * * * * /usr/local/sphinx-jieba/bin/indexer -c /root/zsky/sphinx.conf keywords actors tags --rotate' >> /tmp/crontab.bak
echo '0 5 * * * /usr/local/sphinx-jieba/bin/indexer -c /root/zsky/sphinx.conf film --rotate&&/usr/local/sphinx-jieba/bin/searchd --config ~/zsky/sphinx.conf' >> /tmp/crontab.bak
crontab /tmp/crontab.bak
#查看当前进程运行状态
pgrep -l nginx
pgrep -l searchd
pgrep -l gunicorn


常见问题与回答：
安装过程中会提示输入管理员用户名、密码、邮箱，输入后耐心等待即可访问 http://IP
后台地址 http://IP/admin
Q：拿到手如何对主机进行基本的评测？
A：查看主机CPU、内存、系统、IO性能、带宽
wget -qO- bench.sh|bash
查看服务器硬盘通电时间
yum -y install smartmontools
smartctl -A /dev/sda
#结果中的Power_On_Hours就是通电时间，单位为小时
如果发现通电时间过长，最好找机房商量更换硬盘。
Q：如何给番号/女优添加图片、评分？
A：后台-番号-番号图片-上传图片（图片名不能重复）,或者后台-女优-女优图片-上传图片（图片名不能重复）
后台-热门番号-新建， 在“图片”选项中输入/uploads/fanhao/图片地址 ， 以及片名、评分、显示顺序 , 
后台-女优大全-新建， 在“图片”选项中输入/uploads/fanhao/图片地址 ， 以及片名、评分、显示顺序 ,
在templates/index.html里调用{{k.pic}}代表番号的图片地址,{{k.score}}代表番号的评分，调用{{pic.pic}}代表女优图片地址,{{pic.score}}代表女优评分
Q：怎么限制/提高爬取速度？
A：修改simdht_worker.py里的max_node_qsize=后面的数字，越大爬取越快，越小爬取越慢
Q：觉得数据库空密码不安全，怎么修改数据库密码？
A：执行mysqladmin -uroot -p password 123456!@#$%^     ，将提示输入当前密码，直接回车即可，123456!@#$%^是新密码
Q：修改数据库密码后怎么修改程序里的配置？
A：修改manage.py里的mysql+pymysql://root:密码@127.0.0.1、修改manage.py里的DB_PASS、修改simdht_worker.py里的DB_PASS、修改sphinx.conf里的sql_pass
Q：怎么确定爬虫是在正常运行？
A：2个方法，1.查看后台首页爬虫日志 2.执行 ps -ef|grep -v grep|grep simdht 如果有结果说明爬虫正在运行
Q：更新版本/模板后怎么立即生效？
A：执行 systemctl restart gunicorn 重启gunicorn
Q：为什么首页统计的数据远远小于后台的数据？
A：在数据量变大后，索引将占用CPU 100%，非常影响用户访问网站，为了最小程度减小此影响 默认设置为每天早上5点更新索引，你想现在更新爬取结果的话，手动执行索引 systemctl restart indexer ，需要注意的是，数据量越大 索引所耗费时间越长
Q：如何查看索引是否成功？
A：执行 systemctl status indexer 可以看到索引记录
Q：觉得索引速度有点慢，怎么加快？
A：修改sphinx.conf里面的mem_limit = 512M ，根据你的主机的内存使用情况来修改，越大索引越快，最大可以设置2048M
Q：想确定搜索进程是否正常运行
A：执行 systemctl status searchd ，如果是绿色的running说明搜索进程完全正常
Q：发现又升级了，想重装，直接安装新版本，如何备份数据库？
A：执行 mysqldump -uroot -p zsky>/root/zsky.sql  导出数据库  //将提示输入当前密码，直接回车即可，数据库导出后存在/root/zsky.sql
Q：数据库备份后，现在重新安装了程序，如何导入旧数据？
A：执行 mysql -uroot -p zsky</root/zsky.sql       //假设你的旧数据库文件是/root/zsky.sql，将提示输入当前密码，直接回车即可
Q：怎么修改搜索结果数量，默认5000条太少了
A：修改manage.py里的max_matches=5000
Q：sitemap数量默认是100太少了，怎么修改？
A：修改manage.py里的sql语句 'SELECT info_hash,create_time FROM film order by create_time desc limit 100' 里的数量
Q：我以前使用的搜片大师/手撕包菜，可以迁移过来吗？
A：程序在开发之初就已经考虑到从这些程序迁移过来的问题，所以你不用担心，完全可以无缝迁移。
Q：网站经常收到版权投诉，有没有好的解决办法？
A：除了删除投诉的影片数据外，你可以使用前端Nginx、后端gunicorn+爬虫+数据库+索引在不同主机上的模式，甚至多前端模式，这样 即使前端被主机商强行封机，也能保证后端数据的安全
Q：我的流量超大！用gunicorn+gevent有时候数据库会挂，怎么办？
A：我们还有更好的web架构，只是不能注册为服务，要用命令执行。保证在硬件和带宽足够的情况下，50W PV内没问题。所以你只需要放心做流量即可。
Q：为什么搜索记录、番号、女优不是更新后立马生效的？
A：crontab -e可以看到， 默认是1分钟更新一次番号、女优、搜索记录的索引，为什么不直接从数据库读取呢？这是为了满足10W-100W数据量的番号、女演员、搜索记录的需求，尽量减小对数据库的压力。
Q：如果我需要搭配宝塔面板/lnmp/oneinstack 应该怎么操作？
A：可以先安装宝塔面板/lnmp/oneinstack ，只选择安装其中的nginx，本文档里关于nginx的命令都不执行就OK了
Q：女演员、番号手动输入太麻烦了，怎么办？
A：作者会想办法给大家提供数据/爬虫的
Q：如何一次性修改站点名字，在模板中全部生效？
A：修改manage.py的{{sitename}}=""的内容
Q：如何修改URL规则？
A：修改@app.route后面引号内的内容，除了<变量>内容之外，都可以修改
Q：修改模板后重启gunicorn也没有生效？
A：刷新redis缓存
redis-cli
#进入redis的命令行
flushdb
#刷新全部缓存
systemctl restart gunicorn
#重启gunicorn
Q：如何修改后台地址？
A：修改为如下：
admin = Admin(app,name='管理中心',base_template='admin/my_master.html',index_view=MyAdminIndexView(name='首页',template='admin/index.html',url='/fucku'))
#重启systemctl restart gunicorn
Q：如何手动启动爬虫、索引、搜索进程？
A：查看爬虫当前线程数
ps -ef|grep simdht|awk '{print $2}'|grep -v grep|xargs ps hH |wc -l
或
ps -xH|grep simdht|grep -v grep|wc -l
杀死爬虫
ps -ef|grep simdht_worker.py|grep -v grep|awk '{print $2}'|xargs kill -9
杀死并启动爬虫
ps -ef|grep simdht_worker.py|grep -v grep|awk '{print $2}'|xargs kill -9
cd /root/zsky
nohup python simdht_worker.py>/root/zsky/spider.log 2>&1&
手动索引
/usr/local/sphinx-jieba/bin/indexer -c /root/zsky/sphinx.conf film --rotate
手动启动搜索进程
/usr/local/sphinx-jieba/bin/searchd --config ~/zsky/sphinx.conf
