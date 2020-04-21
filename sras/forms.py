import os
import random
import hashlib
from datetime import datetime
from django import forms
from django.core.files.storage import default_storage
from .models import UploadFile

class UploadForm(forms.Form):
    file = forms.FileField(label='CSVファイル', widget=forms.FileInput(
        attrs={'class':'form-control'}))

    def clean(self):
        data = super().clean()
        upload_file = data.get('file')
        ext = os.path.splitext(upload_file.name)[1]
        # print(upload_file)
        # print(ext)
        if not ext.lower() in ['.csv']:
            msg = "CSVファイルではありません"
            self.add_error('file', msg)
    def store_to_storage(self):
        """ ストレージフォルダにファイルを保存する処理 """
        upload_file = self.cleaned_data['file']

        # 現在の時刻を取得して unixtime (例：1584428130.388625) に変換
        now = datetime.now()
        now_ts = now.timestamp()
        # ランダムなハッシュを生成して unixtime とともにファイル名にする
        hash = hashlib.sha1(str(random.random()).encode("UTF-8")).hexdigest()
        new_file_name = str(now_ts) + '_' + str(hash)  + '.csv'

        # アップロードされたファイル (upload_file) を new_file_name という名前で保存する
        # 保存場所は media フォルダの直下
        # 同じファイルがあれば，自動的に後ろに何らかの文字列を追加してくれる
        # （ハッシュファイル名なので重複はありえないでしょう）
        # 実際に保存されたファイル名が file_name に格納される
        file_name = default_storage.save(new_file_name, upload_file)


        # ストレージへの保存ファイル名とクライアントのオリジナルファイル名を返す
        return (file_name, upload_file.name)