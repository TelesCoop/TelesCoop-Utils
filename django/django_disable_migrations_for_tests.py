# put this in settings.py

# disable migrations for tests so that it's faster
class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


if "test" in sys.argv[1:] or "jenkins" in sys.argv[1:]:
    MIGRATION_MODULES = DisableMigrations()
    # add test runner to add a Locale, otherwise tests crash
    TEST_RUNNER = "main.tests.runner_with_base_objects.MyTestRunner"

# BASE_DIR/main/tests.runner_with_base_objects
from django.test.runner import DiscoverRunner as BaseRunner
from wagtail.models import Locale


class MyMixinRunner(object):
    def setup_databases(self, *args, **kwargs):
        temp_return = super(MyMixinRunner, self).setup_databases(*args, **kwargs)
        # TODO do stuff here, such as adding a locale for watgtail projects
        Locale.objects.create(language_code="fr")
        return temp_return

    def teardown_databases(self, *args, **kwargs):
        # do somthing
        return super(MyMixinRunner, self).teardown_databases(*args, **kwargs)


class MyTestRunner(MyMixinRunner, BaseRunner):
    pass
