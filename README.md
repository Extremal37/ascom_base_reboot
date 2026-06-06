# ascom_base_reboot

Python-скрипт для последовательной перезагрузки Ascom/Avaya IP-DECT баз через веб-интерфейс (HTTP Digest, legacy TLS).

## Установка

Требуется Python 3.6+ (CentOS 7: `python3 --version`).

```bash
pip3 install -r requirements.txt
cp config.example.yaml config.yaml
```

На CentOS 7, если `pip3 install` не находит новые версии пакетов, сначала обновите pip:

```bash
pip3 install --upgrade 'pip<21' 'setuptools<50' wheel
pip3 install -r requirements.txt
```

Или установите зависимости из EPEL/SCL Python 3.8+.

Отредактируйте `config.yaml`: список баз, пароли и интервал между перезагрузками.

## Использование

```bash
# Перезагрузка всех баз из config.yaml
python reboot.py

# Другой конфиг
python reboot.py -c path/to/config.yaml

# Проверка авторизации одной базы
python login.py --url https://192.168.1.10:8023 --password "your-password"
```

## Конфигурация

```yaml
interval_seconds: 120
default_username: admin
default_port: 8023

bases:
  - name: base-1
    host: 192.168.1.10
    password: "secret"

  - name: base-2
    url: https://192.168.1.11:8023
    password: "secret"
```

`config.yaml` с паролями не коммитится (см. `.gitignore`).

## License

GPL-3.0 — см. [LICENSE](LICENSE).
