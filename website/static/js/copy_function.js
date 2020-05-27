'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);


    const content = document.getElementById('data');
    const btn_copy_content = document.getElementById('copy_data');

    const path = urlParams.get('path');
    const btn_copy_path = document.getElementById('copy_path');

    const api_key = document.getElementById('api_key');
    const btn_api_key = document.getElementById('copy_api_key');

    if(content && btn_copy_path) {
        btn_copy_content.addEventListener("click", function () {
            content.select();
            document.execCommand("copy");
            copy_animation(btn_copy_content);
        }, {passive: true});
    }

    if(path && btn_copy_path) {
        btn_copy_path.addEventListener("click", function () {
            var temp = document.createElement("textarea");
            document.body.appendChild(temp);
            temp.value = path;
            temp.select();
            document.execCommand("copy");
            copy_animation(btn_copy_path);
            document.body.removeChild(temp);
        }, {passive: true});
    }

    if(api_key && btn_api_key) {
        const api_key_type = api_key.type;
        btn_api_key.addEventListener("click", function () {
            if(api_key_type !== "text") {
                api_key.type = "text";
            }
            api_key.select();
            document.execCommand("copy");
            if(api_key_type !== "text") {
                api_key.type = api_key_type;
            }
            copy_animation(btn_api_key);
        }, {passive: true});
    }


    function copy_animation(btn) {
        btn.classList.add("is-loading");
        btn.classList.remove("is-link");
        btn.classList.add("is-warning");
        setTimeout(function(){
            btn.classList.remove("is-loading");
            btn.classList.remove("is-warning");
            btn.classList.add("is-link");
        }, 500);
    }
});