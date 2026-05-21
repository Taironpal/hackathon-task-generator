from sympy import Rational, nsimplify, simplify
from sympy.parsing.sympy_parser import parse_expr

from backend.models import Task


def _to_expr(s: str):
    return parse_expr(s.replace(",", "."))


def _to_rational(s: str):
    """Парсим выражение и сразу переводим в точные рациональные числа."""
    return nsimplify(_to_expr(s), rational=True)


def answers_equal(expected: str, actual: str) -> bool:
    """Сравнить два математических выражения как точные рациональные числа."""
    try:
        return simplify(_to_rational(expected) - _to_rational(actual)) == 0
    except Exception:
        return False


def evaluate_expression(expression: str) -> str | None:
    """Вычислить выражение через sympy. Возвращает каноничную строку или None."""
    try:
        return str(_to_expr(expression))
    except Exception:
        return None


def validate_task_math(task: Task) -> list[str]:
    """Проверить математическую корректность задачи через sympy.

    Сценарии:
    - Если задано `expression` - вычисляем его и сверяем с `answer`.
    - Дополнительно: ответ должен быть целым или конечной десятичной дробью.

    Возвращает список найденных проблем (пустой = всё ок).
    """
    issues: list[str] = []

    if not task.expression:
        # без expression sympy-проверка невозможна - это не ошибка задачи,
        # а пропуск проверки. Пайплайн отметит метрикой.
        return issues

    try:
        computed = _to_rational(task.expression)
    except Exception as e:
        issues.append(f"expression не парсится sympy: {e}")
        return issues

    try:
        stated = _to_rational(task.answer)
    except Exception as e:
        issues.append(f"answer не парсится как число: {e}")
        return issues

    if simplify(computed - stated) != 0:
        issues.append(
            f"expression={task.expression} = {computed}, "
            f"но в answer указано {task.answer}"
        )
        return issues

    # Проверка «красоты» ответа: конечная десятичная дробь или целое
    try:
        if isinstance(computed, Rational):
            denom = computed.q
            # 2^a * 5^b → конечная десятичная
            d = denom
            for p in (2, 5):
                while d % p == 0:
                    d //= p
            if d != 1:
                issues.append(
                    f"ответ {computed} - бесконечная десятичная дробь "
                    f"(знаменатель {denom})"
                )
    except Exception:
        pass

    return issues
