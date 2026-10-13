# Software Reliability Assessment Tool
- https://github.com/rinsaka/PythonDjangoSRATool

## ライブラリのインストール

~~~
% pip list | grep ulid
% pip install -r requirements.txt
~~~

## データベースのマイグレーション

~~~
% python manage.py migrate
~~~

## Webサーバの起動

~~~
% python manage.py runserver
~~~

## Docker で実行したい場合
- Docker で実行したい場合は [https://github.com/rinsaka/DockerDjangoSRATool](https://github.com/rinsaka/DockerDjangoSRATool) を参照してください
