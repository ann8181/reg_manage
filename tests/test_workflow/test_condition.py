"""
Workflow 条件评估测试
"""
import pytest


class TestConditionEvaluation:
    """测试条件评估"""

    def test_evaluate_condition_empty(self, workflow):
        """测试空条件返回 True"""
        result = workflow._evaluate_condition("", {})
        assert result is True

    def test_evaluate_condition_simple_greater(self, workflow):
        """测试简单大于条件"""
        result = workflow._evaluate_condition("x > 5", {"x": 10})
        assert result is True
        
        result = workflow._evaluate_condition("x > 5", {"x": 3})
        assert result is False

    def test_evaluate_condition_simple_equal(self, workflow):
        """测试相等条件"""
        result = workflow._evaluate_condition("x == 5", {"x": 5})
        assert result is True
        
        result = workflow._evaluate_condition("x == 5", {"x": 3})
        assert result is False

    def test_evaluate_condition_with_and(self, workflow):
        """测试 AND 条件"""
        result = workflow._evaluate_condition("x > 5 and y < 10", {"x": 10, "y": 5})
        assert result is True
        
        result = workflow._evaluate_condition("x > 5 and y < 10", {"x": 3, "y": 5})
        assert result is False

    def test_evaluate_condition_with_or(self, workflow):
        """测试 OR 条件"""
        result = workflow._evaluate_condition("x > 5 or y > 10", {"x": 3, "y": 15})
        assert result is True
        
        result = workflow._evaluate_condition("x > 5 or y > 10", {"x": 3, "y": 5})
        assert result is False

    def test_evaluate_condition_with_context(self, workflow):
        """测试带上下文变量的条件"""
        workflow.context = {"count": 10, "threshold": 5}
        
        result = workflow._evaluate_condition("count > threshold", workflow.context)
        assert result is True

    def test_evaluate_condition_unsafe_characters(self, workflow):
        """测试不安全字符被拒绝"""
        result = workflow._evaluate_condition("__import__('os').system('ls')", {})
        assert result is False

    def test_evaluate_condition_unsafe_import(self, workflow):
        """测试危险 import 被拒绝"""
        result = workflow._evaluate_condition("eval(__import__('os').popen('ls').read())", {})
        assert result is False

    def test_evaluate_condition_parentheses(self, workflow):
        """测试括号优先级"""
        result = workflow._evaluate_condition("(x > 5)", {"x": 10})
        assert result is True
        
        result = workflow._evaluate_condition("(x > 5) and (y > 5)", {"x": 10, "y": 3})
        assert result is False

    def test_evaluate_condition_string_comparison(self, workflow):
        """测试数值比较"""
        result = workflow._evaluate_condition("x != 5", {"x": 10})
        assert result is True
        
        result = workflow._evaluate_condition("x == 5", {"x": 5})
        assert result is True

    def test_evaluate_condition_error(self, workflow):
        """测试评估出错返回 False"""
        result = workflow._evaluate_condition("x !!! y", {"x": 1, "y": 2})
        assert result is False


class TestConditionEdgeCases:
    """测试条件边界情况"""

    def test_condition_with_extra_whitespace(self, workflow):
        """测试带多余空格的条件"""
        result = workflow._evaluate_condition("  x > 5  ", {"x": 10})
        assert result is True

    def test_condition_none_value(self, workflow):
        """测试值为 None"""
        result = workflow._evaluate_condition("x is None", {"x": None})
        assert result is True

    def test_condition_boolean(self, workflow):
        """测试布尔条件"""
        result = workflow._evaluate_condition("True", {})
        assert result is True
        
        result = workflow._evaluate_condition("False", {})
        assert result is False
