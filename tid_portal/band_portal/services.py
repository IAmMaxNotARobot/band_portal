from django.utils.translation import gettext as _
from django.contrib.auth.models import User

import uuid
from loguru import logger
from datetime import datetime
from slugify import slugify
import os
import shutil
import re
from zipfile import ZipFile

from .exceptions import *
from .models import *
from .logic import *
from .forms import *
from tid_portal import settings

__all__ = ['SongManager', 'ProjectEventManager', 'ProjectManager', 'TabulatureManager',
           'ProjectResourceFileManager', 'ProjectURLManager', 'ProjectTaskManager']

logger.add(settings.BASE_DIR + "/debug.log", format="{time} {level} {message}", rotation="2 week", compression="zip")


class SongManager():
    """ Manages songs - create/update songs, manage live list content and ordering """


    @staticmethod
    def update_song_by_post_data(request_POST: dict, request_FILES: dict) -> bool:
        """ Check request data and update song. Return True on successifully save, otherwise False """

        song_id = request_POST.get('song_id', False)
        song_name = request_POST.get('song_name', False)
        song_tempo = request_POST.get('song_tempo', False)
        song_artist = request_POST.get('song_artist', False)
        if(song_id):
            song = Song.objects.get(pk = song_id)
            logger.info("Updating existing song by POST data")
        elif(song_name and song_tempo and song_artist):
            song = Song()
            logger.info("Creating song by POST data")

        if(song):
            song.played_now = request_POST.get('song_played', False)
            song.artist = song_artist
            song.name = song_name
            song.tempo = song_tempo
            # Handle tab
            song_tabulature = request_POST.get('song_tabulature', False)
            if(request_FILES and 'song_tabulature_file' in request_FILES):
                song_tabulature_file = request_FILES['song_tabulature_file'] #.POST.get('song_tabulature_file', False)
            if(song_tabulature and song_tabulature != 'None'):
                song.tabulature = Tabulature.objects.get(pk = song_tabulature)
            elif(request_FILES and 'song_tabulature_file' in request_FILES and song_tabulature_file):
                tabulature = Tabulature()
                tabulature.name = "{} - {}".format(song.artist, song.name)
                tabulature.save()
                tabulature.create_tabulature_file(song_tabulature_file, True)
                song.tabulature = tabulature
            else:
                song.tabulature = None

            song_lyrics = request_POST.get('song_lyrics', False)
            if(song_lyrics and song_lyrics != 'None'):
                song.lyrics = Lyrics.objects.get(pk = song_lyrics)
            elif (request_FILES and 'song_lyrics_file' in request_FILES):
                song_lyrics_file = request_FILES['song_lyrics_file']
                lyrics = Lyrics()
                lyrics.file.save(song_lyrics_file.name, song_lyrics_file)
                lyrics.save()
                song.lyrics = lyrics
            else:
                song.lyrics = None
            #
            song.save()
            return True
        return False

    @staticmethod
    def live_list_update(request_POST: dict) -> bool:
        """ Update live list ordering """

        ordering = request_POST.get('ordering', False)
        songs = Song.objects.all()
        for song in songs:
            song.live_position = 0
            song.save()
        position = 1
        for i in ordering.split(','):
            song = Song.objects.get(pk=i)
            song.live_position = position
            song.save()
            position+=1


class ProjectEventManager:
    """ Manages ProjectEvents creation"""


    @staticmethod
    def create_event(request_POST: dict, project_slug: str, user: User) -> bool:
        """ Create project event by user note """

        project = Project.objects.get(slug=project_slug)
        logger.info("Creating new event for project {project.name}")
        projectevent_note = request_POST.get('projectevent_note', False)
        if (projectevent_note):
            project_event = ProjectEvent()
            project_event.author = user
            project_event.note = projectevent_note.strip()
            project_event.project = project
            project_event.pub_date = datetime.now()
            project_event.save()
            return True
        return False

    @staticmethod
    def create_event_by_status(request_POST: dict, project_slug: str, user: User) -> bool:
        """ Create project event by user note """

        project = Project.objects.get(slug=project_slug)
        logger.info("Creating new event by status change for project {project.name}")
        projectevent_note = ""
        status_changed = False

        status_categories = StatusCategory.objects.order_by('id')
        for category in status_categories:
            current_project_status = ProjectStatusCategory.objects.filter(project=project, category_id=category.id).first()
            value = request_POST["status_{}".format(category.id)]
            if(current_project_status.status.id != int(value)):
                current_project_status.status = StatusValue.objects.get(id=value)
                current_project_status.save()
                projectevent_note = "{}\n{}: {} {}.".format(projectevent_note,
                                                           current_project_status.category,
                                                           _("status changed to"),
                                                           current_project_status.status)
                status_changed = True
        if (projectevent_note):
            project_event = ProjectEvent()
            project_event.author = user
            project_event.note = projectevent_note.strip()
            project_event.project = project
            project_event.pub_date = datetime.now()
            if (status_changed):
                project_event.save()
            return True
        return False


class ProjectManager:
    """ Manages Project creation """


    @staticmethod
    def project_create(request_POST: dict) -> str:
        """ Create new project from POST request """

        logger.info("Creating new project")
        project_name = request_POST.get('project_name', False)
        if (project_name):
            project = Project()
            project.name = project_name
            project.slug = slugify(project_name)
            project.save()
            return project.slug
        return ""

    @staticmethod
    def project_rename(request_POST: dict, project: Project):
        """ Rename existing project by POST request """

        logger.info("Renaming project")
        project_name = request_POST.get('project_name', False)
        check_project = Project.objects.filter(name=project_name).first()
        if(check_project):
            raise ProjectNameAllreadyExists
        if (project_name):
            project.name = project_name
            project.slug = slugify(project_name)
            project.save()
            return project.slug
        return ""

    @staticmethod
    def add_lyrics(project_slug: str, request_POST: dict, request_FILES: dict) -> bool:
        """ Create new Lyrics or add existing to project """

        logger.info("Adding lyrics to project")
        project = Project.objects.get(slug=project_slug)
        project_lyrics = request_POST.get('project_lyrics', False)
        if (project_lyrics and project_lyrics != 'None'):
            project.lyrics = Lyrics.objects.get(pk=project_lyrics)
        elif (request_FILES and 'project_lyrics_file' in request_FILES):
            project_lyrics_file = request_FILES['project_lyrics_file']
            lyrics = Lyrics()
            lyrics.file.save(project_lyrics_file.name, project_lyrics_file)
            lyrics.save()
            project.lyrics = lyrics
        else:
            project.lyrics = None
        project.save()
        return True

    @staticmethod
    def add_tabulature(project_slug: str, request_POST: dict, request_FILES: dict) -> bool:
        """ Create tabulature related to project   """

        logger.info("Adding tabulature to project")
        project = Project.objects.get(slug=project_slug)
        project_tabulature = request_POST.get('project_tabulature', False)
        if(project_tabulature and project_tabulature != 'None'):
            tabulature = Tabulature.objects.get(id=project_tabulature)
            project.tabulature = tabulature
        elif(request_FILES and 'project_tabulature_file' in request_FILES):
            project_tabulature_file = request_FILES['project_tabulature_file']
            tabulature = Tabulature()
            tabulature.name = "{}".format(project.name)
            tabulature.save()
            tabulature.create_tabulature_file(project_tabulature_file, True)
            project.tabulature = tabulature
        else:
            project.tabulature = None
        project.save()
        return True


class TabulatureManager:
    """ Manages Tabulatures and tabulature files """


    @staticmethod
    def create_tabulature_by_post(request_POST: dict, request_FILES: dict):
        """ Create new tabulature with new tabulature file """

        logger.info("Creating new tabulature with file")
        form = TabulatureForm(request_POST, request_FILES)
        if(form.is_valid()):
            tab_name = form.data['tab_name']
            tab_file = request_FILES['tab_file']
            tabulature = Tabulature()
            tabulature.name = tab_name
            tabulature.save()
            tabulature.create_tabulature_file(tab_file, True)

    @staticmethod
    def file_actuality_change(tabulature_file_id: uuid.UUID):
        """ Toggle tabulature file actuality """

        logger.info("Toggling tabulature file actuality")
        tabulature_file = TabulatureFile.objects.get(pk=tabulature_file_id)
        tabulature_file.is_actual = not tabulature_file.is_actual
        tabulature_file.save()

    @staticmethod
    def file_delete(tabulature_file_id: uuid.UUID):
        """ Delete tabulature file from Tabulature """

        logger.info("Deleting tabulature file")
        tabulature_file = TabulatureFile.objects.get(pk=tabulature_file_id)
        tabulature_file.delete()

    @staticmethod
    def file_add(tabulature_id: uuid.UUID, request_FILES: dict):
        """ Add new file to Tabulature """

        logger.info("Adding tabulature file to existing Tabulature")
        song_tabulature_file = request_FILES['song_tabulature_file']
        if (song_tabulature_file):
            tabulature = Tabulature.objects.get(pk=tabulature_id)
            tabulature.create_tabulature_file(song_tabulature_file, True)

    @staticmethod
    def tabulature_archive(username: str, code: int) -> str:
        """
            create archive from all actual tabulatures, return archive path
            code - defines songs set: 1 - actual, 2 - not actual
        """

        directory_name = os.path.join(settings.MEDIA_ROOT, username+"_archive_tmp")
        try:
            os.mkdir(directory_name)
        except FileExistsError:
            pass

        archive_directory_name = os.path.join(settings.MEDIA_ROOT, username+"_archive")
        if(os.path.isdir(archive_directory_name)):
            shutil.rmtree(archive_directory_name)
        os.mkdir(archive_directory_name)

        actual_tabulatures = {}

        if(code == 1):
            archive_name_base = "takeitdown_actual"
            song_list = Song.objects.played_only_on_practice()
        elif(code == 2):
            archive_name_base = "takeitdown_notactual"
            song_list = Song.objects.not_played()

        # choose actual tabulatures
        for song in song_list:
            if(song.tabulature is None):
                continue
            count = song.tabulature.tab_files.count()
            if(count == 0):
                continue
            for tab in song.tabulature.tab_files.all():
                similarity_counter = 0
                while True:
                    search_result = re.search("\.([\w\d]+)$", tab.file.path)
                    extension = search_result.group(1)
                    new_name = "{} - {}.{}".format(song.artist, song.name, extension)\
                        if similarity_counter == 0 \
                        else "{} - {} {}.{}".format(song.artist, song.name, similarity_counter, extension)

                    if(new_name not in actual_tabulatures):
                        break
                    similarity_counter += 1

                actual_tabulatures[new_name] = tab.file.path

        # copy tabulatures to directory
        new_files = []
        for new_file_name, filename in actual_tabulatures.items():
            shutil.copyfile(filename, "{}\\{}".format(directory_name, new_file_name))
            new_files.append(new_file_name)

        # archive files
        archive_name = archive_name_base + datetime.now().strftime("_%Y_%m_%d__%H%M") + ".zip"
        archive_path = os.path.join(settings.MEDIA_ROOT, archive_directory_name, archive_name)
        with ZipFile(archive_path, "w") as archive:
            for file in new_files:
                archive.write("{}\\{}".format(directory_name, file), file)


        # delete files
        shutil.rmtree(directory_name)

        return archive_path


class ProjectResourceFileManager:
    """ Manages project resource files """


    @staticmethod
    def create_project_resource_file(project_slug: str, request_POST: dict, request_FILES: dict) -> bool:
        """ Create file related to project   """

        logger.info("Creating new project resource file")
        project = Project.objects.get(slug=project_slug)
        file_description = request_POST.get('project_file_description', False)
        if(file_description and
                request_FILES and
                'project_file' in request_FILES):
            file = request_FILES['project_file']
            resource_file = ProjectResourceFile()
            resource_file.description = file_description
            resource_file.file = file
            resource_file.project = project
            resource_file.save()
            return True
        return False


class ProjectURLManager:
    """ Manages project related URLs """


    @staticmethod
    def create_project_related_url(project_slug: str, request_POST: dict) -> bool:
        """  Create URL related to project """

        logger.info("Creating new project related URL")
        project = Project.objects.get(slug=project_slug)
        url_description = request_POST.get('project_url_description', False)
        url_path = request_POST.get('project_url_path', False)
        if(url_description and url_path):
            related_url = ProjectRelatedURL()
            related_url.description = url_description
            related_url.url = url_path
            related_url.project = project
            related_url.save()
            return True
        return False


class ProjectTaskManager:
    """ Manages Project tasks - creation, toggle on finished"""

    @staticmethod
    def create_from_post(request_post: dict, project: Project):

        task = ProjectTask()
        task.project = project
        user_ids = request_post.getlist("users")
        task.description = request_post["description"]
        task.save()
        for id in user_ids:
            user = User.objects.get(id=id)
            task.responsible_persons.add(user)

        task.save()

        #task.responsible_persons.add
        #task.save()

    @staticmethod
    def check_finished():
        pass
