document.addEventListener('DOMContentLoaded', function () {
    var saveNetworkBtn = document.getElementById('saveNetworkBtn');
    if (saveNetworkBtn) {
        saveNetworkBtn.addEventListener('click', function () {
            var nameInput = document.getElementById('newNetworkName');
            var errorDiv = document.getElementById('networkError');
            var name = nameInput.value.trim();

            if (!name) {
                errorDiv.textContent = 'Please enter a network name';
                errorDiv.style.display = 'block';
                return;
            }

            fetch('/api/networks/', {
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
                var select = document.getElementById('id_network');
                var option = new Option(data.name, data.id, true, true);
                select.add(option);

                nameInput.value = '';
                errorDiv.style.display = 'none';
                bootstrap.Modal.getInstance(document.getElementById('addNetworkModal')).hide();
            })
            .catch(function (err) {
                errorDiv.textContent = err.name ? err.name[0] : 'Error creating network';
                errorDiv.style.display = 'block';
            });
        });
    }

    var saveProxyVpnBtn = document.getElementById('saveProxyVpnBtn');
    if (saveProxyVpnBtn) {
        saveProxyVpnBtn.addEventListener('click', function () {
            var nameInput = document.getElementById('newProxyVpnName');
            var errorDiv = document.getElementById('proxyVpnError');
            var name = nameInput.value.trim();

            if (!name) {
                errorDiv.textContent = 'Please enter a proxy/VPN name';
                errorDiv.style.display = 'block';
                return;
            }

            fetch('/api/proxy-vpns/', {
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
                var select = document.getElementById('id_proxy_vpn');
                var option = new Option(data.name, data.id, true, true);
                select.add(option);

                nameInput.value = '';
                errorDiv.style.display = 'none';
                bootstrap.Modal.getInstance(document.getElementById('addProxyVpnModal')).hide();
            })
            .catch(function (err) {
                errorDiv.textContent = err.name ? err.name[0] : 'Error creating proxy/VPN';
                errorDiv.style.display = 'block';
            });
        });
    }

    var saveWalletProviderBtn = document.getElementById('saveWalletProviderBtn');
    if (saveWalletProviderBtn) {
        saveWalletProviderBtn.addEventListener('click', function () {
            var nameInput = document.getElementById('newWalletProviderName');
            var errorDiv = document.getElementById('walletProviderError');
            var name = nameInput.value.trim();

            if (!name) {
                errorDiv.textContent = 'Please enter a wallet provider name';
                errorDiv.style.display = 'block';
                return;
            }

            fetch('/api/wallet-providers/', {
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
                var select = document.getElementById('id_wallet_provider');
                var option = new Option(data.name, data.id, true, true);
                select.add(option);

                nameInput.value = '';
                errorDiv.style.display = 'none';
                bootstrap.Modal.getInstance(document.getElementById('addWalletProviderModal')).hide();
            })
            .catch(function (err) {
                errorDiv.textContent = err.name ? err.name[0] : 'Error creating wallet provider';
                errorDiv.style.display = 'block';
            });
        });
    }
});
