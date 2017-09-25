from django.db.models import Prefetch
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, ListView, RedirectView
from django.http import Http404

from .models import OS, Release, ReleaseFile


class DownloadLatestPython2(RedirectView):
    """ Redirect to latest Python 2 release """
    permanent = False

    def get_redirect_url(self, **kwargs):
        try:
            latest_python2 = Release.objects.latest_python2()
        except Release.DoesNotExist:
            latest_python2 = None

        if latest_python2:
            return latest_python2.get_absolute_url()
        else:
            return reverse('download')


class DownloadLatestPython3(RedirectView):
    """ Redirect to latest Python 3 release """
    permanent = False

    def get_redirect_url(self, **kwargs):
        try:
            latest_python3 = Release.objects.latest_python3()
        except Release.DoesNotExist:
            latest_python3 = None

        if latest_python3:
            return latest_python3.get_absolute_url()
        else:
            return reverse('download')


class DownloadBase:
    """ Include latest releases in all views """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'latest_python2': Release.objects.latest_python2(),
            'latest_python3': Release.objects.latest_python3(),
        })
        return context


class DownloadHome(DownloadBase, TemplateView):
    template_name = 'downloads/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            latest_python2 = Release.objects.latest_python2()
        except Release.DoesNotExist:
            latest_python2 = None

        try:
            latest_python3 = Release.objects.latest_python3()
        except Release.DoesNotExist:
            latest_python3 = None

        python_files = []
        for o in OS.objects.all():
            data = {
                'os': o,
            }
            if latest_python2 is not None:
                data['python2'] = latest_python2.download_file_for_os(o.slug)
            if latest_python3 is not None:
                data['python3'] = latest_python3.download_file_for_os(o.slug)
            python_files.append(data)

        context.update({
            'releases': Release.objects.downloads(),
            'latest_python2': latest_python2,
            'latest_python3': latest_python3,
            'python_files': python_files,
        })

        return context


class DownloadFullOSList(DownloadBase, ListView):
    template_name = 'downloads/full_os_list.html'
    context_object_name = 'os_list'
    model = OS


class DownloadOSList(DownloadBase, DetailView):
    template_name = 'downloads/os_list.html'
    context_object_name = 'os'
    model = OS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        release_files = ReleaseFile.objects.select_related(
            'os',
        ).filter(os=self.object)
        context.update({
            'os_slug': self.object.slug,
            'releases': Release.objects.released().prefetch_related(
                Prefetch('files', queryset=release_files),
            ).order_by('-release_date'),
            'pre_releases': Release.objects.published().pre_release().prefetch_related(
                Prefetch('files', queryset=release_files),
            ).order_by('-release_date'),
        })
        return context


class DownloadReleaseDetail(DownloadBase, DetailView):
    template_name = 'downloads/release_detail.html'
    model = Release
    context_object_name = 'release'

    def get_object(self):
        try:
            return self.get_queryset().select_related().get(
                slug=self.kwargs['release_slug']
            )
        except self.model.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manually add release files for better ordering
        context['release_files'] = []

        # Add source files
        context['release_files'].extend(
            list(self.object.files.filter(os__slug='source').order_by('name'))
        )

        # Add all other OSes
        context['release_files'].extend(
            list(
                self.object.files.exclude(
                    os__slug='source'
                ).order_by('os__slug', 'name')
            )
        )

        return context
