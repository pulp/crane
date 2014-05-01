%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

Name: python-crane
Version: 0.1.0
Release: 0.3.alpha%{?dist}
Summary: docker-registry-like API with redirection, as a wsgi app

License: GPLv2
URL: https://github.com/pulp/crane
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch

BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-mock

Requires: python-flask >= 0.9

%description
This wsgi application exposes a read-only API similar to docker-registry, which
docker can use for "docker pull" operations. Requests for actual image files
are responded to with 302 redirects to a URL formed with per-repository
settings.


%prep
%setup -q -n %{name}-%{version}


%check
%{__python2} setup.py test


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


%changelog
* Wed Apr 30 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.1.0-0.2.alpha
- adding wsgi file specifically for el6 to handle python-jinja2-26 weirdness
  (mhrivnak@redhat.com)

* Wed Apr 30 2014 Michael Hrivnak <mhrivnak@redhat.com> 0.1.0-0.1.alpha
- new package built with tito

