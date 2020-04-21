import ulid
from django.db import models

# Create your models here.

class ULIDField(models.CharField):
    """ see https://qiita.com/ykiu/items/c288b99d0a1956e8ac9f """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 26
        super(ULIDField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'char(26)'

class UploadFile(models.Model):
    """アップロードされたファイルを表すモデル"""
    id = models.CharField(
        default=ulid.new,
        max_length=26,
        primary_key=True,
        editable=False
    )
    name = models.CharField(max_length=50)
    file = models.FileField('CSVファイル')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """ファイルのURLを返す"""
        return self.name