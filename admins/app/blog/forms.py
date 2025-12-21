from django import forms
from app.models import BlogPost
from app.models import BlogComment
from app.models import BlogPostAttachment


class BlogPostForm(forms.ModelForm):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
        label='파일 첨부'
    )    
    # important_grade = forms.ChoiceField(
    #     choices=[('1', '매우중요'), ('2', '중요'), ('3', '기본'), ('4', '상식')],
    #     widget=forms.RadioSelect(),
    #     initial='3'  # 초기 선택 값을 설정합니다.
    # )
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'is_public', 'category', 'new_law', 'important_grade', 'youtube_url']
        labels = {
            'title': '제목',
            'content': '내용',
            'is_public': '공개 여부',
            'important_grade': '중요도',
            'new_law': '새로운 법률',
            'youtube_url': 'YouTube URL'
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'youtube_url': forms.TextInput(attrs={'class': 'form-control'}),
            'important_grade': forms.RadioSelect(),
            'is_public': forms.CheckboxInput(),
            'new_law': forms.CheckboxInput(),
        }



class CommentForm(forms.ModelForm):
    class Meta:
        model = BlogComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control text-area border-0', 'placeholder': 'Message'}),
        }    
class GuestCommentForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control border-0', 'placeholder': 'Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control border-0', 'placeholder': 'Mail'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control text-area border-0', 'placeholder': 'content'}))        

