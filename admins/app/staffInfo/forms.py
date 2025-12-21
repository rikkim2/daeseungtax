from django.forms import ModelForm
from app.models import userProfile

class FileUploadForm(ModelForm):
  class Meta:
    model = userProfile
    fields = ['title','image','description']

    # save 메서드를 오버라이드합니다.
    def save(self, commit=True, *args, **kwargs):
        user_profile_instance = super().save(commit=False, *args, **kwargs)
        user = kwargs.pop('user', None)  # 'user' 인자를 안전하게 추출합니다.
        if user:
            user_profile_instance.user = user
        if commit:
            user_profile_instance.save()
        return user_profile_instance