function init() {
    // Инициализация значений слайдеров
    updateValue("outerRadius");
    updateValue("topTextSpacing");
    updateValue("centerTextSpacing");
    updateValue("bottomTextSpacing");
    updateValue("bottomTextPosition", "°");
    updateValue("innTextSpacing");
    updateValue("innTextPosition", "°");
    updateValue("ogrnTextSpacing");

    // Добавляем обработчик события для кнопки "Обновить печать"
    document.getElementById('updateStampButton').addEventListener('click', updateStamp);

    // Вызываем updateStamp() при изменении любого input или select
    document.querySelectorAll('input, select').forEach(element => {
        element.addEventListener('input', updateStamp);
    });

    // Инициализация печати при загрузке страницы
    updateStamp();
}

// Обновление значений слайдеров
function updateValue(id, suffix = "") {
    var slider = document.getElementById(id);
    var output = document.getElementById(id + "Value");
    output.innerHTML = slider.value + suffix;
    slider.oninput = function() {
        output.innerHTML = this.value + suffix;
    }
}

function updateStamp() {
    const canvas = document.getElementById('stampCanvas');
    const ctx = canvas.getContext('2d');
    const topText = document.getElementById('topText').value.toUpperCase();
    const centerText = document.getElementById('centerText').value.toUpperCase();
    const bottomText = document.getElementById('bottomText').value.toUpperCase();
    const inn = document.getElementById('innText').value;
    const ogrn = document.getElementById('ogrnText').value;

    const outerRadius = parseFloat(document.getElementById('outerRadius').value);
    const innerRadius = 120; // Фиксированное значение

    const topTextSpacing = parseFloat(document.getElementById('topTextSpacing').value);
    const centerTextSpacing = parseFloat(document.getElementById('centerTextSpacing').value);
    const bottomTextSpacing = parseFloat(document.getElementById('bottomTextSpacing').value);
    const innTextSpacing = parseFloat(document.getElementById('innTextSpacing').value);
    const ogrnTextSpacing = parseFloat(document.getElementById('ogrnTextSpacing').value);

    const topTextPosition = 0; // Фиксированное значение 0 градусов
    const bottomTextPosition = parseFloat(document.getElementById('bottomTextPosition').value) * Math.PI / 180;
    const innTextPosition = parseFloat(document.getElementById('innTextPosition').value) * Math.PI / 180;
    const ogrnTextPosition = 0; // Фиксированное значение 0 градусов

    const topTextAlignment = document.getElementById('topTextAlignment').value;
    const bottomTextAlignment = document.getElementById('bottomTextAlignment').value;
    const innTextAlignment = document.getElementById('innTextAlignment').value;
    const ogrnTextAlignment = document.getElementById('ogrnTextAlignment').value;

    // Очищаем canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Устанавливаем цвет печати
    ctx.strokeStyle = '#0000FF';
    ctx.fillStyle = '#0000FF';

    // Рисуем внешний и внутренний круг
    ctx.beginPath();
    ctx.arc(150, 150, outerRadius, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(150, 150, innerRadius, 0, 2 * Math.PI);
    ctx.stroke();

function drawTextAlongArc(text, centerX, centerY, radius, startAngle, letterSpacing, alignment = 'bottom', isReversed = false) {
    ctx.save();
    ctx.translate(centerX, centerY);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const textWidth = ctx.measureText(text).width + (text.length - 1) * letterSpacing;
    const textAngle = textWidth / radius;

    // Вычисляем начальный угол с учетом длины текста
    let angle;
    if (isReversed) {
        angle = startAngle + textAngle / 2;
    } else {
        angle = startAngle - textAngle / 2;
    }

    for (let i = 0; i < text.length; i++) {
        ctx.save();
        ctx.rotate(angle);
        ctx.translate(0, -radius);

        if (alignment === 'top' || isReversed) {
            ctx.rotate(Math.PI);
        }

        ctx.fillText(text[i], 0, 0);
        ctx.restore();

        // Вычисляем угол для следующей буквы
        const charWidth = ctx.measureText(text[i]).width;
        const angleChange = (charWidth + letterSpacing) / radius;
        angle += isReversed ? -angleChange : angleChange;
    }
    ctx.restore();
}

    // Размещаем верхний текст
    ctx.font = '12px Arial';
    drawTextAlongArc(topText, 150, 150, outerRadius - 6, topTextPosition, topTextSpacing, topTextAlignment);

    // Размещаем нижний текст
    drawTextAlongArc(bottomText, 150, 150, outerRadius - 6, bottomTextPosition, bottomTextSpacing, bottomTextAlignment, true);

    // Размещаем ИНН и ОГРН
    ctx.font = '12px Arial';
    drawTextAlongArc(`ИНН ${inn}`, 150, 150, innerRadius - 10, innTextPosition, innTextSpacing, innTextAlignment, true);
    drawTextAlongArc(`ОГРН ${ogrn}`, 150, 150, innerRadius - 10, ogrnTextPosition, ogrnTextSpacing, ogrnTextAlignment);

    // Размещаем название в центре
function drawCenterText(text, maxWidth, maxHeight, padding = 10) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Учитываем отступ при расчете максимальной ширины и высоты
    const adjustedMaxWidth = maxWidth - (padding * 2);
    const adjustedMaxHeight = maxHeight - (padding * 2);

    let fontSize = 30;
    let lines = [];

    function updateLines() {
        lines = [];
        let words = text.split(/\s+/);
        let currentLine = words[0];

        for (let i = 1; i < words.length; i++) {
            let word = words[i];
            let width = ctx.measureText(currentLine + " " + word).width;
            if (width < adjustedMaxWidth) {
                currentLine += " " + word;
            } else {
                lines.push(currentLine);
                currentLine = word;
            }
        }
        lines.push(currentLine);
    }

    // Уменьшаем размер шрифта, пока текст не поместится с учетом отступа
    do {
        ctx.font = `bold ${fontSize}px Arial`;
        updateLines();
        fontSize--;
    } while ((lines.length * fontSize > adjustedMaxHeight || ctx.measureText(lines[0]).width > adjustedMaxWidth) && fontSize > 10);

    // Отрисовка текста с учетом отступа
    let startY = 150 - (lines.length - 1) * fontSize / 2;
    for (let i = 0; i < lines.length; i++) {
        ctx.fillText(lines[i], 150, startY + i * fontSize);
    }
}

    drawCenterText(centerText, innerRadius * 2 - 20, innerRadius * 2 - 20);

    // Добавляем звездочки
    ctx.font = '16px Arial';
    ctx.fillText('*', 15, 150);
    ctx.fillText('*', 285, 150);
}

// Вызываем функцию init при загрузке страницы
window.onload = init;