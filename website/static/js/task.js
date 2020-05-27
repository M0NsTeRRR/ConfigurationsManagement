'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const task_id = window.location.pathname.split('/')[3];

    let interval = setInterval(function () {
        axios.get(`/tasks/task/${task_id}?json`)
            .then(function(response){
                if(JSON.stringify(response.data) !== JSON.stringify(task_json)) {
                    document.location.reload(true);
                }
                else if(response.data.error === 1 || response.data.state === 4) {
                    clearInterval(interval);
                }
            })
            .catch(function (error) {
                console.log(error);
            });
    }, 5000);
});