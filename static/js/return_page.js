let currentLanguage = 'english';

function changeLanguage(language) {
    currentLanguage = language;
    fetch(`static/data/${language}.json`)
        .then(response => response.json())
        .then(data => {
            Object.keys(data).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.textContent = data[key];
                }
            });
        })
        .catch(error => console.error('Error loading language:', error));
}

// Установка фокуса на input
function setAutofocus() {
    const input = document.getElementById('stylish-input');
    if (input) {
        input.focus();
    }
}

// Load default language
changeLanguage(currentLanguage);



// Event listeners for language buttons
document.getElementById('english-btn').addEventListener('click', function(event) {
    event.preventDefault();
    changeLanguage('english');
    setAutofocus();
});

document.getElementById('russian-btn').addEventListener('click', function(event) {
    event.preventDefault();
    changeLanguage('russian');
    setAutofocus();
});

document.getElementById('kazakh-btn').addEventListener('click', function(event) {
    event.preventDefault();
    changeLanguage('kazakh');
    setAutofocus();
});




const barcodeInput = document.getElementById('stylish-input');
const barcodeList = document.getElementById('barcodeList');
const returnButton = document.createElement('button');

returnButton.textContent = 'Return';
returnButton.id = 'submitButton';
barcodeList.parentNode.appendChild(returnButton);

// Создайте кнопку отмены и добавьте ее рядом с кнопкой отправки
const cancelButton = document.createElement('button');
cancelButton.textContent = 'Cancel';
cancelButton.id = 'cancelButton';
cancelButton.style.marginLeft = '10px'; // Добавьте небольшой отступ
returnButton.parentNode.insertBefore(cancelButton, returnButton);

let deviceNumberCount = 0;
let scannedBarcodes = [];

loadScannedBarcodes();



barcodeInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();

        const barcodeString = barcodeInput.value.trim();

        // Validate the barcode format
        if (!isValidBarcode(barcodeString)) {
            Swal.fire({
                icon: 'error',  // Красная иконка ошибки
                title: 'Неверный штрихкод!',
                text: 'Пожалуйста, введите корректный штрихкод.',
                timer: 5000,  // Показывать уведомление 2,5 секунды
                showConfirmButton: false,  // Убирает кнопку "ОК"
                toast: true,  // Компактное уведомление
                position: 'top-end'  // Показывать в верхнем правом углу
            });
            barcodeInput.value = '';
            barcodeInput.focus();
            return;
        }

        if (barcodeString !== '') {
            // Check if the laptop exists in the database
            fetch('/check_laptop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ barcode: barcodeString })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {

                    if (scannedBarcodes.includes(barcodeString)) {
                        Swal.fire({
                            icon: 'info',  // Иконка уведомления (можно заменить на 'success', 'warning', 'error')
                            title: 'Макбук уже сканирован!',
                            text: 'Этот Макбук уже был добавлен в список.',
                            timer: 5000,  // Время показа (в миллисекундах) – 2 секунды
                            showConfirmButton: false,  // Убирает кнопку "ОК"
                            toast: true,  // Делает уведомление компактным
                            position: 'top-end'  // Размещает уведомление в углу экрана
                        });
                        barcodeInput.value = '';  // Clear the input field
                        barcodeInput.focus();  // Refocus the input field
                    } else {
                        // If the laptop exists, add it to the list
                        scannedBarcodes.push(barcodeString);

                        const listItem = document.createElement('li');
                        listItem.textContent = barcodeString;
                        listItem.classList.add('list-item');

                        const cancelButton = document.createElement('button');
                        cancelButton.textContent = 'X';
                        cancelButton.style.marginLeft = '10px';
                        cancelButton.classList.add('cancel-button');

                        listItem.appendChild(cancelButton);
                        barcodeList.appendChild(listItem);

                        cancelButton.addEventListener('click', function () {
                            removeScannedBarcode(barcodeString, listItem);
                        });

                        // Clear the input field and refocus for the next barcode
                        barcodeInput.value = '';
                        barcodeInput.focus();
                        saveScannedBarcodes();
                        scrollToButtons();
                    }
                } else {
                    // If the laptop is not found, show an alert
                    Swal.fire({
                        icon: 'error',
                        title: 'Макбук не найден',
                        text: data.message,
                        timer: 5000,  // Ошибка показывается дольше (3 секунды)
                        showConfirmButton: false,
                        toast: true,
                        position: 'top-end'
                    });
                    barcodeInput.value = '';
                    barcodeInput.focus();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Непредвиденная ошибка',
                        text: data.message,
                        timer: 5000,  // Ошибка показывается дольше (3 секунды)
                        showConfirmButton: false,
                        toast: true,
                        position: 'top-end'
                    });
                barcodeInput.value = '';
                barcodeInput.focus();
            });
        }
    }
});


// Функция для проверки валидности штрих-кода
function isValidBarcode(barcode) {
    const barcodePattern = /^[a-zA-Z0-9-\s]+$/; // Разрешает буквы, цифры, дефисы и пробелы
    return barcodePattern.test(barcode);
}

// Функция для удаления штрих-кодов
function removeScannedBarcode(barcodeString, listItem) {
    const index = scannedBarcodes.indexOf(barcodeString);
    if (index !== -1) {
        scannedBarcodes.splice(index, 1);
    }

    listItem.remove();

    saveScannedBarcodes();
}

// Создайте контейнер для кнопок
const buttonContainer = document.createElement('div');
buttonContainer.id = 'buttonContainer';

// Примените стили флекс-бокса к контейнеру
buttonContainer.style.display = 'flex';
buttonContainer.style.justifyContent = 'space-between'; // Распределяет кнопки по ширине контейнера
buttonContainer.style.alignItems = 'center'; // Выравнивает кнопки по вертикали
buttonContainer.style.marginTop = '10px'; // Отступ сверху контейнера
buttonContainer.style.paddingButtom = '100px'; // Отступ сверху контейнера

// Добавьте кнопки в контейнер
buttonContainer.appendChild(returnButton);
buttonContainer.appendChild(cancelButton);

// Вставьте контейнер после списка штрих-кодов
barcodeList.parentNode.insertBefore(buttonContainer, barcodeList.nextSibling);

// Функция для автоматической прокрутки к кнопкам
function scrollToButtons() {
    buttonContainer.scrollIntoView({ behavior: 'smooth' });
}





// Функция для сохранения отсканированных штрих-кодов в localStorage
function saveScannedBarcodes() {
    localStorage.setItem('scannedBarcodes', JSON.stringify(scannedBarcodes));
}

// Функция для загрузки отсканированных штрих-кодов из localStorage
function loadScannedBarcodes() {
    const savedBarcodes = JSON.parse(localStorage.getItem('scannedBarcodes'));
    if (savedBarcodes) {
        scannedBarcodes = savedBarcodes;
        deviceNumberCount = scannedBarcodes.length;
        renderScannedBarcodes();
    }
}

// Функция для отображения отсканированных штрих-кодов
function renderScannedBarcodes() {
    barcodeList.innerHTML = '';
    scannedBarcodes.forEach((barcodeString, index) => {
        const listItem = document.createElement('li');
        listItem.textContent = `${index + 1}. ${barcodeString}`;

        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'X';
        cancelButton.style.marginLeft = '10px';

        listItem.appendChild(cancelButton);

        cancelButton.addEventListener('click', function() {
            removeScannedBarcode(barcodeString, listItem);
        });

        barcodeList.appendChild(listItem);
    });
}


document.addEventListener('DOMContentLoaded', function() {


    // Event listener for the cancel button
cancelButton.addEventListener('click', function handleCancel(event) {
    event.preventDefault();

    // Send a request to Flask to clear the session
    fetch('/clear_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear the scanned barcodes from the local storage
            scannedBarcodes = [];
            localStorage.removeItem('scannedBarcodes');
            barcodeList.innerHTML = '';

            // Redirect to the homepage
	    fetch('/send_arduino_signal_on', { method: 'POST' });
            window.location.href = '/';
        } else {
            alert('Failed to clear the session.');
        }
    })
    .catch(error => {
        console.error('Error clearing session:', error);
    });

    // Reset the input field
    barcodeInput.value = '';
    barcodeInput.focus();
});
returnButton.addEventListener('click', function handleReturnSubmit(event) {
        event.preventDefault();

        if (scannedBarcodes.length === 0) {
            Swal.fire({
                icon: 'info',
                title: 'Пожалуйста отсканируйте Макбук',
                text: data.message,
                timer: 5000,  // Ошибка показывается дольше (3 секунды)
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
            return;
        }

        // Send scanned barcodes to the server to return the laptops
        fetch('/return_laptops', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ barcodes: scannedBarcodes })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Успешная бронь',
                    text: data.message,
                    timer: 5000,  // Ошибка показывается дольше (3 секунды)
                    showConfirmButton: false,
                    toast: true,
                    position: 'top-end'
                });
                scannedBarcodes = [];
                localStorage.removeItem('scannedBarcodes');  // Clear localStorage
                barcodeList.innerHTML = '';
		fetch('/send_arduino_signal_on', { method: 'POST' });
                window.location.href = '/';  // Redirect to home after successful return
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error returning laptops:', error);
        });
    });
});



