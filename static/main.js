document.addEventListener('DOMContentLoaded', function() {
    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 3000);
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Confirm delete action
    document.querySelectorAll('form[action*="/delete"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this post?')) {
                e.preventDefault();
            }
        });
    });

    // Basic search functionality (redirects to search page)
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = searchInput.value.trim();
            
            if (query) {
                // Redirect to search page with query parameter
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        });
    }
    
    // Live search functionality (for blog.html)
    const blogSearchInput = document.getElementById('blog-search-input');
    const postsContainer = document.getElementById('posts-container');
    
    if (blogSearchInput && postsContainer) {
        let debounceTimer;
        
        blogSearchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const query = this.value.trim().toLowerCase();
                
                if (query.length >= 2) {
                    // Perform live search via AJAX
                    fetch(`/search?q=${encodeURIComponent(query)}`, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            showErrorMessage(data.error);
                        } else {
                            updateSearchResults(data.posts);
                        }
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                        showErrorMessage('An error occurred while searching.');
                    });
                } else if (query.length === 0) {
                    // If search is cleared, load all posts
                    fetch('/search', {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        updateSearchResults(data.posts);
                    })
                    .catch(error => {
                        console.error('Error loading posts:', error);
                    });
                }
            }, 300); // 300ms debounce
        });
    }
    
    // For advanced search form
    const advancedSearchForm = document.getElementById('advanced-search-form');
    if (advancedSearchForm) {
        // Validate date inputs
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        
        if (startDateInput && endDateInput) {
            advancedSearchForm.addEventListener('submit', function(e) {
                if (startDateInput.value && endDateInput.value) {
                    const startDate = new Date(startDateInput.value);
                    const endDate = new Date(endDateInput.value);
                    
                    if (startDate > endDate) {
                        e.preventDefault();
                        alert('End date must be after start date.');
                    }
                }
            });
        }
    }
    
    // Helper function to update search results
    function updateSearchResults(posts) {
        // Clear existing posts
        postsContainer.innerHTML = '';
        
        if (posts && posts.length > 0) {
            posts.forEach(post => {
                const postElement = document.createElement('div');
                postElement.className = 'post card';
                postElement.id = `post-${post.id}`;
                
                postElement.innerHTML = `
                    <h2 class="post-title">${post.title}</h2>
                    <p class="post-content">${post.content.length > 200 ? post.content.substring(0, 200) + '...' : post.content}</p>
                    <p class="post-meta">By <span class="post-author">${post.author}</span> on <span class="post-date">${post.date}</span></p>
                    <a href="/blog#post-${post.id}" class="read-more">Read full post</a>
                `;
                
                postsContainer.appendChild(postElement);
            });
        } else {
            const noResults = document.createElement('p');
            noResults.id = 'no-results';
            noResults.textContent = 'No posts found matching your search criteria.';
            postsContainer.appendChild(noResults);
        }
    }
    
    // Helper function to show error message
    function showErrorMessage(message) {
        postsContainer.innerHTML = `<p class="error-message">${message}</p>`;
    }
});