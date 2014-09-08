# This builds a docker image that can be used to build an el6 rpm for crane.
# Optionally specify a branch besides master by setting the environment variable
# GIT_BRANCH. Mount storage in to the location /tmp/tito in order to capture the
# files produced by the build process. Example:
#
# $ sudo docker run -e "GIT_BRANCH=mhrivnak-packaging" -v /home/mhrivnak/delme:/tmp/tito pulp/cranebuilder

FROM centos:centos7
MAINTAINER Pulp Team <pulp-list@redhat.com>

ENV GIT_BRANCH master

RUN yum -y install http://dl.fedoraproject.org/pub/epel/beta/7/x86_64/epel-release-7-1.noarch.rpm

RUN yum update -y

RUN yum install -y git tito python-rhsm

WORKDIR /root

RUN git clone https://github.com/pulp/crane.git

WORKDIR /root/crane

RUN yum-builddep -y python-crane.spec

CMD cd /root/crane && git pull && git checkout $GIT_BRANCH && tito build --rpm --test
