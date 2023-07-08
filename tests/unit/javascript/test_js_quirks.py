# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2021 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for QtWebEngine JavaScript quirks.

This tests JS functionality which is missing in older QtWebEngine releases, but we have
polyfills for. They should either pass because the polyfill is active, or pass because
the native functionality exists.
"""

import pathlib

import pytest
from qutebrowser.qt.core import QUrl

import qutebrowser
from qutebrowser.utils import usertypes
from qutebrowser.config import configdata


@pytest.mark.parametrize('base_url, source, expected', [
    pytest.param(
        QUrl(),
        '"This is a test".replaceAll("test", "fest")',
        "This is a fest",
        id='replace-all',
    ),
    pytest.param(
        QUrl(),
        '"This is a test".replaceAll(/[tr]est/g, "fest")',
        "This is a fest",
        id='replace-all-regex',
    ),
    pytest.param(
        QUrl(),
        '"This is a [test[".replaceAll("[", "<")',
        "This is a <test<",
        id='replace-all-reserved-string',
    ),
    pytest.param(
        QUrl("https://test.qutebrowser.org/linkedin"),
        '[1, 2, 3].at(1)',
        2,
        id='array-at',
    ),
])
def test_js_quirks(config_stub, js_tester_webengine, base_url, source, expected):
    config_stub.val.content.site_specific_quirks.skip = []
    js_tester_webengine.tab._scripts._inject_site_specific_quirks()
    js_tester_webengine.load('base.html', base_url=base_url)
    js_tester_webengine.run(source, expected, world=usertypes.JsWorld.main)


def test_js_quirks_match_files(webengine_tab):
    quirks_path = pathlib.Path(qutebrowser.__file__).parent / "javascript" / "quirks"
    suffix = ".user.js"
    quirks_files = {p.name[:-len(suffix)] for p in quirks_path.glob(f"*{suffix}")}
    quirks_code = {q.filename for q in webengine_tab._scripts._get_quirks()}
    assert quirks_code == quirks_files


def test_js_quirks_match_settings(webengine_tab, configdata_init):
    opt = configdata.DATA["content.site_specific_quirks.skip"]
    prefix = "js-"
    valid_values = opt.typ.get_valid_values()
    assert valid_values is not None
    quirks_config = {
        val[len(prefix):].replace("-", "_")
        for val in valid_values
        if val.startswith(prefix)
    }

    quirks_code = {q.filename for q in webengine_tab._scripts._get_quirks()}
    quirks_code -= {"googledocs"}  # special case, UA quirk

    assert quirks_code == quirks_config
