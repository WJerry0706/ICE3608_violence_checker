from django.urls import path
from UserInfo import views
from UserAuth import views as auth_model

app_name = "UserInfo"
urlpatterns = [
    path("index/<int:pk>/", views.index, name='index'),
    path("resume/", views.resume, name="resume"),
    path("application/", views.apply, name='application'),
    path("myposition/", views.my_published_position, name='my_position'),
    path("info/", views.info, name='user_info'),
    path("account/", views.account, name='account'),
    path("logout/", auth_model.logout),
    path("modify/", views.modify, name='modify'),
    path("upload/", views.image_upload, name='image_upload'),
    path("resume_upload/", views.resume_upload, name="resume_upload"),
    path("resume_download/", views.resume_download),
    path('resume_remove/<int:rid>/', views.remove_resume, name="resume_remove"),
    path('show_index/', views.show_index),
    path('sendemail/', views.sendemail),
]
