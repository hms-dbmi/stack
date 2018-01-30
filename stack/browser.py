import os
import time

from splinter.driver.webdriver import BaseWebDriver
from splinter.driver.webdriver.firefox import WebDriver as FirefoxDriver
from splinter.driver.webdriver.chrome import WebDriver as ChromeDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from selenium.webdriver.safari.webdriver import WebDriver as SafariDriver
from splinter.driver.webdriver import WebDriverElement
from splinter.driver.webdriver.cookie_manager import CookieManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.by import By


def Browser(browser_name='firefox'):

    if browser_name.lower() == 'firefox':
        return Firefox()

    elif browser_name.lower() == 'chrome':
        return Chrome()

    elif browser_name.lower() == 'safari':
        return Safari()


class BrowserExtensions(BaseWebDriver):

    SCROLL_SCRIPT = """
        const element = arguments[0];
        const elementRect = element.getBoundingClientRect();
        const absoluteElementTop = elementRect.top + window.pageYOffset;
        const middle = absoluteElementTop - (window.innerHeight / 2);
        window.scrollTo(0, middle);
    """

    def find_by_partial_text(self, text):
        return self.find_by_xpath('//*[contains(text(),"{}")]'.format(text))

    def is_element_present_by_partial_text(self, text, wait_time=None):
        return self.is_element_present_by_xpath('//*[contains(text(),"{}")]'.format(text), wait_time=wait_time)

    def is_element_present_by_classname(self, class_name, wait_time=None):
        return self.is_element_present_by_xpath('//*[@class=" {} "]'.format(class_name), wait_time=wait_time)

    def is_element_present_by_partial_classname(self, class_name, wait_time=None):
        return self.is_element_present_by_xpath('//*[contains(@class, "{}")]'.format(class_name), wait_time=wait_time)

    def is_element_visible_by_partial_text(self, text, wait_time=None):
        return self.is_element_visible_by_xpath('//*[contains(text(),"{}")]'.format(text), wait_time=wait_time)

    def is_element_visible_by_text(self, text, wait_time=None):
        return self.is_element_visible_by_xpath('//*[text()="{}"]'.format(text), wait_time=wait_time)

    def is_element_visible_by_name(self, name, wait_time=None):
        return self.is_element_visible_by_xpath('//*[@name="{}"]'.format(name), wait_time=wait_time)

    def is_element_visible_by_id(self, name, wait_time=None):
        return self.is_element_visible_by_xpath('//*[@id="{}"]'.format(name), wait_time=wait_time)

    def is_element_visible_by_classname(self, class_name, wait_time=None):
        return self.is_element_visible_by_xpath('//*[@class="{}"]'.format(class_name), wait_time=wait_time)

    def is_element_visible_by_partial_classname(self, class_name, wait_time=None):
        return self.is_element_visible_by_xpath('//*[contains(@class, "{}")]'.format(class_name), wait_time=wait_time)

    def make_element_visible_by_xpath(self, xpath, index=0, wait_time=None):

        # Check it.
        if self.is_element_present_by_xpath(xpath=xpath, wait_time=wait_time):

            try:
                # Get it.
                element = self.find_by_xpath(xpath)[index]
                if element:
                    self.driver.execute_script(self.SCROLL_SCRIPT, element._element)

                # Pause for a split second.
                time.sleep(0.25)

                return self.is_element_visible_by_xpath(xpath, wait_time)
            except IndexError:
                return False
        else:
            return False

    def make_element_visible_by_id(self, identifier, wait_time=None):
        return self.make_element_visible_by_xpath('//*[@id="{}"]'.format(identifier), wait_time=wait_time)

    def make_element_visible_by_name(self, name, wait_time=None):
        return self.make_element_visible_by_xpath('//*[@name="{}"]'.format(name), wait_time=wait_time)

    def make_element_visible_by_text(self, text, wait_time=None):
        return self.make_element_visible_by_xpath('//*[text()="{}"]'.format(text), wait_time=wait_time)

    def make_element_visible_by_partial_text(self, text, wait_time=None):
        return self.make_element_visible_by_xpath('//*[contains(text(), "{}")]'.format(text), wait_time=wait_time)

    def make_element_visible_by_classname(self, classname, wait_time=None):
        return self.make_element_visible_by_xpath('//*[@class="{}"]'.format(classname), wait_time=wait_time)

    def make_element_visible_by_partial_classname(self, classname, wait_time=None):
        return self.make_element_visible_by_xpath('//*[contains(@class, "{}")]'.format(classname), wait_time=wait_time)

    def make_element_visible_by_tag(self, tag_name, wait_time=None):
        return self.make_element_visible_by_xpath('//{}'.format(tag_name), wait_time=wait_time)


class Firefox(FirefoxDriver, BrowserExtensions):

    def __init__(self):

        # Setup the preferences.
        preferences = dict()
        preferences["browser.download.folderList"] = 2
        preferences["browser.download.manager.showWhenStarting"] = False
        preferences["browser.download.dir"] = os.getcwd()
        preferences["browser.helperApps.neverAsk.saveToDisk"] = "application/octet-stream"

        # Disable browser notifications.
        preferences["dom.webnotifications.enabled"] = False

        # Get the path to the project root.
        driver_root = os.path.realpath(os.path.join(os.path.dirname(__file__), 'drivers'))
        driver_path = os.path.join(driver_root, 'geckodriver')
        kwargs = {'executable_path': driver_path, 'profile_preferences': preferences}

        super(Firefox, self).__init__(wait_time=5, **kwargs)


class Chrome(ChromeDriver, BrowserExtensions):

    def __init__(self):

        # Setup the options.
        options = ChromeOptions()

        # Disable browser notifications.
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')

        # Get the path to the project root.
        driver_root = os.path.realpath(os.path.join(os.path.dirname(__file__), 'drivers'))
        driver_path = os.path.join(driver_root, 'chromedriver_osx')
        kwargs = {'executable_path': driver_path, 'options': options}

        super(Chrome, self).__init__(wait_time=5, **kwargs)


class Safari(BrowserExtensions):

    driver_name = "safari"

    def __init__(self, full_screen=False, wait_time=2, **ability_args):

        self.driver = SafariDriver()

        self.element_class = SafariDriverElement

        self._cookie_manager = CookieManager(self.driver)

        super(Safari, self).__init__(wait_time)


class SafariDriverElement(WebDriverElement):

    def _get_value(self):
        return self['value'] or self._element.text

    def _set_value(self, value):
        if self._element.get_attribute('type') != 'file':
            self._element.clear()
        self._element.send_keys(value)

    value = property(_get_value, _set_value)

    @property
    def text(self):
        return self._element.text

    @property
    def tag_name(self):
        return self._element.tag_name

    def clear(self):
        if self._element.get_attribute('type') in ['textarea', 'text', 'password', 'tel']:
            self.value = ''

    def fill(self, value):
        self.value = value

    def select(self, value):
        self.find_by_xpath('//select[@name="%s"]/option[@value="%s"]' % (self["name"], value))\
            ._element.click()

    def select_by_text(self, text):
        self.find_by_xpath('//select[@name="%s"]/option[text()="%s"]' % (self["name"], text))\
            ._element.click()

    def click(self):
        self.parent.driver.execute_script('arguments[0].click();', self._element)

    def check(self):
        if not self.checked:
            self.parent.driver.execute_script('arguments[0].click();', self._element)

    def uncheck(self):
        if self.checked:
            self.parent.driver.execute_script('arguments[0].click();', self._element)

    @property
    def checked(self):
        return self._element.is_selected()

    selected = checked

    @property
    def visible(self):
        return self._element.is_displayed()

    @property
    def html(self):
        return self['innerHTML']

    @property
    def outer_html(self):
        return self['outerHTML']
