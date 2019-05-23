
try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
except ImportError:
    def hachoir_metadata_dict(filename):
        raise Exception('hachoir library not installed')
else:
    def hachoir_metadata_dict(filename):
        _metadata = extractMetadata(createParser(filename))
        return {
            key: _metadata.get(key)
            for key in _metadata._Metadata__data.keys()
            if _metadata.has(key)
        }
