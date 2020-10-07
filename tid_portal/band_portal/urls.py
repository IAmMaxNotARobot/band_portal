from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token    # Getting_token

from . import views

app_name = 'band_portal'
urlpatterns = [
    path('', views.index, name='index'),
    path('projects/', views.projects, name='projects'),
    path('projects/<str:project_slug>/', views.project, name='project'),
    path('projects/<str:project_slug>/add-tabulature', views.project_add_tabulature, name='project_add_tabulature'),
    path('projects/<str:project_slug>/add-lyrics', views.project_add_lyrics, name='project_add_lyrics'),
    path('projects/<str:project_slug>/add-misc-file', views.project_add_resource_file, name='project_add_resource_file'),
    path('projects/<str:project_slug>/add-url', views.project_add_related_url, name='project_add_related_url'),
    path('projects/<str:project_slug>/add-event', views.project_add_event, name='project_add_event'),
    path('projects/<str:project_slug>/edit-statuses', views.project_edit_statuses, name='project_edit_statuses'),
    path('projects/<str:project_slug>/project-edit-name', views.project_edit_name, name='project_edit_name'),

    path('under-construction', views.under_construction, name='under_construction'),

    # Songs
    path('songs/', views.songs, name='songs'),
    path('songs/<str:song_artist>-<str:song_name>/', views.song, name='song'),
    path('songs/<str:song_artist>-<str:song_name>/edit', views.song_edit, name='song_edit'),
    path('songs/update/', views.song_update, name='song_update'),
    path('songs/live_list/', views.songs_live_list, name='songs_live_list'),
    path('songs/live_list/update', views.songs_live_list_update, name='songs_live_list_update'),
    path('songs/live_list_lookup/', views.songs_live_list_lookup, name='songs_live_list_lookup'),


    # Tabulatures
    path('tabulature/create', views.tabulature_create, name='tabulature_create'),
    path('tabulatures/', views.tabulatures, name='tabulatures'),
    path('tabulatures/<int:id>', views.tabulature, name='tabulature'),
    path('tabulatures/file_actuality/<int:id>', views.tabulature_file_actuality, name='tabulature_file_actuality'),
    path('tabulatures/file_delete/<int:id>', views.tabulature_file_delete, name='tabulature_file_delete'),
    path('tabulatures/file_add/<int:tabulature_id>', views.tabulature_file_add, name='tabulature_file_add'),

    # Lyrics
    path('lyrics_list/', views.lyrics_list, name='lyrics_list'),
    path('lyrics/<int:id>', views.lyrics, name='lyrics'),


    #   Functional urls
    path('projects/create', views.project_create, name='project_create'),
    path('songs/create', views.song_create, name='song_create'),

    # REST
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),  # Getting_token
    path('rest/live-list/all', views.rest_get_live_list),
]