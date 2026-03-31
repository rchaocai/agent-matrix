"""
条件保存脚本（占位）

实际逻辑在 skill_loader.py 的 _execute_conditional_skill 方法中实现
"""

import json
import argparse


def conditional_save(
    input_data: dict,
    conditions: dict = None
) -> dict:
    """
    条件保存（通过subprocess调用时的备用实现）

    Args:
        input_data: 输入数据（包含前序步骤的审核结果）
        conditions: 条件配置

    Returns:
        保存决策结果
    """
    if conditions is None:
        conditions = {}

    min_quality_score = conditions.get('min_quality_score', 60)
    require_safe = conditions.get('require_safe', True)
    skip_on_failure = conditions.get('skip_on_failure', True)

    should_save = True
    reasons = []

    # 检查质量评分
    score = input_data.get('overall_score') or input_data.get('quality_score', 0)
    if score < min_quality_score:
        should_save = False
        reasons.append(f"质量评分不足: {score} < {min_quality_score}")

    # 检查敏感词检测
    is_safe = input_data.get('is_safe', True)
    if 'sensitive_check' in input_data:
        is_safe = input_data['sensitive_check'].get('is_safe', True)

    if require_safe and not is_safe:
        should_save = False
        reasons.append("内容存在敏感词或违规内容")

    # 检查是否有错误
    if 'error' in input_data and skip_on_failure:
        should_save = False
        reasons.append(f"前序步骤出错: {input_data.get('error')}")

    result = {
        'should_save': should_save,
        'reasons': reasons,
        'skip': not should_save
    }

    if should_save:
        result['data'] = input_data

    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='条件保存工具')
    parser.add_argument('--input', required=True, help='输入数据（JSON字符串）')
    parser.add_argument('--conditions', help='条件配置（JSON字符串）')

    args = parser.parse_args()

    # 解析输入
    input_data = json.loads(args.input)
    conditions = json.loads(args.conditions) if args.conditions else {}

    # 执行条件判断
    result = conditional_save(input_data, conditions)

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
