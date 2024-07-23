from django.urls import path
from .views import TranscriptUploadView

urlpatterns = [
    path('upload/', TranscriptUploadView.as_view(), name='transcript-upload'),
]
