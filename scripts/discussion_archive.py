# -*- coding: utf-8 -*-
"""
discussion_archive.py - discussion archive to knowledge base (enhanced v2.2)
New: #34 Discussion Quality Scorecard - auto-calculate 5-dimension score
New: Phase 0-5 - integrated with growth_api.py for role growth tracking + career events
"""

import os
import sys
import io
import codecs
import json
import argparse
import datetime
import re

# UTF-8 重包装：中文 Windows (cp936) 下 print CJK 可能 UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure scripts directory is in path for growth_api import
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import growth_api

# --- Utility functions (original v2.1) ---

def extract_keywords(text, max_keywords=5):
    if not text:
        return []
    stop_words = set(['应该','怎么','什么','为什么','如何','是否',
                       '该不该','能不能','要不要','可不可以','怎么办','好不好'])
    words = []
    for seg in re.findall(r'[\u4e00-\u9fff]+', text):
        if len(seg) >= 2 and seg not in stop_words:
            words.append(seg)
    return words[:max_keywords]

def _is_local_role(role_name):
    """判断角色是否属于「本地库」(持久层)。委托 growth_api._is_local_role_name 统一实现。"""
    return growth_api._is_local_role_name(role_name)


def _has_pending_placeholder(roles):
    """检测阵容里是否仍有「待定」占位名（generate 模式石叔未填真实名就归档）。
    返回占位角色名列表；空列表表示无占位。"""
    pending = []
    for r in roles:
        nm = (r.get('name') or '').strip()
        if not nm or '待定' in nm:
            pending.append(nm or '(空名)')
    return pending


def _ghost_collision(roles):
    """检测一次性角色（非本地库）是否撞本地库核心名。
    generate 模式石叔生成名字时须避开 role-templates.md 本地角色名；
    若某角色未带 local_role=True（非脚本认证的本地库角色）却与本地模板核心名撞名，
    视为幽灵撞名，返回撞名列表，避免混淆成长史。
    """
    ghosts = []
    for r in roles:
        nm = (r.get('name') or '').strip()
        if not nm or '待定' in nm:
            continue
        if r.get('local_role') is True:
            continue  # 脚本认证的本地库角色，正常
        if _template_name_only(nm):
            ghosts.append(nm)
    return ghosts


def _template_name_only(role_name):
    """仅判断名字是否撞 role-templates.md 核心名（括号前部分），用于幽灵撞名检测。
    模板标题格式如「### 🎲 赌徒（老六）」，核心名为「赌徒」；
    对比时取 role_name 与模板名各自的括号前核心段，避免「冰」与「冰（理性派）」漏判。"""
    if not role_name or role_name == 'Unknown':
        return False
    core = role_name.split('（')[0].split('(')[0].strip()
    if not core:
        return False
    tmpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'references', 'role-templates.md')
    try:
        with codecs.open(tmpl_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        for m in re.finditer(r'^###\s+\S+\s+(\S+)', txt, re.M):
            tmpl_core = m.group(1).split('（')[0].split('(')[0].strip()
            if tmpl_core == core:
                return True
    except FileNotFoundError:
        pass
    return False


def make_topic_slug(question, cap=6):
    """Build a filename-safe topic slug from the question.
    Strip punctuation, drop filler words, pick the most topical segment
    (prefer segments containing core semantic chars), cap at `cap` (<= not fixed).
    """
    if not question:
        return 'topic'
    fillers = set(['应该','怎么','什么','为什么','如何','是否',
                   '该不该','能不能','要不要','可不可以','怎么办','好不好',
                   '的','了','吗','呢','吧','是','有','我','你','和','人类','能',
                   '可以','会','就','也','都','在','把','被','让'])
    # keep CJK + alphanumerics only
    segs = re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+', question)
    if not segs:
        return 'topic'
    # Core-token based slug: pull prioritized topic words in order of appearance,
    # then cap at `cap` (<= not fixed). This yields e.g. 'AI绘画著' from the
    # copyright-painting question instead of a raw 6-char cut.
    core_tokens = ['AI', 'AIGC', '绘画', '画', '著作', '著', '版权', '权',
                   '生成', '原创', '文生图', '伦理', '法律', '公司', '投资']
    found = []
    body = question
    acc = ''
    for tok in core_tokens:
        if tok in body and tok not in found and tok not in acc:
            found.append(tok)
            acc += tok
    if not found:
        # fallback: first segment, strip light fillers
        base = re.sub(r'[的了吗呢吧]', '', segs[0])
        return base[:cap] if base else 'topic'
    slug = ''.join(found)
    # cap at `cap` (<= not fixed)
    slug = slug[:cap]
    return slug if slug else 'topic'

def extract_turning_points(log_content):
    if not log_content:
        return []
    points = []
    lines = log_content.split('\n')
    prev_consensus = None
    for line in lines:
        m = re.match(r'.*共识\s*(\d+)%', line)
        if m:
            cur = int(m.group(1))
            if prev_consensus is not None and abs(cur - prev_consensus) >= 15:
                points.append('consensus changed {}% -> {}%'.format(prev_consensus, cur))
            prev_consensus = cur
    if not points:
        if '[让]' in log_content:
            points.append('[让] tag appeared, some role conceded')
        if '[绿]' in log_content:
            points.append('Green hat round triggered, new ideas')
    return points

def find_related_archives(question, archive_dir):
    if not os.path.isdir(archive_dir):
        return []
    keywords = extract_keywords(question,
                                max_keywords=int(growth_api._get_config('archive_keyword_count', '5')))
    related = []
    for fname in os.listdir(archive_dir):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(archive_dir, fname)
        with codecs.open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for kw in keywords:
            if kw in content:
                related.append(fname)
                break
    return related

def classify_question_type(question):
    q = question.lower()
    if any(w in q for w in ['买房','卖房','租房','投资','理财','股票']):
        return 'financial'
    if any(w in q for w in ['辞职','创业','工作','跳槽','加薪']):
        return 'career'
    if any(w in q for w in ['结婚','离婚','出轨','育儿','孩子','父母','家庭']):
        return 'family'
    if any(w in q for w in ['技术','架构','选型','框架','代码']):
        return 'technical'
    return 'general'

# --- Diversity history (original v2.1) ---

_diversity_history = []

def record_discussion(question, q_type, role_names, filename):
    global _diversity_history
    entry = {
        'filename': filename,
        'question': question,
        'type': q_type,
        'roles': list(role_names),
        'timestamp': datetime.datetime.now().isoformat()
    }
    _diversity_history.append(entry)
    return _diversity_history

def check_combo_duplicate(q_type, role_names, history, window=5):
    recent = history[-window:] if len(history) > window else history
    combo = tuple(sorted(role_names))
    count = 0
    matches = []
    for entry in recent:
        if entry['type'] == q_type and tuple(sorted(entry['roles'])) == combo:
            count += 1
            matches.append(entry['filename'])
    return count >= 2, count, matches

# ========== NEW: #34 Scorecard ==========

def make_bar(score, width=10):
    filled = min(width, int(score * width / 100 + 0.5))
    return '[' + '#' * filled + '.' * (width - filled) + ']'

def calc_role_differentiation(log_content):
    """Role differentiation (simplified auto version).
    Real check: Shishu manual blind test. This returns a reasonable default.
    """
    if not log_content:
        return 75, '(no log, default 75%)'
    # Simple heuristic: if 4+ distinct role names appear in log, assume good
    # Extract role names: text between 】 and ：or between ] and ：
    names = set()
    for line in log_content.split('\n'):
        # Half-width: [TAG] NAME：
        m = re.match(r'\[[^\]]+\]\s*([\u4e00-\u9fff]{2,6})\s*[：:]', line)
        if m:
            names.add(m.group(1))
            continue
        # Full-width: 【TAG】 NAME：
        m = re.match(r'【[^】]+】\s*([\u4e00-\u9fff]{2,6})\s*[：:]', line)
        if m:
            names.add(m.group(1))
    unique = len(names)
    if unique >= 4:
        return 100, '4/4 roles found (auto)'
    elif unique == 3:
        return 75, '3/4 roles found (auto)'
    elif unique >= 2:
        return 50, '2/4 roles found (auto)'
    else:
        return 50, '(could not extract roles)'

def calc_conflict_density(log_content):
    if not log_content:
        return 60, 'avg 1.0 [怼]/round (default)', 1.0
    rounds = re.findall(r'\*\*第(\d+)轮', log_content)
    round_count = max(len(rounds), 1)
    conflict_count = len(re.findall(r'\[怼\]', log_content))
    avg_c = conflict_count / round_count
    if avg_c >= 2:
        score = 100
    elif avg_c >= 1.5:
        score = 80
    elif avg_c >= 1.0:
        score = 60
    elif avg_c >= 0.5:
        score = 30
    else:
        score = 0
    return score, 'avg {:.1f} [怼]/round'.format(avg_c), avg_c

def calc_evolution_efficiency(consensus_history):
    if not consensus_history or len(consensus_history) < 2:
        return 40, 'insufficient data (default 40%)'
    deltas = []
    for i in range(1, len(consensus_history)):
        delta = abs(consensus_history[i][1] - consensus_history[i-1][1])
        deltas.append(delta)
    avg_d = sum(deltas) / len(deltas)
    if avg_d >= 15:
        score = 100
    elif avg_d >= 10:
        score = 70
    elif avg_d >= 5:
        score = 40
    else:
        score = 0
    detail = 'consensus {}% -> {}% (avg +{:.1f}%/round)'.format(
        consensus_history[0][1], consensus_history[-1][1], avg_d)
    return score, detail

def calc_convergence_quality(log_content, conclusion):
    let_count = 0
    has_options = False
    has_executable = False
    if log_content:
        let_count = len(re.findall(r'\[让\]', log_content))
        has_options = bool(re.search(r'\nA[\.\s]|选项\s*[A-C]', log_content))
    if conclusion:
        exec_kw = ['建议','可以','应该','先做','如果','满足','条件','步骤','别']
        has_executable = any(kw in conclusion for kw in exec_kw)
    if (has_options or has_executable) and let_count >= 2:
        return 100, 'executable + [让]>=2', let_count
    elif (has_options or has_executable) and let_count >= 1:
        return 80, 'executable + [让]>=1', let_count
    elif has_options or has_executable:
        return 60, 'has conclusion but [让]<1', let_count
    elif let_count >= 2:
        return 70, '[让]>=2 but no clear conclusion', let_count
    elif let_count >= 1:
        return 50, '[让]>=1 but no conclusion', let_count
    else:
        return 0, 'no conclusion + no [让]', let_count

def calc_intervention_utilization(log_content):
    if not log_content:
        return 80, '4/5 roles referenced (default)', 4, 5
    intervention_count = len(re.findall(r'\[真\]', log_content))
    if intervention_count == 0:
        return 100, '(no intervention, full score)', 0, 0
    green_refs = len(re.findall(r'\[绿\]', log_content))
    ref_count = min(green_refs, 4)
    total_roles = 4
    if ref_count == 0:
        if re.search(r'真|当事人|插话', log_content):
            ref_count = 2
    ratio = ref_count / total_roles
    score = int(ratio * 100)
    return score, '{}/{} roles core-referenced'.format(ref_count, total_roles), ref_count, total_roles

def build_scorecard(log_content=None, consensus_history=None, conclusion=''):
    diff_score, diff_reason = calc_role_differentiation(log_content)
    conflict_score, conflict_detail, _ = calc_conflict_density(log_content)
    evol_score, evol_detail = calc_evolution_efficiency(consensus_history or [])
    conv_score, conv_detail, let_count = calc_convergence_quality(log_content, conclusion)
    intervene_score, intervened_detail, _, _ = calc_intervention_utilization(log_content)

    composite = int(diff_score * 0.25 + conflict_score * 0.20 + evol_score * 0.20 + conv_score * 0.25 + intervene_score * 0.10)

    if composite >= 90:
        grade = 'A'
    elif composite >= 80:
        grade = 'B+'
    elif composite >= 70:
        grade = 'B'
    elif composite >= 60:
        grade = 'C'
    else:
        grade = 'D'

    lines = []
    lines.append('## Discussion Quality Scorecard')
    lines.append('')
    lines.append('Role differentiation   {}  {}%  {}'.format(make_bar(diff_score), diff_score, diff_reason))
    lines.append('Conflict density      {}  {}%  {}'.format(make_bar(conflict_score), conflict_score, conflict_detail))
    lines.append('Evolution efficiency  {}  {}%  {}'.format(make_bar(evol_score), evol_score, evol_detail))
    lines.append('Convergence quality   {}  {}%  {}'.format(make_bar(conv_score), conv_score, conv_detail))
    lines.append('Intervention util.   {}  {}%  {}'.format(make_bar(intervene_score), intervene_score, intervened_detail))
    lines.append('')
    lines.append('Composite score: {}  ({} grade)'.format(make_bar(composite), grade))
    lines.append('')

    improvements = []
    if diff_score < 70:
        improvements.append('- Role differentiation < 70%, suggest replacing similar-looking roles')
    if conflict_score < 50:
        improvements.append('- Conflict density < 50%, suggest more antagonistic pairing')
    if evol_score < 40:
        improvements.append('- Evolution efficiency < 40%, suggest mid-summary or green hat round')
    if conv_score < 60:
        improvements.append('- Convergence quality < 60%, Shishu conclusion missing executable judgment')
    if intervene_score < 50:
        improvements.append('- Intervention utilization < 50%, strengthen reference requirement in prompt')
    if improvements:
        lines.append('Improvement points:')
        lines.extend(improvements)
    else:
        lines.append('Improvement points: No obvious short board, archive as excellent case')
    lines.append('')
    return '\n'.join(lines), composite, grade

# ========== Archive builder ==========

def build_archive_content(question, conclusion, roles, timestamp_iso,
                         log_content=None, related_archives=None, scorecard_text=None):
    lines = []
    q_short = question[:30] + ('...' if len(question) > 30 else '')
    lines.append('# Discussion Archive: ' + q_short)
    lines.append('')
    lines.append('**Time**: ' + timestamp_iso)
    lines.append('**Question**: ' + question)
    lines.append('')

    tags = extract_keywords(question,
                             max_keywords=int(growth_api._get_config('archive_keyword_count', '5')))
    if tags:
        lines.append('**Tags**: ' + ' '.join(['#' + t for t in tags]))
        lines.append('')

    lines.append('## Conclusion')
    lines.append('')
    lines.append(conclusion)
    lines.append('')

    if roles:
        lines.append('## Role Lineup')
        lines.append('')
        lines.append('| Role | Stance | Key Quote |')
        lines.append('|---|---|---|')
        for r in roles:
            name = r.get('name', 'Unknown')
            stance = r.get('stance', 'Unknown')
            key = r.get('key_quote', 'TBD')
            lines.append('| {} | {} | {} |'.format(name, stance, key))
        lines.append('')

    if log_content:
        lines.append('## Full Discussion Log')
        lines.append('')
        lines.append('```')
        lines.append(log_content)
        lines.append('```')
        lines.append('')

    lines.append('## Key Turning Points')
    lines.append('')
    if log_content:
        turning_points = extract_turning_points(log_content)
        if turning_points:
            for tp in turning_points:
                lines.append('- ' + tp)
        else:
            lines.append('(No obvious position shift)')
    else:
        lines.append('(Filled manually by Shishu)')
    lines.append('')

    lines.append('## Future Reference')
    lines.append('')
    if related_archives:
        lines.append('**Related historical archives** (keyword match):')
        for fname in related_archives:
            lines.append('- ' + fname)
        lines.append('')
        lines.append('If encountering similar questions, reference above.')
    else:
        lines.append('(No related archives yet)')
    lines.append('')

    if scorecard_text:
        lines.append(scorecard_text)
        lines.append('')

    return '\n'.join(lines)

# ========== Main ==========

def main():
    parser = argparse.ArgumentParser(description='Discussion archiving (enhanced v2.2)')
    parser.add_argument('--question', required=True, help='Original user question')
    parser.add_argument('--conclusion', required=True, help='Shishu summary conclusion')
    parser.add_argument('--roles', help='Role lineup JSON file path')
    parser.add_argument('--log', help='Full discussion log file path (optional)')
    parser.add_argument('--output', default=None, help='Archive output directory (default: config archive_dir)')
    parser.add_argument('--consensus-history', help='Consensus history JSON, e.g. "[[1,25],[2,40]]"')
    parser.add_argument('--no-score', action='store_true', help='Skip scorecard generation')
    args = parser.parse_args()

    # 归档目录：未显式传 --output 时回退 config archive_dir（修复无视配置的旧默认相对 cwd 行为）
    out_dir = args.output or growth_api._get_config('archive_dir')
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.datetime.now()
    timestamp_iso = timestamp.strftime('%Y-%m-%d %H:%M')
    filename = timestamp.strftime('%Y%m%d-%H%M') + '.md'
    filepath = os.path.join(out_dir, filename)

    # topic slug for growth session_id / stance topic (capped at topic_slug_length, <= not fixed)
    _cap = int(growth_api._get_config('topic_slug_length', '6'))
    _slug = make_topic_slug(args.question, cap=_cap)
    q_topic = [_slug]
    topic_slug = _slug

    # archive filename: YYYYMMDD-{slug}.md (date-first for natural time sort)
    filename = timestamp.strftime('%Y%m%d') + '-' + _slug + '.md'
    filepath = os.path.join(out_dir, filename)

    roles = []
    if args.roles:
        with codecs.open(args.roles, 'r', encoding='utf-8') as f:
            roles = json.load(f)

    # ===== 归档护栏（generate 模式相关）=====
    # 1) 占位名检测：generate 模式石叔未填真实名就归档，禁止带「待定」占位落盘
    _pending = _has_pending_placeholder(roles)
    if _pending:
        sys.stderr.write(
            '[归档拦截] 阵容含未填真实名的占位角色 {}，请石叔先按用户问题生成具体名字再归档。\n'.format(_pending))
        sys.exit(2)
    # 2) 幽灵撞名检测：未转正的一次性角色撞本地库名，拒绝以免混淆成长史
    _ghosts = _ghost_collision(roles)
    if _ghosts:
        sys.stderr.write(
            '[归档拦截] 以下一次性角色名与本地库(role-templates.md)撞名 {}，'
            '请改名或先转正存库后再归档。\n'.format(_ghosts))
        sys.exit(3)

    log_content = None
    if args.log:
        with codecs.open(args.log, 'r', encoding='utf-8') as f:
            log_content = f.read()

    consensus_history = None
    if args.consensus_history:
        try:
            consensus_history = json.loads(args.consensus_history.replace("'", '"'))
        except Exception:
            consensus_history = None

    scorecard_text = None
    if not args.no_score:
        scorecard_text, composite, grade = build_scorecard(
            log_content, consensus_history, args.conclusion)
        print('Scorecard: {} points ({} grade)'.format(composite, grade))

    related = find_related_archives(args.question, out_dir)
    content = build_archive_content(
        args.question, args.conclusion, roles, timestamp_iso,
        log_content, related, scorecard_text)

    with codecs.open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print('Archive completed: ' + filepath)
    if related:
        print('Found related archives: ' + ', '.join(related))

    # Diversity detection (#39)
    role_names = [r.get('name', 'Unknown') for r in roles] if roles else []
    if role_names:
        question_type = classify_question_type(args.question)
        history = record_discussion(args.question, question_type, role_names, filename)
        is_dup, count, matches = check_combo_duplicate(question_type, role_names, history)
        if is_dup:
            print('Diversity warning: type [{}] x roles {} appeared {} times recently'.format(
                question_type, role_names, count))
        else:
            print('Diversity check passed')

    # ─── Phase 0-5: Growth tracking + career events ───
    session_id = timestamp.strftime('%Y%m%d') + '-' + topic_slug
    if role_names:
        for r in roles:
            rname = r.get('name', 'Unknown')
            rstance = r.get('stance', '')

            # 纯生成一次性角色（不在本地库）跳过成长写入，避免污染 growth_record.json
            if not _is_local_role(rname):
                print('  [Growth] 跳过「{}」：纯生成一次性角色，未转正不累积'.format(rname))
                continue

            # Update stance history
            growth_api.update_stance_history(
                role_id=rname,
                session_id=session_id,
                topic=args.question,  # 存原文供 _classify_topic 分类（覆盖 8 组角色，slug 会丢词）
                stance=rstance,
                score=composite if not args.no_score else None,
            )

            # Update relationship lines with co-participants
            for co in role_names:
                if co != rname:
                    growth_api.update_relationship(rname, co, 'neutral')

            # Check achievements with career event context
            session_ctx = {
                'session_id': session_id,
                'consensus_jump': 0,
                'stance_shifted': False,
                'session_score': composite if not args.no_score else None,
                'mutual_rang': False,
            }
            new_achs = growth_api.check_achievements(rname, session_ctx)

            # Check milestones (session count thresholds: 5/10/20/50)
            milestones = growth_api._check_milestones(rname, session_id)

            # Update auto tags
            growth_api.update_auto_tags(rname)

            if new_achs:
                print('  [Growth] {} unlocked: {}'.format(rname, ', '.join(new_achs)))
            if milestones:
                for m in milestones:
                    print('  [Milestone] {}: {}'.format(rname, m.get('description', '')))

    # Auto-backup
    backup_path = growth_api.auto_backup_if_needed()
    if backup_path:
        print('Growth auto-backup: ' + backup_path)

    # Clear session override
    growth_api.clear_session_override()

if __name__ == '__main__':
    main()
