// Dynamic Search Suggestions
let searchTimeout = null;
const searchInput = document.querySelector('input[name="q"]');
const suggestionsContainer = document.createElement('div');
suggestionsContainer.className = 'search-suggestions';
suggestionsContainer.style.cssText = 'position:absolute;top:100%;left:0;right:0;background:white;border:1px solid #ddd;border-top:none;max-height:300px;overflow-y:auto;z-index:1000;display:none;box-shadow:0 4px 6px rgba(0,0,0,0.1);';

if (searchInput) {
    searchInput.parentElement.style.position = 'relative';
    searchInput.parentElement.appendChild(suggestionsContainer);

    searchInput.addEventListener('input', function () {
        const query = this.value.trim();

        clearTimeout(searchTimeout);

        if (query.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(() => {
            fetchSearchSuggestions(query);
        }, 300);
    });

    searchInput.addEventListener('blur', function () {
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });

    searchInput.addEventListener('focus', function () {
        if (suggestionsContainer.children.length > 0) {
            suggestionsContainer.style.display = 'block';
        }
    });
}

function fetchSearchSuggestions(query) {
    fetch(`/api/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySuggestions(data.results);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function displaySuggestions(results) {
    suggestionsContainer.innerHTML = '';

    if (results.length === 0) {
        suggestionsContainer.innerHTML = '<div style="padding:10px;color:#999;">No products found</div>';
        suggestionsContainer.style.display = 'block';
        return;
    }

    results.forEach(product => {
        const item = document.createElement('a');
        item.href = `/product/${product.id}/`;
        item.className = 'suggestion-item';
        item.style.cssText = 'display:flex;align-items:center;padding:10px;text-decoration:none;color:#333;border-bottom:1px solid #eee;transition:background 0.2s;';
        item.innerHTML = `
            <img src="${product.image}" alt="${product.name}" style="width:40px;height:40px;object-fit:cover;margin-right:10px;border-radius:4px;">
            <div>
                <div style="font-weight:bold;">${product.name}</div>
                <div style="font-size:12px;color:#666;">$${product.price}</div>
            </div>
        `;
        item.addEventListener('mouseenter', function () {
            this.style.background = '#f8f9fa';
        });
        item.addEventListener('mouseleave', function () {
            this.style.background = 'white';
        });
        suggestionsContainer.appendChild(item);
    });

    suggestionsContainer.style.display = 'block';
}

// Keyboard navigation for suggestions
document.addEventListener('keydown', function (e) {
    if (!searchInput) return;

    const items = suggestionsContainer.querySelectorAll('.suggestion-item');
    let currentIndex = -1;

    items.forEach((item, index) => {
        if (item.classList.contains('active')) {
            currentIndex = index;
        }
    });

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (currentIndex < items.length - 1) {
            if (currentIndex >= 0) items[currentIndex].classList.remove('active');
            currentIndex++;
            items[currentIndex].classList.add('active');
            items[currentIndex].style.background = '#e9ecef';
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (currentIndex > 0) {
            items[currentIndex].classList.remove('active');
            currentIndex--;
            items[currentIndex].classList.add('active');
            items[currentIndex].style.background = '#e9ecef';
        }
    } else if (e.key === 'Enter' && currentIndex >= 0) {
        e.preventDefault();
        items[currentIndex].click();
    }
});
