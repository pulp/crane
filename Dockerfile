# This runs crane (http://github.com/pulp/crane) on centos7
#
# Example usage:
# $ sudo docker run -p 5000:80 -v /home/you/cranedata:/var/lib/crane/metadata pulp/crane

FROM centos:centos7
MAINTAINER Pulp Team <pulp-list@redhat.com>

RUN yum -y install epel-release

RUN yum update -y

RUN yum install -y python-flask python-pip httpd mod_wsgi python-rhsm

RUN mkdir -p /var/lib/crane/metadata/

ADD deployment/apache24.conf /etc/httpd/conf.d/crane.conf
ADD deployment/crane.wsgi /usr/share/crane/crane.wsgi

ADD crane /usr/local/src/crane/crane
ADD setup.py /usr/local/src/crane/
ADD setup.cfg /usr/local/src/crane/
ADD requirements.txt /usr/local/src/crane/
ADD test-requirements.txt /usr/local/src/crane/

ADD LICENSE /usr/share/doc/python-crane/
ADD COPYRIGHT /usr/share/doc/python-crane/
ADD README.rst /usr/share/doc/python-crane/

RUN pip install /usr/local/src/crane/

ENV APACHE_RUN_USER apache
ENV APACHE_RUN_GROUP apache

EXPOSE 80

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D", "FOREGROUND"]
