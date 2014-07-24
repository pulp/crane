# This builds a docker image that can be used to build an el6 rpm for crane.
# Optionally specify a branch besides master by setting the environment variable
# GIT_BRANCH. Mount storage in to the location /tmp/tito in order to capture the
# files produced by the build process. Example:
#
# $ sudo docker run -e "GIT_BRANCH=mhrivnak-packaging" -v /home/mhrivnak/delme:/tmp/tito pulp/cranebuilder

FROM centos
MAINTAINER Pulp Team <pulp-list@redhat.com>

ENV GIT_BRANCH master

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

RUN yum update -y

RUN yum install -y python2-devel python-setuptools python-mock python-flask git tito

WORKDIR /root

RUN git clone https://github.com/pulp/crane.git

WORKDIR /root/crane

CMD cd /root/crane && git pull && git checkout $GIT_BRANCH && tito build --rpm
