from django.conf.urls import url

from solr_ranking_analysis import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
]
