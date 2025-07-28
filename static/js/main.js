/**
 * Korean Learning Platform - Main JavaScript
 * Handles interactive features and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeAnimations();
    initializeFormValidation();
    initializeSearchFeatures();
    initializeNotifications();
    initializeDeleteButtons();

    console.log('Korean Learning Platform initialized');
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize scroll animations and hover effects
 */
function initializeAnimations() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Fade in animation for cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all cards for animation
    document.querySelectorAll('.card, .feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

/**
 * Enhanced form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Real-time validation for specific fields
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateEmail(this);
        });
    });

    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        field.addEventListener('input', function() {
            validatePassword(this);
        });
    });
}

/**
 * Email validation
 */
function validateEmail(emailField) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(emailField.value);

    updateFieldValidation(emailField, isValid, '유효한 이메일 주소를 입력해주세요.');
    return isValid;
}

/**
 * Password validation
 */
function validatePassword(passwordField) {
    const password = passwordField.value;
    const minLength = 6;
    let isValid = true;
    let message = '';

    if (password.length < minLength) {
        isValid = false;
        message = `비밀번호는 최소 ${minLength}자 이상이어야 합니다.`;
    }

    updateFieldValidation(passwordField, isValid, message);
    return isValid;
}

/**
 * Update field validation state
 */
function updateFieldValidation(field, isValid, message) {
    const feedbackDiv = field.parentNode.querySelector('.invalid-feedback') || 
                       field.parentNode.querySelector('.valid-feedback');

    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        if (feedbackDiv) {
            feedbackDiv.textContent = '올바른 형식입니다.';
            feedbackDiv.className = 'valid-feedback';
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        if (feedbackDiv) {
            feedbackDiv.textContent = message;
            feedbackDiv.className = 'invalid-feedback';
        } else {
            // Create feedback element
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = message;
            field.parentNode.appendChild(feedback);
        }
    }
}

/**
 * Initialize search features
 */
function initializeSearchFeatures() {
    const searchInputs = document.querySelectorAll('.search-input, #searchInput');

    searchInputs.forEach(input => {
        // Add search suggestions
        input.addEventListener('input', function() {
            handleSearchInput(this);
        });

        // Clear search button
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-outline-secondary btn-sm';
        clearBtn.innerHTML = '<i class="fas fa-times"></i>';
        clearBtn.style.position = 'absolute';
        clearBtn.style.right = '10px';
        clearBtn.style.top = '50%';
        clearBtn.style.transform = 'translateY(-50%)';
        clearBtn.style.display = 'none';

        // Position the input container relatively
        if (input.parentNode.style.position !== 'relative') {
            input.parentNode.style.position = 'relative';
        }

        clearBtn.addEventListener('click', function() {
            input.value = '';
            input.focus();
            this.style.display = 'none';
            input.dispatchEvent(new Event('input'));
        });

        input.parentNode.appendChild(clearBtn);

        input.addEventListener('input', function() {
            clearBtn.style.display = this.value ? 'block' : 'none';
        });
    });
}

/**
 * Handle search input with debouncing
 */
function handleSearchInput(input) {
    clearTimeout(input.searchTimeout);

    input.searchTimeout = setTimeout(function() {
        const query = input.value.trim();

        if (query.length >= 2) {
            // Show search suggestions or trigger search
            showSearchSuggestions(input, query);
        } else {
            hideSearchSuggestions(input);
        }
    }, 300);
}

/**
 * Show search suggestions
 */
function showSearchSuggestions(input, query) {
    // This would typically fetch suggestions from server
    // For now, show basic suggestions based on context

    let suggestions = [];

    // Context-aware suggestions
    if (window.location.pathname.includes('english')) {
        suggestions = getEnglishWordSuggestions(query);
    } else if (window.location.pathname.includes('korean')) {
        suggestions = getKoreanWordSuggestions(query);
    }

    if (suggestions.length > 0) {
        displaySuggestions(input, suggestions);
    }
}

/**
 * Get English word suggestions
 */
function getEnglishWordSuggestions(query) {
    const commonWords = [
        'beautiful', 'education', 'knowledge', 'student', 'teacher',
        'school', 'book', 'learn', 'study', 'language', 'english',
        'computer', 'technology', 'science', 'mathematics', 'history'
    ];

    return commonWords.filter(word => 
        word.toLowerCase().startsWith(query.toLowerCase())
    ).slice(0, 5);
}

/**
 * Get Korean word suggestions
 */
function getKoreanWordSuggestions(query) {
    const commonWords = [
        '소생', '나리', '상감', '마마', '어르신', '할아버지', '할머니'
    ];

    return commonWords.filter(word => 
        word.includes(query)
    ).slice(0, 5);
}

/**
 * Display search suggestions
 */
function displaySuggestions(input, suggestions) {
    // Remove existing suggestions
    hideSearchSuggestions(input);

    const suggestionList = document.createElement('div');
    suggestionList.className = 'search-suggestions position-absolute bg-white border rounded shadow-sm';
    suggestionList.style.top = '100%';
    suggestionList.style.left = '0';
    suggestionList.style.right = '0';
    suggestionList.style.zIndex = '1000';
    suggestionList.style.maxHeight = '200px';
    suggestionList.style.overflowY = 'auto';

    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item px-3 py-2 cursor-pointer';
        item.textContent = suggestion;
        item.style.cursor = 'pointer';

        item.addEventListener('click', function() {
            input.value = suggestion;
            hideSearchSuggestions(input);

            // Trigger search if applicable
            if (typeof searchWord === 'function') {
                searchWord();
            }
        });

        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });

        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'transparent';
        });

        suggestionList.appendChild(item);
    });

    input.parentNode.appendChild(suggestionList);
}

/**
 * Hide search suggestions
 */
function hideSearchSuggestions(input) {
    const existingSuggestions = input.parentNode.querySelector('.search-suggestions');
    if (existingSuggestions) {
        existingSuggestions.remove();
    }
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                fadeOutElement(alert);
            }
        }, 5000);
    });

    // Add close functionality to alerts
    document.querySelectorAll('.alert .btn-close').forEach(btn => {
        btn.addEventListener('click', function() {
            fadeOutElement(this.closest('.alert'));
        });
    });
}

/**
 * Fade out element with animation
 */
function fadeOutElement(element) {
    element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    element.style.opacity = '0';
    element.style.transform = 'translateY(-10px)';

    setTimeout(() => {
        if (element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }, 500);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';

    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            fadeOutElement(notification);
        }
    }, duration);

    return notification;
}

/**
 * Quiz utilities
 */
const QuizUtils = {
    /**
     * Shuffle array
     */
    shuffleArray: function(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    },

    /**
     * Calculate percentage
     */
    calculatePercentage: function(correct, total) {
        if (total === 0) return 0;
        return Math.round((correct / total) * 100);
    },

    /**
     * Get grade based on percentage
     */
    getGrade: function(percentage) {
        if (percentage >= 90) return { grade: 'A', message: '완벽합니다! 🏆', color: 'success' };
        if (percentage >= 80) return { grade: 'B', message: '훌륭합니다! 👏', color: 'success' };
        if (percentage >= 70) return { grade: 'C', message: '잘했습니다! 👍', color: 'warning' };
        if (percentage >= 60) return { grade: 'D', message: '좋습니다! 📚', color: 'warning' };
        return { grade: 'F', message: '더 열심히 공부해보세요! 💪', color: 'danger' };
    }
};

/**
 * File upload utilities
 */
const FileUtils = {
    /**
     * Format file size
     */
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Validate file type
     */
    validateFileType: function(file, allowedTypes) {
        return allowedTypes.includes(file.type);
    },

    /**
     * Validate file size
     */
    validateFileSize: function(file, maxSize) {
        return file.size <= maxSize;
    }
};

/**
 * Local storage utilities
 */
const StorageUtils = {
    /**
     * Save to local storage
     */
    save: function(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('Failed to save to localStorage:', e);
            return false;
        }
    },

    /**
     * Load from local storage
     */
    load: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Failed to load from localStorage:', e);
            return defaultValue;
        }
    },

    /**
     * Remove from local storage
     */
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Failed to remove from localStorage:', e);
            return false;
        }
    }
};

/**
 * Theme utilities (White theme only)
 */
const ThemeUtils = {
    /**
     * Force white theme
     */
    initializeTheme: function() {
        // Always use white theme
        document.body.classList.remove('dark-mode');
        StorageUtils.save('theme', 'light');
    }
};

/**
 * Pomodoro Timer
 */
const PomodoroTimer = {
    state: {
        isRunning: false,
        currentTime: 25 * 60, // 25분 기본값
        totalTime: 25 * 60,
        isBreak: false,
        timer: null,
        notificationPermission: false
    },

    init: function() {
        this.requestNotificationPermission();
        this.loadSettings();
        this.fetchQuote();
        this.updateDisplay();
        this.bindEvents();
    },

    requestNotificationPermission: function() {
        if ('Notification' in window) {
            Notification.requestPermission().then(permission => {
                this.state.notificationPermission = permission === 'granted';
            });
        }
    },

    loadSettings: function() {
        const settings = StorageUtils.load('pomodoroSettings', {
            focusTime: 25,
            breakTime: 5,
            soundEnabled: true
        });
        
        document.getElementById('focusTime').value = settings.focusTime;
        document.getElementById('breakTime').value = settings.breakTime;
        document.getElementById('soundEnabled').checked = settings.soundEnabled;
        
        this.state.currentTime = settings.focusTime * 60;
        this.state.totalTime = settings.focusTime * 60;
    },

    saveSettings: function() {
        const settings = {
            focusTime: parseInt(document.getElementById('focusTime').value),
            breakTime: parseInt(document.getElementById('breakTime').value),
            soundEnabled: document.getElementById('soundEnabled').checked
        };
        StorageUtils.save('pomodoroSettings', settings);
    },

    fetchQuote: function() {
        fetch('https://korean-advice-open-api.vercel.app/api/advice')
            .then(response => response.json())
            .then(data => {
                document.getElementById('quoteText').textContent = data.message;
                document.getElementById('quoteAuthor').textContent = `- ${data.author} (${data.authorProfile})`;
            })
            .catch(error => {
                console.error('명언 로딩 실패:', error);
                document.getElementById('quoteText').textContent = '성공은 준비와 기회가 만나는 곳에서 일어난다.';
                document.getElementById('quoteAuthor').textContent = '- 바비 언저';
            });
    },

    bindEvents: function() {
        document.getElementById('startBtn').addEventListener('click', () => this.start());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pause());
        document.getElementById('resetBtn').addEventListener('click', () => this.reset());
        document.getElementById('settingsBtn').addEventListener('click', () => this.showSettings());
        document.getElementById('saveSettingsBtn').addEventListener('click', () => this.applySettings());
        document.getElementById('newQuoteBtn').addEventListener('click', () => this.fetchQuote());
    },

    start: function() {
        if (!this.state.isRunning) {
            this.state.isRunning = true;
            this.state.timer = setInterval(() => this.tick(), 1000);
            
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('pauseBtn').style.display = 'inline-block';
            
            this.updateProgress();
        }
    },

    pause: function() {
        this.state.isRunning = false;
        clearInterval(this.state.timer);
        
        document.getElementById('startBtn').style.display = 'inline-block';
        document.getElementById('pauseBtn').style.display = 'none';
    },

    reset: function() {
        this.pause();
        
        const settings = StorageUtils.load('pomodoroSettings', { focusTime: 25, breakTime: 5 });
        this.state.currentTime = this.state.isBreak ? settings.breakTime * 60 : settings.focusTime * 60;
        this.state.totalTime = this.state.currentTime;
        
        this.updateDisplay();
        this.updateProgress();
    },

    tick: function() {
        this.state.currentTime--;
        
        if (this.state.currentTime <= 0) {
            this.complete();
        }
        
        this.updateDisplay();
        this.updateProgress();
    },

    complete: function() {
        this.pause();
        
        const settings = StorageUtils.load('pomodoroSettings', { focusTime: 25, breakTime: 5, soundEnabled: true });
        
        // 알림 표시
        if (this.state.notificationPermission) {
            const title = this.state.isBreak ? '휴식 시간 완료!' : '집중 시간 완료!';
            const message = this.state.isBreak ? '다시 집중할 시간입니다.' : '잠시 휴식을 취하세요.';
            new Notification(title, { body: message, icon: '/static/favicon.ico' });
        }
        
        // 소리 재생
        if (settings.soundEnabled) {
            this.playNotificationSound();
        }
        
        // 자동 전환
        this.state.isBreak = !this.state.isBreak;
        this.state.currentTime = this.state.isBreak ? settings.breakTime * 60 : settings.focusTime * 60;
        this.state.totalTime = this.state.currentTime;
        
        this.updateDisplay();
        this.updateProgress();
        
        // 새로운 명언 가져오기
        this.fetchQuote();
        
        showNotification(
            this.state.isBreak ? '휴식 시간이 시작되었습니다!' : '집중 시간이 시작되었습니다!',
            'info',
            5000
        );
    },

    playNotificationSound: function() {
        // Web Audio API를 사용한 간단한 알림음
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1);
        
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 1);
    },

    updateDisplay: function() {
        const minutes = Math.floor(this.state.currentTime / 60);
        const seconds = this.state.currentTime % 60;
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        document.getElementById('timerDisplay').textContent = display;
        document.getElementById('timerStatus').textContent = this.state.isBreak ? '휴식 시간' : '집중 시간';
        
        // 파비콘에 시간 표시 (선택사항)
        document.title = `${display} - ${this.state.isBreak ? '휴식' : '집중'} | WackyDocs`;
    },

    updateProgress: function() {
        const progress = ((this.state.totalTime - this.state.currentTime) / this.state.totalTime) * 100;
        const circle = document.getElementById('progressCircle');
        const circumference = 2 * Math.PI * 90; // 반지름 90
        const offset = circumference - (progress / 100) * circumference;
        
        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = offset;
        circle.style.stroke = this.state.isBreak ? '#28a745' : '#007bff';
    },

    showSettings: function() {
        const modal = new bootstrap.Modal(document.getElementById('timerSettingsModal'));
        modal.show();
    },

    applySettings: function() {
        this.saveSettings();
        
        const settings = StorageUtils.load('pomodoroSettings');
        this.state.currentTime = this.state.isBreak ? settings.breakTime * 60 : settings.focusTime * 60;
        this.state.totalTime = this.state.currentTime;
        
        this.updateDisplay();
        this.updateProgress();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('timerSettingsModal'));
        modal.hide();
        
        showNotification('설정이 저장되었습니다!', 'success');
    }
};

/**
 * Performance monitoring
 */
const PerformanceUtils = {
    /**
     * Measure page load time
     */
    measurePageLoad: function() {
        window.addEventListener('load', function() {
            const loadTime = performance.now();
            console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);

            // Send to analytics if available
            if (typeof gtag !== 'undefined') {
                gtag('event', 'page_load_time', {
                    value: Math.round(loadTime)
                });
            }
        });
    },

    /**
     * Debounce function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Initialize theme and performance monitoring
ThemeUtils.initializeTheme();
PerformanceUtils.measurePageLoad();


/**
 * Initialize delete buttons for vocab and categories
 */
function initializeDeleteButtons() {
    // 어휘 삭제
    document.querySelectorAll('.vocab-delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const vocabId = this.dataset.id;
            if (confirm('정말 이 어휘를 삭제하시겠습니까?')) {
                fetch(`/vocab/delete/${vocabId}`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.closest('.vocab-item').remove();
                        showNotification('어휘가 삭제되었습니다.', 'success');
                    } else {
                        showNotification('삭제에 실패했습니다.', 'danger');
                    }
                });
            }
        });
    });

    // 카테고리 삭제
    document.querySelectorAll('.category-delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const categoryId = this.dataset.id;
            if (confirm('정말 이 카테고리를 삭제하시겠습니까?')) {
                fetch(`/category/delete/${categoryId}`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        this.closest('.category-item').remove();
                        showNotification('카테고리가 삭제되었습니다.', 'success');
                    } else {
                        showNotification('삭제에 실패했습니다.', 'danger');
                    }
                });
            }
        });
    });
}

// CSRF 토큰 가져오기 (Flask-WTF 사용 시)
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}


// Export utilities for use in other scripts
window.KoreanLearningPlatform = {
    QuizUtils,
    FileUtils,
    StorageUtils,
    ThemeUtils,
    PerformanceUtils,
    PomodoroTimer,
    showNotification,
    fadeOutElement
};