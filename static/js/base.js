const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

let currentEditIndex = null;
// Store current filter state
let currentFilterState = {
    transactionType: 'all',
    category: 'all',
    description: ''
}

// Pagination variables
let currentPage = 1;
let pageSize = 10; // Default items per page
let totalPages = 1;

// Function to update pagination controls
function updatePaginationControls(totalItems) {
    // Calculate total pages
    totalPages = Math.ceil(totalItems / pageSize);
    
    // Update page info
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
    
    // Update showing info
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalItems);
    document.getElementById('currentShowing').textContent = totalItems > 0 ? `${start}-${end}` : '0';
    document.getElementById('totalItems').textContent = totalItems;
    
    // Update buttons state
    document.getElementById('prevPage').parentElement.classList.toggle('disabled', currentPage <= 1);
    document.getElementById('nextPage').parentElement.classList.toggle('disabled', currentPage >= totalPages);
}

// Function to handle page navigation
function changePage(direction) {
    if (direction === 'prev' && currentPage > 1) {
    currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
    currentPage++;
    }
    refreshTables();
}

// Function to handle page size change
function changePageSize(newSize) {
    pageSize = parseInt(newSize);
    // Save to localStorage
    localStorage.setItem('preferredPageSize', pageSize);
    currentPage = 1; // Reset to first page when changing page size
    refreshTables();
}

// Sidebar collapse
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.querySelector('.hamburger-btn');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    // Function to check if device is mobile
    function isSmallScreen() {
    return window.innerWidth <= 768;
    }
    
    // Initialize sidebar state based on screen size
    function initializeSidebarState() {
    const savedState = localStorage.getItem('sidebarCollapsed');
    
    if (savedState !== null) {
        if (savedState === 'true') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
        }
        return;
    }
    
    // Set default state based on screen size
    if (isSmallScreen()) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
        localStorage.setItem('sidebarCollapsed', 'true');
    } else {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
        localStorage.setItem('sidebarCollapsed', 'false');
    }
    }
    
    // Initialize on page load
    initializeSidebarState();
    
    // Handle window resize
    window.addEventListener('resize', function() {
    // Only change state if there's no saved preference
    if (localStorage.getItem('sidebarCollapsed') === null) {
        initializeSidebarState();
    }
    });
    
    toggleBtn.addEventListener('click', function() {
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
});

// Filter transactions
function getFilteredTransactions() {
    if(!window.transactions || !Array.isArray(window.transactions)) {
    console.log('No transactions available');
    return [];
    }

    let filtered = [...window.transactions];
    
    if (currentFilterState.transactionType === 'in') {
    filtered = filtered.filter(t => t.transaction_type === true);
    } else if (currentFilterState.transactionType === 'out') {
    filtered = filtered.filter(t => t.transaction_type === false);
    }

    if (currentFilterState.category !== 'all') {
    filtered = filtered.filter(t => t.category === currentFilterState.category);
    }

    if (currentFilterState.description && currentFilterState.description.trim() !== '') {
    const searchTerm = currentFilterState.description.toLowerCase();
    filtered = filtered.filter(t => 
        t.description && 
        t.description.toLowerCase().includes(searchTerm)
    );
    console.log('After description filter:', filtered.length, 'Search term:', searchTerm);
    }

    return filtered;
}

// Update filter state and re-render tables
function updateFilterState(filterType, value) {
    if (filterType === 'transactionType') {
    currentFilterState.transactionType = value;
    
    // highlight active button
    document.querySelectorAll('.btn-secondary, .btn-success, .btn-danger').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (value === 'all') {
        document.querySelector('.btn-secondary').classList.add('active');
    } else if (value === 'in') {
        document.querySelector('.btn-success').classList.add('active');
    } else if (value === 'out') {
        document.querySelector('.btn-danger').classList.add('active');
    }
    } else if (filterType === 'category') {
    currentFilterState.category = value;
    } else if (filterType === 'description') {
    currentFilterState.description = value;
    };

    currentPage = 1;

    const filteredData = getFilteredTransactions();
    refreshTables();
}

function filterTransactions(type) {
    updateFilterState('transactionType', type);
}

function filterCategory() {
    const filterEl = document.getElementById('category-filter');
    if (!filterEl) return;

    const selectedCategory = filterEl.value;
    updateFilterState('category', selectedCategory);
}

function filterDescription() {
    const filterEl = document.getElementById('description-filter');
    if (!filterEl) {
    console.error('Description filter element not found');
    return;
    }

    const searchTerm = filterEl.value.trim();
    console.log('Searching for:', searchTerm);
    updateFilterState('description', searchTerm);
}

function refreshTables() {
    if (!document.getElementById('detail-page')) {
        console.log('Not on detail page, skipping table refresh.');
        return;
    }
    
    if(document.getElementById('description-filter')) {
    document.getElementById('description-filter').value = '';
    }
    if(document.getElementById('category-filter')) {
    document.getElementById('category-filter').value = 'all';
    }

    const filteredData = getFilteredTransactions().map(transaction => ({
    ...transaction,
    description: transaction.description || ''
    }));

    updateTable(filteredData, "transaction-table-month");
    updateTable(filteredData, "transaction-table-category");
    updateTable(filteredData, "transaction-table-saved");
    updateTable(filteredData, "transaction-table-search");
}

function updateTable(data, tableId) {
    const tableElement = document.getElementById(tableId);
    if (!tableElement) {
        console.log(`Table with id ${tableId} not found, skipping update.`);
        return;
    }

    const isSavedView = tableId === "transaction-table-saved";
    
    let displayData = data;
    if (isSavedView) {
        displayData = data.filter(t => t.is_saved === true);
    }
    
    // For pagination: Only apply pagination to the transaction-table-month
    // Other tables (category and saved) will show all items
    let paginatedData = displayData;
    if (tableId === "transaction-table-month" && !isSavedView) {
        // Update pagination controls first
        updatePaginationControls(displayData.length);
        
        // Then paginate the data
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, displayData.length);
        paginatedData = displayData.slice(startIndex, endIndex);
    }

    let tableContent = paginatedData.map((t, index) => {
        const btnClass = t.is_saved ? "btn-secondary" : "btn-success";
        const btnText = t.is_saved ? "Unsave" : "Save";
        
        const description = t.description ?? '';

        // Find the index of the original transaction in the complete transactions array
        const originalIndex = window.transactions.findIndex(original => 
            original.id === t.id
        );
        
        return `<tr>
            <td>${t.date}</td>
            <td>${t.category}</td>
            <td>${t.transaction_type ? "Income" : "Expense"}</td>
            <td>${t.currency}</td>
            <td>${t.amount}</td>
            <td>${t.account_name}</td>
            <td>${t.description}</td>
            <td>
                <button class="btn ${btnClass} btn-sm" onclick="toggleSaveTransaction(${originalIndex}, ${isSavedView})">
                    ${btnText}
                </button>
            </td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="openEditModal(${originalIndex})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteTransaction(${originalIndex})">Delete</button>
            </td>
        </tr>`;
    }).join('');
    
    if (paginatedData.length === 0) {
        tableContent = '<tr><td colspan="9" class="text-center">No data available</td></tr>';
    }
    
    tableElement.innerHTML = tableContent;
}

function findOriginalIndex(transactionId) {
    return window.transactions.findIndex(t => t.id === transactionId);
}

function isInSavedTab() {
    return document.querySelector('#by-saved.active, #by-saved.show.active') !== null;
}

function toggleSaveTransaction(index, fromSavedView = false) {
    let transaction;
    let originalIndex;
    
    if (fromSavedView) {
        const savedTransactions = getFilteredTransactions().filter(t => t.is_saved);
        if (index >= savedTransactions.length) {
            console.error('Invalid index for saved transactions');
            return;
        }
        transaction = savedTransactions[index];
        originalIndex = window.transactions.findIndex(t => t.id === transaction.id);
        if (originalIndex === -1) {
            console.error('Transaction not found in original array');
            return;
        }
    } else {
        transaction = window.transactions[index];
        originalIndex = index;
    }

    if (!transaction || !transaction.id) {
        console.error('Invalid transaction or missing ID');
        return;
    }

    const transactionId = transaction.id;
    const currentSavedState = transaction.is_saved;
    
    let saveUrl = 'toggle-save-transaction/';
    const urlMeta = document.querySelector('meta[name="toggle-save-transaction-url"]');
    if (urlMeta) {
        saveUrl = urlMeta.getAttribute('content');
    }
    
    fetch(saveUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `transaction_id=${transactionId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.transactions[originalIndex].is_saved = data.is_saved;
                            
            if (fromSavedView && !data.is_saved) {
                console.log('Removing transaction from saved tab');
            } else {
                console.log(`Transaction ${data.is_saved ? 'saved' : 'unsaved'} successfully`);
            }
            refreshTables();
        } else {
            console.error('Failed to toggle save status:', data.message);
            alert(`Failed to update: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the transaction');
    });
}

// Populate transaction currency dropdowns with user's currencies
function populateTransactionCurrencyDropdowns() {
    // Get the currency dropdown elements
    const addCurrencyDropdown = document.getElementById('addCurrency');
    const editCurrencyDropdown = document.getElementById('editCurrency');
    
    if (!addCurrencyDropdown && !editCurrencyDropdown) return;
    
    // Get currencies URL
    let getCurrenciesUrl = 'get-currencies/';
    const getCurrenciesUrlMeta = document.querySelector('meta[name="get-currencies-url"]');
    if (getCurrenciesUrlMeta) {
    getCurrenciesUrl = getCurrenciesUrlMeta.getAttribute('content');
    }
    
    // Fetch currencies from the server
    fetch(getCurrenciesUrl)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.currencies && Array.isArray(data.currencies)) {
        // Store currencies globally for other functions to use
        window.userCurrencies = data.currencies;
        
        // Update the Add Transaction dropdown
        if (addCurrencyDropdown) {
            addCurrencyDropdown.innerHTML = '<option value="GBP">GBP</option>';
            data.currencies.forEach(currency => {
            const option = document.createElement('option');
            option.value = currency.currency_code;
            option.textContent = currency.currency_code;
            if(option.value !== 'GBP') {
                addCurrencyDropdown.appendChild(option);
            }
            });
        }
        
        // Update the Edit Transaction dropdown
        if (editCurrencyDropdown) {
            editCurrencyDropdown.innerHTML = '';
            data.currencies.forEach(currency => {
            const option = document.createElement('option');
            option.value = currency.currency_code;
            option.textContent = currency.currency_code;
            editCurrencyDropdown.appendChild(option);
            });
        }
        } else {
        console.error('Failed to load currencies for transaction dropdowns:', data);
        }
    })
    .catch(error => {
        console.error('Error loading currencies for transaction dropdowns:', error);
    });
}

// Open Add Transaction Modal
function openAddModal() {
    // Set current date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('addDate').value = today;
    
    // Reset form fields
    document.getElementById('addType').value = 'false'; // Default to expense
    document.getElementById('addAmount').value = '';
    document.getElementById('addDescription').value = '';
    
    // Update dropdowns with latest data
    updateCategoryDropdown();
    updateAccountDropdown();
    populateTransactionCurrencyDropdowns();
    
    // Show modal
    const addModal = new bootstrap.Modal(document.getElementById('addModal'));
    addModal.show();
}

// Open Edit Transaction Modal
function openEditModal(index) {
    const transaction = window.transactions[index];
    if (!transaction) {
    console.error('Transaction not found at index:', index);
    return;
    }
    
    // Store the current index for later use
    currentEditIndex = index;

    // Fill form fields with transaction data
    document.getElementById('editDate').value = transaction.date;
    document.getElementById('editType').value = transaction.transaction_type ? "true" : "false";
    
    // Update category dropdown based on transaction type
    updateEditCategoryDropdown(transaction.transaction_type ? "true" : "false");

    populateTransactionCurrencyDropdowns();
    
    // Set values after dropdowns are populated
    setTimeout(() => {
    // Find and select the correct category
    const editCategoryElement = document.getElementById('editCategory');
    if (editCategoryElement) {
        // Try to find the option with matching text
        for (let i = 0; i < editCategoryElement.options.length; i++) {
        if (editCategoryElement.options[i].text === transaction.category) {
            editCategoryElement.selectedIndex = i;
            break;
        }
        }
    }
    
    const editCurrencyElement = document.getElementById('editCurrency');
    if (editCurrencyElement) {
        for (let i = 0; i < editCurrencyElement.options.length; i++) {
        if (editCurrencyElement.options[i].value === transaction.currency) {
            editCurrencyElement.selectedIndex = i;
            break;
        }
        }
    }
    
    const editAccountElement = document.getElementById('editAccount');
    if (editAccountElement) {
        for (let i = 0; i < editAccountElement.options.length; i++) {
        if (editAccountElement.options[i].value === transaction.account_name) {
            editAccountElement.selectedIndex = i;
            break;
        }
        }
    }
    }, 100);

    updateEditAccountDropdown();
    
    document.getElementById('editAmount').value = transaction.amount;
    document.getElementById('editDescription').value = transaction.description || '';

    // Show modal
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    editModal.show();
}

function updateEditCategoryDropdown(type) {
    const categoryDropdown = document.getElementById('editCategory');
    if (!categoryDropdown) return;
    
    categoryDropdown.innerHTML = '';
    
    if (!window.categories || !window.categories[type]) {
    console.error('Categories not defined or invalid type:', type);
    return;
    }
    
    window.categories[type].forEach(category => {
    const option = document.createElement('option');
    option.value = category.name;
    option.textContent = category.name;
    categoryDropdown.appendChild(option);
    });
    console.log('Updated edit category dropdown:', window.categories[type]);
}

// Update drop-down box
function updateCategoryDropdown() {
    const categoryDropdown = document.getElementById('addCategory');
    const addTypeEl = document.getElementById('addType');
    if (!categoryDropdown || !addTypeEl) return;

    const selectedType = addTypeEl.value;
    categoryDropdown.innerHTML = '';

    if (!window.categories || !window.categories[selectedType]) {
    console.error('Categories not defined or invalid type:', selectedType);
    return;
    }

    window.categories[selectedType].forEach(category => {
    const option = document.createElement('option');
    option.value = category.name;
    option.textContent = category.name;
    categoryDropdown.appendChild(option);
    });
    console.log('Updated category dropdown:', window.categories[selectedType]);
}

function updateBudgetCategoryDropdown(elementId = 'budgetCategory') {
    const categoryDropdown = document.getElementById(elementId);
    if (!categoryDropdown) return;

    categoryDropdown.innerHTML = '';

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = '-- Select Category --';
    categoryDropdown.appendChild(defaultOption);

    if (window.categories && window.categories['false']) {
    window.categories['false'].forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        categoryDropdown.appendChild(option);
    });
    }
}

function updateAccountDropdown() {
    const accountDropdown = document.getElementById('addedAccount');
    if (!accountDropdown) return;
    
    accountDropdown.innerHTML = '';
    
    if (!window.accounts || !Array.isArray(window.accounts)) {
    console.error('Accounts not defined or not an array');
    return;
    }
    
    window.accounts.forEach(account => {
    const option = document.createElement('option');
    option.value = account.account_name;
    option.textContent = account.account_name;
    accountDropdown.appendChild(option);
    });
    
    console.log('Updated account dropdown with accounts:', window.accounts.length);
}

function updateEditAccountDropdown() {
    const accountDropdown = document.getElementById('editAccount');
    if (!accountDropdown) return;
    
    accountDropdown.innerHTML = '';
    
    if (!window.accounts || !Array.isArray(window.accounts)) {
    console.error('Accounts not defined or not an array');
    return;
    }
    
    window.accounts.forEach(account => {
    const option = document.createElement('option');
    option.value = account.account_name;
    option.textContent = account.account_name;
    accountDropdown.appendChild(option);
    });
}

function deleteTransaction(index) {
    const transactionId = transactions[index].id;
    console.log('Deleting transaction:', transactionId);

    let deleteUrl = 'delete-transaction/';
    const urlMeta = document.querySelector('meta[name="delete-transaction-url"]');
    if (urlMeta) {
    deleteUrl = urlMeta.getAttribute('content');
    }
    
    console.log('Delete URL:', deleteUrl);

    fetch(deleteUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: `transaction_id=${transactionId}`
    })
    .then(response => {
    console.log('HTTP response status:', response.status);
    return response.text();
    })
    .then(text => {
    console.log('Response text:', text);
    // try analyzing JSON, if failed, return original text
    try {
        return JSON.parse(text);
    } catch (e) {
        console.error('Failed to parse JSON:', e);
        return { status: 'error', message: 'Invalid JSON response: ' + text };
    }
    })
    .then(data => {
    console.log('Parsed data:', data);
    if (data.status === 'success') {
        transactions.splice(index, 1);
        refreshTables();
        console.log('Transaction deleted successfully:', data.message);
    } else {
        console.error('Failed to delete:', data.message);
        alert(`Failed to delete: ${data.message}`);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('An error occurred while deleting the transaction. Please check console.');
    });
}

// For Statistics Page
function initStatisticsPage() {
    console.log('Initializing statistics page...');

    // Get transaction data from backend
    fetch('/api/transactions/dates/')
    .then(response => response.json())
    .then(data => {
        window.monthsByYear = data.monthsByYear; 
        initYearOptions(data.years);
        initMonthOptions(data.monthsByYear[Math.max(...data.years)]);  // init month options for the latest year
        switchMode('month');
        
        // Initialize budget pie chart category select with "entire_period"
        const categorySelect = document.getElementById('categorySelect');
        if (categorySelect) {
        categorySelect.value = 'entire_period';
        // initial budget pie chart 
        updateCharts(document.getElementById('monthSelect').parentElement.style.display === 'none' ? 'year' : 'month');
        }
    })
    .catch(error => {
        console.error('Error fetching transaction dates:', error);
    });

    // Add event listener for budget pie chart category select
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect) {
    categorySelect.addEventListener('change', function() {
        const selectedCategory = this.value;
        const mode = document.getElementById('monthSelect').parentElement.style.display === 'none' ? 'year' : 'month';
        updateCharts(mode);
    });
    }
}

function initYearOptions(availableYears) {
    const yearSelect = document.getElementById('yearSelect');
    if (!yearSelect) return;

    yearSelect.innerHTML = ''; // clear existing options
    
    // generate options based on available years
    availableYears.forEach(year => {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    yearSelect.appendChild(option);
    });

    // set the latest year as default
    if (availableYears.length > 0) {
    yearSelect.value = Math.max(...availableYears);
    }
}

function initMonthOptions(availableMonths) {
    const monthSelect = document.getElementById('monthSelect');
    if (!monthSelect) return;

    monthSelect.innerHTML = ''; // clear existing options

    const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
    ];

    // generate options based on available months
    availableMonths.forEach(month => {
    const option = document.createElement('option');
    option.value = month;
    option.textContent = monthNames[month - 1];
    monthSelect.appendChild(option);
    });

    // set the latest month as default
    if (availableMonths.length > 0) {
    monthSelect.value = Math.max(...availableMonths);
    }
}

function switchMode(mode) {
    // update button status
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`.filter-btn[onclick="switchMode('${mode}')"]`);
    if (activeBtn) {
    activeBtn.classList.add('active');
    }

    // handle month dropdown
    const monthSelect = document.getElementById('monthSelect');
    const yearSelect = document.getElementById('yearSelect');
    
    if (monthSelect) {
    const monthSelectContainer = monthSelect.parentElement;

    if (mode === 'year') {
        monthSelectContainer.style.display = 'none'; // hide the month dropdown
        monthSelect.disabled = true;
        monthSelect.value = '';
    } else {
        // when switch to month mode
        monthSelectContainer.style.display = ''; // show the month dropdown
        monthSelect.disabled = false;
        monthSelect.style.color = '';
        
        // automatically select the latest month
        const selectedYear = yearSelect.value;
        
        if (window.monthsByYear && window.monthsByYear[selectedYear]) {
        const availableMonths = window.monthsByYear[selectedYear];
        const latestMonth = Math.max(...availableMonths);
        monthSelect.value = latestMonth;
        }
    }
    }
    updateCharts(mode);
}

function handleYearChange() {
    const yearSelect = document.getElementById('yearSelect');
    if (yearSelect) {
    const selectedYear = yearSelect.value;
    
    // update month options
    if (window.monthsByYear && window.monthsByYear[selectedYear]) {
        initMonthOptions(window.monthsByYear[selectedYear]);
    }
    
    // keep current mode unchanged
    const currentMode = document.getElementById('monthSelect').parentElement.style.display === 'none' ? 'year' : 'month';
    updateCharts(currentMode);
    }
}

function handleMonthChange() {
    if (document.getElementById('monthSelect') && !document.getElementById('monthSelect').disabled) {
    updateCharts('month');  
    }
}

function updateCharts(mode) {
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    
    if (!yearSelect) return;

    const selectedYear = yearSelect.value;
    const selectedMonth = mode === 'month' ? monthSelect.value : null;

    const params = new URLSearchParams();
    params.append('year', selectedYear || '');
    params.append('mode', mode || 'year');
    if (selectedMonth) {
    params.append('month', selectedMonth);
    }

    const url = `/api/statistics/data/?${params.toString()}`;
    
    console.log('Fetching URL:', url);

    fetch(url)
    .then(response => {
        if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        updateStatistics(data);
        updateBudgetDropdown(data);
    })
    .catch(error => alert('Error updating statistics.')
    );
}

function updateBudgetDropdown(data) {
    const categorySelect = document.getElementById('categorySelect');
    if (!categorySelect) return;

    // store current selection before clearing
    const currentSelection = categorySelect.value;

    categorySelect.innerHTML = ''; 

    if (data.budget_data && data.budget_data.category_budgets && Object.keys(data.budget_data.category_budgets).length > 0) {
    // add "entire period" in to list
    const defaultOption = document.createElement('option');
    defaultOption.value = 'entire_period';
    defaultOption.textContent = 'Entire Period';
    categorySelect.appendChild(defaultOption);

    // set options for categories that have budgets
    Object.keys(data.budget_data.category_budgets).forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });

    // restore previous selection if it still exists in the options, otherwise use "entire_period"
    if (currentSelection && (currentSelection === 'entire_period' || data.budget_data.category_budgets[currentSelection])) {
        categorySelect.value = currentSelection;
    } else {
        categorySelect.value = 'entire_period';
    }

    // trigger chart update immediately if this is the initial load
    if (!currentSelection) {
        const mode = document.getElementById('monthSelect').parentElement.style.display === 'none' ? 'year' : 'month';
        updateBudgetChart(budgetChart, data);
    }
    } else {
    // if there is no budget
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No Data';
    categorySelect.appendChild(option);
    }
}

function updateBudgetChart(chart, data) {
    const budgetData = data.budget_data;
    const selectedCategory = document.getElementById('categorySelect').value;

    if (!budgetData || !budgetData.category_budgets) {
    chart.data.labels = ['No Budget Data'];
    chart.data.datasets[0].data = [1];
    chart.data.datasets[0].backgroundColor = ['#E0E0E0'];
    chart.update();
    return;
    }
    
    // get budget data
    let usedAmount = 0;
    let totalAmount = 0;

    if (selectedCategory === 'entire_period') {
    // calculate total amount of all categories
    totalAmount = Object.values(budgetData.category_budgets).reduce((sum, amount) => sum + amount, 0);
    
    // sum up expense by category which has budget
    Object.keys(budgetData.category_budgets).forEach(category => {
        if (data.expense_by_category[category]) {
        usedAmount += data.expense_by_category[category];
        }
    });
    } else if (selectedCategory) {
    usedAmount = data.expense_by_category[selectedCategory] || 0;
    totalAmount = budgetData.category_budgets?.[selectedCategory] || 0;
    }

    const remainingAmount = Math.max(0, totalAmount - usedAmount);
        
    if (totalAmount !== 0) {
    // update budget pie chart
    chart.data.labels = ['Used', 'Remaining'];
    chart.data.datasets[0].data = [usedAmount, remainingAmount];
    chart.data.datasets[0].backgroundColor = ['#A8DFF1', '#ECBA73'];
    } else {
    // no budget data
    chart.data.labels = ['No Budget Data'];
    chart.data.datasets[0].data = [1];
    chart.data.datasets[0].backgroundColor = ['#E0E0E0'];
    chart.data.datasets[0].datalabels.color = '#FFCE56';
    }
    
    chart.update();
}

function updateLineChart(data, mode) {

    if (!incomeExpenseChart) return;

    let labels = [];
    let expenseData = [];
    let incomeData = [];
    let balanceData = [];

    if (mode === 'year') {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let month = 1; month <= 12; month++) {
        labels.push(months[month - 1]);
        const monthData = data.monthly_data?.[month] || { income: 0, expense: 0 };
        expenseData.push(monthData.expense);
        incomeData.push(monthData.income);
        balanceData.push(monthData.income - monthData.expense);
    }
    } else {
    const selectedYear = parseInt(document.getElementById('yearSelect').value);
    const selectedMonth = parseInt(document.getElementById('monthSelect').value);
    
    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
    
    for (let day = 1; day <= daysInMonth; day++) {
        labels.push(day.toString());
        const dayData = data.daily_data?.[day] || { income: 0, expense: 0 };
        expenseData.push(dayData.expense);
        incomeData.push(dayData.income);
        balanceData.push(dayData.income - dayData.expense);
    }
    }

    // update line chart data
    incomeExpenseChart.data.labels = labels;
    incomeExpenseChart.data.datasets[0].data = expenseData;
    incomeExpenseChart.data.datasets[1].data = incomeData;
    incomeExpenseChart.data.datasets[2].data = balanceData;

    incomeExpenseChart.update();
}

function updatePieChart(chart, data, type) {
    const categoryData = data[`${type}_by_category`];
    if (categoryData && Object.keys(categoryData).length > 0) {
    chart.data.labels = Object.keys(categoryData);
    chart.data.datasets[0].data = Object.values(categoryData);
    chart.data.datasets[0].backgroundColor = ['#A8DFF1', '#ECBA73', '#F5E2D4', '#024757', '#E5989B'];
    chart.data.datasets[0].datalabels.color = '#FFCE56';
    } else {
    chart.data.labels = [`No ${type.charAt(0).toUpperCase() + type.slice(1)} Data`];
    chart.data.datasets[0].data = [1];
    chart.data.datasets[0].backgroundColor = ['#E0E0E0'];
    chart.data.datasets[0].datalabels.color = '#FFCE56';
    }
    chart.update();
}

function updateRankingTable(data, type) {
    const tableId = type === 'expense' ? 'expenseRankingTable' : 'incomeRankingTable';
    const rankingTable = document.getElementById(tableId);
    if (!rankingTable) return;

    // clear existing content
    rankingTable.innerHTML = '';

    const createEmptyRows = (startIndex, count) => {
    for (let i = startIndex; i < count; i++) {
        const row = document.createElement('tr');
        row.className = `rank-item ${type}${i + 1}`;
        row.innerHTML = `
        <td>${i + 1}</td>
        <td>-</td>
        <td>0.00 £</td>
        `;
        rankingTable.appendChild(row);
    }
    };

    const categoryData = data[`${type}_by_category`];
    if (categoryData && Object.keys(categoryData).length > 0) {
    // convert category and amount to array and sort
    const items = Object.entries(categoryData)
        .map(([category, amount]) => ({category, amount}))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 5);

    items.forEach((item, index) => {
        const row = document.createElement('tr');
        row.className = `rank-item ${type}${index + 1}`;
        row.innerHTML = `
        <td>${index + 1}</td>
        <td>${item.category}</td>
        <td>${item.amount.toFixed(2)} £</td>
        `;
        rankingTable.appendChild(row);
    });

    // if no data, show 5 empty rows
    createEmptyRows(items.length, 5);
    } else {
    // if no data, show 5 empty rows
    createEmptyRows(0, 5);
    }
}

function updateStatistics(data) {
    try {
    console.log('Updating statistics with data:', data);
    
    const formatCurrency = (number) => {
        const prefix = number >= 0 ? '+' : '';
        return `${prefix}${number.toFixed(2)} £`;
    };

    // update statistics block
    const incomeElement = document.querySelector('.stat-item.in h3');
    const expenseElement = document.querySelector('.stat-item.out h3');
    const balanceElement = document.querySelector('.stat-item.balance h3');
    const balanceBox = document.querySelector('.stat-item.balance');
    const mode = document.getElementById('monthSelect').parentElement.style.display === 'none' ? 'year' : 'month';


    if (incomeElement) incomeElement.textContent = formatCurrency(data.income);
    if (expenseElement) expenseElement.textContent = formatCurrency(-data.expense);
    if (balanceElement) {
        balanceElement.textContent = formatCurrency(data.balance);
        if (balanceBox) {
        if (data.balance < 0) {
            balanceBox.style.backgroundColor = '#E50046'; 
        } else if (data.balance > 0) {
            balanceBox.style.backgroundColor = '#1F7D53'; 
        } else {
            balanceBox.style.backgroundColor = ''; 
        }
        }
    }

    //update budget pie chart
    updateBudgetChart(budgetChart, data)
    // update line chart
    updateLineChart(data, mode);
    // update pie charts
    updatePieChart(expenseChart, data, 'expense');
    updatePieChart(incomeChart, data, 'income');
    // update ranking tables
    updateRankingTable(data, 'expense');
    updateRankingTable(data, 'income');
    } catch (error) {
    console.error('Error in updateStatistics:', error);
    throw error;
    }
}

// initialize when DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('statistics-page')) {
    initStatisticsPage();
    
    // rebind month selector event
    const monthSelect = document.getElementById('monthSelect');
    const yearSelect = document.getElementById('yearSelect');
    if (monthSelect) {
        monthSelect.addEventListener('change', handleMonthChange);
    }
    if (yearSelect) {
        yearSelect.addEventListener('change', handleYearChange);
    }
    }
});

// Edit Transaction Submit Handler
document.getElementById('saveChanges').addEventListener('click', () => {
    if (currentEditIndex !== null) {
    const transaction = window.transactions[currentEditIndex];
    const transactionId = transaction.id;

    // get the current description value
    const description = document.getElementById('editDescription').value.trim();
    
    const updatedTransaction = {
        date: document.getElementById('editDate').value,
        category: document.getElementById('editCategory').value,
        transaction_type: document.getElementById('editType').value === 'true',
        currency: document.getElementById('editCurrency').value,
        amount: document.getElementById('editAmount').value,
        account: document.getElementById('editAccount').value,
        description: description || null
    };
    
    // Validate required fields
    if (!updatedTransaction.date || !updatedTransaction.category || !updatedTransaction.amount || !updatedTransaction.account) {
        alert('Please fill in all required fields');
        return;
    }
    
    let updateUrl = 'update-transaction/';
    const updateUrlMeta = document.querySelector('meta[name="update-transaction-url"]');
    if (updateUrlMeta) {
        updateUrl = updateUrlMeta.getAttribute('content');
    }

    // Close the modal
    document.getElementById('saveChanges').blur();
    const editModal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
    editModal.hide();
    
    fetch(updateUrl, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
        },
        body: new URLSearchParams({
        'id': transactionId,
        'date': updatedTransaction.date,
        'category': updatedTransaction.category,
        'transaction_type': updatedTransaction.transaction_type,
        'currency': updatedTransaction.currency,
        'amount': updatedTransaction.amount,
        'account': updatedTransaction.account,
        'description': description // Explicitly send description to avoid null value
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
        // Update local transaction data
        // Object.assign(window.transactions[currentEditIndex], updatedTransaction);
        window.transactions[currentEditIndex] = {
            ...window.transactions[currentEditIndex],
            ...updatedTransaction,
            description: data.description ?? ''
        };
        
        refreshTables();
        
        // Reload to get updated category totals
        // window.location.reload();
        } else {
        console.error('Failed to update:', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the transaction');
    });
    }
});

// Add Transaction Submit Handler
document.getElementById('addTransaction').addEventListener('click', () => {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const newTransaction = {
    date: document.getElementById('addDate').value,
    category: document.getElementById('addCategory').value,
    transaction_type: document.getElementById('addType').value === 'true',
    currency: document.getElementById('addCurrency').value,
    amount: document.getElementById('addAmount').value,
    account: document.getElementById('addedAccount').value,
    description: document.getElementById('addDescription').value || ''
    }

    // Validate required fields
    if (!newTransaction.date || !newTransaction.category || !newTransaction.amount || !newTransaction.account) {
    alert('Please fill in all required fields');
    return;
    }

    let addUrl = 'add-transaction/';
    const addUrlMeta = document.querySelector('meta[name="add-transaction-url"]');
    if (addUrlMeta) {
    addUrl = addUrlMeta.getAttribute('content');
    }
    
    fetch(addUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'date': newTransaction.date,
        'category': newTransaction.category,
        'transaction_type': newTransaction.transaction_type,
        'currency': newTransaction.currency,
        'amount': newTransaction.amount,
        'account': newTransaction.account,
        'description': newTransaction.description
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        // Add new transaction to local array with returned ID
        newTransaction.id = data.transaction_id;
        newTransaction.is_saved = false; // Default to not saved
        if (!Array.isArray(window.transactions)) {
        window.transactions = []; // Initialize as empty array if it's not an array
        }
        transactions.push(newTransaction);
        
        // Refresh tables and budgets
        refreshTables();
        if (typeof calculateRemainingBudget === 'function') {
        calculateRemainingBudget();
        }

        // Reload page to get updated data
        window.location.reload();
    } else {
        console.error('Failed to add:', data.message);
        alert(`Failed to add: ${data.message}`);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('An error occurred while adding the transaction');
    });

    // Close the modal
    const addModal = bootstrap.Modal.getInstance(document.getElementById('addModal'));
    addModal.hide();
});

function updateCategoryTables() {
    const incomeTable = document.getElementById('income-categories-table');
    const expenseTable = document.getElementById('expense-categories-table');
    
    if (!incomeTable || !expenseTable) {
    console.log('Category tables not found, skipping update');
    return;
    }
    
    if (!window.categories) {
    console.error('Categories not defined');
    return;
    }
    
    console.log('Updating management tables with:', window.categories);
    
    if (Array.isArray(window.categories.true)) {
    incomeTable.innerHTML = window.categories.true.length > 0 ?
        window.categories.true.map(cat => `
        <tr>
            <td>${cat.name}</td>
            <td>${cat.transaction_count}</td>
            <td>£${cat.total_amount}</td>
            <td>
            <button class='btn btn-danger btn-sm' onclick="deleteCategory('true', ${cat.id})">Delete</button>
            </td>
        </tr>
        `).join('') :
        '<tr><td colspan="4" class="text-center">No income categories available</td></tr>';
    }

    if (Array.isArray(window.categories.false)) {
    expenseTable.innerHTML = window.categories.false.length > 0 ?
        window.categories.false.map(cat => `
        <tr>
            <td>${cat.name}</td>
            <td>${cat.transaction_count}</td>
            <td>£${cat.total_amount}</td>
            <td>
            <button class='btn btn-danger btn-sm' onclick="deleteCategory('false', ${cat.id})">Delete</button>
            </td>
        </tr>
        `).join('') :
        '<tr><td colspan="4" class="text-center">No expense categories available</td></tr>';
    }
}
    
let budgets = [];

function loadBudgets() {
    let getBudgetsUrl = 'get-budgets/';
    const getBudgetsUrlMeta = document.querySelector('meta[name="get-budgets-url"]');
    if (getBudgetsUrlMeta) {
    getBudgetsUrl = getBudgetsUrlMeta.getAttribute('content');
    }
    
    fetch(getBudgetsUrl)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
        budgets = data.budgets;
        updateBudgetTable();
        } else {
        console.error('Failed to load budgets:', data.message);
        }
    })
    .catch(error => {
        console.error('Error loading budgets:', error);
    });
}

function openAddBudgetModal() {
    document.getElementById('budgetYearMonth').value = '';
    document.getElementById('budgetAmount').value = '';
    updateBudgetCategoryDropdown('budgetCategory');
    const addBudgetModal = new bootstrap.Modal(document.getElementById('addBudgetModal'));
    addBudgetModal.show();
}

function openEditBudgetModal(budgetId) {
    const budget = budgets.find(b => b.id == budgetId);
    if (!budget) {
    console.error('Budget not found:', budgetId);
    return;
    }
    
    document.getElementById('editBudgetId').value = budget.id;
    document.getElementById('editBudgetYearMonth').value = budget.period;
    document.getElementById('editBudgetAmount').value = budget.budget_amount;
    
    updateBudgetCategoryDropdown('editBudgetCategory');
    
    setTimeout(() => {
    document.getElementById('editBudgetCategory').value = budget.category_id;
    }, 100);
    
    const editBudgetModal = new bootstrap.Modal(document.getElementById('editBudgetModal'));
    editBudgetModal.show();
}

document.getElementById('saveBudget').addEventListener('click', () => {
    const yearMonth = document.getElementById('budgetYearMonth').value;
    const amount = document.getElementById('budgetAmount').value;
    const categoryEl = document.getElementById('budgetCategory');

    if (!yearMonth) {
    alert('Please select a year-month');
    return;
    }
    if (!amount || isNaN(parseFloat(amount))) {
    alert('Please enter a valid amount');
    return;
    }
    if (!categoryEl.value) {
    alert('Please select a category');
    return;
    }
    
    let addBudgetUrl = 'add-budget/';
    const addBudgetUrlMeta = document.querySelector('meta[name="add-budget-url"]');
    if (addBudgetUrlMeta) {
    addBudgetUrl = addBudgetUrlMeta.getAttribute('content');
    }
    
    fetch(addBudgetUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'period': yearMonth,
        'category_id': categoryEl.value,
        'budget_amount': amount
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        loadBudgets();
        const addBudgetModal = bootstrap.Modal.getInstance(document.getElementById('addBudgetModal'));
        addBudgetModal.hide();
    } else {
        console.error('Failed to add budget:', data.message);
        alert(`Failed to add budget: ${data.message}`);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('Error adding budget. Please check console.');
    });
});

document.getElementById('updateBudget').addEventListener('click', () => {
    const budgetId = document.getElementById('editBudgetId').value;
    const yearMonth = document.getElementById('editBudgetYearMonth').value;
    const amount = document.getElementById('editBudgetAmount').value;
    const categoryEl = document.getElementById('editBudgetCategory');
    
    if (!yearMonth) {
    alert('Please select a year-month');
    return;
    }
    if (!amount || isNaN(parseFloat(amount))) {
    alert('Please enter a valid amount');
    return;
    }
    if (!categoryEl.value) {
    alert('Please select a category');
    return;
    }
    
    let updateBudgetUrl = 'update-budget/';
    const updateBudgetUrlMeta = document.querySelector('meta[name="update-budget-url"]');
    if (updateBudgetUrlMeta) {
    updateBudgetUrl = updateBudgetUrlMeta.getAttribute('content');
    }
    
    fetch(updateBudgetUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'budget_id': budgetId,
        'period': yearMonth,
        'category_id': categoryEl.value,
        'budget_amount': amount
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        loadBudgets();
        const editBudgetModal = bootstrap.Modal.getInstance(document.getElementById('editBudgetModal'));
        editBudgetModal.hide();
    } else {
        console.error('Failed to update budget:', data.message);
        alert(`Failed to update budget: ${data.message}`);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('Error updating budget. Please check console.');
    });
});

function deleteBudget(budgetId) {
    if (!confirm('You are about to delete this budget. Are you sure?')) {
    return;
    }
    
    let deleteBudgetUrl = 'delete-budget/';
    const deleteBudgetUrlMeta = document.querySelector('meta[name="delete-budget-url"]');
    if (deleteBudgetUrlMeta) {
    deleteBudgetUrl = deleteBudgetUrlMeta.getAttribute('content');
    }
    
    fetch(deleteBudgetUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: `budget_id=${budgetId}`
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        loadBudgets();
    } else {
        console.error('Failed to delete budget:', data.message);
        alert(`Failed to delete budget: ${data.message}`);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('Error deleting budget. Please check console.');
    });
}

function updateBudgetTable() {
    const tableBody = document.getElementById('budget-table');
    if (!tableBody) return;
    tableBody.innerHTML = budgets.length > 0 ?
    budgets.map(budget => `
        <tr>
        <td>${budget.period}</td>
        <td>${budget.category_name}</td>
        <td>£${parseFloat(budget.budget_amount).toFixed(2)}</td>
        <td>£${parseFloat(budget.remaining_amount).toFixed(2)}</td>
        <td>
            <button class="btn btn-warning btn-sm" onclick="openEditBudgetModal(${budget.id})">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteBudget(${budget.id})">Delete</button>
        </td>
        </tr>
    `).join('') :
    '<tr><td colspan="5" class="text-center">No budgets available</td></tr>';
}

function calculateRemainingBudget() {
    budgets.forEach(budget => {
    const [year, month] = budget.yearMonth.split('-'); 
    let totalSpent = 0;

    //  calculate total spent for the budget period
    totalSpent = transactions
        .filter(transaction => {
        const transactionDate = new Date(transaction.date);
        return (
            transactionDate.getFullYear() === parseInt(year) &&
            transactionDate.getMonth() + 1 === parseInt(month) && // months are 0-indexed
            transaction.amount.startsWith('-') // only count expenses
        );
        })
        .reduce((sum, transaction) => sum + Math.abs(parseFloat(transaction.amount.replace('£', ''))), 0);

    budget.remainingAmount = budget.amount - totalSpent;
    });

    updateBudgetTable();
}

const majorCurrencies = [
    { code: 'GBP', name: 'British Pound' },
    { code: 'EUR', name: 'Euro' },
    { code: 'USD', name: 'US Dollar' },
    { code: 'JPY', name: 'Japanese Yen' },
    { code: 'CNY', name: 'Chinese Yuan' },
    { code: 'HKD', name: 'Hong Kong Dollar' },
    { code: 'TWD', name: 'Taiwan Dollar' },
    { code: 'CAD', name: 'Canadian Dollar' },
    { code: 'AUD', name: 'Australian Dollar' },
    { code: 'SGD', name: 'Singapore Dollar' },
    { code: 'CHF', name: 'Swiss Franc' },
    { code: 'KRW', name: 'South Korean Won' },
    { code: 'INR', name: 'Indian Rupee' },
    { code: 'BRL', name: 'Brazilian Real' },
    { code: 'RUB', name: 'Russian Ruble' },
    { code: 'NZD', name: 'New Zealand Dollar' },
    { code: 'THB', name: 'Thai Baht' },
    { code: 'MYR', name: 'Malaysian Ringgit' },
    { code: 'IDR', name: 'Indonesian Rupiah' },
    { code: 'PHP', name: 'Philippine Peso' },
    { code: 'VND', name: 'Vietnamese Dong' },
    { code: 'MXN', name: 'Mexican Peso' },
    { code: 'SEK', name: 'Swedish Krona' },
    { code: 'NOK', name: 'Norwegian Krone' },
    { code: 'DKK', name: 'Danish Krone' },
    { code: 'PLN', name: 'Polish Złoty' },
    { code: 'ZAR', name: 'South African Rand' },
    { code: 'TRY', name: 'Turkish Lira' },
    { code: 'SAR', name: 'Saudi Riyal' },
    { code: 'AED', name: 'UAE Dirham' },
    { code: 'ILS', name: 'Israeli New Shekel' }
];

function populateCurrencyDropdown() {
    const currencySelect = document.getElementById('currencySelect');
    if (!currencySelect) return;
    
    // Clear existing options and keep default options
    currencySelect.innerHTML = '<option value="">-- Select Currency --</option>';
    
    // Get the currency displayed in the table
    const existingCurrencies = Array.from(document.querySelectorAll('#currency-table tr'))
    .map(row => {
        const firstCell = row.querySelector('td');
        return firstCell ? firstCell.textContent.trim() : '';
    })
    .filter(code => code !== '');
    
    console.log('Existing currencies:', existingCurrencies);
    
    // Add major currencies, exclude existing ones
    majorCurrencies
    .filter(currency => !existingCurrencies.includes(currency.code))
    .forEach(currency => {
        const option = document.createElement('option');
        option.value = currency.code;
        option.textContent = `${currency.code} - ${currency.name}`;
        currencySelect.appendChild(option);
    });
}

function openAddCurrencyModal() {
    if (document.getElementById('newCurrencyCode')) {
    document.getElementById('newCurrencyCode').value = '';
    }
    if (document.getElementById('exchangeRate')) {
    document.getElementById('exchangeRate').value = '';
    }
    
    populateCurrencyDropdown();
    
    const addCurrencyModal = new bootstrap.Modal(document.getElementById('addCurrencyModal'));
    addCurrencyModal.show();
}

function openAddAccountModal() {
    const addAccountModal = new bootstrap.Modal(document.getElementById('addAccountModal'));
    addAccountModal.show();
}
    

document.getElementById('addType').addEventListener('change', function() {
    updateCategoryDropdown();
});

document.getElementById('editType').addEventListener('change', function() {
    updateEditCategoryDropdown(this.value);
});

function deleteCategory(is_income, categoryId) {
    console.log('Deleting category:', categoryId);
    if (!confirm('Are you sure you want to delete this category?')) {
    return;
    }

    let deleteUrl = 'delete-category/';
    const urlMeta = document.querySelector('meta[name="delete-category-url"]');
    if (urlMeta) {
    deleteUrl = urlMeta.getAttribute('content');
    }
    console.log('Delete URL:', deleteUrl);

    fetch(deleteUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: `category_id=${categoryId}`
    })
    .then(response => {
    console.log('HTTP response status:', response.status);
    return response.text();
    })
    .then(text => {
    console.log('Response text:', text);
    // try analyzing JSON, if failed, return original text
    try {
        return JSON.parse(text);
    } catch (e) {
        console.error('Failed to parse JSON:', e);
        return { status: 'error', message: 'Invalid JSON response: ' + text };
    }
    })
    .then(data => {
    console.log('Parsed data:', data);
    if (data.status === 'success') {
        window.categories[is_income] = categories[is_income].filter(c => c.id !== categoryId);
        updateCategoryTables();
        updateCategoryDropdown();
        console.log('Category deleted successfully:', data.message);
    } else {
        console.error('Failed to delete:', data.message);
        alert(`Failed to delete: ${data.message}`);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('An error occurred while deleting the category. Please check console.');
    });
}

function openAddIncomeCategoryModal() {
    document.getElementById('incomeCategoryName').value = ''; // Clear the input box
    const addIncomeCategoryModal = new bootstrap.Modal(document.getElementById('addIncomeCategoryModal'));
    addIncomeCategoryModal.show();
}

function openAddExpenseCategoryModal() {
    document.getElementById('expenseCategoryName').value = ''; // Clear the input box
    const addExpenseCategoryModal = new bootstrap.Modal(document.getElementById('addExpenseCategoryModal'));
    addExpenseCategoryModal.show();
}

document.getElementById('saveIncomeCategory').addEventListener('click', () => {
    const categoryName = document.getElementById('incomeCategoryName').value;

    let addCategoryUrl = 'add-category/';
    const addCategoryUrlMeta = document.querySelector('meta[name="add-category-url"]');
    if (addCategoryUrlMeta) {
    addCategoryUrl = addCategoryUrlMeta.getAttribute('content');
    }

    document.getElementById('saveIncomeCategory').blur();
    const modal = bootstrap.Modal.getInstance(document.getElementById('addIncomeCategoryModal'));
    modal.hide();

    fetch(addCategoryUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'name': categoryName,
        'is_income': 'true'
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        window.categories['true'].push({
        id: data.id || Date.now(),
        name: data.name || categoryName,
        transaction_count: 0,
        total_amount: "0.00"
        });
        updateCategoryTables();
        updateCategoryDropdown();
    } else if(data.status === 'exists'){
        alert("Category already exists");          
    }else {
        alert(data.message);
    }
    })
    .catch(error => {
    console.error('Error details:', error);
    alert('Error when adding income category: ' + error.message);
    });
});

document.getElementById('saveExpenseCategory').addEventListener('click', () => {
    const categoryName = document.getElementById('expenseCategoryName').value;

    let addCategoryUrl = 'add-category/';
    const addCategoryUrlMeta = document.querySelector('meta[name="add-category-url"]');
    if (addCategoryUrlMeta) {
    addCategoryUrl = addCategoryUrlMeta.getAttribute('content');
    }

    document.getElementById('saveExpenseCategory').blur();
    const modal = bootstrap.Modal.getInstance(document.getElementById('addExpenseCategoryModal'));
    modal.hide();

    fetch(addCategoryUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'name': categoryName,
        'is_income': 'false'
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        window.categories['false'].push({
        id: data.id || Date.now(),
        name: data.name || categoryName,
        transaction_count: 0,
        total_amount: "0.00"
        });
        updateCategoryTables();
        updateCategoryDropdown();
    } else if(data.status === 'exists'){
        alert("Category already exists");          
    }else {
        alert(data.message);
    }
    })
    .catch(error => {
    alert('Error when adding expense category');
    });
});

// get available currencies
function loadAvailableCurrencies() {
    let getAvailableCurrenciesUrl = '/get-available-currencies/';
    const getAvailableCurrenciesUrlMeta = document.querySelector('meta[name="get-available-currencies-url"]');
    if (getAvailableCurrenciesUrlMeta) {
    getAvailableCurrenciesUrl = getAvailableCurrenciesUrlMeta.getAttribute('content');
    }
    
    fetch(getAvailableCurrenciesUrl, {
    method: 'GET',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
    }
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        updateCurrencyDropdown(data.currencies);
    } else {
        console.error('Failed to load available currencies:', data.message);
    }
    })
    .catch(error => {
    console.error('Error loading available currencies:', error);
    });
}

// Update currency dropdown
function updateCurrencyDropdown(currencies) {
    const currencySelect = document.getElementById('currencySelect');
    if (!currencySelect) return;
    
    if (!currencies || !Array.isArray(currencies)) {
    console.error('Invalid currencies data:', currencies);
    currencies = [];
    }
    
    currencySelect.innerHTML = '<option value="">-- Select Currency --</option>';
    
    const systemOptions = document.createElement('optgroup');
    systemOptions.label = 'System Currencies';
    
    const userOptions = document.createElement('optgroup');
    userOptions.label = 'Your Currencies';
    
    currencies.forEach(currency => {
    const option = document.createElement('option');
    option.value = currency.id;
    option.textContent = currency.currency_code;
    option.dataset.exchangeRate = currency.exchange_rate;
    
    if (currency.user) {
        userOptions.appendChild(option);
    } else {
        systemOptions.appendChild(option);
    }
    });
    
    if (systemOptions.children.length > 0) {
    currencySelect.appendChild(systemOptions);
    }
    if (userOptions.children.length > 0) {
    currencySelect.appendChild(userOptions);
    }
}

// Monitor currency change event
document.getElementById('currencySelect').addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    if (selectedOption && selectedOption.dataset.exchangeRate) {
    document.getElementById('exchangeRate').value = selectedOption.dataset.exchangeRate;
    document.getElementById('newCurrencyCode').value = '';
    }
});

function loadCurrencies() {
    let getCurrenciesUrl = '/get-currencies/';
    const getCurrenciesUrlMeta = document.querySelector('meta[name="get-currencies-url"]');
    if (getCurrenciesUrlMeta) {
    getCurrenciesUrl = getCurrenciesUrlMeta.getAttribute('content');
    }
    
    fetch(getCurrenciesUrl)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
        updateCurrencyTable(data.currencies);
        } else {
        console.error('Failed to load currencies:', data.message);
        }
    })
    .catch(error => {
        console.error('Error loading currencies:', error);
    });
}

function updateCurrencyTable(currencies) {
    console.log('Updating currency table with data:', currencies);
    const currencyTable = document.getElementById('currency-table');

    if (!currencyTable) {
    console.error('Currency table element not found');
    return;
    }
    
    if (currencies && currencies.length > 0) {
    let tableContent = '';
    currencies.forEach(currency => {
        let lastUpdated = 'N/A';
        try {
        lastUpdated = new Date(currency.last_updated).toLocaleString('en-US');
        } catch (e) {
        console.error('Error formatting date:', e);
        }
        
        tableContent += `
        <tr>
            <td>${currency.currency_code}</td>
            <td>${currency.exchange_rate}</td>
            <td>${lastUpdated}</td>
            <td>
            <button class="btn btn-danger btn-sm" onclick="deleteCurrency(${currency.id})">Delete</button>
            </td>
        </tr>
        `;
    });
    currencyTable.innerHTML = tableContent;
    console.log('Currency table updated with', currencies.length, 'items');
    } else {
    currencyTable.innerHTML = '<tr><td colspan="4" class="text-center">No currency available</td></tr>';
    console.log('No currencies available, showing empty message');
    }
}

document.getElementById('saveCurrency').addEventListener('click', () => {
    const selectedCurrency = document.getElementById('currencySelect').value;
    
    if (!selectedCurrency) {
    alert('Please select a currency');
    return;
    }
    
    let addCurrencyUrl = 'add-currency/';
    const addCurrencyUrlMeta = document.querySelector('meta[name="add-currency-url"]');
    if (addCurrencyUrlMeta) {
    addCurrencyUrl = addCurrencyUrlMeta.getAttribute('content');
    }

    document.getElementById('saveCurrency').blur();
    const modal = bootstrap.Modal.getInstance(document.getElementById('addCurrencyModal'));
    modal.hide();
    
    fetch(addCurrencyUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'currency_code': selectedCurrency
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        loadCurrencies();
    } else if(data.status === 'exists') {
        alert("Currency already exists");
    } else {
        alert(data.message);
    }
    })
    .catch(error => {
    console.error('Error:', error);
    alert('Error when adding currency');
    });
});

function deleteCurrency(id) {
    let deleteCurrencyUrl = 'delete-currency/';
    const deleteCurrencyUrlMeta = document.querySelector('meta[name="delete-currency-url"]');
    if (deleteCurrencyUrlMeta) {
    deleteCurrencyUrl = deleteCurrencyUrlMeta.getAttribute('content');
    }

    fetch(deleteCurrencyUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: `currency_id=${id}`
    })
    .then(response => {
    if (!response.ok) {
        return response.json().then(errorData => {
        throw new Error(errorData.message || 'Network response was not ok');
        });
    }
    return response.json();
    })
    .then(data => {
    if (data.status === 'success') {
        loadCurrencies();
        showSuccessMessage('Currency deleted successfully');
    } else {
        throw new Error(data.message || 'Failed to delete currency');
    }
    })
    .catch(error => {
    console.error('Delete currency error:', error);
    
    if (error.message.includes('Currency not found')) {
        window.currencies = window.currencies.filter(c => c.id !== id);
        updateCategoryTables();
    }
    
    showErrorMessage(error.message || 'Error when deleting currency');
    });
}

// Helper function to show success messages
function showSuccessMessage(message) {
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
    messageContainer.innerHTML = `
        <div class="alert alert-success" role="alert">
        ${message}
        </div>
    `;
    // Optional: Auto-hide the message after a few seconds
    setTimeout(() => {
        messageContainer.innerHTML = '';
    }, 3000);
    }
}

// Helper function to show error messages
function showErrorMessage(message) {
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
    messageContainer.innerHTML = `
        <div class="alert alert-danger" role="alert">
        ${message}
        </div>
    `;
    // Optional: Auto-hide the message after a few seconds
    setTimeout(() => {
        messageContainer.innerHTML = '';
    }, 3000);
    }
}

function loadAccounts() {
    let getAccountsUrl = 'get-accounts/';
    const getAccountsUrlMeta = document.querySelector('meta[name="get-accounts-url"]');
    if (getAccountsUrlMeta) {
    getAccountsUrl = getAccountsUrlMeta.getAttribute('content');
    }
    
    fetch(getAccountsUrl)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.accounts && Array.isArray(data.accounts)) {
        console.log('Successfully loaded accounts from API:', data.accounts.length);
        if (data.accounts.length > 0) {
            window.accounts = data.accounts;
            updateAccountTable();
        } else {
            console.warn('API returned empty accounts array, keeping current data');
        }
        } else {
        console.error('Failed to load accounts:', data);
        }
    })
    .catch(error => {
        console.error('Error loading accounts:', error);
    });
}

function updateAccountTable() {
    const accountTable = document.getElementById('account-table');
    if (!accountTable) {
    console.error('Account table element not found');
    return;
    }
    
    if (!window.accounts || !Array.isArray(window.accounts)) {
    console.error('Accounts not defined or not an array:', window.accounts);
    return;
    }
    
    console.log('Updating account table with', window.accounts.length, 'accounts');
    
    if (window.accounts.length > 0) {
    let tableContent = '';
    window.accounts.forEach((account, index) => {
        tableContent += `
        <tr data-account-id="${account.id}" data-index="${index}">
            <td>${account.account_name}</td>
            <td>${account.account_type}</td>
            <td>£${account.balance}</td>
            <td>
            <button class="btn btn-danger btn-sm" onclick="deleteAccount(${account.id})">Delete</button>
            <span class="drag-handle"><i class="bi bi-list"></i></span>
            </td>
        </tr>
        `;
    });
    accountTable.innerHTML = tableContent;
    
    // initialize drag functionality
    initDragAndDrop();
    } else {
    accountTable.innerHTML = '<tr><td colspan="4" class="text-center">No accounts available</td></tr>';
    }
}

function initDragAndDrop() {
    const table = document.getElementById('account-table');
    const rows = table.querySelectorAll('tr[data-account-id]');
    let draggedRow = null;
    
    // Add event listeners to each row
    rows.forEach(row => {
    const handle = row.querySelector('.drag-handle');
    
    if (!handle) return;
    
    // ensure only draggable when handle is clicked
    handle.addEventListener('mousedown', () => {
        row.setAttribute('draggable', 'true');
    });
    
    row.addEventListener('mouseup', () => {
        row.setAttribute('draggable', 'false');
    });
    
    row.addEventListener('dragstart', (e) => {
        draggedRow = row;
        row.classList.add('dragging');
        
        e.dataTransfer.setData('text/plain', '');
    });
    
    row.addEventListener('dragend', () => {
        row.classList.remove('dragging');
        draggedRow = null;
        
        rows.forEach(r => r.classList.remove('drop-target'));
    });
    
    row.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (!draggedRow || row === draggedRow) return;
        
        // add drop-target class to row
        rows.forEach(r => r.classList.remove('drop-target'));
        row.classList.add('drop-target');
    });
    
    row.addEventListener('drop', (e) => {
        e.preventDefault();
        if (!draggedRow || row === draggedRow) return;
        
        const fromIndex = parseInt(draggedRow.getAttribute('data-index'));
        const toIndex = parseInt(row.getAttribute('data-index'));
        
        // Reorder the accounts array
        const movedAccount = window.accounts.splice(fromIndex, 1)[0];
        window.accounts.splice(toIndex, 0, movedAccount);
        
        updateAccountTable();
        
        saveAccountOrderToBackend();
    });
    });
    
    const saveButton = document.getElementById('saveAccountOrder');
    if (saveButton) {
    const newSaveButton = saveButton.cloneNode(true);
    saveButton.parentNode.replaceChild(newSaveButton, saveButton);
    
    newSaveButton.addEventListener('click', saveAccountOrder);
    }
}

function saveAccountOrderToBackend() {
    const accountIds = window.accounts.map(a => a.id);

    let orderAccountUrl = 'order-accounts/';
    const orderAccountUrlMeta = document.querySelector('meta[name="order-accounts-url"]');
    if (orderAccountUrlMeta) {
    orderAccountUrl = orderAccountUrlMeta.getAttribute('content');
    }
    
    fetch(orderAccountUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({
        account_ids: accountIds
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status !== 'success') {
        console.error('Failed to save account order:', data.message);
        alert('Failed to order: ' + data.message);
    }
    })
    .catch(error => {
    console.error('Error saving account order:', error);
    });
}

document.getElementById('saveAccount').addEventListener('click', () => {
    const accountName = document.getElementById('accountName').value;
    const accountType = document.getElementById('addAccount').value;
    const balance = document.getElementById('addBalance').value;

    let addAccountUrl = 'add-account/';
    const addAccountUrlMeta = document.querySelector('meta[name="add-account-url"]');
    if (addAccountUrlMeta) {
    addAccountUrl = addAccountUrlMeta.getAttribute('content');
    }

    document.getElementById('saveAccount').blur();
    const modal = bootstrap.Modal.getInstance(document.getElementById('addAccountModal'));
    modal.hide();

    fetch(addAccountUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: new URLSearchParams({
        'account_name': accountName,
        'account_type': accountType,
        'balance': balance,
    })
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        loadAccounts();
    } else if(data.status === 'exists'){
        alert("Account already exists");          
    }else {
        alert(data.message);
    }
    })
    .catch(error => {
    console.error('Error when adding account:', error);
    alert('Error when adding account' + error);
    });
})

function deleteAccount(account_id) {
    if (!confirm('You are about to delete this budget. Are you sure?')) {
    return;
    }

    let deleteAccountUrl = 'delete-account/';
    const deleteAccountUrlMeta = document.querySelector('meta[name="delete-account-url"]');
    if (deleteAccountUrlMeta) {
    deleteAccountUrl = deleteAccountUrlMeta.getAttribute('content');
    }

    fetch(deleteAccountUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrftoken
    },
    body: `account_id=${account_id}`
    })
    .then(response => response.json())
    .then(data => {
    if (data.status === 'success') {
        loadAccounts();
    } else {
        alert(data.message);
    }
    })
    .catch(error => {
    alert('Error when deleting account:' + error);
    });
}

function exportToCSV() {
    const headers = ["Date", "Category", "Type", "Currency", "Amount", "Account", "Description"];
    const csvContent = "data:text/csv;charset=utf-8," 
        + headers.join(",") + "\n" 
        + transactions.map(t => 
            `${t.date},${t.category},${t.transaction_type ? "Income" : "Expense"},${t.currency},${t.amount},${t.account_name},${t.description}`
        ).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "transactions.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initialize data
function initializeData() {
    if (!document.getElementById('detail-page') && !document.getElementById('statistics-page') && 
    !document.getElementById('management-page')) {
    return;
    }
    
    // Initialize transactions data
    const transactionsDataElement = document.getElementById('transactions_data');
    if (transactionsDataElement) {
    try {
        window.transactions = JSON.parse(transactionsDataElement.textContent);
    } catch (e) {
        console.error('Failed to parse transactions data:', e);
        window.transactions = [];
    }
    }

    if (!window.accounts) {
    const accountsDataElement = document.getElementById('accounts_data');
    if(accountsDataElement){
        try {
        window.accounts = JSON.parse(accountsDataElement.textContent);
        console.log('Successfully parsed accounts:', window.accounts);
        console.log('Accounts data type:', typeof window.accounts);
        console.log('Is array?', Array.isArray(window.accounts));
        if (Array.isArray(window.accounts)) {
            console.log('Accounts length:', window.accounts.length);
            console.log('First account sample:', window.accounts.length > 0 ? JSON.stringify(window.accounts[0]) : 'none');
        }
        } catch (e) {
        console.error('Failed to parse accounts data:', e);
        window.accounts = [];
        }
    } else {
        console.warn('Accounts data element not found, initializing empty accounts');
        window.accounts = [];
    }
    }
    
    // Initialize category data only if window.categories has not been set yet
    if (!window.categories) {
    const categoriesDataElement = document.getElementById('categories_data');
    if (categoriesDataElement) {
        try {
        window.categories = JSON.parse(categoriesDataElement.textContent);
        console.log('Successfully parsed categories:', window.categories);
        } catch (e) {
        console.error('Failed to parse categories data:', e);
        window.categories = {'true': [], 'false': []};
        }
    } else {
        console.warn('Categories data element not found, initializing empty categories');
        window.categories = {'true': [], 'false': []};
    }
    }
    
    if (!window.categories) {
    console.warn('Categories still not defined after initialization, creating empty object');
    window.categories = {};
    }
    
    if (!window.categories['true']) {
    console.warn('true category array not found, initializing empty array');
    window.categories['true'] = [];
    }
    
    if (!window.categories['false']) {
    console.warn('false category array not found, initializing empty array');
    window.categories['false'] = [];
    }
    
    console.log('Final categories structure:', window.categories);
}

document.addEventListener("DOMContentLoaded", () => {
    initializeData();
    console.log('After initialization, accounts:', window.accounts);
    const accountTable = document.getElementById('account-table');
    if (accountTable) {
    console.log('Account table found, updating with current data');
    updateAccountTable();
    }

    const tabLinks = document.querySelectorAll('a[data-bs-toggle="tab"]');

    tabLinks.forEach(tab => {
    tab.addEventListener('shown.bs.tab', function(event) {
        currentFilterState = {
        transactionType: 'all',
        category: 'all',
        description: ''
        };
        
        document.querySelectorAll('.btn-secondary, .btn-success, .btn-danger').forEach(btn => {
        btn.classList.remove('active');
        });
        const defaultAllBtn = document.querySelector('.btn-secondary');
        if (defaultAllBtn) {
        defaultAllBtn.classList.add('active');
        }

        const descriptionFilter = document.getElementById('description-filter');
        if (descriptionFilter) {
        descriptionFilter.value = '';
        }
        
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
        categoryFilter.value = 'all';
        }
        
        refreshTables();
    });
    });

    // Initialize pagination controls
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const pageSizeSelector = document.getElementById('pageSizeSelector');
    
    if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => changePage('prev'));
    }
    
    if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => changePage('next'));
    }
    
    if (pageSizeSelector) {
    pageSizeSelector.addEventListener('change', (e) => changePageSize(e.target.value));
    }

    const savedPageSize = localStorage.getItem('preferredPageSize');
    if (savedPageSize) {
        pageSize = parseInt(savedPageSize);
        
        // Update the page size selector to reflect saved preference
        const pageSizeSelector = document.getElementById('pageSizeSelector');
        if (pageSizeSelector) {
            pageSizeSelector.value = savedPageSize;
        }
    }

    if(document.getElementById('detail-page')){
    refreshTables();
    filterCategory();
    filterDescription();
    updateCategoryDropdown(); // Refresh drop-down box
    updateAccountDropdown();
    populateTransactionCurrencyDropdowns();
    }
    
    if(document.getElementById('management-page')){
    updateCategoryTables(); // Initialize Management Table
    }

    if (document.getElementById('budget-table')) {
    loadBudgets();
    }

    if(document.getElementById('currency-table')){
    loadCurrencies();
    }

    if (document.getElementById('currency')) {
    loadAvailableCurrencies();
    }

    if (document.getElementById('account-table')) {
    loadAccounts();
    }
    if(document.getElementById('contact-page')){
    console.log("  £££ \n £   £\n£££££££\n £    \n££££££\n");
    }

    // Other general initialization
    calculateRemainingBudget();
    const toggleButton = document.getElementById('theme-toggle');
    const lightIcon = document.querySelector('.light-icon');
    const darkIcon = document.querySelector('.dark-icon');
    
    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateIcons(savedTheme);
    } else if (prefersDark) {
    document.documentElement.setAttribute('data-theme', 'dark');
    updateIcons('dark');
    } else {
    document.documentElement.setAttribute('data-theme', 'light');
    updateIcons('light');
    }

    // Toggle theme when button is clicked
    toggleButton.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Update theme attribute
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // Save preference to localStorage
        localStorage.setItem('theme', newTheme);
        
        // Update icons
        updateIcons(newTheme);
    });

    function updateIcons(theme) {
    if (theme === 'dark') {
        lightIcon.classList.add('d-none');
        darkIcon.classList.remove('d-none');
    } else {
        lightIcon.classList.remove('d-none');
        darkIcon.classList.add('d-none');
    }
    }
});