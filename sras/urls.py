from django.urls import path

from . import views

app_name = 'sras'
urlpatterns = [
    # ファイルの一覧ページ
    path('', views.FileIndexView.as_view(), name='index'),

    # 通常のフォーム
    path('upload/', views.UploadView.as_view(), name='upload'),

    # 詳細表示ページ
    path('<str:pk>/', views.ShowSrmView.as_view(), name='show'),

    # 分析ページ
    # path('<str:pk>/analyst/', views.SrmAnalystView.as_view(), name='analyst'),
    path('<str:uploadfile_id>/analyst/', views.analyst, name='analyst'),
    path('<str:uploadfile_id>/analyst/download/', views.analyst_result_download, name='analyst_result_download'),

    # チャート表示ページ
    path('<str:pk>/chart/', views.ShowChartView.as_view(), name='chart'),
    path('<str:uploadfile_id>/analyst/mvfchart/', views.analyst_mvfchart, name='analyst_mvfchart'),
    path('<str:uploadfile_id>/analyst/intensitychart/', views.analyst_intensitychart, name='analyst_intensitychart'),

    # テーブル表示ページ
    path('<str:pk>/table/', views.ShowTableView.as_view(), name='table'),
    path('<str:uploadfile_id>/analyst/table/', views.analyst_table, name='analyst_table'),
    path('<str:uploadfile_id>/analyst/table/download/', views.analyst_table_download, name='analyst_table_download'),

    # 削除のページ
    path('<str:pk>/delete/', views.DeleteSrmView.as_view(), name='delete'),
]
