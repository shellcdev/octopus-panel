# -*- coding: utf-8 -*-
"""
validate_role.py - 角色卡质量校验（自动过前置风控三问）
用法：python validate_role.py --file role_card.json
      或 python validate_role.py --interactive（交互式校验）
"""

import argparse
import json
import sys
import codecs

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
    # 风控三问
    for q in RISK_QUESTIONS:
        # 简单启发式检查（实际应人工确认）
        if role_card.get("archetype", "") in ["小资", "凤凰男", "体制内"]:
            issues.append("风险提示： archetype '{}' 可能冒犯真实人群，请加软肋".format(role_card["archetype"]))
    passed = len(issues) == 0
    return passed, issues

def validate_file(filepath):
    """从 JSON 文件加载角色卡并校验"""
    with codecs.open(filepath, "r", encoding="utf-8") as f:
        role_card = json.load(f)
    passed, issues = validate_role_card(role_card)
    if passed:
        print("✅ 角色卡通过校验")
    else:
        print("❌ 角色卡存在问题：")
        for issue in issues:
            print("  - " + issue)

def interactive_validate():
    """交互式校验（逐问确认）"""
    print("=== 角色卡质量校验（前置风控三问）===")
    role_card = {}
    role_card["name"] = input("角色名: ").strip()
    role_card["archetype"] = input("原型: ").strip()
    role_card["stance"] = input("立场: ").strip()
    role_card["style_lock"] = input("风格锁: ").strip()
    role_card["soft_spot"] = input("软肋: ").strip()
    print("\n--- 风控三问 ---")
    all_pass = True
    for q in RISK_QUESTIONS:
        ans = input(q + " (y/n): ").strip().lower()
        if ans != "y":
            print("  ⚠️  请修改角色卡后重新校验")
            all_pass = False
    if all_pass:
        print("\n✅ 通过风控三问，角色卡可以投入使用")
    else:
        print("\n❌ 未通过，请修改后重新校验")

def main():
    parser = argparse.ArgumentParser(description="角色卡质量校验")
    parser.add_argument("--file", help="角色卡 JSON 文件路径")
    parser.add_argument("--interactive", action="store_true", help="交互式校验")
    args = parser.parse_args()
    if args.interactive:
        interactive_validate()
    elif args.file:
        validate_file(args.file)
    else:
        print("请指定 --file 或 --interactive")
        sys.exit(1)

if __name__ == "__main__":
    main()
