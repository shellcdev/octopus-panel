# -*- coding: utf-8 -*-
"""
generate_roles.py - 基于问题类型自动生成角色卡
用法：python generate_roles.py --question "是否应该跳槽" --count 4
"""

import argparse
import json
import sys
import codecs
import os

# 问题类型 → 推荐角色组 映射
QUESTION_TYPE_MAP = {
    "职场": ["王经理", "李阿姨", "张总", "赵猎头"],
    "技术": ["架构师老张", "运维小李", "安全老王", "产品小周"],
    "教育": ["学霸家长刘妈", "佛系家长陈爸", "班主任吴老师", "留学顾问Fiona"],
    "医疗": ["医生老李", "患者家属小王", "医保专员小周", "年轻医生小赵"],
    "法律": ["律师张姐", "合规官小刘", "法官老郑", "法学教授老吴"],
    "创业": ["天使投资人老钱", "连续创业者老孙", "行业专家老周", "失败创业者老吴"],
    "家庭": ["外婆", "都市青年", "年轻人伴侣小雨", "邻居王阿姨"],
}
# 角色简称 → role-templates.md 里的完整标题（用于查找角色定义）
ROLE_ALIAS = {
    "王经理": "🎯 王经理（中层管理者）",
    "李阿姨": "🏠 李阿姨（家人视角）",
    "张总": "💰 张总（创业者/老板）",
    "赵猎头": "🕵️ 赵猎头（职场情报员）",
    "架构师老张": "👨‍💻 架构师老张（资深架构师）",
    "运维小李": "🛠️ 运维小李（SRE/运维）",
    "安全老王": "🔒 安全老王（安全工程师）",
    "产品小周": "📱 产品小周（产品经理）",
    "学霸家长刘妈": "👩 学霸家长刘妈（鸡娃家长）",
    "佛系家长陈爸": "👨 佛系家长陈爸（佛系家长）",
    "班主任吴老师": "👩‍🏫 班主任吴老师（班主任）",
    "留学顾问Fiona": "✈️ 留学顾问Fiona（留学顾问）",
    "医生老李": "🩺 医生老李（主治医生）",
    "患者家属小王": "😰 患者家属小王（患者家属）",
    "医保专员小周": "💳 医保专员小周（医保专员）",
    "年轻医生小赵": "🧑‍⚕️ 年轻医生小赵（住院医）",
    "律师张姐": "⚖️ 律师张姐（诉讼律师）",
    "合规官小刘": "📋 合规官小刘（企业合规）",
    "法官老郑": "⚖️ 法官老郑（退休法官）",
    "法学教授老吴": "🎓 法学教授老吴（法学教授）",
    "天使投资人老钱": "💰 天使投资人老钱（早期投资人）",
    "连续创业者老孙": "🚀 连续创业者老孙（三次创业成功）",
    "行业专家老周": "🔬 行业专家老周（行业研究员）",
    "失败创业者老吴": "💔 失败创业者老吴（连续创业失败者）",
    "外婆": "👵 外婆（传统智慧）",
    "都市青年": "👨‍💼 都市青年（当代焦虑体）",
    "年轻人伴侣小雨": "💑 年轻人伴侣小雨（设计师）",
    "邻居王阿姨": "🏘️ 邻居王阿姨（退休教师）",
    "HR李姐": "👩‍💼 HR总监李姐（HR总监）",
    "老板陈总": "👔 老板陈总（制造厂老板）",
    "员工小张": "🧑‍💼 员工小张（基层员工·被画饼专业户）",
    "赌徒": "🃏 赌徒（老六）",
    "寂": "💀 寂（观察者）",
    "爆破手": "💣 爆破手（拆迁办主任）",
    "冰": "🧊 冰（理性派/数据分析师）",
}


def detect_question_type(question):
    """简单关键词匹配，判断问题类型"""
    keywords = {
        "职场": ["跳槽", "加薪", "面试", "老板", "同事", "裁员"],
        "技术": ["架构", "API", "自研", "技术选型", "代码"],
        "教育": ["升学", "留学", "补课", "学校", "专业"],
        "医疗": ["手术", "治疗", "诊断", "医保", "用药"],
        "法律": ["合同", "诉讼", "违法", "合规", "法律风险"],
        "创业": ["融资", "合伙人", "股权", "赛道", "MVP"],
        "家庭": ["父母", "外婆", "老人", "结婚", "伴侣", "代际", "婆媳"],
    }
    for qtype, kws in keywords.items():
        if any(kw in question for kw in kws):
            return qtype
    return "通用"

def generate_roles(question, count=4):
    """生成角色卡（草稿，需人工确认）"""
    qtype = detect_question_type(question)
    templates = QUESTION_TYPE_MAP.get(qtype, QUESTION_TYPE_MAP["职场"])
    # 去重 + 截取
    selected = list(dict.fromkeys(templates))[:count]
    # 若不够，补充通用角色
    generic = ["理性分析师", "感性体验者", "风险厌恶者", "机会捕捉者"]
    while len(selected) < count:
        for g in generic:
            if g not in selected:
                selected.append(g)
                break
        else:
            break
    roles = []
    for name in selected[:count]:
        roles.append({
            "name": name,
            "archetype": qtype + "视角",
            "stance": "待定（需根据用户问题细化）",
            "style_lock": "待定",
            "soft_spot": "待定",
        })
    return roles

def main():
    parser = argparse.ArgumentParser(description="基于问题类型自动生成角色卡")
    parser.add_argument("--question", required=True, help="用户原始问题")
    parser.add_argument("--count", type=int, default=4, help="生成角色数量")
    args = parser.parse_args()
    roles = generate_roles(args.question, args.count)
    print("生成的角色草稿（请人工确认后使用）：")
    print(json.dumps(roles, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
