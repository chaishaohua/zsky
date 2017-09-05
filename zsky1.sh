#!/bin/sh
#By 我本戏子 2017.8

yum -y update
yum -y install git

导入女忧
mysql -uroot -p zsky</root/zsky/search_actors.sql
导入番号
mysql -uroot -p zsky</root/zsky/search_keywords.sql

net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr



cd zsky&&sh zsky2.sh