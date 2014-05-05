# This runs crane (http://github.com/pulp/crane) on centos6
#
# Example usage:
# $ sudo docker run -p 5000:80 -v /home/you/cranedata:/var/lib/crane/metadata pulp/crane

FROM centos
MAINTAINER Pulp Team <pulp-list@redhat.com>

RUN rpm -iUvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

RUN yum update -y

RUN yum install -y python-flask python-pip httpd mod_wsgi

RUN mkdir -p /var/lib/crane/metadata/

ADD deployment/apache22.conf /etc/httpd/conf.d/crane.conf
ADD deployment/crane_el6.wsgi /usr/share/crane/crane.wsgi

ADD crane /usr/local/src/crane/crane
ADD setup.py /usr/local/src/crane/
ADD setup.cfg /usr/local/src/crane/
ADD requirements.txt /usr/local/src/crane/
ADD test-requirements.txt /usr/local/src/crane/

ADD LICENSE /usr/share/doc/python-crane/
ADD COPYRIGHT /usr/share/doc/python-crane/
ADD README.rst /usr/share/doc/python-crane/

RUN pip-python install /usr/local/src/crane/

ENV APACHE_RUN_USER apache
ENV APACHE_RUN_GROUP apache

EXPOSE 80

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D", "FOREGROUND"]
