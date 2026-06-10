function updateThemeButton(){

    const themeToggle =
    document.getElementById(
        "themeToggle"
    );

    if(!themeToggle){
        return;
    }

    themeToggle.innerText =
    document.body.classList.contains(
        "dark"
    )
    ? "☀ Light Mode"
    : "🌙 Dark Mode";
}

function initializeTheme(){

    const savedTheme =
    localStorage.getItem(
        "theme"
    );

    if(savedTheme === "dark"){

        document.body.classList.add(
            "dark"
        );
    }

    updateThemeButton();

    const themeToggle =
    document.getElementById(
        "themeToggle"
    );

    if(!themeToggle){
        return;
    }

    themeToggle.addEventListener(
        "click",
        function(){

            document.body.classList.toggle(
                "dark"
            );

            const isDark =
            document.body.classList.contains(
                "dark"
            );

            localStorage.setItem(
                "theme",
                isDark
                ? "dark"
                : "light"
            );

            updateThemeButton();
        }
    );
}

document.addEventListener(
    "DOMContentLoaded",
    initializeTheme
);