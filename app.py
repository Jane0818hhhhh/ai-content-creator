#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI内容创作与发布分析系统 - 主应用
基于WorkBuddy能力构建的内容创作辅助工具
"""

from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'ai-content-creator-2024'

# 模拟AI响应函数
def mock_ai_response(module, input_data):
    """模拟AI响应，用于Demo演示"""
    
    if module == 'topic_brainstorm':
        topic = input_data.get('topic', '')
        return {
            'success': True,
            'data': {
                'topic': topic,
                'ideas': [
                    {
                        'title': f'{topic}的10个实用技巧',
                        'angle': '实用指南',
                        'reason': '用户喜欢可操作性强的干货内容',
                        'platform': '公众号',
                        'heat_score': 85
                    },
                    {
                        'title': f'聊聊{topic}背后的那些事',
                        'angle': '故事化',
                        'reason': '故事化内容更容易引发共鸣和转发',
                        'platform': '小红书',
                        'heat_score': 90
                    },
                    {
                        'title': f'{topic} vs 传统方法：到底差在哪？',
                        'angle': '对比分析',
                        'reason': '对比内容容易引发讨论和关注',
                        'platform': '知乎',
                        'heat_score': 80
                    },
                    {
                        'title': f'2024年{topic}趋势预测',
                        'angle': '趋势分析',
                        'reason': '趋势类内容具有时效性和话题性',
                        'platform': '公众号',
                        'heat_score': 88
                    },
                    {
                        'title': f'小白也能懂的{topic}入门指南',
                        'angle': '入门科普',
                        'reason': '入门内容受众广，适合涨粉',
                        'platform': '小红书',
                        'heat_score': 82
                    }
                ]
            }
        }
    
    elif module == 'viral_analysis':
        content = input_data.get('content', '')
        url = input_data.get('url', '')
        
        return {
            'success': True,
            'data': {
                'content_source': url if url else '手动输入',
                'structure_analysis': {
                    'opening': '开篇用提问/故事吸引注意力，3秒内抓住读者',
                    'body': '采用"问题-分析-解决方案"结构，逻辑清晰',
                    'transition': '使用小标题和过渡句，保证阅读流畅',
                    'ending': '结尾呼吁行动或留下悬念，提高互动率'
                },
                'title_techniques': [
                    '使用数字：增加可信度和可操作性',
                    '制造悬念：激发好奇心',
                    '直击痛点：让读者感觉"这就是写给我的"'
                ],
                'emotional_nodes': [
                    '共鸣点：开头讲述普遍困扰',
                    '转折点：揭示反常识的认知',
                    '爽点：提供立即可用的解决方案'
                ],
                'reusable_framework': '开篇(提问/故事) → 痛点分析 → 核心观点 → 实操步骤 → 总结升华',
                'optimization_suggestions': [
                    '增加更多具体案例',
                    '在关键位置添加金句',
                    '结尾可以增加互动提问'
                ]
            }
        }
    
    elif module == 'platform_adaptation':
        content = input_data.get('content', '')
        target_platform = input_data.get('platform', 'wechat')
        
        platform_configs = {
            'wechat': {
                'name': '公众号',
                'max_length': '2000-5000字',
                'style': '深度、专业、结构化',
                'features': '支持超链接、小程序卡片、赞赏',
                'adapted_content': f'【公众号版本】\n\n{content}\n\n（已调整为：深度分析风格，增加小标题，添加相关文章链接，字数扩展至3000字左右）'
            },
            'xiaohongshu': {
                'name': '小红书',
                'max_length': '1000字以内',
                'style': '轻松、emoji、短句、真实感',
                'features': '封面图重要，正文要分段，@相关账号',
                'adapted_content': f'【小红书版本】\n\n💡 {content[:100]}...\n\n（已调整为：口语化风格，添加emoji，分段排版，增加#话题标签）'
            },
            'zhihu': {
                'name': '知乎',
                'max_length': '不限，但建议3000字内',
                'style': '专业、逻辑严密、有深度',
                'features': '重视开头hook，多用数据和案例',
                'adapted_content': f'【知乎版本】\n\n{ncontent}\n\n（已调整为：学术化表达，增加数据支撑，添加参考文献格式）'
            }
        }
        
        config = platform_configs.get(target_platform, platform_configs['wechat'])
        
        return {
            'success': True,
            'data': {
                'platform': config['name'],
                'requirements': {
                    'max_length': config['max_length'],
                    'style': config['style'],
                    'features': config['features']
                },
                'adapted_content': config['adapted_content'],
                'optimization_tips': [
                    f'针对{config["name"]}的算法优化建议',
                    '发布时间建议：工作日晚上8-10点',
                    '互动引导：文末添加提问或投票'
                ]
            }
        }
    
    elif module == 'title_ab_test':
        topic = input_data.get('topic', '')
        
        return {
            'success': True,
            'data': {
                'topic': topic,
                'titles': [
                    {'title': f'{topic}完全指南：从入门到精通', 'score': 75, 'reason': '经典教程式标题，搜索友好'},
                    {'title': f'我研究了100个{topic}案例，总结了这5点', 'score': 92, 'reason': '数字化+权威性，点击率高'},
                    {'title': f'为什么别人{topic}能成功，你却不行？', 'score': 88, 'reason': '对比+悬念，引发好奇'},
                    {'title': f'{topic}的真相：90%的人都理解错了', 'score': 95, 'reason': '反常识+认知冲突，最强吸引力'},
                    {'title': f'2024最新{topic}实战手册', 'score': 82, 'reason': '时效性+实用性，中规中矩'}
                ],
                'best_title': f'{topic}的真相：90%的人都理解错了',
                'optimization_tips': [
                    '标题中加入数字可以提高20%点击率',
                    '使用"真相""秘密""背后"等词制造悬念',
                    '避免标题党，内容要支撑标题的承诺'
                ]
            }
        }
    
    return {'success': False, 'error': '未知模块'}


# 路由定义
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/topic-brainstorm')
def topic_brainstorm():
    return render_template('topic_brainstorm.html')


@app.route('/api/topic-brainstorm', methods=['POST'])
def api_topic_brainstorm():
    data = request.json
    result = mock_ai_response('topic_brainstorm', data)
    return jsonify(result)


@app.route('/viral-analysis')
def viral_analysis():
    return render_template('viral_analysis.html')


@app.route('/api/viral-analysis', methods=['POST'])
def api_viral_analysis():
    data = request.json
    result = mock_ai_response('viral_analysis', data)
    return jsonify(result)


@app.route('/platform-adaptation')
def platform_adaptation():
    return render_template('platform_adaptation.html')


@app.route('/api/platform-adaptation', methods=['POST'])
def api_platform_adaptation():
    data = request.json
    result = mock_ai_response('platform_adaptation', data)
    return jsonify(result)


@app.route('/title-ab-test')
def title_ab_test():
    return render_template('title_ab_test.html')


@app.route('/api/title-ab-test', methods=['POST'])
def api_title_ab_test():
    data = request.json
    result = mock_ai_response('title_ab_test', data)
    return jsonify(result)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    print("="*60)
    print("AI内容创作与发布分析系统 启动中...")
    print("访问地址: http://0.0.0.0:8081")
    print("="*60)
    
    app.run(host='0.0.0.0', port=8081, debug=True)
