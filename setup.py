import os
from setuptools import setup, find_packages

import crane


_abs_dir = os.path.dirname(os.path.abspath(__file__))
_req_path = os.path.join(_abs_dir, 'requirements.txt')
requirements = open(_req_path).read()
_test_req_path = os.path.join(_abs_dir, 'test-requirements.txt')
test_requirements = open(_test_req_path).read()


setup(
    name='crane',
    version=crane.version,
    packages=find_packages(exclude=['tests', 'tests.*']),
    url='http://www.pulpproject.org',
    license='GPLv2+',
    author='Pulp Team',
    author_email='pulp-list@redhat.com',
    description='docker-registry-like API with redirection, as a wsgi app',
    install_requires=requirements,
    tests_require=test_requirements,
    test_suite='unittest2.collector',
    package_data={
        'crane': ['data/*.conf', 'templates/*.html', 'static/css/*', 'static/js/*',
                  'static/fonts/*', 'static/img/*']
    },
)
