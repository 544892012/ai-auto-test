from __future__ import annotations

import pytest

from aitest.gen import _validate_generated_code


def test_validate_allows_re_compile() -> None:
    src = "import re\nx = re.compile(r'a')\n"
    _validate_generated_code(src)


def test_validate_forbids_builtin_compile() -> None:
    src = "x = compile('1', 'x', 'eval')\n"
    with pytest.raises(ValueError, match="compile"):
        _validate_generated_code(src)
