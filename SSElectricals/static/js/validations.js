// Form Validation Functions
const validationRules = {
    email: {
        pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        message: 'Please enter a valid email address'
    },
    phone: {
        pattern: /^\d{10}$/,
        message: 'Phone number must be exactly 10 digits'
    },
    password: {
        minLength: 8,
        requireUppercase: true,
        requireNumber: true,
        requireSymbol: true,
        messages: {
            minLength: 'Password must be at least 8 characters',
            uppercase: 'Password must contain at least one uppercase letter',
            number: 'Password must contain at least one number',
            symbol: 'Password must contain at least one special character'
        }
    },
    upi: {
        pattern: /^[\w.-]+@[\w.-]+$/,
        message: 'Invalid UPI ID format (e.g., username@upi)'
    }
};

function validateEmail(email) {
    return validationRules.email.pattern.test(email);
}

function validatePhone(phone) {
    return validationRules.phone.pattern.test(phone);
}

function validatePassword(password) {
    const errors = [];

    if (password.length < validationRules.password.minLength) {
        errors.push(validationRules.password.messages.minLength);
    }
    if (validationRules.password.requireUppercase && !/[A-Z]/.test(password)) {
        errors.push(validationRules.password.messages.uppercase);
    }
    if (validationRules.password.requireNumber && !/\d/.test(password)) {
        errors.push(validationRules.password.messages.number);
    }
    if (validationRules.password.requireSymbol && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        errors.push(validationRules.password.messages.symbol);
    }

    return errors;
}

function validateUPI(upi) {
    return validationRules.upi.pattern.test(upi);
}

function showError(field, message) {
    clearError(field);
    field.classList.add('is-invalid');
    field.style.borderColor = '#dc3545';

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.style.display = 'block';
    errorDiv.textContent = message;
    field.parentElement.appendChild(errorDiv);
}

function showSuccess(field) {
    clearError(field);
    field.classList.add('is-valid');
    field.style.borderColor = '#28a745';
}

function clearError(field) {
    field.classList.remove('is-invalid', 'is-valid');
    field.style.borderColor = '';
    const existingError = field.parentElement.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

// Real-time validation handlers
document.addEventListener('DOMContentLoaded', function () {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"], input[name*="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function () {
            if (this.value) {
                if (validateEmail(this.value)) {
                    showSuccess(this);
                } else {
                    showError(this, validationRules.email.message);
                }
            }
        });
    });

    // Phone validation
    const phoneInputs = document.querySelectorAll('input[name*="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '').slice(0, 10);
        });

        input.addEventListener('blur', function () {
            if (this.value) {
                if (validatePhone(this.value)) {
                    showSuccess(this);
                } else {
                    showError(this, validationRules.phone.message);
                }
            }
        });
    });

    // Password validation
    const passwordInputs = document.querySelectorAll('input[type="password"][name*="password"]');
    passwordInputs.forEach(input => {
        // Skip password confirmation fields
        if (input.name.includes('confirm') || input.name.includes('2')) return;

        input.addEventListener('blur', function () {
            if (this.value) {
                const errors = validatePassword(this.value);
                if (errors.length === 0) {
                    showSuccess(this);
                } else {
                    showError(this, errors.join('. '));
                }
            }
        });
    });

    // Password confirmation matching
    const confirmPasswordInputs = document.querySelectorAll('input[name*="confirm"], input[name$="2"]');
    confirmPasswordInputs.forEach(input => {
        input.addEventListener('blur', function () {
            const passwordField = document.querySelector('input[name*="password1"], input[name="password"]');
            if (passwordField && this.value) {
                if (this.value === passwordField.value) {
                    showSuccess(this);
                } else {
                    showError(this, 'Passwords do not match');
                }
            }
        });
    });

    // Form submission validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            let isValid = true;

            // Validate all required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    showError(field, 'This field is required');
                    isValid = false;
                }
            });

            // Check for any existing validation errors
            if (form.querySelector('.is-invalid')) {
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
                alert('Please correct the errors in the form');
            }
        });
    });
});

// Floating labels animation
document.querySelectorAll('.form-floating input, .form-floating textarea').forEach(input => {
    input.addEventListener('focus', function () {
        this.parentElement.classList.add('focused');
    });

    input.addEventListener('blur', function () {
        if (!this.value) {
            this.parentElement.classList.remove('focused');
        }
    });
});
