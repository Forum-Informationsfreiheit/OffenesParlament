from .models import CommentedContent
from django.forms import ModelForm


class CommentedContentForm(ModelForm):
    class Meta:
        model = CommentedContent
        exclude = ['created_by', 'approved_by', 'approved_at', 'admin_notification_sent']

