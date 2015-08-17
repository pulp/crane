%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

Name: python-crane
Version: 1.2.0
Release: 0.4.beta%{?dist}
Summary: docker-registry-like API with redirection, as a wsgi app

License: GPLv2
URL: https://github.com/pulp/crane
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch

BuildRequires: python2-devel
BuildRequires: python-setuptools

Requires: python-flask >= 0.9
Requires: python-setuptools
Requires: python-rhsm
Requires(post): policycoreutils-python
Requires(postun): policycoreutils-python

%description
This wsgi application exposes a read-only API similar to docker-registry, which
docker can use for "docker pull" operations. Requests for actual image files
are responded to with 302 redirects to a URL formed with per-repository
settings.


%prep
%setup -q -n %{name}-%{version}


%build
%{__python2} setup.py build


%install
%{__python2} setup.py install --skip-build --root %{buildroot}

mkdir -p %{buildroot}/%{_usr}/share/crane/
mkdir -p %{buildroot}/%{_var}/lib/crane/metadata/

cp deployment/crane.wsgi %{buildroot}/%{_usr}/share/crane/

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
cp deployment/apache24.conf %{buildroot}/%{_usr}/share/crane/apache.conf
cp deployment/crane.wsgi %{buildroot}/%{_usr}/share/crane/
%else
cp deployment/apache22.conf %{buildroot}/%{_usr}/share/crane/apache.conf
cp deployment/crane_el6.wsgi %{buildroot}/%{_usr}/share/crane/crane.wsgi
%endif

rm -rf %{buildroot}%{python2_sitelib}/tests


%files
%defattr(-,root,root,-)
%{python2_sitelib}/crane
%{python2_sitelib}/crane*.egg-info
%{_usr}/share/crane/
%dir %{_var}/lib/crane/
%dir %{_var}/lib/crane/metadata/
%doc AUTHORS COPYRIGHT LICENSE README.rst


%post
semanage fcontext -a -t httpd_sys_content_t '%{_var}/lib/crane(/.*)?'
restorecon -R -v %{_var}/lib/crane

%postun
if [ $1 -eq 0 ] ; then  # final removal
semanage fcontext -d -t httpd_sys_content_t '%{_var}/lib/crane(/.*)?'
restorecon -R -v %{_var}/lib/crane
fi


%changelog
* Fri Nov 21 2014 Chris Duryee <cduryee@redhat.com> 0.2.2-1
- Bump release to 1 (cduryee@redhat.com)

* Wed Oct 22 2014 Chris Duryee <cduryee@redhat.com> 0.2.2-0.3.beta
- the /v1/repositories/<repo_id>/images call now handles the default "library"
  namespace (mhrivnak@redhat.com)
- review improvements (mhrivnak@redhat.com)
- Adding a basic "what is crane?" section to the README (mhrivnak@redhat.com)

* Mon Sep 15 2014 Randy Barlow <rbarlow@redhat.com> 0.2.2-0.2.beta
- Do not run unit tests during RPM build (cduryee@redhat.com)

* Mon Sep 15 2014 Randy Barlow <rbarlow@redhat.com> 0.2.2-0.1.beta
- updating pulp/cranebuilder for centos7 (mhrivnak@redhat.com)
- updating the Dockerfile to use centos7 and add the python-rhsm dependency
  (mhrivnak@redhat.com)

* Mon Jul 28 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.2.1-1.beta
- Add python-rhsm to spec (bcourt@redhat.com)
- Move indirect-requirements needed for the travis environment to a separate
  requirements.txt file (bcourt@redhat.com)

* Fri Jul 25 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.2.0-1.beta
- Monitor the data directory for changes (bcourt@redhat.com)
- ensuring that setuptools excludes tests from a distribution package
  (mhrivnak@redhat.com)
- simplifying the config loading so that it uses a default config file
  (mhrivnak@redhat.com)
- Implementing the search API to use a Google Search Appliance backend.
  (mhrivnak@redhat.com)
- adding Dockerfile for cranebuilder (mhrivnak@redhat.com)
- Add Entitlement support for Crane (bcourt@redhat.com)
- Added Dockerfile for crane (mhrivnak@redhat.com)

* Fri May 02 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.1.0-0.4.beta
- Incrementing the release number. (mhrivnak@redhat.com)
- adding selinux fcontext changes to spec file (mhrivnak@redhat.com)
- Adding comments about how to deploy crane. (mhrivnak@redhat.com)

* Thu May 01 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.1.0-0.3.alpha
- adding metadata dir to rpm spec file (mhrivnak@redhat.com)

* Wed Apr 30 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.1.0-0.2.alpha
- adding wsgi file specifically for el6 to handle python-jinja2-26 weirdness
  (mhrivnak@redhat.com)

* Wed Apr 30 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.1.0-0.1.alpha
- new package built with tito

