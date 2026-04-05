
## 1. Установка MinIO
```shell
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo cp minio /usr/local/bin
```

## 2. Создание директории для minio
```shell
sudo mkdir -p /mnt/data
sudo chown -R $USER:$USER /mnt/data/
```

## 3.  Запуск сервера

```shell
MINIO_PROMETHEUS_AUTH_TYPE="public" minio server /mnt/data
```

## 4. Создаение бакета
1. Переходим по адресу http://<MINIO_IP>:9000
2. Нажимаем "Create Bucket" и вводим имя data


