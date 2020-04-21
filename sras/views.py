import os
import pandas as pd
import math
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse

from .models import UploadFile
from .forms import UploadForm

from sras.modules import nhpp_analyst
from sras.modules import dmalt_analyst

# Create your views here.

class FileIndexView(generic.ListView):
    model = UploadFile
    template_name = 'sras/index.html'
    queryset = UploadFile.objects.order_by('-updated_at')

class UploadView(generic.FormView):
    """ モデルを使わずにアップロードするビュー """
    model = UploadFile
    form_class = UploadForm
    template_name = 'sras/upload.html'
    # success_url = reverse_lazy('sras:index')

    def form_valid(self, form):
        # アップロードファイルをストレージに保存する
        # file_names = ('ストレージでの保存名', 'クライアントでのオリジナル名')
        file_names = form.store_to_storage()
        # モデルを構築してデータベースに保存する
        f = UploadFile(file=file_names[0], name=file_names[1])
        f.save()
        messages.success(self.request, "アップロードしました．ID は " + str(f.id) + " です")
        return redirect('sras:show', f.id)

class ShowSrmView(generic.DetailView):
    model = UploadFile
    template_name = 'sras/show.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uploadfile = context.get("object")
        # do something

        uploadfile.df = open_csv_file(uploadfile.file.name)
        uploadfile.df_html = df2html(uploadfile)

        # Google Chart 用にカンマ区切り文字列にする
        uploadfile.xdata = df2text(uploadfile.df.iloc[:, 0])
        uploadfile.ydata = df2text(uploadfile.df.iloc[:, 1])
        uploadfile.xlabel = uploadfile.df.columns[0]
        uploadfile.ylabel = uploadfile.df.columns[1]

        # メトリクス数（列数）を取得する
        uploadfile.n_metrics = self.getNumberOfMetrics(uploadfile)
        # メトリクスの列名ラベルを取得する
        uploadfile.label_metrics = self.getLabelsOfMetrics(uploadfile)
        # フォールト数の最大値を取得する（初期値に設定する）
        (uploadfile.max_tData, uploadfile.maxDefects) = self.getMaxDataXY(uploadfile)
        # 横軸の最大値を取得する
        uploadfile.max_tPrediction = self.getMaxX(uploadfile)
        # print(uploadfile.max_tData, uploadfile.max_tPrediction, uploadfile.maxDefects)
        # 推定用と予測用の str_tData, str_yData, str_tPrediction を取得する
        (uploadfile.str_tData, uploadfile.str_yData, uploadfile.str_tPrediction) = self.getStrXY(uploadfile)

        return context

    def getNumberOfMetrics(self, uploadfile):
        """ メトリクス数を返す """
        col = uploadfile.df.shape[1] - 2 # サイズを取り出す
        return col
    def getLabelsOfMetrics(self, uploadfile):
        """ メトリクスのラベル名リスト """
        labels = uploadfile.df.columns[2:]
        return labels

    def getMaxDataXY(self, uploadfile):
        """ 推定の初期値用にフォールト数の最大値とそのXを取得する """
        (row,col) = uploadfile.df.shape # サイズを取り出す
        r = row -1
        while r > 0:  ## データの後半が nan の可能性があるので，最後の数値を取り出す
            maxDefects = uploadfile.df.iloc[r,1]
            if maxDefects > 0: ## nan でない
                maxDataX   = uploadfile.df.iloc[r,0]
                break
            r -= 1
        return (maxDataX, maxDefects)

    def getMaxX(self, uploadfile):
        # 横軸の最大値を取得する
        (row, col) = uploadfile.df.shape  # サイズを取り出す
        maxX = uploadfile.df.iloc[row-1, 0]
        # print(maxX)
        return maxX

    def getStrXY(self, uploadfile):
        """ 推定用に文字列にした t と y を準備する """
        str_tData = ''
        str_yData = ''
        str_tPrediction = ''
        for r in range(0, uploadfile.max_tData+1):
            str_tData = str_tData + str(uploadfile.df.iloc[r,0]) + ','
            str_yData = str_yData + str(uploadfile.df.iloc[r,1]) + ','
        for r in range(0, uploadfile.max_tPrediction+1):
            str_tPrediction = str_tPrediction+ str(uploadfile.df.iloc[r,0]) + ','
        # 最後のカンマを消去
        str_tData = str_tData[0:-1]
        str_yData = str_yData[0:-1]
        str_tPrediction = str_tPrediction[0:-1]
        return (str_tData, str_yData, str_tPrediction)

def analyst(request, uploadfile_id):
    """ 分析（推定） """


    if request.method == "POST":
        uploadfile = get_object_or_404(UploadFile, pk=uploadfile_id)

        # response = "POST request of uploadfile %s."
        # form = MyForm(data=request.POST)
        # if form.is_valid():
        #     pass
    else:
        messages.error(request, 'POST 以外のメソッドは許可されていません')
        redirect_url = reverse('sras:show', kwargs=dict(pk=uploadfile_id))
        return redirect(redirect_url)


    uploadfile.df = open_csv_file(uploadfile.file.name)

    # フォームからパラメータを取得する
    getPostParams(request, uploadfile)
    # ソフトウェア信頼性モデルのパラメータ推定
    if estimateSRM(request, uploadfile) == False:
        # 最適化に失敗したときは前のページに戻る
        return redirect(request.META['HTTP_REFERER'])

    # CSV 書き出し用のデータを準備する
    mkParamsCsvData(uploadfile)

    model = uploadfile.srmodel
    if model in ["nhpp_exp", "nhpp_earlang", "nhpp_ray", "nhpp_gamma", "nhpp_wei"]:
        # テーブル用のデータを作成する
        uploadfile.df_html = df2html(uploadfile)
        # テーブル拡大表示用のデータ（文字列形式）を作成する
        df2largeTable(uploadfile)

        # Google Chart用のデータを作成する
        mkChartDF(uploadfile)

        return render(request, 'sras/nhpp_analyst.html', {'uploadfile': uploadfile})
    elif model in ["dmalt_exp", "dmalt_earlang", "dmalt_ray", "dmalt_gamma", "dmalt_wei"]:
        # テーブル用のデータを作成する
        uploadfile.df_html = df2html(uploadfile)
        # テーブル拡大表示用のデータ（文字列形式）を作成する
        df2largeTable(uploadfile)

        # Google Chart用のデータを作成する
        mkChartDF(uploadfile)

        return render(request, 'sras/dmalt_analyst.html', {'uploadfile': uploadfile})
    else:
        return redirect(request.META['HTTP_REFERER'])
    # return HttpResponse(response % uploadfile.id)

def mkParamsCsvData(uploadfile):
    """ パラメータのCsv用データを生成する """
    uploadfile.str_result_csv = ""

    # 初期値
    uploadfile.str_result_csv += "Model," + uploadfile.srmodel + '|'
    uploadfile.str_result_csv += "Initial Value,-----|"
    uploadfile.str_result_csv += "init_a," + str(uploadfile.init_a) + '|'
    uploadfile.str_result_csv += "init_b," + str(uploadfile.init_b) + '|'
    if uploadfile.srmodel in ['nhpp_gamma', 'nhpp_wei', 'dmalt_gamma', 'dmalt_wei']:
        uploadfile.str_result_csv += "init_c," + str(uploadfile.init_c) + '|'

    for met in uploadfile.metrics_info:
        uploadfile.str_result_csv += met['name'] + "," + str(met['init']) + '|'

    uploadfile.str_result_csv += "Estimated Results,-----|"

    # 推定結果
    for key, value in uploadfile.result.items():
        uploadfile.str_result_csv += key + ',' + str(value) + '|'

    uploadfile.str_result_csv = uploadfile.str_result_csv[0:-1]

def analyst_table(request, uploadfile_id):
    """ 分析結果のテーブル拡大表示 """
    if request.method == "POST":
        uploadfile = get_object_or_404(UploadFile, pk=uploadfile_id)
        str_label= str(request.POST.get('label'))
        str_df = str(request.POST.get('df'))
    else:
        messages.error(request, 'POST 以外のメソッドは許可されていません')
        redirect_url = reverse('sras:index')
        return redirect(redirect_url)

    # データの最後の文字が'|'なら削除
    if str_df[-1] == '|':
        str_df = str_df[:-1]
    # カンマ区切りラベルをリストに変換
    labels = str_label.split(',')
    str_datas = str_df.split('|')

    # データフレームを作成する
    dim = len(labels)
    c = 0
    while c < dim:
        datas = str_datas[c].split(',')
        if c == 0:
            # データフレームを新規に作成
            uploadfile.df = pd.DataFrame({labels[c]:datas})
        else:
            # データフレームに列を追加
            uploadfile.df[labels[c]] = datas
        c += 1

    # データフレームをHTMLのTableに変換
    uploadfile.df_html = df2html(uploadfile)

    return render(request, 'sras/analyst_table.html', {'uploadfile': uploadfile})

def analyst_table_download(request, uploadfile_id):
    """ 分析結果のテーブルをCSVファイルとしてダウンロードする """
    if request.method == "POST":
        uploadfile = get_object_or_404(UploadFile, pk=uploadfile_id)
        str_label = str(request.POST.get('label'))
        str_df = str(request.POST.get('df'))
    else:
        messages.error(request, 'POST 以外のメソッドは許可されていません')
        redirect_url = reverse('sras:index')
        return redirect(redirect_url)

    # データの最後の文字が'|'なら削除
    if str_df[-1] == '|':
        str_df = str_df[:-1]
    # カンマ区切りラベルをリストに変換
    labels = str_label.split(',')
    str_csv_data = str_df.split('|')

    # レスポンスの設定
    response = HttpResponse(content_type='text/csv')
    filename = 'result_mean_value_function.csv'
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    writer = csv.writer(response)

    # ヘッダーの書き出し
    writer.writerow(labels)

    # データの書き出し
    for r in str_csv_data:
        csv_data = r.split(',')
        writer.writerow(csv_data)
    return response


def analyst_result_download(request, uploadfile_id):
    """ 分析結果のテーブルをCSVファイルとしてダウンロードする """
    if request.method == "POST":
        uploadfile = get_object_or_404(UploadFile, pk=uploadfile_id)
        str_result = str(request.POST.get('result'))
    else:
        messages.error(request, 'POST 以外のメソッドは許可されていません')
        redirect_url = reverse('sras:index')
        return redirect(redirect_url)

    # レスポンスの設定
    response = HttpResponse(content_type='text/csv')
    filename = 'result_parameters.csv'
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    writer = csv.writer(response)

    str_csv_data = str_result.split('|')
    # CSV の書き出し

    # filename
    writer.writerow(['filename',uploadfile.name])

    # 推定結果
    for r in str_csv_data:
        csv_data = r.split(',')
        writer.writerow(csv_data)

    return response



def analyst_mvfchart(request, uploadfile_id):
    """ 平均値関数のグラフを全画面表示 """
    if request.method == "POST":
        uploadfile = get_object_or_404(UploadFile, pk=uploadfile_id)
        uploadfile.xdata= str(request.POST.get('xdata'))
        uploadfile.ydata= str(request.POST.get('ydata'))
        uploadfile.hdata= str(request.POST.get('hdata'))
        uploadfile.xlabel= str(request.POST.get('xlabel'))
        uploadfile.ylabel= str(request.POST.get('ylabel'))
        uploadfile.hlabel= str(request.POST.get('hlabel'))
    else:
        messages.error(request, 'POST 以外のメソッドは許可されていません')
        redirect_url = reverse('sras:index')
        return redirect(redirect_url)
    return render(request, 'sras/analyst_mvf_chart.html', {'uploadfile': uploadfile})

def analyst_intensitychart(request, uploadfile_id):
    """ 強度関数のグラフを全画面表示 """
    if request.method == "POST":
        uploadfile = get_object_or_404(UploadFile, pk=uploadfile_id)
        uploadfile.xdata= str(request.POST.get('xdata'))
        uploadfile.ydata= str(request.POST.get('ydata'))
        uploadfile.hdata= str(request.POST.get('hdata'))
        uploadfile.xlabel= str(request.POST.get('xlabel'))
        uploadfile.ylabel= str(request.POST.get('ylabel'))
        uploadfile.hlabel= str(request.POST.get('hlabel'))
    else:
        messages.error(request, 'POST 以外のメソッドは許可されていません')
        redirect_url = reverse('sras:index')
        return redirect(redirect_url)
    return render(request, 'sras/analyst_intensity_chart.html', {'uploadfile': uploadfile})




class ShowChartView(generic.DetailView):
    model = UploadFile
    template_name = 'sras/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uploadfile = context.get("object")
        # do something

        uploadfile.df = open_csv_file(uploadfile.file.name)
        # uploadfile.df_html = df2html(uploadfile)

        # Google Chart 用にカンマ区切り文字列にする
        uploadfile.xdata = df2text(uploadfile.df.iloc[:, 0])
        uploadfile.ydata = df2text(uploadfile.df.iloc[:, 1])
        uploadfile.xlabel = uploadfile.df.columns[0]
        uploadfile.ylabel = uploadfile.df.columns[1]

        return context

class ShowTableView(generic.DetailView):
    model = UploadFile
    template_name = 'sras/table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uploadfile = context.get("object")
        # do something

        uploadfile.df = open_csv_file(uploadfile.file.name)
        uploadfile.df_html = df2html(uploadfile)

        return context

class DeleteSrmView(generic.DeleteView):
    """ 削除する """
    model = UploadFile
    success_url = reverse_lazy('sras:index')

    def delete(self, request, *args, **kwargs):
        self.object = uploadfile = self.get_object()
        delete_csv_file(uploadfile.file.name) ## CSV ファイルをディスクから削除する
        uploadfile.delete()
        messages.success(self.request, 'CSVファイルを削除しました')
        return redirect(self.get_success_url())

def open_csv_file(filename):
    """ CSV ファイルを開いてその中身を返す"""
    path = os.path.join(settings.MEDIA_ROOT, filename)
    df = pd.read_csv(path)

    return df
def delete_csv_file(filename):
    """ CSV ファイルを削除する """
    path = os.path.join(settings.MEDIA_ROOT, filename)
    result = os.remove(path)
    return result

def df2html(uploadfile):
    """
        Pandas の DataFrame を Bootstrap の HTML Table に変換する．
        df.to_html でも可能であるが，スタイルが決まらないので
        この関数で行う．
    """
    html = '<div class="table-responsive">\n<table class="table table-striped">\n<caption>'
    html += uploadfile.name
    html += '</caption>\n<thead>\n<tr>'
    for column in uploadfile.df.columns:
        html += '<th>' + column + '</th>'
    html += '</tr>\n</thead>\n'
    html += '<tbody>\n'

    (row,col) = uploadfile.df.shape # サイズを取り出す
    for r in range(0, row):
        html += '<tr>'
        for c in range(0, col):
            val = formatFloatValue(uploadfile.df.iloc[r,c]) # 実数なら桁数を揃える
            html += '<td>' + str(val) + '</td>'
        html += '</tr>\n'

    html += '</tbody></table></div>'
    return html

def formatFloatValue(val):
    """ val が実数なら，小数点以下の桁数を config 指定の桁数にする """
    type_val = type(val)
    format_string = '{:.' + str(settings.DISPLAY_DIGITS) + 'f}'   # '{:.2f}'
    if str(type_val) == "<class 'numpy.float64'>":  # str を付けないと判定できない
        val = format_string.format(val)
    ## 文字列の '3.14' の場合も実数とみなしてフォーマット
    elif str(type_val) == "<class 'str'>":
        if "." in val:
            val = format_string.format(float(val))
    return val

def df2text(dfdata):
    """ Google Chart 用に DataFrame を受け取って，カンマ区切り文字列に変換して返す """
    d_str = ""
    for d in dfdata:
        d_str += str(d) + ',' # カンマ区切りの文字列に変換
    # 最後のカンマを消去
    d_str = d_str[0:-1]
    return d_str

def getPostParams(request, uploadfile):
    """ フォームからパラメータを取得する"""
    uploadfile.srmodel = request.POST.get('srmodel')
    uploadfile.init_a = request.POST.get('init_a')
    uploadfile.init_b = request.POST.get('init_b')
    uploadfile.init_c = request.POST.get('init_c')
    uploadfile.max_tData = int(request.POST.get('max_tData'))
    uploadfile.max_tPrediction = int(request.POST.get('max_tPrediction'))
    # カンマ区切りデータをリストに変換
    uploadfile.tData = request.POST.get('str_tData').split(',')
    uploadfile.yData = request.POST.get('str_yData').split(',')
    uploadfile.tPrediction = request.POST.get('str_tPrediction').split(',')

    # リストの中身が文字列なので数値に変換
    iter = 0
    while iter < len(uploadfile.tData):
        uploadfile.tData[iter] = int(uploadfile.tData[iter])
        iter += 1
    # リストの中身が文字列なので数値に変換
    iter = 0
    while iter < len(uploadfile.yData):
        uploadfile.yData[iter] = float(uploadfile.yData[iter])
        iter += 1
    # リストの中身が文字列なので数値に変換
    iter = 0
    while iter < len(uploadfile.tPrediction):
        uploadfile.tPrediction[iter] = int(uploadfile.tPrediction[iter])
        iter += 1
    # メトリクスの数
    uploadfile.n_metrics = int(request.POST.get('n_metrics'))

    # メトリクスのパラメータ
    metrics_info = []
    iter = 1
    while iter <= uploadfile.n_metrics:
        metric = {}
        metric['name'] = uploadfile.df.columns[iter+1]
        metric['acumulation'] = request.POST.get(
            "acumulation_met" + str(iter))  # [None] or [on]
        metric['init'] = request.POST.get("init_met" + str(iter)) # [None] or 0.01
        metrics_info.append(metric)
        iter += 1
    uploadfile.metrics_info = metrics_info
    return True

def estimateSRM(request, uploadfile):
    """ ソフトウェア信頼性モデルのパラメータ推定を行う """
    model = uploadfile.srmodel
    if model in ["nhpp_exp", "nhpp_earlang", "nhpp_ray", "nhpp_gamma", "nhpp_wei"]:
        nhppanalyst = nhpp_analyst.NHPPanalyst(uploadfile=uploadfile)
        uploadfile.result = nhppanalyst.run(uploadfile)
        if uploadfile.success == True:
            messages.success(request, 'NHPPモデルのパラメータ推定に成功しました')
            return True
    elif model in ["dmalt_exp", "dmalt_earlang", "dmalt_ray", "dmalt_gamma", "dmalt_wei"]:
        dmaltanalyst = dmalt_analyst.DMALTanalyst(uploadfile=uploadfile)
        uploadfile.result = dmaltanalyst.run(uploadfile)
        if uploadfile.success == True:
            messages.success(request, 'DMALT モデルのパラメータ推定に成功しました')
            return True
    messages.error(request, 'パラメータ推定に失敗しました')
    return False

def mkChartDF(uploadfile):
    """ Google Chart 用にカンマ区切り文字列にする """
    (row,col) = uploadfile.df.shape # サイズを取り出す
    # 横軸
    uploadfile.xdata = df2text(uploadfile.df.iloc[:, 0])
    uploadfile.xlabel = uploadfile.df.columns[0]

    # 発見フォールト数（実測値）
    uploadfile.ydata = df2text(uploadfile.df.iloc[:, 1])
    uploadfile.ylabel = uploadfile.df.columns[1]

    # 平均値関数
    uploadfile.hdata = df2text(uploadfile.df.iloc[:, col-3]) # 右から3番目
    uploadfile.hlabel = uploadfile.df.columns[col-3]

    # 週毎の発見フォールト数（実測値）
    uploadfile.dydata = df2text(uploadfile.df.iloc[:, col-2]) # 右から2番目
    uploadfile.dylabel = uploadfile.df.columns[col-2]

    # 週毎の発見フォールト数（実測値）
    uploadfile.intensitydata = df2text(uploadfile.df.iloc[:, col-1]) # 右から1番目
    uploadfile.intensitylabel = uploadfile.df.columns[col-1]

def df2largeTable(uploadfile):
    columns = uploadfile.df.columns
    uploadfile.str_labels = ''
    for col in columns:
        uploadfile.str_labels += col + ','
    uploadfile.str_labels = uploadfile.str_labels[:-1] # 最後の','を削除

    (rows,cols) = uploadfile.df.shape
    uploadfile.str_datas = ""
    col = 0
    while col < cols:
        row = 0
        while row < rows:
            uploadfile.str_datas += str(uploadfile.df.iloc[row,col]) + ','
            row += 1
        uploadfile.str_datas = uploadfile.str_datas[:-1] # 最後の','を削除
        uploadfile.str_datas += '|'
        col += 1
    uploadfile.str_datas = uploadfile.str_datas[:-1] # 最後の'|'を削除

    # CSV 用のデータもここで仕込む
    uploadfile.str_csv_data = ""
    row = 0
    while row < rows:
        col = 0
        while col < cols:
            uploadfile.str_csv_data += str(uploadfile.df.iloc[row,col]) + ','
            col += 1
        uploadfile.str_csv_data = uploadfile.str_csv_data[:-1]  # 最後の ',' を削除
        uploadfile.str_csv_data += '|'
        row += 1
    uploadfile.str_csv_data = uploadfile.str_csv_data[:-1] # 最後の '|' を削除
