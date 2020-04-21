# Software Reliability Assessment Tool
- https://github.com/rinsaka/PythonDjangoSRATool

## ulid パッケージのインストール

~~~
% pip list | grep ulid
% pip install ulid-py
Collecting ulid-py
  Downloading https://files.pythonhosted.org/packages/ea/28/d81c57e6f39ac31e560c937968f9584ccc90fc9b32ab150475affc01486a/ulid_py-0.0.12-py2.py3-none-any.whl
Installing collected packages: ulid-py
Successfully installed ulid-py-0.0.12
% pip list | grep ulid
ulid-py                            0.0.12
%
~~~

## データベースのマイグレーション

~~~
% python manage.py migrate
~~~

## Webサーバの起動

~~~
% python manage.py runserver
~~~
