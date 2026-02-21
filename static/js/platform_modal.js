document.addEventListener('DOMContentLoaded', function () {
    var saveBtn = document.getElementById('savePlatformBtn');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', function () {
        var nameInput = document.getElementById('newPlatformName');
        var errorDiv = document.getElementById('platformError');
        var name = nameInput.value.trim();

        if (!name) {
            errorDiv.textContent = 'Please enter a platform name';
            errorDiv.style.display = 'block';
            return;
        }

        fetch('/api/platforms/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ name: name })
        })
        .then(function (response) {
            if (!response.ok) return response.json().then(function (err) { return Promise.reject(err); });
            return response.json();
        })
        .then(function (data) {
            var select = document.getElementById('id_platform');
            var option = new Option(data.name, data.id, true, true);
            select.add(option);

            nameInput.value = '';
            errorDiv.style.display = 'none';
            bootstrap.Modal.getInstance(document.getElementById('addPlatformModal')).hide();
        })
        .catch(function (err) {
            errorDiv.textContent = err.name ? err.name[0] : 'Error creating platform';
            errorDiv.style.display = 'block';
        });
    });
});
