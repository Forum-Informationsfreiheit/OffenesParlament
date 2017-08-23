from op_scraper.forms import CommentedContentForm
from op_scraper.models import User, CommentedContent
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from offenesparlament.constants import MESSAGES
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404

from django.core.mail import mail_admins

class SameUserMixin(object):
    def dispatch(self, request, *args, **kwargs):
        email = kwargs['email']
        key = kwargs['key']
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if key is not None and user.verification.verification_hash == key:
                if not pk or self.get_object().created_by == user:
                    return super(SameUserMixin, self).dispatch(
                        request, *args, **kwargs)


        message = MESSAGES.EMAIL.VERIFICATION_HASH_WRONG
        return render(request, 'subscription/login_attempted.html', {'message': message})

class CommentedContentCreate(SameUserMixin, CreateView):
    form_class = CommentedContentForm
    model = CommentedContent

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by=User.objects.get(email=self.kwargs['email'])
        obj.save()

        ka = {}
        ka.update(self.kwargs)
        ka['pk'] = obj.pk

        if not obj.admin_notification_sent:
            obj.admin_notification_sent=True
            mail_admins('[OffenesParlament] New CommentedContent to approve!',"""
                CommentedContent PK %d was saved and needs to be approved
                """ % obj.pk
                )
            obj.save()

        return HttpResponseRedirect(obj.get_edit_url())


class CommentedContentUpdate(SameUserMixin, UpdateView):
    form_class = CommentedContentForm
    model = CommentedContent

    def get_success_url(self):
        return self.object.get_edit_url()

class CommentedContentDelete(SameUserMixin, DeleteView):
    form_class = CommentedContentForm
    model = CommentedContent

def preview(request):
    text = request.POST['text']

    text = CommentedContent.sanitize_and_expand_text(text)

    return HttpResponse(text, mimetype='text/html')

def view(request, pk):
    cc = get_object_or_404(CommentedContent, pk=pk, approved_by__isnull=False)
    return render(request, 'op_scraper/commentedcontent_detail.html', {'commentedcontent': cc})

