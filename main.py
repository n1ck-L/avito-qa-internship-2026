
import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Запуск тестов с поддержкой прокси')
    parser.add_argument('--proxy', nargs='?', const='auto', default='none',
                        help='Режим прокси: auto (автопоиск), ip:port (конкретный), или не указывать для работы без прокси')
    args = parser.parse_args()

    # Определяем режим прокси
    proxy_mode = args.proxy
    if proxy_mode is None:
        proxy_mode = 'none'
    elif proxy_mode == 'auto':
        proxy_mode = 'auto'
    # иначе считаем, что это строка вида ip:port

    cmd = [sys.executable, '-m', 'pytest', '-v', '--tb=no']

    # Передаём режим через переменную окружения
    env = os.environ.copy()
    env['TEST_PROXY_MODE'] = proxy_mode
    # PYTHONUTF8 нужен для корректной записи HTML-отчёта
    env['PYTHONUTF8'] = '1'

    try:
        result = subprocess.run(cmd, env=env)
    except FileNotFoundError:
        print("Ошибка: pytest не найден. Убедитесь, что он установлен в данном окружении.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при запуске: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(result.returncode)

if __name__ == '__main__':
    main()