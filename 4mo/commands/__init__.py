# commands/__init__.py
import os
import importlib

__all__ = []

def register_commands(application):
    os.chdir("./commands")
    commands = [f for f in os.listdir() if f.endswith('.py') and f != '__init__.py']
    for command in commands:
        module_name = command[:-3]  # Удаляем .py
        module = importlib.import_module(f'{__name__}.{module_name}')  # Импортируем модуль
        if hasattr(module, 'register'):
            module.register(application)  # Вызов функции регистрации, если она есть
            __all__.append(module_name)
