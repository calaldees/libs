import os
import re
import shutil
import urllib.parse
from functools import lru_cache

from pyramid.view import view_config, view_defaults
import pyramid.response

from ...misc import hash_data

import logging
log = logging.getLogger(__name__)


class FileHandle(object):
    
    @staticmethod
    def get_files_from_request(request):
        return [FileHandle(fieldStorage) for name, fieldStorage in request.POST.items() if hasattr(fieldStorage, 'filename')]

    def __init__(self, field_storage):
        self.file = field_storage.file
        self.name = field_storage.filename
        self.size = self._get_file_size(field_storage.file)

    @staticmethod
    def _get_file_size(file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size
    
    def to_dict(self):
        return vars(self)

class AbstractFileUploadHandler(object):
    def __init__(self, request):
        self.request = request
        
        # Identify user session
        #   This is probably not wise to hash the cookie.
        #   The cookie could change at at any point, (hopefully not during an upload).
        #   Could be a sbaility bug waiting to happen
        self.session_id = self.header('Session-ID') or hash_data(self.header('Cookie'))
        assert self.session_id

    def header(self, header_name):
        return self.request.headers.get(header_name) or self.request.headers.get('X-{0}'.format(header_name))

    @property
    @lru_cache()
    def path_session(self):
        """
        A path area that is unique to this user
        Used for temporary files
        """
        return os.path.join(self._path_upload, str(self.session_id))

    @property
    def _path_upload(self):
        return self.request.registry.settings.get('upload.path','upload')
    
    def file_route(self, name):
        return self.request.route_url(self.request.registry.settings.get('upload.file_route','uploaded')) + name
    
    @property
    def delete_method(self):
        return self.request.registry.settings.get('upload.delete.method','DELETE')
    
    def delete_route(self, name):
        url =  self.request.route_url(
            self.request.registry.settings.get('upload.route','upload'),
            sep='/', name=name
        )
        if self.delete_method != 'DELETE':  # can this be part of the route_url() call?
            url += '&_method=DELETE'
        return url
    
    def filelist(self):
        return [f for f in os.listdir(self._path_upload())]
    
    def fileinfo(self, name=None):
        if name==None:  # and hasattr(self, name):  # Why the fuck was this ever here?
            name = self.name
        assert name, 'filename required to aquire file info'
        filename = os.path.join(self._path_upload, name)
        if os.path.exists(filename):
            return {
                'name': name,
                'size': os.path.getsize(filename),
                'type': None,  # Todo, magic?
                'url': self.file_route(name),
                'thumbnail_url': None,
                'delete_type': self.delete_method,
                'delete_url': self.delete_route(name),
            }


class FileUploadMultipleHandler(AbstractFileUploadHandler):
    
    def __init__(self, request):
        super().__init__(request)
        self.file_handles = FileHandle.get_files_from_request(request)
        assert self.file_handles, 'No file data in request'
        self.save()

    def save(self):
        for file_handle in self.file_handles:
            with open(os.path.join(self._path_upload, file_handle.name), 'wb') as f:
                shutil.copyfileobj(file_handle.file, f)

    def files(self):
        return tuple(self.fileinfo(file_handle.name) for file_handle in self.file_handles)


class FileUploadChunkDetails(AbstractFileUploadHandler):

    def __init__(self, request, name=None):
        super().__init__(request)
        if name:
            self.name = name
            assert os.path.exists(self.path)

    @property
    @lru_cache()
    def path(self):
        return os.path.join(self.path_session, self.name)

    @property
    @lru_cache()
    def path_destination(self):
        return os.path.join(self._path_upload, self.name)

    @property
    @lru_cache()
    def chunk_filenames(self):
        return tuple(os.path.join(self.path, filename) for filename in sorted(os.listdir(self.path), key=lambda f: '{0:010}'.format(int(f))))

    @property
    @lru_cache()
    def bytes_recived(self):
        bytes_recived = sum(os.path.getsize(filename) for filename in self.chunk_filenames)
        assert bytes_recived <= self.size, 'recived more data than total filesize'
        return bytes_recived

    def incomplete_file_details(self):
        return (FileUploadChunkDetails(self.request, incomplete_filename) for incomplete_filename in os.listdir(self.path_session))
    
    def cleanup_chunks(self):
        """
        Remove all traces of all files associated with this upload
        """
        try:
            log.info('Cleaning up chunks for {0}'.format(self.path))
            shutil.rmtree(self.path)
        except os.error:
            log.warn('unable to remove'.format(self.path))
        if not os.listdir(self.path_session):
            os.rmdir(self.path_session)

    def cleanup_destination(self):
        try:
            log.info('Cleaning up destination for {0}'.format(self.path_destination))
            os.remove(self.path_destination)
        except os.error:
            log.warn('unable to remove'.format(self.path_destination))

    def fileinfo(self):
        return {
            'name': self.name,
            'size': self.bytes_recived,
        }

    

class FileUploadChunkHandler(FileUploadChunkDetails):
    """
    Todo: keep track of chunks uploaded (out of sequence).
    e.g: it is possible for the last chunk is uploaded before the first chunk
    """
    RE_CONTENT_RANGE = re.compile(r'bytes (?P<data_start>\d+)-(?P<data_end>\d{1,9})/(?P<size>\d{1,9})')
    RE_CONTENT_DISPOSITION = re.compile(r'attachment; filename="(.*?)"')

    def __init__(self, request):
        super().__init__(request)
        self.handle_chunk()

    def handle_chunk(self):
        chunk = self.request.body
        
        # Extract and validate chunk filename
        self.name = urllib.parse.unquote_plus(self.RE_CONTENT_DISPOSITION.match(self.header('Content-Disposition')).group(1))
        assert not os.path.exists(self.path_destination), 'destination file already exisits - {0}'.format(self.path_destination)
        
        # Extract and validate type
        self.type = self.header('Content-Type')
        for content_type in ('multipart/form-data',):  #, 'text/html', 'application/json'
            assert content_type not in self.type, 'The specification explicitly states that for chuncked uploads the forms should not be submitted as {0}'.format(content_type)
        
        # Extract and validate chunk range
        if self.header('Content-Range'):
            range_dict = {k:int(v) for k, v in self.RE_CONTENT_RANGE.match(self.header('Content-Range')).groupdict().items()}
            self.size = range_dict['size']
            self.data_start = range_dict['data_start']
            self.data_end = range_dict['data_end']
        else:
            self.size = int(self.header('Content-Length'))
            self.data_start = 0
            self.data_end = self.size - 1
        assert self.chunk_size == len(chunk), 'Content-Range [{0}] does not match filesize [{1}]'.format(self.chunk_size, len(chunk))

        try:
            os.makedirs(os.path.dirname(self.path_chunk_current))
        except os.error:
            pass
        with open(self.path_chunk_current, 'wb') as f:
            f.write(chunk)
        # After writing chunk self.bytes_recived and self.chunk_filenames need to be invalidated.
        # If they havent been called before this point then everything is fine.
    
    @property
    @lru_cache()
    def path_chunk_current(self):
        return os.path.join(self.path, str(self.data_start))

    @property
    def chunk_size(self):
        return self.data_end - self.data_start + 1

    @property
    def progress(self):
        return self.bytes_recived / self.size

    @property
    def range_recived(self):
        """
        Spec states a range string should be provided in the response
        Although the spec states that the chunks can arrive in any order,
        There is no mention of how it reports this.
        """
        return "{start}-{end}/{size}".format(start=0, end=self.bytes_recived-1, size=self.size)

    @property
    def complete(self):
        return self.bytes_recived == self.size

    def reconstitue_chunked_file(self):
        """
        All chunks for a file are in the same folder
        list the files in the folder and sort them by
        """
        assert self.complete, 'Cant reconstitue incomplete file'
        try:
            with open(self.path_destination, 'wb') as destination:
                for chunk_filename in self.chunk_filenames:
                    with open(chunk_filename, 'rb') as chunk:
                        destination.write(chunk.read())
            self.cleanup_chunks()
        except IOError:
            log.error('Failed to reconstitute file {0}'.format(self.path_destination))
            self.cleanup_chunks()
            self.cleanup_destination()

    def fileinfo(self):
        if self.complete:
            return super(FileUploadChunkDetails, self).fileinfo()
        else:
            #return super().fileinfo()
            return super(FileUploadChunkHandler, self).fileinfo()

    def files(self):
        return (self.fileinfo(),)


@view_defaults(route_name='upload')
class Upload():
    """
    Pyramid route class that supports segmented file upload from jQuery-File-Upload
    https://github.com/blueimp/jQuery-File-Upload/wiki/
    
    HTML 5 Spec refernce
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.16
    
    https://github.com/blueimp/jQuery-File-Upload/wiki/Chunked-file-uploads
     - The byte range of the blob is transmitted via the Content-Range header.
     - The file name of the blob is transmitted via the Content-Disposition header.
     
    http://stackoverflow.com/questions/21352995/how-to-handle-file-upload-asynchronously-in-pyramid
    
    http://www.grid.net.ru/nginx/resumable_uploads.en.html
    """
    DELETEMETHOD = 'DELETE'
    MIN_FILE_SIZE =   1 * 1000 * 1000  # 1mb - A video smaller than that is not worth having
    MAX_FILE_SIZE = 100 * 1000 * 1000  # 100Mb
    #IMAGE_TYPES = re.compile('image/(gif|p?jpeg|(x-)?png)')
    #ACCEPT_FILE_TYPES = IMAGE_TYPES
    EXPIRATION_TIME = 300  # seconds
    
    def __init__(self, request, **options):
        self.request = request
        
        # Set default options (useful for overriding in tests or other file uses)
        # (this is truly a dangerious approach, set anything!?)
        for key, value in options.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Pre populate response headers
        request.response.headers['Access-Control-Allow-Origin'] = '*'
        request.response.headers['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST, PUT, DELETE'
        request.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Content-Range, Content-Disposition'

    def _validate(self, file):
        if file['size'] < self.MIN_FILE_SIZE:
            file['error'] = 'File is too small'
        elif file['size'] > self.MAX_FILE_SIZE:
            file['error'] = 'File is too big'
        #elif not ACCEPT_FILE_TYPES.match(file['type']):
        #    file['error'] = 'Filetype not allowed'
        else:
            return True
        return False

    @view_config(request_method='OPTIONS')
    def options(self):
        log.info('options')
        return self.head()

    @view_config(request_method='HEAD')
    def head(self):
        log.info('head')
        return pyramid.response.Response(body='')

    @view_config(request_method='GET', renderer="json")
    def get(self):
        log.info('get')
        name = self.request.matchdict.get('name') or self.request.params.get('file')
        if not name:
            return AbstractFileUploadHandler(self.request).filelist()
        try:
            return {'file': AbstractFileUploadHandler(self.request).fileinfo(name)}
        except AssertionError:
            pass
        try:
            return {'file': FileUploadChunkDetails(self.request, name).fileinfo()}
        except AssertionError:
            pass
        return {'file': None}

    @view_config(request_method='DELETE', xhr=True, accept="application/json", renderer='json')
    def delete(self):
        log.info('delete')
        filename = self.request.matchdict.get('name')
        try:
            os.remove()
        except IOError:
            return False
        return True
    
    @view_config(request_method='POST', xhr=True, accept="application/json", renderer='json')
    def post(self):
        if self.request.matchdict.get('_method') == "DELETE":
            return self.delete()
        
        if set(self.request.headers) & {'Content-Range', 'Content-Disposition', 'X-Content-Range', 'X-Content-Disposition'}:
            handler = FileUploadChunkHandler(self.request)
            if handler.complete:
                log.debug('Reconstituting file {0}'.format(handler.name))
                handler.reconstitue_chunked_file()
            else:
                log.debug('Recived chunk {0} of {1}'.format(handler.range_recived, handler.name))
                self.request.response.status_code = 201
                self.request.response.headerlist.append(('Range', handler.range_recived))
                return handler.range_recived
        else:
            handler = FileUploadMultipleHandler(self.request)

        files = handler.files()
        log.debug(files)
        return {'files': files}
