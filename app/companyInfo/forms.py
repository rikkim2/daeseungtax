from django.forms import ModelForm
from app.models import userProfile

class FileUploadForm(ModelForm):
  class Meta:
    model = userProfile
    fields = ['title','image','description']