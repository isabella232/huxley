# Copyright (c) 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import threading

from huxley.consts import TestRunModes
from huxley.errors import TestError
from huxley.images import images_identical, image_diff

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

# Since we want consistent focus screenshots we steal focus
# when taking screenshots. To avoid races we lock during this
# process.
SCREENSHOT_LOCK = threading.RLock()

class TestStep(object):
    def __init__(self, offset_time):
        self.offset_time = offset_time

    def execute(self, run):
        raise NotImplementedError


class ClickTestStep(TestStep):
    CLICK_ID = '_huxleyClick'

    def __init__(self, offset_time, pos):
        super(ClickTestStep, self).__init__(offset_time)
        self.pos = pos

    def execute(self, run):
        print '  Clicking', self.pos

        if run.d.name == 'phantomjs':
            # PhantomJS 1.x does not support 'click()' so use Selenium
            body = run.d.find_element_by_tag_name('body')
            ActionChains(run.d).move_to_element_with_offset(body, self.pos[0], self.pos[1]).click().perform()
        elif run.d.name == 'Safari':
            el = run.d.execute_script('return document.elementFromPoint(%d, %d);' % (self.pos[0], self.pos[1]))
            if el:
                el.click()
            else:
                print '   warning, no element found at (%d, %d);' % (self.pos[0], self.pos[1])
        else:
            # Work around multiple bugs in WebDriver's implementation of click()
            run.d.execute_script(
                'document.elementFromPoint(%d, %d).click();' % (self.pos[0], self.pos[1])
            )
            run.d.execute_script(
                'document.elementFromPoint(%d, %d).focus();' % (self.pos[0], self.pos[1])
            )


class ScrollTestStep(TestStep):
    SCROLL_OFFSET_ID = '_huxleyScroll'

    def __init__(self, offset_time, pos):
        super(ScrollTestStep, self).__init__(offset_time)
        self.pos = pos

    def execute(self, run):
        print '  Scrolling', self.pos
        run.d.execute_script(
            'window.scrollTo(%d, %d);' % (self.pos[0], self.pos[1])
        )

class KeyTestStep(TestStep):
    KEYS_BY_JS_KEYCODE = {
        33: Keys.PAGE_UP,
        34: Keys.PAGE_DOWN,
        35: Keys.END,
        36: Keys.HOME,
        37: Keys.LEFT,
        38: Keys.UP,
        39: Keys.RIGHT,
        40: Keys.DOWN,
        46: Keys.DELETE,
        186: ";",
        187: "=",
        188: ",",
        190: ".",
        191: "/",
        192: "`",
        219: "[",
        220: "\\",
        221: "]",
        222: "'",
    }
    KEYS_BY_JS_KEYCODE_SHIFT = dict(KEYS_BY_JS_KEYCODE.items() + {
        48: ")",
        49: "!",
        50: "@",
        51: "#",
        52: "$",
        53: "%",
        54: "^",
        55: "&",
        56: "*",
        57: "(",
        186: ":",
        187: "+",
        188: "<",
        190: ">",
        191: "?",
        192: "~",
        219: "{",
        220: "|",
        221: "}",
        222: "\"",
    }.items())
    KEY_ID = '_huxleyKey'

    # param is [keyCode, shiftKey]
    def __init__(self, offset_time, param):
        super(KeyTestStep, self).__init__(offset_time)
        # backwards compat. for old records where a string was saved
        if isinstance(param, basestring):
            self.key = param
        else:
            codes = self.KEYS_BY_JS_KEYCODE_SHIFT if param[1] else self.KEYS_BY_JS_KEYCODE

            char = chr(param[0])
            if not param[1]:
                char = char.lower()

            self.key = codes.get(param[0], char)

    def execute(self, run):
        if self.key == Keys.HOME:
            print '  Scrolling to top'
            run.d.execute_script('window.scrollTo(0, 0)')
        elif self.key == Keys.END:
            print '  Scrolling to bottom'
            run.d.execute_script('window.scrollTo(0, document.body.clientHeight)')
        else:
            print '  Typing', self.key
            id = run.d.execute_script('return document.activeElement.id;')
            if id is None or id == '':
                run.d.execute_script(
                    'document.activeElement.id = %r;' % self.KEY_ID
                )
                id = self.KEY_ID
            run.d.find_element_by_id(id).send_keys(self.key)


class ScreenshotTestStep(TestStep):
    def __init__(self, offset_time, run, index):
        super(ScreenshotTestStep, self).__init__(offset_time)
        self.index = index

    def get_path(self, run):
        return os.path.join(run.path, 'screenshot' + str(self.index) + '.png')

    def execute(self, run):
        print '  Taking screenshot', self.index
        original = self.get_path(run)
        new = os.path.join(run.path, 'last.png')

        with SCREENSHOT_LOCK:
            # Steal focus for a consistent screenshot
            run.d.switch_to_window(run.d.window_handles[0])

            # iOS insertion points are visible in screenshots
            if run.d.name == 'Safari':
                active = run.d.execute_script('a = document.activeElement; a.blur(); return a;')

            if run.mode == TestRunModes.RERECORD:
                run.d.save_screenshot(original)
            else:
                run.d.save_screenshot(new)
                try:
                    if not images_identical(original, new, run.test.mask):
                        if run.save_diff:
                            diffpath = os.path.join(run.path, 'diff.png')
                            diff = image_diff(original, new, diffpath, run.diffcolor, run.test.mask)
                            raise TestError(
                                ('Screenshot %s was different; compare %s with %s. See %s ' +
                                 'for the comparison. diff=%r') % (
                                    self.index, original, new, diffpath, diff
                                )
                            )
                        else:
                            raise TestError('Screenshot %s was different.' % self.index)
                finally:
                    if not run.save_diff:
                        os.unlink(new)

