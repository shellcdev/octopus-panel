# -*- coding: utf-8 -*-
"""
archive_discussion.py - 讨论结果归档至知识库（增强版 v2.1）
新增：讨论多样性评测（#39）- 按「议题类型×角色组合」去重检测
"""

import argparse
import json
import codecs
import os
import datetime
import re


# --- 新增：多样性评测相关函数（#39）---

DIVERSITY_HISTORY_FILE = "memory/discussion_diversity.json"


def classify_question_type(question):
    """简单关键词匹配，将问题分类为议题类型"""
    q = question.lower()
    type_rules = [
        ("买房/租房/住房", ["买房", "购房", "租房", "住房", "首付", "房贷", "月供"]),
        ("职业/辞职/创业", ["辞职", "创业", "跳槽", "转行", "找工作", "offer", "失业"]),
        ("婚恋/家庭", ["结婚", "离婚", "恋爱", "出轨", "二胎", "生孩子", "育儿"]),
        ("投资/理财", ["投资", "理财", "股票", "基金", "杠杆", "风险", "收益"]),
        ("教育/升学", ["教育", "升学", "出国", "留学", "高考", "考研", "择校"]),
        ("健康/医疗", ["健康", "医疗", "手术", "体检", "生病"]),
        ("人际/社交", ["朋友", "同事", "领导", "人际", "社交", "吵架"]),
    ]
    for type_name, keywords in type_rules:
        if any(kw in q for kw in keywords):
            return type_name
    return "其他"


def load_diversity_history():
    """加载历史讨论记录"""
    if not os.path.exists(DIVERSITY_HISTORY_FILE):
        return []
    try:
        with codecs.open(DIVERSITY_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_diversity_history(history):
    """保存历史讨论记录"""
    os.makedirs(os.path.dirname(DIVERSITY_HISTORY_FILE) or ".", exist_ok=True)
    with codecs.open(DIVERSITY_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def check_combo_duplicate(question_type, role_names, history, max_recent=5):
    """检测「议题类型×角色组合」是否在最近max_recent场中重复出现≥2次
    Returns: (is_duplicate, count, recent_matches)
    """
    recent = history[-max_recent:] if len(history) >= max_recent else history
    combo_key = (question_type, tuple(sorted(role_names)))
    matches = [h for h in recent if h.get("combo_key") == combo_key]
    return (len(matches) >= 2, len(matches), matches)


def record_discussion(question, question_type, role_names, archive_file):
    """记录本次讨论到历史"""
    history = load_diversity_history()
    combo_key = (question_type, tuple(sorted(role_names)))
    record = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "question": question[:50],
        "question_type": question_type,
        "roles": role_names,
        "combo_key": combo_key,
        "archive_file": archive_file,
    }
    history.append(record)
    # 只保留最近50条
    if len(history) > 50:
        history = history[-50:]
    save_diversity_history(history)
    return history


# --- 原有函数（保持不变）---

def extract_keywords(text):
    """简单关键词提取（中文）"""
    stop_words = ["的", "了", "是", "在", "有", "和", "与", "或", "该", "不", "吗", "呢", "吧", "啊",
                  "该不该", "要不要", "能不能", "应该", "可以", "怎么"]
    words = re.findall(r"[\u4e00-\u9fff]+", text)  # 只提取中文词
    keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
    return list(dict.fromkeys(keywords))[:10]  # 去重，最多10个


def extract_turning_points(log_content):
    """从讨论日志提取关键转折点（检测立场变化关键词）"""
    turning_points = []
    lines = log_content.split("\n")
    current_round = None
    for line in lines:
        round_match = re.match(r"\*\*第(\d+)轮\*\*", line)
        if round_match:
            current_round = int(round_match.group(1))
        # 检测立场变化信号
        if current_round and any(kw in line for kw in ["但是", "不过", "换个角度", "我改主意了", "立场松动", "也行吧"]):
            # 提取角色名和发言片段
            role_match = re.match(r"\[[^\]]+\]\s*([^（(]+)", line)
            role_name = role_match.group(1).strip() if role_match else "未知角色"
            snippet = line[:50].strip()
            turning_points.append("第 {} 轮：{} 立场出现松动 —— {}".format(current_round, role_name, snippet))
    return turning_points


def find_related_archives(question, archive_dir):
    """查找历史归档中相关话题（关键词重叠≥2）"""
    keywords = extract_keywords(question)
    related = []
    if not os.path.exists(archive_dir):
        return related
    for fname in sorted(os.listdir(archive_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(archive_dir, fname)
        try:
            with codecs.open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            overlap = sum(1 for kw in keywords if kw in content)
            if overlap >= 2:
                related.append((fname, overlap))
        except Exception:
            continue
    related.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in related[:3]]


def build_archive_content(question, conclusion, roles, timestamp_iso, log_content=None, related_archives=None):
    """构建归档 Markdown 内容（增强版）"""
    lines = []
    lines.append("# 讨论归档：" + question[:30] + ("..." if len(question) > 30 else ""))
    lines.append("")
    lines.append("**时间**：" + timestamp_iso)
    lines.append("**问题**：" + question)
    lines.append("")

    # 标签
    tags = extract_keywords(question)
    if tags:
        lines.append("**标签**：" + " ".join(["#" + t for t in tags]))
        lines.append("")

    lines.append("## 结论")
    lines.append("")
    lines.append(conclusion)
    lines.append("")

    if roles:
        lines.append("## 角色阵容")
        lines.append("")
        lines.append("| 角色 | 立场 | 关键发言 |")
        lines.append("|---|---|---|")
        for r in roles:
            name = r.get("name", "未知")
            stance = r.get("stance", "未知")
            key = r.get("key_quote", "待补充")
            lines.append("| {} | {} | {} |".format(name, stance, key))
        lines.append("")

    # 完整讨论记录
    if log_content:
        lines.append("## 完整讨论记录")
        lines.append("")
        lines.append("```")
        lines.append(log_content)
        lines.append("```")
        lines.append("")

    # 关键转折点
    lines.append("## 关键转折点")
    lines.append("")
    if log_content:
        turning_points = extract_turning_points(log_content)
        if turning_points:
            for tp in turning_points:
                lines.append("- " + tp)
        else:
            lines.append("（本场讨论无明显立场转折）")
    else:
        lines.append("（由石叔在讨论过程中手动填写）")
    lines.append("")

    # 后续可引用
    lines.append("## 后续可引用")
    lines.append("")
    if related_archives:
        lines.append("**相关历史归档**（关键词匹配）：")
        for fname in related_archives:
            lines.append("- " + fname)
        lines.append("")
        lines.append("若再遇类似问题，可引用以上归档的结论。")
    else:
        lines.append("（暂无相关历史归档，后续讨论触发时自动填充）")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="讨论结果归档（增强版 v2.1）")
    parser.add_argument("--question", required=True, help="原始用户问题")
    parser.add_argument("--conclusion", required=True, help="石叔总结结论")
    parser.add_argument("--roles", help="角色阵容 JSON 文件路径")
    parser.add_argument("--log", help="完整讨论日志文件路径（可选）")
    parser.add_argument("--output", default="memory/octopus-archive", help="归档输出目录")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    timestamp = datetime.datetime.now()
    timestamp_iso = timestamp.strftime("%Y-%m-%d %H:%M")
    filename = timestamp.strftime("%Y%m%d-%H%M") + ".md"
    filepath = os.path.join(args.output, filename)

    roles = []
    if args.roles:
        with codecs.open(args.roles, "r", encoding="utf-8") as f:
            roles = json.load(f)

    log_content = None
    if args.log:
        with codecs.open(args.log, "r", encoding="utf-8") as f:
            log_content = f.read()

    related = find_related_archives(args.question, args.output)

    content = build_archive_content(args.question, args.conclusion, roles, timestamp_iso, log_content, related)

    with codecs.open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 归档完成：" + filepath)
    if related:
        print("📂 发现相关历史归档：" + "，".join(related))

    # --- 新增：多样性检测（#39）---
    role_names = [r.get("name", "未知") for r in roles] if roles else []
    if role_names:
        question_type = classify_question_type(args.question)
        history = record_discussion(args.question, question_type, role_names, filename)
        is_dup, count, matches = check_combo_duplicate(question_type, role_names, history)
        if is_dup:
            print("⚠️ 多样性提醒：议题类型[{}] × 角色组合{} 在最近讨论中已出现 {} 次".format(
                question_type, role_names, count))
            print("   石叔应在下一轮建议换人，标注「这个组合最近出现过」")
        else:
            print("✅ 多样性检查通过：议题类型[{}] × 角色组合{} 未重复".format(question_type, role_names))


if __name__ == "__main__":
    main()
