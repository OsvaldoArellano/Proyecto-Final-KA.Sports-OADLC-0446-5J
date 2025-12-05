
const menuBtn = document.getElementById('menu-btn');
const menu = document.getElementById('menu');
const dropdown = document.getElementById('dropdown');
const dropdownToggle = dropdown ? dropdown.querySelector('.dropdown-toggle') : null;

// Alternar menú hamburguesa
menuBtn.addEventListener('click', () => {
    menu.classList.toggle('active');
    menuBtn.classList.toggle('active');
});


if (dropdown && dropdownToggle) {
    dropdownToggle.addEventListener('click', (e) => {
        
        if (window.innerWidth > 768) {
            return;
        }
        
        
        e.preventDefault();
        dropdown.classList.toggle('active');
    });
}


document.querySelectorAll('.menu a').forEach(link => {
    link.addEventListener('click', () => {
        
        if (window.innerWidth <= 768 && link === dropdownToggle) {
            return;
        }
        
        menuBtn.classList.remove('active');
        menu.classList.remove('active');
        if (dropdown) {
            dropdown.classList.remove('active');
        }
    });
});


document.addEventListener('click', (e) => {
    if (window.innerWidth > 768) return;
    
    if (!dropdown.contains(e.target) && !menuBtn.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});
