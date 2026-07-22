# -*- coding: utf-8 -*-
"""
生成_roles.py - 基于问题类型生成角色卡，并受 role_source_mode 开关控制

角色来源模式（config.md: role_source_mode）：
  generate      : 每场动态生成；生成前合并查本地库(growth_record + role-templates)
                 做撞名去重 + 给动态角色注入已有成长记忆（若有同名历史）。[默认]
  local_priority: 优先复用本地有成长史角色，不足数量再动态补。
  local_only    : 只从本地库挑，绝不现场造。

合并提取源（config.md: role_extract_merge）：
  true  : growth_record.json 成长角色优先 + role-templates.md 模板库兜底
  false : 仅 role-templates.md 模板库
"""

import argparse
import json
import sys
import codecs
import os
import io
import re

# Windows GBK 终端兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- 路径解析 ---
def get_skill_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)

SKILL_ROOT = get_skill_root()

# 让本脚本能 import 同目录的 growth_api
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import growth_api
# 问题类型 → 推荐角色组 映射
QUESTION_TYPE_MAP = {
    "职场": ["王经理", "李阿姨", "张总", "赵猎头"],
    "技术": ["架构师老张", "运维小李", "安全老王", "产品小周"],
    "教育": ["学霸家长刘妈", "佛系家长陈爸", "班主任吴老师", "留学顾问Fiona"],
    "医疗": ["医生老李", "患者家属小王", "医保专员小周", "年轻医生小赵"],
    "法律": ["律师张姐", "合规官小刘", "法官老郑", "法学教授老吴"],
    "创业": ["天使投资人老钱", "连续创业者老孙", "行业专家老周", "失败创业者老亏"],
    "家庭": ["外婆", "都市青年", "年轻人伴侣小雨"],
}

def detect_question_type(question):
    """简单关键词匹配，判断问题类型"""
    keywords = {
        "职场": ["跳槽", "加薪", "面试", "老板", "同事", "裁员", "铁饭碗", "编制", "灵活就业"],
        "技术": ["架构", "API", "自研", "技术选型", "代码"],
        "教育": ["升学", "留学", "补课", "学校", "专业"],
        "医疗": ["手术", "治疗", "诊断", "医保", "用药"],
        "法律": ["合同", "诉讼", "违法", "合规", "法律风险"],
        "创业": ["融资", "合伙人", "股权", "赛道", "MVP"],
        "家庭": ["父母", "外婆", "老人", "结婚", "伴侣", "代际", "婆媳"],
        "人生": ["人生", "选择", "意义", "后悔", "该不该", "要不要"],
    }
    for qtype, kws in keywords.items():
        if any(kw in question for kw in kws):
            return qtype
    return "通用"

def _load_local_roles():
    """合并提取本地角色库：growth_record.json(成长角色,优先) + role-templates.md(模板库)。
    返回 dict: role_id -> {source, archetype, stance, style_lock, soft_spot}
    """
    local = {}
    merge = growth_api._get_config('role_extract_merge', 'true').lower() != 'false'
    # 1) 成长角色优先（来自 growth_record.json）
    if merge:
        try:
            data = growth_api._read_growth_record()
            for r in data.get('roles', []):
                rid = r.get('role_id')
                if not rid:
                    continue
                last = (r.get('stance_history') or [{}])[-1]
                local[rid] = {
                    'name': rid,
                    'archetype': '本地成长角色',
                    'stance': last.get('stance', '待定'),
                    'style_lock': '待定',
                    'soft_spot': '待定',
                    'source': 'growth',
                    'sessions': r.get('total_sessions', 0),
                }
        except Exception:
            pass
    # 2) 模板库兜底（role-templates.md 中的角色名，仅在未命中成长时补）
    tmpl_path = os.path.join(SKILL_ROOT, 'references', 'role-templates.md')
    try:
        with codecs.open(tmpl_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        # 匹配 '### 🃏 赌徒（老六）' 这种标题行
        for m in re.finditer(r'^###\s+\S+\s+([^\n（(]+)', txt, re.M):
            nm = m.group(1).strip()
            if nm and nm not in local:
                local[nm] = {
                    'name': nm,
                    'archetype': '模板库角色',
                    'stance': '待定（需根据用户问题细化）',
                    'style_lock': '待定',
                    'soft_spot': '待定',
                    'source': 'template',
                }
    except FileNotFoundError:
        pass
    return local

def _pick_local_roles(question, count, qtype=None):
    """从本地库按问题类型挑角色（模板库别名匹配 qtype）。"""
    local = _load_local_roles()
    # 模板库里按 qtype 推荐组挑；成长角色无类型则全部候选
    picked = []
    if qtype and qtype in QUESTION_TYPE_MAP:
        for nm in QUESTION_TYPE_MAP[qtype]:
            if nm in local and local[nm]['source'] == 'template':
                picked.append(local[nm])
    # 不足再补任意本地角色
    for nm, info in local.items():
        if len(picked) >= count:
            break
        if info not in picked:
            picked.append(info)
    return picked[:count]

def _inject_growth_hint(role_name):
    """若本地成长库有同名角色，返回其最新立场作为生成提示注入。"""
    try:
        data = growth_api._read_growth_record()
        for r in data.get('roles', []):
            if r.get('role_id') == role_name:
                last = (r.get('stance_history') or [{}])[-1]
                return last.get('stance')
    except Exception:
        pass
    return None

def generate_roles(question, count=4):
    """生成角色卡（草稿，受 role_source_mode 控制）。
    返回 (roles, mode_used, notes) —— notes 用于告知调用方实际走了哪条路径。
    roles 中每个 dict 可能含字段：
      local_role (bool)        : 名字是否在本地库（template/growth）
      growth_hint (str)        : 若有本地成长史，注入的上次立场
      suggest_localize (bool) : 纯生成且建议转正（仅 pure_generated_handling=ask 时置 True）
    """
    qtype = detect_question_type(question)
    mode = growth_api._get_config('role_source_mode', 'generate').lower()
    handling = growth_api._get_config('pure_generated_handling', 'ask').lower()
    notes = []

    def _mark_pure(roles_list):
        """对纯生成(不在本地库)角色按 handling 开关打标记/提示。"""
        for r in roles_list:
            in_lib = growth_api._is_local_role_name(r['name'])
            r['local_role'] = in_lib
            if not in_lib and handling == 'ask':
                r['suggest_localize'] = True
                notes.append('PROMPT: 角色「{}」为本次纯生成、本地库无记录，是否转正存库？(回复 存/不存)'.format(r['name']))
        return roles_list

    if mode == 'local_only':
        picked = _pick_local_roles(question, count, qtype)
        if len(picked) < count:
            notes.append('local_only 模式但本地库不足 {} 个，仅返回 {} 个'.format(count, len(picked)))
        return picked, 'local_only', notes

    if mode == 'local_priority':
        picked = _pick_local_roles(question, count, qtype)
        for r in picked:
            r['local_role'] = True  # 来自本地库
        if len(picked) >= count:
            return picked, 'local_priority', notes
        # 不足再动态补（避免撞名，含本地库名）；动态补的角色若本地库无记录则按 handling 提示
        dyn = _dynamic_generate(question, count - len(picked), exclude=[p['name'] for p in picked], exclude_local=True)
        dyn = _mark_pure(dyn)
        notes.append('local_priority: 复用 {} 个本地 + 动态补 {} 个'.format(len(picked), len(dyn)))
        return picked + dyn, 'local_priority', notes

    # 默认 generate：每次生成用完就丢弃（ephemeral）。
    # 纯动态生成，不查本地库、不注入成长、不弹转正提示；
    # 关键约束：generate 模式下脚本只产出「空壳」——名字与立场/风格锁/软肋均为待定，
    # 由调用方（石叔）按用户问题生成具体名字与实质属性，避免脚本硬塞不贴题的名字，
    # 也不会与本地库角色名撞名（因脚本此时不产出任何名字）。
    # 所有角色标记 local_role=False，归档时由 archive_discussion 跳过 growth 写入。
    dyn = _dynamic_generate(question, count, exclude=[], mode='generate')
    for r in dyn:
        r['local_role'] = False
        r['ephemeral'] = True
    notes.append('generate: 纯动态生成 {} 个一次性空壳（名字/立场由石叔按题生成，用完丢弃，不累积成长）'.format(len(dyn)))
    return dyn, 'generate', notes

def _dynamic_generate(question, count, exclude=None, exclude_local=False, mode='local'):
    """动态生成逻辑（从 QUESTION_TYPE_MAP），排除 exclude 中已存在的名字。
    exclude_local=True 时，额外排除所有本地库角色名（role-templates.md / growth_record.json），
    用于 local_priority 补足，避免产出与本地库撞名的「幽灵角色」。

    mode='generate' 时，脚本只产出「空壳」：名字与立场/风格锁/软肋均为待定占位，
    具体名字与实质属性由调用方（石叔）按用户问题生成。此时不跑 QUESTION_TYPE_MAP 取名，
    也不做本地名排除（因本就不产出名字）。
    """
    exclude = exclude or []
    if mode == 'generate':
        roles = []
        for _ in range(count):
            roles.append({
                "name": "待定（由石叔按用户问题生成）",
                "archetype": "通用视角",
                "stance": "待定（需根据用户问题细化）",
                "style_lock": "待定",
                "soft_spot": "待定",
            })
        return roles
    qtype = detect_question_type(question)
    templates = QUESTION_TYPE_MAP.get(qtype, QUESTION_TYPE_MAP["职场"])
    selected = [n for n in dict.fromkeys(templates)
                if n not in exclude and not (exclude_local and growth_api._is_local_role_name(n))][:count]
    all_roles = []
    for qt in ["职场", "家庭", "创业", "技术"]:
        if qt != qtype:
            all_roles.extend(QUESTION_TYPE_MAP.get(qt, []))
    generic = [g for g in dict.fromkeys(all_roles)
               if g not in exclude and not (exclude_local and growth_api._is_local_role_name(g))]
    while len(selected) < count:
        added = False
        for g in generic:
            if g not in selected:
                selected.append(g)
                added = True
                break
        if not added:
            break
    # 兜底：过滤本地名后仍不足，用合成名补齐（保证不与本地库撞名、且唯一不重复）。
    # 优先从具象一次性代号池取（更具辨识度），池耗尽再回退到「新视角N」。
    SYNTHETIC_POOL = ["老椿", "青", "默", "川", "樵", "砚", "凛", "遐"]
    if exclude_local:
        used = set(selected)
        for cand in SYNTHETIC_POOL:
            if len(selected) >= count:
                break
            if cand not in used and not growth_api._is_local_role_name(cand):
                selected.append(cand)
                used.add(cand)
        extra = 1
        while len(selected) < count and extra <= 999:
            cand = "新视角{}".format(extra)
            if cand not in used and not growth_api._is_local_role_name(cand):
                selected.append(cand)
                used.add(cand)
            extra += 1
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
    parser = argparse.ArgumentParser(description="基于问题类型生成角色卡（受 role_source_mode 开关控制）")
    parser.add_argument("--question", required=True, help="用户原始问题")
    parser.add_argument("--count", type=int, default=4, help="生成角色数量")
    args = parser.parse_args()
    roles, mode, notes = generate_roles(args.question, args.count)
    handling = growth_api._get_config('pure_generated_handling', 'ask').lower()
    print("[角色来源模式] role_source_mode = {}".format(mode))
    print("[纯生成处置] pure_generated_handling = {}".format(handling))
    prompt_lines = [n for n in notes if n.startswith('PROMPT:')]
    for n in notes:
        print("  - " + n)
    # 若有纯生成需确认的，单独高亮（调用方/石叔据此提示用户）
    if prompt_lines:
        print("\n⚠ 需用户决策：以下角色为本地库查无记录的纯生成角色")
        for p in prompt_lines:
            print("   " + p)
    print("\n生成的角色草稿（请人工确认后使用）：")
    # 标注每个角色是否本地库 + 是否建议转正
    for r in roles:
        tag = []
        if r.get('local_role'):
            tag.append('[本地库]')
        if r.get('suggest_localize'):
            tag.append('[建议转正]')
        if r.get('growth_hint'):
            tag.append('[已注入成长]')
        r['_tag'] = ' '.join(tag)
    print(json.dumps(roles, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
