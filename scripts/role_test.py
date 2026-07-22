# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
role_test.py - spawn 单角色测试发言是否符合风格锁
用法：python role_test.py --role-card role_card.json --test-question "..." --model qclaw/modelroute
需要 OpenClaw sessions_spawn 支持（本脚本生成测试 prompt，人工或自动化执行）
"""

import argparse
import json
import codecs
import sys
import io

# UTF-8 重包装：中文 Windows (cp936) 下 print CJK 可能 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def build_test_prompt(role_card, test_question, round_num=1):
    """构建测试 prompt（发给子 Agent）"""
    name = role_card.get("name", "未知角色")
    archetype = role_card.get("archetype", "")
    stance = role_card.get("stance", "")
    style_lock = role_card.get("style_lock", "")
    soft_spot = role_card.get("soft_spot", "")
    lines = []
    lines.append("你是 {}（{}）。".format(name, archetype))
    lines.append("")
    lines.append("你的立场：{}".format(stance))
    lines.append("你的风格约束锁：{}".format(style_lock))
    lines.append("你的软肋：{}（如果被戳中，你会失控或改变立场）".format(soft_spot))
    lines.append("")
    lines.append("## 当前讨论")
    lines.append("")
    lines.append("问题：" + test_question)
    lines.append("轮次：第 {} 轮（共 2 轮）".format(round_num))
    lines.append("讨论板：[当前无历史，这是第一轮]")
    lines.append("")
    lines.append("## 严格要求")
    lines.append("")
    lines.append("- 发言 ≤50 字")
    lines.append("- 立场鲜明，不中立")
    lines.append("- 必须遵守风格约束锁：{}".format(style_lock))
    lines.append("- 用 「怼」格式：先引用对方原话（如有），再反驳")
    lines.append("- 字数超限 → 截断，不追加「...」")
    lines.append("")
    lines.append("直接输出你的发言（不需要解释或自我介绍）：")
    return "\n".join(lines)

def run_test(role_card_path, test_question, model):
    """运行测试（生成 prompt，等待人工执行）"""
    with codecs.open(role_card_path, "r", encoding="utf-8") as f:
        role_card = json.load(f)
    print("=== 角色测试：{} ===".format(role_card.get("name", "未知")))
    print("")
    print("【测试 Prompt（发给子 Agent）】")
    print("")
    prompt = build_test_prompt(role_card, test_question)
    print(prompt)
    print("")
    print("【执行方式】")
    print("1. 复制上方 prompt")
    print("2. 用 OpenClaw sessions_spawn 或直接在对话里让角色发言")
    print("3. 检查输出是否符合风格锁（人工或自动化断言）")
    print("")
    # 简单的自动化检查（示例）
    print("【自动化检查清单】")
    print("- [ ] 发言字数 ≤50 字")
    print("- [ ] 立场与角色卡一致（不漂移）")
    print("- [ ] 没有违反风格锁（如冰没有用比喻）")
    print("- [ ] 有 「怼」结构（引用 + 反驳）")

def main():
    parser = argparse.ArgumentParser(description="角色风格锁测试")
    parser.add_argument("--role-card", required=True, help="角色卡 JSON 文件路径")
    parser.add_argument("--test-question", required=True, help="测试问题")
    parser.add_argument("--model", default="qclaw/modelroute", help="使用的模型（仅作记录）")
    args = parser.parse_args()
    run_test(args.role_card, args.test_question, args.model)

if __name__ == "__main__":
    main()
