from dataclasses import dataclass
from naq_utils.settings import GSInt, GSStr
import pytest


@dataclass
class SettingsUnderTest:
    setting_a = GSInt("setting_a", 1)
    setting_b = GSStr("setting_b", "Hello")


@pytest.fixture
def test_settings():
    settings = SettingsUnderTest()
    yield settings
    settings.setting_a.delete()
    settings.setting_b.delete()



class TestSettings:
    
    def test_global_setting_defaults(self, test_settings: SettingsUnderTest):
        assert test_settings
        assert type(test_settings.setting_a.value) == int
        assert test_settings.setting_a.value == 1
        assert type(test_settings.setting_b.value) == str
        assert test_settings.setting_b.value == "Hello"

    def test_global_setting_update(self, test_settings: SettingsUnderTest):
        test_settings.setting_a.value = 10
        test_settings.setting_b.value = "Something else"

        new_settings_obj = SettingsUnderTest()
        assert new_settings_obj

        assert new_settings_obj.setting_a.value == 10
        assert new_settings_obj.setting_b.value == "Something else"
