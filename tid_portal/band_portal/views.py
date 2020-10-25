from django.utils.translation import gettext as _
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.contrib.auth.models import User

from loguru import logger
from datetime import datetime
import sys
import os

from .exceptions import *
from tid_portal import settings
from .forms import TabulatureForm
from .models import *
from .views_rest import *
from .services import *

__all__ = []

logger.add(settings.BASE_DIR + "/debug.log", format="{time} {level} {message}", rotation="2 week", compression="zip")


def base_view(view):
    """ Handle all unhandled exceptions """


    def inner(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except Exception as e:
            logger.error("{} {}".format(sys.exc_info()[0], e))
            #raise Http404('Unexpected error!')
    return inner

@base_view
@login_required
def index(request):
    """ Show dashboard page with played songs, live list songs, last several project events, not played songs   """


    songs = Song.objects.played_on_practice()
    live_songs = Song.objects.live_list()
    last_events = ProjectEvent.objects.last_events()
    unplayed_songs = Song.objects.not_played()
    context = {
        "songs": songs,
        "last_events": last_events,
        "live_songs": live_songs,
        "unplayed_songs": unplayed_songs
    }
    return render(request, 'band_portal/index.html', context)


@base_view
@login_required
def projects(request):
    """ Show all projects """


    projects = Project.objects.all()
    context = {"projects" : projects}
    return render(request, 'band_portal/projects.html', context)


@base_view
@login_required
def project(request, project_slug):
    """ Show project parameters, related objects and events """


    project = Project.objects.get(slug=project_slug)
    events = ProjectEvent.objects.owned_by_project(project.id)
    resource_files = ProjectResourceFile.objects.owned_by_project(project.id)
    related_urls = ProjectRelatedURL.objects.owned_by_project(project.id)
    tasks = ProjectTask.objects.owned_by_project(project.id)
    context = {
        "project" : project,
        "events": events,
        "resource_files": resource_files,
        "related_urls": related_urls,
        "tasks": tasks,
    }
    return render(request, 'band_portal/project.html', context)


@base_view
@login_required
def project_edit_name(request, project_slug):
    """ Edit project name """


    project = Project.objects.get(slug=project_slug)
    context = {"project": project}
    if(request.method == "POST"):
        try:
            project_slug = ProjectManager.project_rename(request.POST, project)
            if project_slug:
                return HttpResponseRedirect(reverse('band_portal:project', args=(project_slug,)))
        except ProjectNameAllreadyExists:
            error_message = _("Name allready exists. Choose another name!")
            context["error_message"] = error_message
    return render(request, 'band_portal/project_edit_name.html', context)


@base_view
@login_required
def project_create(request):
    """ Create new empty project """


    if (request.method == 'POST'):
        project_slug = ProjectManager.project_create(request.POST)
        if project_slug:
            return HttpResponseRedirect(reverse('band_portal:project', args=(project_slug,)))
    return render(request, 'band_portal/project_create.html')


@base_view
@login_required
def project_add_tabulature(request, project_slug):
    """ Create or choose existing tabulature for project """


    project = Project.objects.get(slug=project_slug)
    tabulatures = Tabulature.objects.all()
    context = {"project" : project, "tabulatures": tabulatures}
    if (request.method == 'POST'):
        create_success = ProjectManager.add_tabulature(project_slug, request.POST, request.FILES)
        if create_success:
            return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    return render(request, 'band_portal/project_add_tabulature.html', context)


@base_view
@login_required
def project_add_lyrics(request, project_slug):
    """ Create or choose existing lyrics for project """


    project = Project.objects.get(slug=project_slug)
    lyrics_list = Lyrics.objects.all()
    context = {"project" : project, "lyrics_list": lyrics_list}
    if (request.method == 'POST'):
        create_success = ProjectManager.add_lyrics(project_slug, request.POST, request.FILES)
        if create_success:
            return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    return render(request, 'band_portal/project_add_lyrics.html', context)


@base_view
@login_required
def project_add_resource_file(request, project_slug):
    """ Create related to project resource file """


    project = Project.objects.get(slug=project_slug)
    context = {"project" : project}
    if (request.method == 'POST'):
        create_success = ProjectResourceFileManager.create_project_resource_file(project_slug, request.POST, request.FILES)
        if create_success:
            return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    return render(request, 'band_portal/project_add_resource_file.html', context)


@base_view
@login_required
def project_add_related_url(request, project_slug):
    """ Create related to project URL """


    project = Project.objects.get(slug=project_slug)
    context = {"project" : project}
    if (request.method == 'POST'):
        create_success = ProjectURLManager.create_project_related_url(project_slug, request.POST)
        if create_success:
            return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    return render(request, 'band_portal/project_add_related_url.html', context)


@base_view
@login_required
def project_add_event(request, project_slug):
    """ Event note creation view and functionality """


    project = Project.objects.get(slug=project_slug)
    context = {"project" : project}
    if (request.method == 'POST'):
        create_success = ProjectEventManager.create_event(request.POST, project_slug, request.user)
        if(create_success):
            return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    return render(request, 'band_portal/project_add_event.html', context)


@base_view
@login_required
def project_edit_statuses(request, project_slug):
    """ Show project statuses for changing them """


    project = Project.objects.get(slug=project_slug)
    status_values = StatusValue.objects.all()
    context = {"project" : project, "status_values": status_values}
    if (request.method == 'POST'):
        create_success = ProjectEventManager.create_event_by_status(request.POST, project_slug, request.user)
        if(create_success):
            return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    return render(request, 'band_portal/project_edit_status.html', context)


@base_view
@login_required
def songs(request):
    """ Show all songs """


    songs = Song.objects.order_by('artist', 'name')
    context = {"songs": songs}
    return render(request, 'band_portal/songs.html', context=context)


@base_view
@login_required
def song(request, song_artist, song_name):
    """ Show song parameters, lyrics and tabulatures """

    song = Song.objects.get(artist = song_artist, name = song_name)
    context = {"song": song}
    return render(request, 'band_portal/song.html', context=context)


@base_view
@login_required
def song_edit(request, song_artist, song_name):
    """ Edit existing song """

    song = Song.objects.get(artist = song_artist, name = song_name)
    tabulatures = Tabulature.objects.all()
    lyrics_list = Lyrics.objects.all()
    context = {
        "song": song,
        "tabulatures": tabulatures,
        "lyrics_list": lyrics_list,
    }
    return render(request, 'band_portal/song_editor.html', context=context)


@base_view
@login_required
def song_create(request):
    """ Create new song with tabulature and lyrics """

    tabulatures = Tabulature.objects.all()
    lyrics_list = Lyrics.objects.all()
    context = {
        "tabulatures": tabulatures,
        "lyrics_list": lyrics_list,
    }
    return render(request, 'band_portal/song_editor.html', context=context)


@base_view
@login_required
def song_update(request):
    """ Update song parameters """


    if (request.method == 'POST'):
        SongManager.update_song_by_post_data(request.POST, request.FILES)
    return HttpResponseRedirect(reverse('band_portal:songs'))


@base_view
@login_required
def songs_live_list(request):
    """ Show live songs and other played songs for managing """


    live_songs = Song.objects.live_list()       #Song.objects.filter(live_position__gt=0).order_by('live_position')
    all_songs = Song.objects.played_only_on_practice()
    context = {"live_songs": live_songs, "all_songs": all_songs}
    return render(request, 'band_portal/songs_live_list.html', context)


@base_view
#@login_required
def songs_live_list_lookup(request):
    """ Show live list """


    live_songs = Song.objects.filter(live_position__gt=0).order_by('live_position')
    context = {"live_songs": live_songs}
    return render(request, 'band_portal/songs_live_list_lookup.html', context)


@base_view
@login_required
def songs_live_list_update(request):
    """ Update live list content and ordering """


    if (request.method == 'POST'):
        SongManager.live_list_update(request.POST)
    return HttpResponseRedirect(reverse('band_portal:songs_live_list'))


@base_view
@login_required
def tabulature_create(request):
    """ Create tabulature view """


    if(request.method == 'POST'):
        create_success = TabulatureManager.create_tabulature_by_post(request.POST, request.FILES)
        if create_success:
            return HttpResponseRedirect(reverse('band_portal:tabulatures'))

    form = TabulatureForm()
    context = {"form": form}
    return render(request, 'band_portal/tabulature_create.html', context)


@base_view
@login_required
def tabulatures(request):
    """ Show list of all tabulatures """


    tabulatures = Tabulature.objects.all()
    context = {'tabulatures': tabulatures}
    return render(request, 'band_portal/tabulatures.html', context)


@base_view
@login_required
def tabulature(request, id):
    """ Show Tabulature with all related files   """


    tabulature = Tabulature.objects.get(pk=id)
    tabulature_files =  TabulatureFile.objects.owned_by_project(tabulature) #filter(tabulature = tabulature).order_by('-is_actual', 'pub_date')
    project = Project.objects.filter(tabulature_id = tabulature.id).first()
    song = Song.objects.filter(tabulature_id = tabulature.id).first()
    context = {
        "tabulature": tabulature,
        "tabulature_files": tabulature_files,
    }
    if(project):
        context["project"] = project
    if(song):
       context["song"] = song
    return render(request, 'band_portal/tabulature.html', context)


@base_view
@login_required
def tabulature_file_actuality(request, id):
    """ Toggle tabulature file actuality """

    tabulature_file = TabulatureFile.objects.get(pk=id)
    tabulature_id = tabulature_file.tabulature.id
    TabulatureManager.file_actuality_change(id)
    return HttpResponseRedirect(reverse('band_portal:tabulature', args=(tabulature_id,)))


@base_view
@login_required
def tabulature_file_delete(request, id):
    """ Delete one file from tabulature set """


    tabulature_file = TabulatureFile.objects.get(pk=id)
    tabulature_id = tabulature_file.tabulature.id
    TabulatureManager.file_delete(id)
    return HttpResponseRedirect(reverse('band_portal:tabulature', args=(tabulature_id,)))


@base_view
@login_required
def tabulature_file_add(request, tabulature_id):
    """ Tabulature file add view """


    if (request.FILES):
        TabulatureManager.file_add(tabulature_id, request.FILES)
    return HttpResponseRedirect(reverse('band_portal:tabulature', args=(tabulature_id,)))


@base_view
@login_required
def tabulatures_download_actual(request):
    """ create tabullatures archive for downloading """

    archive_path = TabulatureManager.tabulature_archive(request.user.username, 1)
    if os.path.exists(archive_path):
        with open(archive_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(archive_path)
            return response

    raise Http404


@base_view
@login_required
def tabulatures_download_notactual(request):
    """ create tabullatures archive for downloading """

    archive_path = TabulatureManager.tabulature_archive(request.user.username, 2)
    if os.path.exists(archive_path):
        with open(archive_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(archive_path)
            return response

    raise Http404


@base_view
@login_required
def project_completed_tasks(request, project_slug):
    """ show completed tasks for project """

    project = Project.objects.get(slug=project_slug)
    completed_tasks = ProjectTask.objects.finished_by_project(project.id)
    context = {"completed_tasks": completed_tasks, "project": project}
    return render(request, 'band_portal/project_completed_tasks.html', context)


@base_view
@login_required
def user_tasks(request):
    """ show completed tasks for project """

    user = request.user
    tasks = ProjectTask.objects.owned_by_user(user, False)
    completed_tasks = ProjectTask.objects.owned_by_user(user, True)
    context = {"completed_tasks": completed_tasks, "tasks": tasks}
    return render(request, 'band_portal/user_tasks.html', context)


@base_view
@login_required
def project_add_task(request, project_slug):
    """ Add task to related to project"""

    project = Project.objects.get(slug=project_slug)
    users = User.objects.filter(is_superuser=False)
    if(request.method == "POST"):
        ProjectTaskManager.create_from_post(request.POST, project)
        return HttpResponseRedirect(reverse('band_portal:project', args=(project.slug,)))
    context = {"project": project, "users": users}
    return render(request, 'band_portal/project_add_task.html', context)


@base_view
@login_required
def project_toggle_finished_task(request, project_slug):
    pass


@base_view
@login_required
def lyrics_list(request):
    """ List of lyrics files """


    pass


@base_view
@login_required
def lyrics(request, id: int):
    """ Concrete lyrics file """


    pass


@base_view
@login_required
def under_construction(request):
    """ Dummy view """


    return HttpResponse('Functionality not ready yet!')


@base_view
@login_required
def tasks_toggle_status(request):
    """ toggle is_finished status of a task and redirects to the tasks page """

    if(request.method == "POST"):
        task_id = request.POST["task_id"]
        project_task = ProjectTask.objects.get(id=task_id)
        project_task.is_finished = not project_task.is_finished
        project_task.save()

    return HttpResponseRedirect(reverse('band_portal:user_tasks'))


@base_view
@login_required
def project_task_toggle_status(request):
    """ """
    return HttpResponseRedirect()



