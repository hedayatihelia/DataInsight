function launchAlgorithm() {
    const selectedAlgorithm = document.getElementById('algorithm-options').value;
    const algorithmTitle = document.getElementById('algorithm-title');
    const bfrcontent = document.getElementById('bfr-upload');
    const pcycontent = document.getElementById('pcy-upload');
    const winnowcontent = document.getElementById('winnow-upload');
    const algorithmForm = document.getElementById('algorithm-form');
    const selectedAlgorithmInput = document.getElementById('selected-algorithm');

    bfrcontent.classList.add('hidden');
    pcycontent.classList.add('hidden');
    winnowcontent.classList.add('hidden');

    selectedAlgorithmInput.value = selectedAlgorithm;

    if (selectedAlgorithm === 'bfr') {
        bfrcontent.classList.remove('hidden');
        algorithmTitle.textContent = 'Launching BFR Algorithm';
    } else if (selectedAlgorithm === 'pcy') {
        pcycontent.classList.remove('hidden');
        algorithmTitle.textContent = 'Launching PCY Algorithm';
    } else if (selectedAlgorithm === 'winnow') {
        winnowcontent.classList.remove('hidden');
        algorithmTitle.textContent = 'Launching Winnow Algorithm';
    }
}

function validateForm() {
    const selectedAlgorithm = document.getElementById('selected-algorithm').value;
    let isValid = true;
    let errorMessage = '';

    if (selectedAlgorithm === 'bfr') {
        const fileInput = document.getElementById('bfr-file');
        const threshold = document.getElementById('bfr-threshold').value.trim();
        const clusters = document.getElementById('clusters').value.trim();
        const columns = document.getElementById('columns').value.trim();

        if (fileInput.files.length === 0) {
            isValid = false;
            errorMessage += 'Please select a data file.\n';
        }

        if (threshold === '') {
            isValid = false;
            errorMessage += 'Threshold is required.\n';
        } else if (isNaN(threshold) || threshold < 0) {
            isValid = false;
            errorMessage += 'Threshold must be a non-negative number.\n';
        }

        if (clusters === '') {
            isValid = false;
            errorMessage += 'Number of clusters is required.\n';
        } else if (!Number.isInteger(Number(clusters)) || clusters < 1) {
            isValid = false;
            errorMessage += 'Number of clusters must be a positive integer.\n';
        }

        if (columns === '') {
            isValid = false;
            errorMessage += 'Columns field is required.\n';
        } else {
            const columnNames = columns.split(',').map(col => col.trim());
            if (columnNames.length !== 2 || columnNames.some(col => col === '')) {
                isValid = false;
                errorMessage += 'Please provide two column names separated by a comma.\n';
            } else if (fileInput.files.length > 0) {
                // Validate column names with the server
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('columns', columns);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/validate_columns', false);
                xhr.onload = function() {
                    const response = JSON.parse(xhr.responseText);
                    if (!response.is_valid) {
                        isValid = false;
                        errorMessage += 'Column names must exist in the dataset.\n';
                    }
                };
                xhr.send(formData);
            }
        }
    }

    if (!isValid) {
        showErrorPopup(errorMessage);
    }

    return isValid;
}

document.addEventListener('DOMContentLoaded', function() {
    const thresholdInput = document.getElementById('bfr-threshold');
    const clustersInput = document.getElementById('clusters');

    thresholdInput.addEventListener('input', restrictToPositiveIntegers);
    clustersInput.addEventListener('input', restrictToPositiveIntegers);
});

function restrictToPositiveIntegers(event) {
    const input = event.target;
    const value = input.value;

    // Remove any non-digit characters
    input.value = value.replace(/[^0-9]/g, '');
}

function showErrorPopup(message) {
    const errorPopup = document.getElementById('error-popup');
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorPopup.style.display = 'block';
}

function closeErrorPopup() {
    const errorPopup = document.getElementById('error-popup');
    errorPopup.style.display = 'none';
}
