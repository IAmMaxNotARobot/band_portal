from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.contrib.auth.models import User

from _datetime import datetime
from loguru import logger

from .logic import *
from tid_portal import settings

__all__ = ['Lyrics', 'Tabulature', 'TabulatureFile', 'Song', 'Project',
           'ProjectEvent', 'ProjectResourceFile', 'ProjectRelatedURL',
           'StatusValue', 'StatusCategory', 'ProjectStatusCategory',
           'ProjectTask']

logger.add(settings.BASE_DIR + "/debug.log", format="{time} {level} {message}", rotation="2 week", compression="zip")


class Lyrics(models.Model):
    """
    Lyrics file for song or project
    """


    pub_date = models.DateTimeField(default=datetime.now())
    file = models.FileField(upload_to='lyrics',
                            validators=[FileExtensionValidator(allowed_extensions=['txt', 'doc'])],
                            )

    def show_lyrics(self) -> str:
        """ Show text from lyrics file """

        logger.info("Trying to read file: {}".format(self.file.path))
        f = open(self.file.path, encoding="utf-8")
        file_content = f.read()
        f.close()
        return file_content

    def __str__(self):
        return "{0} {1}".format(self.file.name.split('/')[-1], self.pub_date)
    def filename(self):
        return self.file.name.split('/')[-1]

class Tabulature(models.Model):
    """
    Tab that will have different versions
    artist, name, project or song
    """


    name = models.CharField(max_length=30, verbose_name="Tabulature set name")

    def create_tabulature_file(self, file, is_actual: bool = False):
        """ Create TabulatureFile by file """

        tabulature_file = TabulatureFile()
        tabulature_file.tabulature = self
        tabulature_file.file.save(file.name, file)
        tabulature_file.is_actual = is_actual
        tabulature_file.save()

    def __str__(self):
        return self.name


class TabulatureFileQuerySet(models.QuerySet):
    """ Additional queries for ProjectEvent """


    def owned_by_project(self, tabulature):
        return self.filter(tabulature = tabulature).order_by('-is_actual', 'pub_date')


class TabulatureFile(models.Model):
    """
    Versions of a tab
    tabulature, pub_date, is_actual, file
    """


    tabulature = models.ForeignKey(
        Tabulature,
        on_delete=models.CASCADE,
        verbose_name="Tabulature",
        related_name='tab_files'
    )
    pub_date = models.DateTimeField(default=datetime.now(), verbose_name="Publication date")
    is_actual = models.BooleanField(default=False, verbose_name="Is actual file")
    file = models.FileField(upload_to='tabs', null=True,
                            validators=[FileExtensionValidator(allowed_extensions=['gpx', 'gp5', 'gp'])],
                            verbose_name="Tabulature file name"
                            )
    objects = TabulatureFileQuerySet.as_manager()

    def __str__(self):
        return "{0} {1}".format(self.tabulature.name, self.pub_date)

    def filename(self):
        return self.file.name.split('/')[-1]


class SongQuerySet(models.QuerySet):
    """ Additional queries for Songs - played, unplayed and live list """


    def live_list(self):
        return self.filter(live_position__gt=0).order_by('live_position')

    def played_only_on_practice(self):
        return self.filter(live_position=0).filter(played_now=True)

    def played_on_practice(self):
        return self.exclude(played_now=False).order_by('artist', 'name')

    def not_played(self):
        return self.exclude(played_now=True)


class Song(models.Model):
    """
    Song that we have played or plaing now on practice and lives.
    artist, name, tab, played_now
    """


    artist = models.CharField(max_length=100, verbose_name="Artist name")
    name = models.CharField(max_length = 100, verbose_name="Song name")
    played_now = models.BooleanField(default = False, verbose_name="Is played on practices")
    tempo = models.IntegerField(default=100, verbose_name="Tempo")
    live_position = models.IntegerField(default = 0, verbose_name="Position in live list")
    tabulature = models.ForeignKey(Tabulature,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   verbose_name="Tabulature")
    lyrics = models.ForeignKey(Lyrics,
                               on_delete=models.SET_NULL,
                               null=True,
                               blank=True,
                               verbose_name="Lyrics")
    objects = SongQuerySet.as_manager()

    def __str__(self):
        return "{0} - {1}".format(self.artist, self.name)

    def save(self, *args, **kwargs):
        if settings.DEBUG:
            logger.info("Song was saved: {} {} {}".format(self.artist, self.name, self.tempo))
        super().save(*args, **kwargs)


class Project(models.Model):
    """
    Song that we recording, contains history, status and files
    name, created_date, is_released,
    """


    name = models.CharField(max_length=100, default="",
                            verbose_name="Project name")
    created_date = models.DateTimeField(default=datetime.now(),
                                        verbose_name="Created date")
    is_released = models.BooleanField(default=False,
                                      verbose_name="Project song is released")
    riffs_status = models.CharField(max_length=20,
                                    choices=StatusChoices.choices,
                                    default=StatusChoices.NOTDONE,
                                    verbose_name="Riffs readiness status")
    solo_status = models.CharField(max_length=20,
                                   choices=StatusChoices.choices,
                                   default=StatusChoices.NOTDONE,
                                   verbose_name="Solo readiness status")
    bass_status = models.CharField(max_length=20,
                                   choices=StatusChoices.choices,
                                   default=StatusChoices.NOTDONE,
                                   verbose_name="Bass readiness status")
    drums_status = models.CharField(max_length=20,
                                    choices=StatusChoices.choices,
                                    default=StatusChoices.NOTDONE,
                                    verbose_name="Drums readiness status")
    lyrics_status = models.CharField(max_length=20,
                                     choices=StatusChoices.choices,
                                     default=StatusChoices.NOTDONE,
                                     verbose_name="Lyrics readiness status")
    vox_status = models.CharField(max_length=20,
                                  choices=StatusChoices.choices,
                                  default=StatusChoices.NOTDONE,
                                  verbose_name="Vox readiness status")
    slug = models.SlugField(max_length=100, unique=True, null=True)
    tabulature = models.ForeignKey(Tabulature, on_delete=models.SET_NULL, null=True, blank=True)
    lyrics = models.ForeignKey(Lyrics, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class ProjectEventQuerySet(models.QuerySet):
    """ Additional queries for ProjectEvent """


    def owned_by_project(self, project_id: int):
        return self.filter(project__id=project_id).order_by('-pub_date')

    def last_events(self):
        return self.order_by('-pub_date')[0:10]


class ProjectEvent(models.Model):
    """
    Project history event - changed status, added new file or etc
    project, pub_date, note, author, is_important, is_deleted
    """


    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name='events', verbose_name="Related project")
    pub_date = models.DateTimeField(default=datetime.now(),
                                    verbose_name="Publication date")
    note = models.TextField(verbose_name="Note text")
    author = models.ForeignKey(User, null=True, blank=True,
                               on_delete=models.CASCADE,
                               verbose_name="Author")
    url = models.URLField(null=True,
                          blank=True,
                          verbose_name="Related URL")
    is_important = models.BooleanField(default=False,
                                       verbose_name="Event contains important info")
    is_deleted = models.BooleanField(default=False,
                                     verbose_name="Event marked for deletion")
    objects = ProjectEventQuerySet.as_manager()

    def __str__(self):
        return "{0} - {1} --- {2}".format(self.project.name, self.pub_date, self.note[:20])


class ProjectResourceFileQuerySet(models.QuerySet):
    """ Additional queries for ProjectEvent """


    def owned_by_project(self, project_id: int):
        return self.filter(project__id=project_id).order_by('-created_date')


class ProjectResourceFile(models.Model):
    """
    File related to project
    """


    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                verbose_name="Related project")
    created_date = models.DateTimeField(default=datetime.now(), verbose_name="Creation date")
    description = models.CharField(max_length=200, verbose_name="Resource file description")
    file = models.FileField(upload_to='project_resource_files',
                            verbose_name="Resource file")
    objects = ProjectResourceFileQuerySet.as_manager()

    def __str__(self):
        return self.description


class ProjectRelatedURLQuerySet(models.QuerySet):
    """ Additional queries for ProjectEvent """


    def owned_by_project(self, project_id: int):
        return self.filter(project__id=project_id).order_by('-created_date')


class ProjectRelatedURL(models.Model):
    """
    URL related to project
    """


    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name='related_urls',
                                verbose_name="Related project")
    created_date = models.DateTimeField(default=datetime.now(), verbose_name="Creation date")
    description = models.CharField(max_length=200, verbose_name="Related URL description")
    url = models.URLField(verbose_name='URL')
    objects = ProjectRelatedURLQuerySet.as_manager()

    def __str__(self):
        return self.description


class StatusValue(models.Model):
    """ Value of a project status. Like Done, Not done etc """


    value = models.CharField(max_length=100,
                             verbose_name="Status value",
                             unique=True)
    styling_class = models.CharField(max_length=100, verbose_name="CSS styling class")
    priority = models.IntegerField(unique=True, null=True, default=None)

    class Meta:
        ordering = ['priority']

    def __str__(self):
        return self.value


class StatusCategory(models.Model):
    """ Status Category - like Solo status, Riffs status and etc... """


    name = models.CharField(max_length=30, verbose_name="Category name")

    class Meta:
        verbose_name_plural = "Status categories"
        ordering = ['-id']

    def __str__(self):
        return self.name


class ProjectStatusCategory(models.Model):
    """ Status Category related to a project """


    category = models.ForeignKey(StatusCategory,
                                 on_delete=models.CASCADE,
                                 )
    status = models.ForeignKey(StatusValue,
                               on_delete=models.SET_NULL,
                               null=True)
    project = models.ForeignKey(Project,
                                related_name="statuses",
                                on_delete=models.CASCADE,
                                verbose_name="Related project")

    class Meta:
        verbose_name_plural = "Project status categories"
        ordering = ['project', '-category']
        #order_with_respect_to = 'category'

    def __str__(self):
        return "{} {} ({})".format(self.project.name, self.category, self.status)


class ProjectTaskQuerySet(models.QuerySet):
    """ Additional queries for ProjectTask """


    def owned_by_project(self, project_id: int):
        return self.filter(project__id=project_id, is_finished=False).order_by('-created_date')

    def finished_by_project(self, project_id: int):
        return self.filter(project__id=project_id, is_finished=True).order_by('-created_date')

    def owned_by_user(self, user: User, is_finished: bool = False):
        return self.filter(responsible_persons__id=user.id, is_finished=is_finished).order_by('-created_date')


class ProjectTask(models.Model):
    """ Project tasks that should be done by users """

    description = models.CharField(max_length=200, verbose_name="Description")
    is_finished = models.BooleanField(default=False, verbose_name="Task is finished")
    created_date = models.DateTimeField(default=datetime.now(), verbose_name="Created date")
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Related project"
    )
    responsible_persons = models.ManyToManyField(User)
    objects = ProjectTaskQuerySet.as_manager()

    def __str__(self):
        return self.description


@receiver(post_delete, sender=TabulatureFile)
def submission_delete(sender, instance, **kwargs):
    instance.file.delete(False)


@receiver(post_delete, sender=Lyrics)
def submission_delete(sender, instance, **kwargs):
    instance.file.delete(False)


@receiver(post_save, sender=Project)
def init_project_statuses(sender, instance, **kwargs):
    """ Creates all status categories for project """

    logger.info('Project status initialization!')
    project = instance
    project_status_categories = ProjectStatusCategory.objects.filter(project=project.id)
    if(project_status_categories):
        logger.info('Allready have statuses!')
    else:
        categories = StatusCategory.objects.all()
        default_status_value = StatusValue.objects.order_by('priority').first()
        for category in categories:
            project_status_category = ProjectStatusCategory()
            project_status_category.category = category
            project_status_category.project = project
            project_status_category.status = default_status_value
            project_status_category.save()


