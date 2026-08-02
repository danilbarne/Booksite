// ============================
// ПЕРЕКЛЮЧЕНИЕ ТЕМЫ
// ============================

const themeButton = document.getElementById("themeButton");

// Загружаем сохранённую тему
if (localStorage.getItem("theme") === "light") {
    document.body.classList.add("light");
    themeButton.textContent = "☀";
} else {
    themeButton.textContent = "🌙";
}

// Переключение темы
themeButton.addEventListener("click", () => {

    document.body.classList.toggle("light");

    if (document.body.classList.contains("light")) {

        localStorage.setItem("theme", "light");
        themeButton.textContent = "☀";

    } else {

        localStorage.setItem("theme", "dark");
        themeButton.textContent = "🌙";

    }

});

// ============================
// ЗАКРЫТЫЕ РАЗДЕЛЫ
// ============================

function lockedSection(name) {

    document.getElementById("popupText").innerHTML =
        "<b>" + name + "</b><br><br>Этот раздел пока находится в разработке.<br><br>Следите за будущими обновлениями сайта.";

    document.getElementById("overlay").style.display = "flex";

}

// ============================
// ЗАКРЫТЬ ОКНО
// ============================

function closePopup() {

    document.getElementById("overlay").style.display = "none";

}

// Закрытие по клику на затемнение
document.getElementById("overlay").addEventListener("click", function (e) {

    if (e.target === this) {
        closePopup();
    }

});