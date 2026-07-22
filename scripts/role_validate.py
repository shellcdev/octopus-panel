# -*- coding: utf-8 -*-
"""
role_validate.py - 角色卡质量校验（自动过前置风控三问）
用法：python role_validate.py --file role_card.json
      python role_validate.py --dir roles/  （批量校验目录下所有.json）
"""

import argparse
import json
import sys
import codecs
import os
import io

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 前置风控三问
RISK_QUESTIONS = [
    "这个角色的立场有没有可能冒犯真实人群？（如有，加软肋中和）",
    "这个角色的知识边界是否清晰？（不说超出人设的话）",
    "这个角色是否可能被误认为真实人物？（如可能，改名+模糊化）",
]

def validate_role_card(role_card):
    """校验单个角色卡，返回 (passed, issues)"""
    issues = []
    # 检查必填字段
    required = ["name", "archetype", "stance", "style_lock", "soft_spot"]
    for field in required:
        if field not in role_card or not role_card[field]:
            issues.append("缺少必填字段: {}".format(field))
    # 风控三问（启发式检查）
    risk_archetypes = ["小资", "凤凰男", "体制内"]
    if role_card.get("archetype", "") in risk_archetypes:
        issues.append("风险提示： archetype '{}' 可能冒犯真实人群，请加软肋".format(role_card["archetype"]))
    # 风格锁为空或太短
    style = role_card.get("style_lock", "")
    if style and len(style) < 4:
        issues.append("风格锁过短（<4字），可能无法有效约束角色表达")
    # 软肋为空或太短
    spot = role_card.get("soft_spot", "")
    if spot and len(spot) < 4:
        issues.append("软肋描述过短（<4字），可能无法触发有效动摇")
    passed = len(issues) == 0
    return passed, issues

def validate_file(filepath):
    """从 JSON 文件加载角色卡并校验"""
    with codecs.open(filepath, "r", encoding="utf-8") as f:
        role_card = json.load(f)
    passed, issues = validate_role_card(role_card)
    name = role_card.get("name", os.path.basename(filepath))
    if passed:
        print("✅ {} 通过校验".format(name))
    else:
        print("❌ {} 存在问题：".format(name))
        for issue in issues:
            print("  - " + issue)
    return passed

def validate_dir(dirpath):
    """批量校验目录下所有 .json 文件"""
    files = sorted([f for f in os.listdir(dirpath) if f.endswith('.json')])
    if not files:
        print("目录下无 .json 文件：{}".format(dirpath))
        return
    total = len(files)
    passed = 0
    for fname in files:
        fp = os.path.join(dirpath, fname)
        if validate_file(fp):
            passed += 1
    print("\n=== 汇总 === {}/{} 通过".format(passed, total))

def main():
    parser = argparse.ArgumentParser(description="角色卡质量校验")
    parser.add_argument("--file", help="角色卡 JSON 文件路径")
    parser.add_argument("--dir", help="批量校验目录下所有 .json")
    args = parser.parse_args()
    if args.file:
        validate_file(args.file)
    elif args.dir:
        validate_dir(args.dir)
    else:
        print("请指定 --file <路径> 或 --dir <目录>")
        sys.exit(1)

if __name__ == "__main__":
    main()
