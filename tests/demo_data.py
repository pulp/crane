import os

metadata_good_path = os.path.join(os.path.dirname(__file__), 'data/metadata_good/')
metadata_bad_path = os.path.join(os.path.dirname(__file__), 'data/metadata_good/')
metadata_good_path_v2 = os.path.join(os.path.dirname(__file__), 'data/v2/metadata_good/')
metadata_bad_path_v2 = os.path.join(os.path.dirname(__file__), 'data/v2/metadata_bad/')

demo_config_path = os.path.join(os.path.dirname(__file__), 'data/demo_config.conf')
foo_metadata_path = os.path.join(os.path.dirname(__file__), 'data/metadata_good/foo.json')
wrong_version_path = os.path.join(os.path.dirname(__file__),
                                  'data/metadata_bad/wrong_version.json')

demo_entitlement_cert_path = os.path.join(os.path.dirname(__file__), 'data/test_entitlement.pem')
demo_no_entitlement_cert_path = os.path.join(os.path.dirname(__file__),
                                             'data/test_no_entitlement.pem')
