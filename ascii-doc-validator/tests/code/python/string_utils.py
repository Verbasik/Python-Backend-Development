# tests/code/python/string_utils.py
class StringUtils:
    """Утилитарные методы работы со строками."""

    @staticmethod
    def capitalize(input_str: str) -> str:
        if not input_str:
            return input_str
        return input_str[0].upper() + input_str[1:]

    @staticmethod
    def reverse(input_str: str) -> str:
        return input_str[::-1]