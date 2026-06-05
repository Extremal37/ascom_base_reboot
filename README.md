# ascom_base_reboot

Python-скрипт для последовательной перезагрузки Ascom/Avaya IP-DECT баз через веб-интерфейс (HTTP Digest, legacy TLS).

## Установка

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

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
