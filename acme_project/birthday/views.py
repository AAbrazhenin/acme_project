from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import BirthDayForm, CongratulationsForm
from .models import Birthday
from .utils import calculate_birthday_countdown


class BirthdayListView(ListView):
    model = Birthday
    queryset = Birthday.objects.prefetch_related(
        'tags'
    ).select_related('author')
    ordering = 'id'
    paginate_by = 10


class BirthdayMixIn:
    model = Birthday


class BirthdayFormMixIn:
    form_class = BirthDayForm


class BirthdayCreateView(
    LoginRequiredMixin,
    BirthdayFormMixIn,
    BirthdayMixIn,
    CreateView
):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class BirthdayUpdateView(
    LoginRequiredMixin,
    BirthdayFormMixIn,
    BirthdayMixIn,
    UpdateView
):

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Birthday, pk=kwargs['pk'])
        if instance.author != request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class BirthdayDeleteView(LoginRequiredMixin, BirthdayMixIn, DeleteView):

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Birthday, pk=kwargs['pk'])
        if instance.author != request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class BirthdayDetailView(DetailView):
    model = Birthday

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['birthday_countdown'] = calculate_birthday_countdown(
            self.object.birthday
        )
        context['form'] = CongratulationsForm()
        context['congratulations'] = (
            self.object.congratulations.select_related('author')
        )
        return context


@login_required
def add_comment(request, pk):
    birthday = get_object_or_404(Birthday, pk=pk)
    form = CongratulationsForm(request.POST)
    if form.is_valid():
        congratulations = form.save(commit=False)
        congratulations.author = request.user
        congratulations.birthday = birthday
        congratulations.save()
    return redirect('birthday:detail', pk=pk)
