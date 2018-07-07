
export function queryStringListOrInit(
    QUERY_STRING_KEY_index,  // query string key name to override index path (if omitted will take DEFAULT_PATH_index)
    QUERY_STRING_KEY_file, // query string key name for data file to load
    DEFAULT_PATH_index,  // If no index path is given in query string, default to this value
    initFunc,  // init function passed file data
    initFuncDefault,  // If data file cannot be loaded
    hostElement,  // The HTML Element to appendChild list
) {
    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.has(QUERY_STRING_KEY_file)) {
        const PATH = urlParams.get(QUERY_STRING_KEY_file);
        fetch(PATH)
            .then(response => response.json())
            .then(initFunc)
            .catch(error => {
                console.error(`Unable to load ${PATH}`, error);
                if (initFuncDefault) {
                    console.warn(`Falling back to default`)
                    initFuncDefault();
                }
            })
        ;
    } else {
        const PATH = urlParams.get(QUERY_STRING_KEY_index) || DEFAULT_PATH_index;
        function renderList(data) {
            // data is JSON_INDEX from nginx file listing
            const files = data.map(i => i.name).filter(i => i.indexOf('.json') >= 0);
            const elementContainer = document.createElement('div');
            for (const file of files) {
                const _urlParams = new URLSearchParams(urlParams);
                _urlParams.append(QUERY_STRING_KEY_file, PATH + file);
                elementContainer.insertAdjacentHTML('beforeend', `<li><a href="${window.location.pathname}?${_urlParams.toString()}">${file}</a></li>`);
            }
            const _hostElement = hostElement || document.getElementsByTagName('body').item(0);
            _hostElement.appendChild(elementContainer);
        }
        console.log(`Loading ${PATH}. You can optionally override this path with querystring param ${QUERY_STRING_KEY_index}`);
        fetch(PATH)
            .then(response => response.json())
            .then(data => renderList(data))
            .catch(error => {
                console.error(`Failed to list files from ${PATH}`, error);
                if (initFuncDefault) {
                    console.warn(`Falling back to default`)
                    initFuncDefault();
                }
            })
        ;
    }
}

export default {
    queryStringListOrInit,
}