// Table Sorting JavaScript
function initTableSorting() {
    // Helper function to build sort URL
    function getSortUrl(column) {
        const urlParams = new URLSearchParams(window.location.search);
        const currentSort = urlParams.get('sort_by');
        const currentOrder = urlParams.get('sort_order') || 'desc';
        
        // Toggle order if same column, otherwise default to desc
        let newOrder = 'desc';
        if (currentSort === column) {
            newOrder = currentOrder === 'desc' ? 'asc' : 'desc';
        }
        
        urlParams.set('sort_by', column);
        urlParams.set('sort_order', newOrder);
        
        // Reset to page 1 when sorting
        urlParams.set('page', '1');
        
        return `?${urlParams.toString()}`;
    }
    
    // Add click handlers to sortable headers
    const sortableHeaders = document.querySelectorAll('.sortable-header');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column;
            window.location.href = getSortUrl(column);
        });
    });
    
    // Reset sort button
    const resetBtn = document.getElementById('resetSortBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.delete('sort_by');
            urlParams.delete('sort_order');
            urlParams.set('page', '1');
            
            const newParams = urlParams.toString();
            window.location.href = newParams ? `?${newParams}` : window.location.pathname;
        });
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTableSorting);
} else {
    initTableSorting();
}
