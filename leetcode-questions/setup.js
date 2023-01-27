function import_from_url(url) {
    const script = document.createElement("script");
    script.type = "text/javascript";
    script.src = url;
    document.head.appendChild(script);
}

import_from_url("https://code.jquery.com/jquery-3.6.1.slim.min.js");
import_from_url("https://cdn.jsdelivr.net/npm/underscore@1.13.6/underscore-umd-min.js");
