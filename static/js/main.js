let currentLanguage = 'english'; // Default language

function changeLanguage(language) {
    currentLanguage = language;
    // Send the selected language to the server
    fetch('/set_language', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: currentLanguage })
    })
    .then(response => response.json())
    .then(data => {
        // After setting the language in the session, update the page text
        Object.keys(data).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.textContent = data[key];
            }
        });
    })
    .catch(error => console.error('Error loading language:', error));
}

// Event listeners for language buttons on the homepage
document.getElementById('english-btn').addEventListener('click', function(event) {
    event.preventDefault();
    changeLanguage('english');
});

document.getElementById('russian-btn').addEventListener('click', function(event) {
    event.preventDefault();
    changeLanguage('russian');
});

document.getElementById('kazakh-btn').addEventListener('click', function(event) {
    event.preventDefault();
    changeLanguage('kazakh');
});
