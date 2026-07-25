# -*- coding: utf-8 -*-
"""八爪议事厅脚本测试包。

运行方式（任选其一）：

  # 在 skill 根目录下跑全部
  python -m unittest discover -s scripts/tests -p "test_*.py" -v

  # 跑单个模块
  python -m unittest tests.test_growth_api -v

  # 用本目录的 runner 一键跑 + 汇总
  python scripts/tests/run_tests.py

注：本 ``__init__.py`` 在包被导入时最先执行，负责把 ``scripts/tests`` 自身与
同级 ``scripts`` 目录注入 ``sys.path``，使 ``from _helpers import`` 与
``import growth_api`` 均直接可用，免去每个用例重复 path 处理。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_SCRIPTS = os.path.normpath(os.path.join(_HERE, '..'))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
