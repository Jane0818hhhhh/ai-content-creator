"""
AI 内容创作系统 - 主应用
北极星-炼术师 队伍作品（腾讯 AI 黑客松 - 方向二·内容）

功能模块：
1. 选题脑暴 - AI + 素材库联想
2. 爆款拆解 - 结构分析 + 复用建议
3. 多平台适配 - 公众号/小红书/知乎/视频号 一稿多平台
4. 标题 AB 测试 - 5-10 个候选 + 点击率打分
5. 私有素材库 - 上传灵感/参考文/自己写过的稿子
"""
import os
import json
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

import llm_client
import knowledge_base as kb

app = Flask(__name__)
app.secret_key = 'polaris-alchemist-content-2024'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

ALLOWED_EXT = {'txt', 'md', 'pdf', 'docx', 'doc', 'csv', 'json', 'log'}


# ============ Mock ============
def mock_topic(topic):
    return json.dumps({
        'topic': topic,
        'ideas': [
            {'title': f'{topic}的 10 个实用技巧', 'angle': '实用指南', 'platform': '公众号', 'heat': 85, 'hook': '3 步搞定'},
            {'title': f'聊聊 {topic} 背后没人告诉你的那些事', 'angle': '故事化', 'platform': '小红书', 'heat': 90, 'hook': '认知反差'},
            {'title': f'{topic} vs 传统方法：一场认知革命', 'angle': '对比分析', 'platform': '知乎', 'heat': 80, 'hook': '争议话题'},
            {'title': f'2024 年 {topic} 趋势预测', 'angle': '趋势分析', 'platform': '公众号', 'heat': 88, 'hook': '时效性'},
            {'title': f'小白也能懂的 {topic} 入门', 'angle': '入门科普', 'platform': '小红书', 'heat': 82, 'hook': '门槛低'},
            {'title': f'我用 {topic} 一个月赚了 xxx', 'angle': '亲历故事', 'platform': '小红书', 'heat': 95, 'hook': '结果导向'},
        ],
    }, ensure_ascii=False, indent=2)


def mock_viral():
    return json.dumps({
        'structure': '开篇 hook → 痛点具象化 → 核心洞察 → 实操框架 → 案例佐证 → 升华金句',
        'title_tips': ['标题带数字', '制造悬念', '直击痛点', '反常识钩子'],
        'emotion_nodes': ['开头 30% 处第一次共鸣', '中段 60% 处认知反转', '结尾金句留白'],
        'framework': '提问 → 痛点 → 观点 → 步骤 → 案例 → 升华',
        'suggestions': ['增加 2-3 个真实案例', '每段末尾埋金句', '结尾设置互动 CTA'],
        'why_viral': '这类文章之所以爆款，是因为在开头 3 秒完成了「共情+悬念」双钩，读者只要点进来就很难滑走。',
    }, ensure_ascii=False, indent=2)


def mock_platform(platform, original):
    return json.dumps({
        'platform': platform,
        'adapted_content': f'（针对 {platform} 优化后的正文）\n\n{original[:200]}...\n\n[此处为 Mock，配置 OPENAI_API_KEY 后启用真实改写]',
        'title_suggestions': [f'{platform}版标题 1', f'{platform}版标题 2'],
        'cover_advice': '首图建议使用高饱和度大字报',
        'best_publish_time': '晚上 8-10 点',
        'tags_suggested': ['#干货', '#职场', '#成长'],
    }, ensure_ascii=False, indent=2)


def mock_title(topic):
    return json.dumps({
        'topic': topic,
        'titles': [
            {'title': f'{topic} 完全指南', 'score': 75, 'reason': '经典教程式', 'audience': '初学者'},
            {'title': f'我研究了 100 个 {topic} 案例，发现…', 'score': 92, 'reason': '数字化 + 权威感 + 悬念', 'audience': '实践者'},
            {'title': f'为什么别人做 {topic} 能成功，你不行？', 'score': 88, 'reason': '对比 + 悬念', 'audience': '焦虑型'},
            {'title': f'{topic} 的真相，99% 的人都错了', 'score': 95, 'reason': '反常识 + 认知冲突', 'audience': '好奇心'},
            {'title': f'2024 最新 {topic} 手册（含实操模板）', 'score': 82, 'reason': '时效 + 福利', 'audience': '搜索党'},
        ],
        'best': f'{topic} 的真相，99% 的人都错了',
        'tips': ['数字化标题平均点击率 +20%', '"真相/秘密"制造悬念，慎用避免党味', '控制在 22 字内适合手机端'],
    }, ensure_ascii=False, indent=2)


# ============ 页面路由 ============
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/topic-brainstorm')
def p_topic():
    return render_template('topic_brainstorm.html')


@app.route('/viral-analysis')
def p_viral():
    return render_template('viral_analysis.html')


@app.route('/platform-adaptation')
def p_platform():
    return render_template('platform_adaptation.html')


@app.route('/title-ab-test')
def p_title():
    return render_template('title_ab_test.html')


@app.route('/library')
def p_library():
    return render_template('library.html')


@app.route('/about')
def about():
    return render_template('about.html')


# ============ API：选题脑暴 ============
@app.route('/api/topic', methods=['POST'])
def api_topic():
    d = request.json or {}
    topic = d.get('topic', '').strip()
    audience = d.get('audience', '').strip()
    tone = d.get('tone', '').strip()

    # 检索素材库
    hits = kb.search(topic, top_k=3) if topic else []
    kb_ctx = '\n'.join([f"- {h['filename']}: {h['snippet'][:150]}" for h in hits])

    system = '你是资深内容策划，擅长为公众号、小红书、知乎、视频号生成有传播力的选题。'
    user = f"""围绕主题「{topic}」生成 6 个不同角度的选题，输出 JSON（title/angle/platform/hook 必须是字符串，不能是数组或对象；heat 必须是 0-100 的数字）：
{{
  "topic": "字符串",
  "ideas": [{{"title":"字符串，标题", "angle":"字符串，角度类型", "platform":"字符串，推荐平台", "heat":预估热度分数(0-100的数字), "hook":"字符串，钩子类型"}}]
}}

- 目标读者：{audience or '通用'}
- 语气：{tone or '不限'}
- 参考素材：
{kb_ctx or '（无）'}

要求：
1. 6 个选题角度必须不同（实用/故事/争议/对比/趋势/案例）
2. 标题控制 18-24 字，无党味
3. 仅返回 JSON"""

    r = llm_client.chat(system, user, mock_fn=lambda: mock_topic(topic), temperature=0.9)
    parsed = try_parse_json(r['content'])
    return jsonify({'success': True, 'source': r['source'], 'data': parsed, 'raw': r['content'], 'kb_hits': hits})


# ============ API：爆款拆解 ============
@app.route('/api/viral', methods=['POST'])
def api_viral():
    d = request.json or {}
    content = d.get('content', '').strip()
    doc_id = d.get('doc_id')
    if doc_id and not content:
        doc = kb.get_document(int(doc_id))
        if doc: content = doc['content'][:6000]

    if not content:
        return jsonify({'success': False, 'error': '请粘贴爆款文本或选择素材库文件'})

    system = '你是爆款内容拆解专家，善于从一篇爆款中提炼可复用的结构与模板。'
    user = f"""请拆解以下爆款内容，输出 JSON（以下字段全部要求字符串或字符串数组，禁止嵌套对象）：
{{
  "structure": "字符串，全文结构一句话概括",
  "title_tips": ["字符串数组，标题技巧"],
  "emotion_nodes": ["字符串数组，情绪节点位置与作用"],
  "framework": "字符串，可复用的写作框架（如 提问→痛点→观点→步骤）",
  "suggestions": ["字符串数组，下次自己写同类主题的建议"],
  "why_viral": "字符串，一段话解释这篇为什么爆"
}}

爆款正文：
\"\"\"{content[:5000]}\"\"\"

仅返回 JSON。"""

    r = llm_client.chat(system, user, mock_fn=mock_viral, max_tokens=1800)
    parsed = try_parse_json(r['content'])
    return jsonify({'success': True, 'source': r['source'], 'data': parsed, 'raw': r['content']})


# ============ API：多平台适配 ============
@app.route('/api/platform', methods=['POST'])
def api_platform():
    d = request.json or {}
    platform = d.get('platform', '公众号')
    original = d.get('content', '').strip()
    if not original:
        return jsonify({'success': False, 'error': '请粘贴原稿'})

    platform_specs = {
        '公众号': '深度专业，2000-3500 字，可用小标题、金句、案例，结尾引导关注',
        '小红书': '亲切真实，800-1200 字，多用「我」「大家」「爆炸」等感叹词，段短行短，emoji 适量',
        '知乎': '专业严谨，2000-5000 字，开头强 hook（反常识/故事），中间理论+案例，结尾金句',
        '视频号': '口播风格，600-900 字，前 3 秒必须钩住人，全程口语化，句短，节奏明快',
        'LinkedIn': '职业化、克制、观点导向，300-500 字，2-3 段，结尾开放式问题',
    }
    spec = platform_specs.get(platform, platform_specs['公众号'])

    system = '你是全平台内容适配专家。'
    user = f"""把下面原稿改写为「{platform}」平台风格：

平台调性：{spec}

原稿：
\"\"\"{original[:4000]}\"\"\"

输出 JSON（以下字段全部要求字符串或字符串数组，禁止嵌套对象）：
{{
  "platform": "{platform}",
  "adapted_content": "字符串，改写后的完整正文",
  "title_suggestions": ["字符串数组，标题1/标题2/标题3"],
  "cover_advice": "字符串，封面/首图建议",
  "best_publish_time": "字符串，最佳发布时间",
  "tags_suggested": ["字符串数组，#标签1/#标签2"]
}}

仅返回 JSON。"""

    r = llm_client.chat(system, user, mock_fn=lambda: mock_platform(platform, original), max_tokens=3000)
    parsed = try_parse_json(r['content'])
    return jsonify({'success': True, 'source': r['source'], 'data': parsed, 'raw': r['content']})


# ============ API：标题 AB ============
@app.route('/api/title', methods=['POST'])
def api_title():
    d = request.json or {}
    topic = d.get('topic', '').strip()
    platform = d.get('platform', '公众号')
    n = int(d.get('n', 6))
    if not topic:
        return jsonify({'success': False, 'error': '请填选题'})

    system = '你是标题工程师，懂算法推荐机制。'
    user = f"""为选题「{topic}」（平台：{platform}）生成 {n} 个候选标题，输出 JSON（title/reason/audience 必须是字符串，score 必须是 0-100 的数字）：
{{
  "topic": "{topic}",
  "titles": [{{"title":"字符串", "score":点击率预估0-100的数字, "reason":"字符串，打分理由", "audience":"字符串，目标读者"}}],
  "best": "字符串，推荐使用的最佳标题",
  "tips": ["字符串数组，优化建议"]
}}

要求：
1. 每个标题风格必须不同（数字/悬念/反差/故事/福利/焦虑）
2. 每个不超过 24 字
3. score 结合平台算法+读者心理综合打分
4. 仅返回 JSON"""

    r = llm_client.chat(system, user, mock_fn=lambda: mock_title(topic), temperature=0.85)
    parsed = try_parse_json(r['content'])
    return jsonify({'success': True, 'source': r['source'], 'data': parsed, 'raw': r['content']})


# ============ 素材库（复用同一份 API）============
@app.route('/api/library/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '未收到文件'})
    f = request.files['file']
    if not f.filename:
        return jsonify({'success': False, 'error': '文件名为空'})
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in ALLOWED_EXT:
        return jsonify({'success': False, 'error': f'不支持的类型 .{ext}'})
    filename = secure_filename(f.filename) or f'upload_{int(time.time())}.{ext}'
    save_name = f'{int(time.time()*1000)}_{filename}'
    filepath = os.path.join(kb.UPLOAD_DIR, save_name)
    f.save(filepath)
    category = request.form.get('category', '通用')
    tags = request.form.get('tags', '')
    doc_id = kb.add_document(filename, filepath, ext, category=category, tags=tags)
    return jsonify({'success': True, 'id': doc_id, 'filename': filename})


@app.route('/api/library/list')
def api_list():
    return jsonify({'success': True, 'docs': kb.list_documents(category=request.args.get('category'))})


@app.route('/api/library/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q: return jsonify({'success': True, 'hits': []})
    return jsonify({'success': True, 'hits': kb.search(q, top_k=10)})


@app.route('/api/library/delete/<int:doc_id>', methods=['DELETE'])
def api_delete(doc_id):
    return jsonify({'success': kb.delete_document(doc_id)})


@app.route('/api/library/get/<int:doc_id>')
def api_get_doc(doc_id):
    d = kb.get_document(doc_id)
    return jsonify({'success': bool(d), 'doc': d})


@app.route('/api/system/info')
def api_info():
    return jsonify({
        'llm_mode': 'real' if llm_client.is_real_llm() else 'mock',
        'model': llm_client.MODEL,
        'team': '北极星 · 炼术师',
    })


def try_parse_json(text):
    if not text: return None
    t = text.strip()
    if t.startswith('```'):
        t = t.split('```')[1] if '```' in t[3:] else t
        if t.startswith('json'): t = t[4:]
        t = t.strip()
    try:
        return json.loads(t)
    except Exception:
        s, e = t.find('{'), t.rfind('}')
        if s >= 0 and e > s:
            try: return json.loads(t[s:e+1])
            except Exception: pass
    return None


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    print('=' * 60)
    print('🎨 AI Content Creator | 北极星·炼术师')
    print(f'LLM: {"real" if llm_client.is_real_llm() else "mock"} | Model: {llm_client.MODEL}')
    print(f'Port: {port}')
    print('=' * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
