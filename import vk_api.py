import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
import io

TOKEN = 'vk1.a.UWuFFMPL_k2HMuSbAHNypDNbnWR8jJi-TnvcGPnPss0JeCcidSoCADNUXJ0zgimbp6xhxmIxNz_kEmR7Y2Z8DHQHmMT49q8k4_WerUJppXoojS5TEDrzMraPdAaTvhTBxhICJLUZRySiB2MaBRuuqzkXZzL1qgR9X0G8OnhCx9VzLSex4GHULrzRt1-R__2Ex3YtCzsx8vkfCdtTB8iqvQ'

vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()
upload = VkUpload(vk_session)

def calculate_expression(expression):
    try:
        # sympify превращает строку в математический объект
        result = sp.sympify(expression)
        
        # Если результат — это дробь (как 100/3), вычисляем её до десятичного вида
        # .evalf(5) ограничит вывод до 5 знаков после запятой
        numeric_result = result.evalf(5) 
        
        return f"Ответ: {numeric_result}"
    except Exception as e:
        return "Ошибка в выражении."

def solve_equation(text_input):
    """
    Решает как одиночные уравнения, так и системы.
    Пример для системы: реши x + y = 5; x - y = 1
    """
    try:
        if ';' in text_input:
            eq_strings = text_input.split(';')
            equations = []
            all_symbols = set()
            
            for eq_str in eq_strings:
                if '=' in eq_str:
                    left, right = eq_str.split('=')
                    eq = sp.Eq(sp.sympify(left.strip()), sp.sympify(right.strip()))
                else:
                    eq = sp.Eq(sp.sympify(eq_str.strip()), 0)
                equations.append(eq)
                all_symbols.update(eq.free_symbols)
            
            solution = sp.solve(equations, list(all_symbols))
            return f"Решение системы {list(all_symbols)}: {solution}"
        
        else:
            if '=' in text_input:
                left, right = text_input.split('=')
                eq = sp.Eq(sp.sympify(left), sp.sympify(right))
            else:
                eq = sp.Eq(sp.sympify(text_input), 0)
            
            symbols = list(eq.free_symbols)
            if not symbols: return "Переменные не найдены."
            
            solution = sp.solve(eq, symbols[0])
            return f"Решение для {symbols[0]}: {solution}"

    except Exception as e:
        return "Ошибка. Для систем используйте ';' (напр: реши x+y=5; x-y=1)"
    

def create_graph(func_str):
    """Строит график функции и возвращает его в виде байтового потока."""
    try:
        x = sp.Symbol('x')
        func = sp.sympify(func_str)
        
        f = sp.lambdify(x, func, "numpy")
        
        # Генерируем точки
        x_vals = np.linspace(-10, 10, 400)
        y_vals = f(x_vals)
        
        plt.figure(figsize=(8, 6))
        plt.plot(x_vals, y_vals, label=f'y = {func_str}', color='#1f77b4', linewidth=2)
        plt.title('График функции', fontsize=14)
        plt.xlabel('X', fontsize=12)
        plt.ylabel('Y', fontsize=12)
        plt.axhline(0, color='black', linewidth=0.5)
        plt.axvline(0, color='black', linewidth=0.5)
        plt.grid(color='gray', linestyle='--', linewidth=0.5)
        plt.legend()
        
        # Сохраняем график в буфер памяти (чтобы не засорять диск файлами)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    except Exception as e:
        plt.close()
        return None

def send_message(user_id, message, attachment=None):
    """Отправляет текстовое сообщение и/или медиа пользователю."""
    vk.messages.send(
        user_id=user_id,
        message=message,
        attachment=attachment,
        random_id=0
    )

def send_graph_to_vk(user_id, buf, func_str):
    """Загружает график на серверы VK и отправляет пользователю."""
    try:
        photo = upload.photo_messages(photos=buf)[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        send_message(user_id, f"График для функции: y = {func_str}", attachment)
    except Exception as e:
        send_message(user_id, "Произошла ошибка при загрузке графика.")

def main():
    print("Бот запущен и ожидает сообщения...")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text.strip().lower()
            user_id = event.user_id

            if text in ['привет', 'start', '/start']:
                help_text = (
                    "Привет! 👋\n\n"
                    "Я математический бот.\n"
                    "Я умею:\n"
                    "• выполнять вычисления\n"
                    "• решать уравнения\n"
                    "• решать системы уравнений\n"
                    "• строить графики функций\n\n"
                    "Доступные команды:\n"
                    "посчитай 2+2*2\n"
                    "реши x**2-4=0\n"
                    "реши x+y=10; x-y=2\n"
                    "график x**2\n\n"
                    "Важно:\n"
                    "• используйте * для умножения\n"
                    "• используйте ** для степени\n"
                    "• системы уравнений разделяются символом ;\n\n"
                    "Для повторного просмотра справки напишите: помощь"
                )
                send_message(user_id, help_text)

            elif text.startswith('посчитай '):
                expression = text.replace('посчитай ', '')
                result = calculate_expression(expression)
                send_message(user_id, result)

            elif text.startswith('реши '):
                equation = text.replace('реши ', '')
                result = solve_equation(equation)
                send_message(user_id, result)

            elif text.startswith('график '):
                func = text.replace('график ', '')
                buf = create_graph(func)

                if buf:
                    send_graph_to_vk(user_id, buf, func)
                else:
                    send_message(
                        user_id,
                        "Ошибка построения графика. Проверьте правильность написания функции."
                    )

            elif text == 'помощь' or text == '/help':
                help_text = (
                    "Я математический бот 🤖\n\n"
                    "Доступные команды:\n\n"
                    "посчитай 2+2*2\n"
                    "реши x**2-4=0\n"
                    "реши x+y=10; x-y=2\n"
                    "график x**2\n\n"
                    "Важно:\n"
                    "• используйте * для умножения\n"
                    "• используйте ** для степени\n"
                    "• системы уравнений разделяются символом ;"
                )
                send_message(user_id, help_text)

            else:
                send_message(
                    user_id,
                    "Я не смог распознать запрос 😔\n"
                    "Пожалуйста, повторите запрос или напишите 'помощь'."
                )


if __name__ == '__main__':
    main()