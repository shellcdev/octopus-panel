# 🤝 贡献指南（CONTRIBUTING）

感谢你考虑为「八爪议事厅」做贡献！本文件说明开发环境、测试方式、代码约定与提交流程。

## 环境要求

- **Python 3.8+**（脚本与测试均只依赖标准库，**无需安装任何第三方包**）
- Git
- 一个支持本技能的客户端：OpenClaw（qclaw）或 WorkBuddy

无需 `pip install`、无需虚拟环境、无构建步骤。安装方式见 [README.md](README.md) 的「快速上手 / 开源用户：先安装」。

## 本地开发

```bash
git clone https://github.com/shellcdev/octopus-panel.git
cd octopus-panel
# 可选：软链到 skills 目录以便实时测试
#   ln -s "$(pwd)" ~/.qclaw/skills/octopus-panel
```

## 运行测试

```bash
# 在仓库根目录
python scripts/tests/run_tests.py                  # 全部，详细输出
python scripts/tests/run_tests.py -q               # 安静模式（点点点 + 汇总）
python scripts/tests/run_tests.py test_growth_api  # 只跑某模块

# 也兼容标准 unittest 入口
python -m unittest discover -s scripts/tests -p "test_*.py" -v
```

所有脚本均为纯标准库实现；CI 在 Python 3.8–3.12 上自动跑 `run_tests.py -q`。

## 代码约定

- 文件头统一 `# -*- coding: utf-8 -*-`；
- 注释用**中文**，变量/函数名用**英文小写下划线**（与项目既有风格一致）；
- **不引入第三方依赖**；如需新能力，优先用标准库实现；
- 每个脚本改动后跑对应测试 + `python scripts/audit.py all` 做文档一致性校验。

## 运维脚本（改完 references/ 或 scripts/ 后必跑）

```bash
python scripts/audit.py all        # 文档一致性 + 别名校验
python scripts/audit_links.py      # 链接健康扫描（0 真死链才算通过）
```

> ⚠️ 改了文件名时，务必同步更新 `README.md` 的脚本表与 `SKILL.md` 索引，否则审计会报孤儿/断链。

## 如何贡献

### 新增角色模板
1. 在 `references/role-templates.md` 对应分组下追加；
2. 必须通过**前置风控三问**（见该文件）；
3. 在 `CHANGELOG.md` 记录。

### 新增讨论案例
1. 在 `references/discussion-examples.md` 追加；
2. 标注"案例 N"、讨论问题、完整发言、石叔总结；
3. 在 `CHANGELOG.md` 记录。

### 优化规则 / 修复文档
- 规则类：说明优化理由 + 影响范围；
- typo、断链、格式问题：直接提 PR 即可。

## 提交 PR

1. Fork → 新建分支（`feat/xxx`、`fix/xxx`）；
2. 确保 `python scripts/tests/run_tests.py -q` 全绿；
3. 在 PR 模板中填写改动说明、关联 issue、自查清单；
4. 等待维护者 review。

> 行为准则见 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)；安全漏洞请走 [SECURITY.md](SECURITY.md) 的私报通道，**勿开公开 issue**。
