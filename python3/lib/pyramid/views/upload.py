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

    @property
    def _path_upload(self):
        return self.request.registry.settings.get('upload.path','upload')


class FileUploadHandlerMultiple(AbstractFileUploadHandler):
    
    def __init__(self, request):
        super().__init__(request)
        self.files = FileHandle.get_files_from_request(request)
        assert self.files, 'No file data in request'
        
    def save(self):
        for file_handle in self.files:
            with open(os.path.join(self._path_upload, file_handle.name), 'wb') as f:
                shutil.copyfileobj(file_handle.file, f)



class FileUploadHandlerChunked(AbstractFileUploadHandler):
    """
    Todo: keep track of chunks uploaded (out of sequence).
    e.g: it is possible for the last chunk is uploaded before the first chunk
    """
    RE_CONTENT_RANGE = re.compile(r'bytes (?P<data_start>\d+)-(?P<data_end>\d{1,9})/(?P<size>\d{1,9})')
    RE_CONTENT_DISPOSITION = re.compile(r'attachment; filename="(.*?)"')

    def __init__(self, request):
        super().__init__(request)
        chunk = request.body
        
        # Extract and validate chunk filename
        self.name = urllib.parse.unquote_plus(self.RE_CONTENT_DISPOSITION.match(self.header('Content-Disposition')).group(1))
        assert not os.path.exists(self.path_destination), 'destination file already exisits - {0}'.format(self.path_destination)
        
        # Extract and validate type
        self.type = self.header('Content-Type')
        for content_type in ('multipart/form-data',):  #, 'text/html', 'application/json'
            assert content_type not in self.type, 'The specification explicitly states that for chuncked uploads the forms should not be submitted as {0}'.format(content_type)
        
        # Extract and validate chunk range
        range_dict = {k:int(v) for k, v in self.RE_CONTENT_RANGE.match(self.header('Content-Range')).groupdict().items()}
        self.data_start = range_dict['data_start']
        self.data_end = range_dict['data_end']
        self.size = range_dict['size']
        assert len(chunk) == self.chunk_size, 'Content-Range does not match filesize'

        # Identify user session
        #   This is probably not wise to hash the cookie.
        #   The cookie could change at at any point, (hopefully not during an upload).
        #   Could be a sbaility bug waiting to happen
        self.session_id = self.header('Session-ID') or hash_data(self.header('Cookie'))
        assert self.session_id

        try:
            os.makedirs(os.path.dirname(self.path_chunk_current))
        except os.error:
            pass
        with open(self.path_chunk_current, 'wb') as f:
            f.write(chunk)

    def header(self, header_name):
        return self.request.headers.get(header_name) or self.request.headers.get('X-{0}'.format(header_name))

    @property
    def chunk_size(self):
        return self.data_end - self.data_start + 1

    @property
    @lru_cache()
    def path(self):
        return os.path.join(self._path_upload, '{0}-{1}'.format(self.name, self.session_id))

    @property
    @lru_cache()
    def path_destination(self):
        return os.path.join(self._path_upload, self.name)

    @property
    @lru_cache()
    def chunk_filenames(self):
        return tuple(os.path.join(self.path, filename) for filename in sorted(os.listdir(self.path), key=lambda f: '{0}-{1}'.format(len(f),f)))

    @property
    @lru_cache()
    def bytes_recived(self):
        bytes_recived = sum(os.path.getsize(filename) for filename in self.chunk_filenames)
        if bytes_recived >= self.size:
            import pdb ; pdb.set_trace()
        assert bytes_recived < self.size, 'recived more data than total filesize'
        return bytes_recived

    @property
    def progress(self):
        return (self.bytes_recived + 1) / self.size

    @property
    def range_recived(self):
        """
        Spec states a range string should be provided in the response
        Although the spec states that the chunks can arrive in any order,
        There is no mention of how it reports this.
        """
        return "{start}-{end}/{size}".format(start=0, end=self.bytes_recived, size=self.size)

    @property
    def complete(self):
        return self.bytes_recived + 1 == self.size  # +1 because we include the 0'th position

    @property
    @lru_cache()
    def path_chunk_current(self):
        return os.path.join(self.path, str(self.data_start))

    def cleanup_chunks(self):
        """
        Remove all traces of all files associated with this upload
        """
        try:
            log.info('Cleaning up chunks for {0}'.format(self.path))
            shutil.rmtree(self.path)
        except os.error:
            log.warn('unable to remove'.format(self.path))

    def cleanup_destination(self):
        try:
            log.info('Cleaning up destination for {0}'.format(self.path_destination))
            os.remove(self.path_destination)
        except os.error:
            log.warn('unable to remove'.format(self.path_destination))


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

    def files(self):
        return (self, )
        

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
    
    def __init__(self, request):
        self.request = request
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
        return pyramid.response.Response(body='')

    @view_config(request_method='HEAD')
    def head(self):
        log.info('head')
        return pyramid.response.Response(body='')

    @view_config(request_method='GET', renderer="json")
    def get(self):
        log.info('get')
        filename = self.request.matchdict.get('name')
        return [f for f in os.listdir(self._path_upload())]

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
            handler = FileUploadHandlerChunked(self.request)
            if handler.complete:
                log.debug('Reconstituting file {0}'.format(handler.name))
                handler.reconstitue_chunked_file()
            else:
                log.debug('Recived chunk {0} of {1}'.format(handler.range_recived, handler.name))
                self.request.response.status_code = 201
                self.request.response.headerlist.append(('Range', handler.range_recived))
                return handler.range_recived
        else:
            handler = FileUploadHandlerMultiple(self.request)
        
        files = []
        for file_handle in handler.files():
            file = {attr: getattr(file_handle, attr) for attr in ('name', 'type', 'size')}
            #if self._validate(result):
                #with open( self.imagepath(result['name'] + '.type'), 'w') as f:
                #    f.write(result['type'])
                #self.createthumbnail(result['name'])

            file['delete_type'] = self.DELETEMETHOD
            file['delete_url'] = self.request.route_url('upload') + '/' + file['name']
            file['url'] = 'needs_implementing' # self.request.route_url('comunity',)
            if self.DELETEMETHOD != 'DELETE':
                file['delete_url'] += '&_method=DELETE'
                #if (IMAGE_TYPES.match(result['type'])):
                #    try:
                #        result['thumbnail_url'] = self.thumbnailurl(result['name'])
                #    except: # Could not get an image serving url
                #        pass
            files.append(file)
        log.debug(files)
        return {'files': files}
