# -*- coding: utf-8 -*-
from urllib.parse import quote_plus

from plexapi import media, utils
from plexapi.base import PlexPartialObject
from plexapi.exceptions import BadRequest, NotFound, Unsupported
from plexapi.library import LibrarySection
from plexapi.mixins import AdvancedSettingsMixin, ArtMixin, PosterMixin
from plexapi.mixins import LabelMixin
from plexapi.playqueue import PlayQueue
from plexapi.utils import deprecated


@utils.registerPlexObject
class Collection(PlexPartialObject, AdvancedSettingsMixin, ArtMixin, PosterMixin, LabelMixin):
    """ Represents a single Collection.

        Attributes:
            TAG (str): 'Directory'
            TYPE (str): 'collection'
            addedAt (datetime): Datetime the collection was added to the library.
            art (str): URL to artwork image (/library/metadata/<ratingKey>/art/<artid>).
            artBlurHash (str): BlurHash string for artwork image.
            childCount (int): Number of items in the collection.
            collectionMode (str): How the items in the collection are displayed.
            collectionPublished (bool): True if the collection is published to the Plex homepage.
            collectionSort (str): How to sort the items in the collection.
            content (str): The filter URI string for smart collections.
            contentRating (str) Content rating (PG-13; NR; TV-G).
            fields (List<:class:`~plexapi.media.Field`>): List of field objects.
            guid (str): Plex GUID for the collection (collection://XXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXX).
            index (int): Plex index number for the collection.
            key (str): API URL (/library/metadata/<ratingkey>).
            labels (List<:class:`~plexapi.media.Label`>): List of label objects.
            librarySectionID (int): :class:`~plexapi.library.LibrarySection` ID.
            librarySectionKey (str): :class:`~plexapi.library.LibrarySection` key.
            librarySectionTitle (str): :class:`~plexapi.library.LibrarySection` title.
            maxYear (int): Maximum year for the items in the collection.
            minYear (int): Minimum year for the items in the collection.
            ratingCount (int): The number of ratings.
            ratingKey (int): Unique key identifying the collection.
            smart (bool): True if the collection is a smart collection.
            subtype (str): Media type of the items in the collection (movie, show, artist, or album).
            summary (str): Summary of the collection.
            thumb (str): URL to thumbnail image (/library/metadata/<ratingKey>/thumb/<thumbid>).
            thumbBlurHash (str): BlurHash string for thumbnail image.
            title (str): Name of the collection.
            titleSort (str): Title to use when sorting (defaults to title).
            type (str): 'collection'
            updatedAt (datatime): Datetime the collection was updated.
    """

    TAG = 'Directory'
    TYPE = 'collection'

    def _loadData(self, data):
        self._data = data
        self.addedAt = utils.toDatetime(data.attrib.get('addedAt'))
        self.art = data.attrib.get('art')
        self.artBlurHash = data.attrib.get('artBlurHash')
        self.childCount = utils.cast(int, data.attrib.get('childCount'))
        self.collectionMode = utils.cast(int, data.attrib.get('collectionMode', '-1'))
        self.collectionPublished = utils.cast(bool, data.attrib.get('collectionPublished', '0'))
        self.collectionSort = utils.cast(int, data.attrib.get('collectionSort', '0'))
        self.content = data.attrib.get('content')
        self.contentRating = data.attrib.get('contentRating')
        self.fields = self.findItems(data, media.Field)
        self.guid = data.attrib.get('guid')
        self.index = utils.cast(int, data.attrib.get('index'))
        self.key = data.attrib.get('key', '').replace('/children', '')  # FIX_BUG_50
        self.labels = self.findItems(data, media.Label)
        self.librarySectionID = utils.cast(int, data.attrib.get('librarySectionID'))
        self.librarySectionKey = data.attrib.get('librarySectionKey')
        self.librarySectionTitle = data.attrib.get('librarySectionTitle')
        self.maxYear = utils.cast(int, data.attrib.get('maxYear'))
        self.minYear = utils.cast(int, data.attrib.get('minYear'))
        self.ratingCount = utils.cast(int, data.attrib.get('ratingCount'))
        self.ratingKey = utils.cast(int, data.attrib.get('ratingKey'))
        self.smart = utils.cast(bool, data.attrib.get('smart', '0'))
        self.subtype = data.attrib.get('subtype')
        self.summary = data.attrib.get('summary')
        self.thumb = data.attrib.get('thumb')
        self.thumbBlurHash = data.attrib.get('thumbBlurHash')
        self.title = data.attrib.get('title')
        self.titleSort = data.attrib.get('titleSort', self.title)
        self.type = data.attrib.get('type')
        self.updatedAt = utils.toDatetime(data.attrib.get('updatedAt'))
        self._items = None  # cache for self.items
        self._section = None  # cache for self.section

    def __len__(self):  # pragma: no cover
        return len(self.items())

    def __iter__(self):  # pragma: no cover
        for item in self.items():
            yield item

    def __contains__(self, other):  # pragma: no cover
        return any(i.key == other.key for i in self.items())

    def __getitem__(self, key):  # pragma: no cover
        return self.items()[key]

    @property
    def listType(self):
        """ Returns the listType for the collection. """
        if self.isVideo:
            return 'video'
        elif self.isAudio:
            return 'audio'
        elif self.isPhoto:
            return 'photo'
        else:
            raise Unsupported('Unexpected collection type')

    @property
    def metadataType(self):
        """ Returns the type of metadata in the collection. """
        return self.subtype

    @property
    def isVideo(self):
        """ Returns True if this is a video collection. """
        return self.subtype in {'movie', 'show', 'season', 'episode'}

    @property
    def isAudio(self):
        """ Returns True if this is an audio collection. """
        return self.subtype in {'artist', 'album', 'track'}

    @property
    def isPhoto(self):
        """ Returns True if this is a photo collection. """
        return self.subtype in {'photoalbum', 'photo'}

    @property
    @deprecated('use "items" instead', stacklevel=3)
    def children(self):
        return self.items()

    def section(self):
        """ Returns the :class:`~plexapi.library.LibrarySection` this collection belongs to.
        """
        if self._section is None:
            self._section = super(Collection, self).section()
        return self._section

    def item(self, title):
        """ Returns the item in the collection that matches the specified title.

            Parameters:
                title (str): Title of the item to return.

            Raises:
                :class:`plexapi.exceptions.NotFound`: When the item is not found in the collection.
        """
        for item in self.items():
            if item.title.lower() == title.lower():
                return item
        raise NotFound('Item with title "%s" not found in the collection' % title)

    def items(self):
        """ Returns a list of all items in the collection. """
        if self._items is None:
            key = '%s/children' % self.key
            items = self.fetchItems(key)
            self._items = items
        return self._items

    def get(self, title):
        """ Alias to :func:`~plexapi.library.Collection.item`. """
        return self.item(title)

    def modeUpdate(self, mode=None):
        """ Update the collection mode advanced setting.

            Parameters:
                mode (str): One of the following values:
                    "default" (Library default),
                    "hide" (Hide Collection),
                    "hideItems" (Hide Items in this Collection),
                    "showItems" (Show this Collection and its Items)

            Example:

                .. code-block:: python

                    collection.updateMode(mode="hide")
        """
        mode_dict = {
            'default': -1,
            'hide': 0,
            'hideItems': 1,
            'showItems': 2
        }
        key = mode_dict.get(mode)
        if key is None:
            raise BadRequest('Unknown collection mode : %s. Options %s' % (mode, list(mode_dict)))
        self.editAdvanced(collectionMode=key)

    def sortUpdate(self, sort=None):
        """ Update the collection order advanced setting.

            Parameters:
                sort (str): One of the following values:
                    "realease" (Order Collection by realease dates),
                    "alpha" (Order Collection alphabetically),
                    "custom" (Custom collection order)

            Example:

                .. code-block:: python

                    collection.updateSort(mode="alpha")
        """
        sort_dict = {
            'release': 0,
            'alpha': 1,
            'custom': 2
        }
        key = sort_dict.get(sort)
        if key is None:
            raise BadRequest('Unknown sort dir: %s. Options: %s' % (sort, list(sort_dict)))
        self.editAdvanced(collectionSort=key)

    def addItems(self, items):
        """ Add items to the collection.

            Parameters:
                items (List): List of :class:`~plexapi.audio.Audio`, :class:`~plexapi.video.Video`,
                    or :class:`~plexapi.photo.Photo` objects to be added to the collection.

            Raises:
                :class:`plexapi.exceptions.BadRequest`: When trying to add items to a smart collection.
        """
        if self.smart:
            raise BadRequest('Cannot add items to a smart collection.')

        if items and not isinstance(items, (list, tuple)):
            items = [items]

        ratingKeys = []
        for item in items:
            if item.type != self.subtype:  # pragma: no cover
                raise BadRequest('Can not mix media types when building a collection: %s and %s' %
                    (self.subtype, item.type))
            ratingKeys.append(str(item.ratingKey))

        ratingKeys = ','.join(ratingKeys)
        uri = '%s/library/metadata/%s' % (self._server._uriRoot(), ratingKeys)

        key = '%s/items%s' % (self.key, utils.joinArgs({
            'uri': uri
        }))
        self._server.query(key, method=self._server._session.put)

    def removeItems(self, items):
        """ Remove items from the collection.

            Parameters:
                items (List): List of :class:`~plexapi.audio.Audio`, :class:`~plexapi.video.Video`,
                    or :class:`~plexapi.photo.Photo` objects to be removed from the collection.

            Raises:
                :class:`plexapi.exceptions.BadRequest`: When trying to remove items from a smart collection.
        """
        if self.smart:
            raise BadRequest('Cannot remove items from a smart collection.')

        if items and not isinstance(items, (list, tuple)):
            items = [items]

        for item in items:
            key = '%s/items/%s' % (self.key, item.ratingKey)
            self._server.query(key, method=self._server._session.delete)

    def updateFilters(self, libtype=None, limit=None, sort=None, filters=None, **kwargs):
        """ Update the filters for a smart collection.

            Parameters:
                libtype (str): The specific type of content to filter
                    (movie, show, season, episode, artist, album, track, photoalbum, photo, collection).
                limit (int): Limit the number of items in the collection.
                sort (str or list, optional): A string of comma separated sort fields
                    or a list of sort fields in the format ``column:dir``.
                    See :func:`~plexapi.library.LibrarySection.search` for more info.
                filters (dict): A dictionary of advanced filters.
                    See :func:`~plexapi.library.LibrarySection.search` for more info.
                **kwargs (dict): Additional custom filters to apply to the search results.
                    See :func:`~plexapi.library.LibrarySection.search` for more info.

            Raises:
                :class:`plexapi.exceptions.BadRequest`: When trying update filters for a regular collection.
        """
        if not self.smart:
            raise BadRequest('Cannot update filters for a regular collection.')

        section = self.section()
        searchKey = section._buildSearchKey(
            sort=sort, libtype=libtype, limit=limit, filters=filters, **kwargs)
        uri = '%s%s' % (self._server._uriRoot(), searchKey)

        key = '%s/items%s' % (self.key, utils.joinArgs({
            'uri': uri
        }))
        self._server.query(key, method=self._server._session.put)

    def edit(self, title=None, titleSort=None, contentRating=None, summary=None, **kwargs):
        """ Edit the collection.
        
            Parameters:
                title (str, optional): The title of the collection.
                titleSort (str, optional): The sort title of the collection.
                contentRating (str, optional): The summary of the collection.
                summary (str, optional): The summary of the collection.
        """
        args = {}
        if title is not None:
            args['title.value'] = title
            args['title.locked'] = 1
        if titleSort is not None:
            args['titleSort.value'] = titleSort
            args['titleSort.locked'] = 1
        if contentRating is not None:
            args['contentRating.value'] = contentRating
            args['contentRating.locked'] = 1
        if summary is not None:
            args['summary.value'] = summary
            args['summary.locked'] = 1

        args.update(kwargs)
        super(Collection, self).edit(**args)

    def delete(self):
        """ Delete the collection. """
        super(Collection, self).delete()

    def playQueue(self, *args, **kwargs):
        """ Returns a new :class:`~plexapi.playqueue.PlayQueue` from the collection. """
        return PlayQueue.create(self._server, self.items(), *args, **kwargs)

    @classmethod
    def _create(cls, server, title, section, items):
        """ Create a regular collection. """
        if not items:
            raise BadRequest('Must include items to add when creating new collection.')

        if not isinstance(section, LibrarySection):
            section = server.library.section(section)

        if items and not isinstance(items, (list, tuple)):
            items = [items]

        itemType = items[0].type
        ratingKeys = []
        for item in items:
            if item.type != itemType:  # pragma: no cover
                raise BadRequest('Can not mix media types when building a collection.')
            ratingKeys.append(str(item.ratingKey))

        ratingKeys = ','.join(ratingKeys)
        uri = '%s/library/metadata/%s' % (server._uriRoot(), ratingKeys)

        key = '/library/collections%s' % utils.joinArgs({
            'uri': uri,
            'type': utils.searchType(itemType),
            'title': title,
            'smart': 0,
            'sectionId': section.key
        })
        data = server.query(key, method=server._session.post)[0]
        return cls(server, data, initpath=key)

    @classmethod
    def _createSmart(cls, server, title, section, limit=None, libtype=None, sort=None, filters=None, **kwargs):
        """ Create a smart collection. """
        if not isinstance(section, LibrarySection):
            section = server.library.section(section)

        libtype = libtype or section.TYPE

        searchKey = section._buildSearchKey(
            sort=sort, libtype=libtype, limit=limit, filters=filters, **kwargs)
        uri = '%s%s' % (server._uriRoot(), searchKey)

        key = '/library/collections%s' % utils.joinArgs({
            'uri': uri,
            'type': utils.searchType(libtype),
            'title': title,
            'smart': 1,
            'sectionId': section.key
        })
        data = server.query(key, method=server._session.post)[0]
        return cls(server, data, initpath=key)

    @classmethod
    def create(cls, server, title, section, items=None, smart=False, limit=None,
               libtype=None, sort=None, filters=None, **kwargs):
        """ Create a collection.

            Parameters:
                server (:class:`~plexapi.server.PlexServer`): Server to create the collection on.
                title (str): Title of the collection.
                section (:class:`~plexapi.library.LibrarySection`, str): The library section to create the collection in.
                items (List): Regular collections only, list of :class:`~plexapi.audio.Audio`,
                    :class:`~plexapi.video.Video`, or :class:`~plexapi.photo.Photo` objects to be added to the collection.
                smart (bool): True to create a smart collection. Default False.
                limit (int): Smart collections only, limit the number of items in the collection.
                libtype (str): Smart collections only, the specific type of content to filter
                    (movie, show, season, episode, artist, album, track, photoalbum, photo, collection).
                sort (str or list, optional): Smart collections only, a string of comma separated sort fields
                    or a list of sort fields in the format ``column:dir``.
                    See :func:`~plexapi.library.LibrarySection.search` for more info.
                filters (dict): Smart collections only, a dictionary of advanced filters.
                    See :func:`~plexapi.library.LibrarySection.search` for more info.
                **kwargs (dict): Smart collections only, additional custom filters to apply to the
                    search results. See :func:`~plexapi.library.LibrarySection.search` for more info.

            Raises:
                :class:`plexapi.exceptions.BadRequest`: When no items are included to create the collection.
                :class:`plexapi.exceptions.BadRequest`: When mixing media types in the collection.

            Returns:
                :class:`~plexapi.collection.Collection`: A new instance of the created Collection.
        """
        if smart:
            return cls._createSmart(server, title, section, limit, libtype, sort, filters, **kwargs)
        else:
            return cls._create(server, title, section, items)

    def sync(self, videoQuality=None, photoResolution=None, audioBitrate=None, client=None, clientId=None, limit=None,
             unwatched=False, title=None):
        """ Add the collection as sync item for the specified device.
            See :func:`~plexapi.myplex.MyPlexAccount.sync` for possible exceptions.

            Parameters:
                videoQuality (int): idx of quality of the video, one of VIDEO_QUALITY_* values defined in
                                    :mod:`~plexapi.sync` module. Used only when collection contains video.
                photoResolution (str): maximum allowed resolution for synchronized photos, see PHOTO_QUALITY_* values in
                                       the module :mod:`~plexapi.sync`. Used only when collection contains photos.
                audioBitrate (int): maximum bitrate for synchronized music, better use one of MUSIC_BITRATE_* values
                                    from the module :mod:`~plexapi.sync`. Used only when collection contains audio.
                client (:class:`~plexapi.myplex.MyPlexDevice`): sync destination, see
                                                               :func:`~plexapi.myplex.MyPlexAccount.sync`.
                clientId (str): sync destination, see :func:`~plexapi.myplex.MyPlexAccount.sync`.
                limit (int): maximum count of items to sync, unlimited if `None`.
                unwatched (bool): if `True` watched videos wouldn't be synced.
                title (str): descriptive title for the new :class:`~plexapi.sync.SyncItem`, if empty the value would be
                             generated from metadata of current photo.

            Raises:
                :exc:`~plexapi.exceptions.BadRequest`: When collection is not allowed to sync.
                :exc:`~plexapi.exceptions.Unsupported`: When collection content is unsupported.

            Returns:
                :class:`~plexapi.sync.SyncItem`: A new instance of the created sync item.
        """
        if not self.section().allowSync:
            raise BadRequest('The collection is not allowed to sync')

        from plexapi.sync import SyncItem, Policy, MediaSettings

        myplex = self._server.myPlexAccount()
        sync_item = SyncItem(self._server, None)
        sync_item.title = title if title else self.title
        sync_item.rootTitle = self.title
        sync_item.contentType = self.listType
        sync_item.metadataType = self.metadataType
        sync_item.machineIdentifier = self._server.machineIdentifier

        sync_item.location = 'library:///directory/%s' % quote_plus(
            '%s/children?excludeAllLeaves=1' % (self.key)
        )
        sync_item.policy = Policy.create(limit, unwatched)

        if self.isVideo:
            sync_item.mediaSettings = MediaSettings.createVideo(videoQuality)
        elif self.isAudio:
            sync_item.mediaSettings = MediaSettings.createMusic(audioBitrate)
        elif self.isPhoto:
            sync_item.mediaSettings = MediaSettings.createPhoto(photoResolution)
        else:
            raise Unsupported('Unsupported collection content')

        return myplex.sync(sync_item, client=client, clientId=clientId)
