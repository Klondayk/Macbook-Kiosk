// Function to update the laptop status
function updateLaptopStatus() {
    fetch('/get_laptop_status')
        .then(response => response.json())
        .then(data => {
            // Update the laptop count in the UI
            const laptopCountElement = document.getElementById('amount__info-id');
            if (laptopCountElement) {
                laptopCountElement.textContent = data.laptop_count;
            }
        })
        .catch(error => {
            console.error('Error fetching laptop status:', error);
        });
}

// Function to check if the user is on the home page or a relevant page
function isRelevantPage() {
    return window.location.pathname === '/';  // Adjust this path to your actual page if needed
}

// Start the polling only if the user is on the relevant page
if (isRelevantPage()) {
    var laptopStatusInterval = setInterval(updateLaptopStatus, 5000);  // Poll every 5 seconds
}
