// Tap Bonds AI Layer - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // API base URL
    const API_BASE_URL = '/api';

    // DOM elements
    const queryInput = document.getElementById('query-input');
    const queryButton = document.getElementById('query-button');
    const resultsContainer = document.getElementById('results-container');
    const isinInput = document.getElementById('isin-input');
    const isinButton = document.getElementById('isin-button');
    const compareInput = document.getElementById('compare-input');
    const compareButton = document.getElementById('compare-button');
    const portfolioInput = document.getElementById('portfolio-input');
    const portfolioButton = document.getElementById('portfolio-button');
    const screenerForm = document.getElementById('screener-form');

    // Event listeners
    queryButton.addEventListener('click', handleQuerySubmit);
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleQuerySubmit();
        }
    });

    isinButton.addEventListener('click', handleIsinSearch);
    compareButton.addEventListener('click', handleCompareSubmit);
    portfolioButton.addEventListener('click', handlePortfolioSubmit);
    screenerForm.addEventListener('submit', handleScreenerSubmit);

    // Handle natural language query
    async function handleQuerySubmit() {
        const query = queryInput.value.trim();
        if (!query) return;

        showLoading();

        try {
            const response = await fetch(`${API_BASE_URL}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            displayError('Error processing query', error);
        }
    }

    // Handle ISIN search
    async function handleIsinSearch() {
        const isin = isinInput.value.trim();
        if (!isin) return;

        showLoading();

        try {
            const response = await fetch(`${API_BASE_URL}/bond/${isin}`);
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            displayError('Error searching for bond', error);
        }
    }

    // Handle bond comparison
    async function handleCompareSubmit() {
        const isinsText = compareInput.value.trim();
        if (!isinsText) return;

        const isins = isinsText.split(',').map(isin => isin.trim());
        if (isins.length < 2) {
            displayError('Please enter at least two ISINs separated by commas');
            return;
        }

        showLoading();

        try {
            const response = await fetch(`${API_BASE_URL}/compare`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ isins })
            });

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            displayError('Error comparing bonds', error);
        }
    }

    // Handle portfolio analysis
    async function handlePortfolioSubmit() {
        const isinsText = portfolioInput.value.trim();
        if (!isinsText) return;

        const isins = isinsText.split(',').map(isin => isin.trim());
        if (isins.length < 1) {
            displayError('Please enter at least one ISIN');
            return;
        }

        showLoading();

        try {
            const response = await fetch(`${API_BASE_URL}/portfolio/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ isins })
            });

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            displayError('Error analyzing portfolio', error);
        }
    }

    // Handle screener form submission
    async function handleScreenerSubmit(e) {
        e.preventDefault();

        // Get form values
        const minYield = document.getElementById('min-yield').value;
        const maxYield = document.getElementById('max-yield').value;
        const rating = document.getElementById('rating').value;
        const sector = document.getElementById('sector').value;
        const minMaturity = document.getElementById('min-maturity').value;
        const maxMaturity = document.getElementById('max-maturity').value;
        const issuerType = document.getElementById('issuer-type').value;
        const financialHealth = document.getElementById('financial-health').value;

        // Build query parameters
        const params = new URLSearchParams();
        if (minYield) params.append('min_yield', minYield);
        if (maxYield) params.append('max_yield', maxYield);
        if (rating) params.append('rating', rating);
        if (sector) params.append('sector', sector);
        if (minMaturity) params.append('min_maturity', minMaturity);
        if (maxMaturity) params.append('max_maturity', maxMaturity);
        if (issuerType) params.append('issuer_type', issuerType);
        if (financialHealth) params.append('financial_health', financialHealth);

        showLoading();

        try {
            const response = await fetch(`${API_BASE_URL}/screen?${params.toString()}`);
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            displayError('Error screening bonds', error);
        }
    }

    // Display results
    function displayResults(data) {
        resultsContainer.innerHTML = '';

        if (data.status === 'error') {
            displayError(data.message);
            return;
        }

        // Create results header
        const header = document.createElement('div');
        header.className = 'alert alert-success';
        header.textContent = data.message;
        resultsContainer.appendChild(header);

        // Display data
        if (data.data) {
            if (Array.isArray(data.data)) {
                // Display list of bonds
                displayBondsList(data.data);
            } else if (data.data.bonds) {
                // Display portfolio analysis
                displayPortfolioAnalysis(data.data);
            } else if (data.data.cashflows) {
                // Display cashflow schedule
                displayCashflowSchedule(data.data);
            } else {
                // Display single bond
                displayBondDetails(data.data);
            }
        }
    }

    // Display list of bonds
    function displayBondsList(bonds) {
        const container = document.createElement('div');
        container.className = 'bond-list';

        bonds.forEach(bond => {
            const bondItem = document.createElement('div');
            bondItem.className = 'bond-item';

            // Bond header
            const header = document.createElement('h4');
            header.textContent = bond.issuer || 'Unknown Issuer';
            bondItem.appendChild(header);

            // ISIN
            if (bond.isin) {
                const isin = document.createElement('p');
                isin.innerHTML = `<strong>ISIN:</strong> ${bond.isin}`;
                bondItem.appendChild(isin);
            }

            // Yield
            if (bond.yield !== undefined) {
                const yieldEl = document.createElement('p');
                yieldEl.innerHTML = `<strong>Yield:</strong> ${bond.yield.toFixed(2)}%`;
                bondItem.appendChild(yieldEl);
            }

            // Effective yield (if available)
            if (bond.effective_yield !== undefined) {
                const effectiveYield = document.createElement('p');
                effectiveYield.innerHTML = `<strong>Effective Yield:</strong> ${bond.effective_yield.toFixed(2)}%`;
                bondItem.appendChild(effectiveYield);
            }

            // Rating
            if (bond.rating) {
                const rating = document.createElement('p');
                rating.innerHTML = `<strong>Rating:</strong> ${bond.rating}`;
                bondItem.appendChild(rating);
            }

            // Maturity
            if (bond.maturity_date) {
                const maturity = document.createElement('p');
                maturity.innerHTML = `<strong>Maturity:</strong> ${new Date(bond.maturity_date).toLocaleDateString()}`;
                bondItem.appendChild(maturity);
            }

            // Financial health (if available)
            if (bond.financial_health && bond.financial_health.rating) {
                const healthClass = `financial-health-${bond.financial_health.rating.toLowerCase()}`;
                const health = document.createElement('p');
                health.innerHTML = `<strong>Financial Health:</strong> <span class="${healthClass}">${bond.financial_health.rating}</span>`;
                bondItem.appendChild(health);
            }

            container.appendChild(bondItem);
        });

        resultsContainer.appendChild(container);
    }

    // Display portfolio analysis
    function displayPortfolioAnalysis(data) {
        const container = document.createElement('div');

        // Summary section
        const summary = document.createElement('div');
        summary.className = 'card mb-4';
        
        const summaryHeader = document.createElement('div');
        summaryHeader.className = 'card-header';
        summaryHeader.innerHTML = '<h4>Portfolio Summary</h4>';
        
        const summaryBody = document.createElement('div');
        summaryBody.className = 'card-body';
        
        // Add summary metrics
        if (data.summary) {
            const metrics = document.createElement('div');
            metrics.className = 'row';
            
            // Total value
            const totalValue = document.createElement('div');
            totalValue.className = 'col-md-3 mb-3';
            totalValue.innerHTML = `<strong>Total Value:</strong> ${data.summary.total_value.toLocaleString()}`;
            metrics.appendChild(totalValue);
            
            // Weighted yield
            const weightedYield = document.createElement('div');
            weightedYield.className = 'col-md-3 mb-3';
            weightedYield.innerHTML = `<strong>Weighted Yield:</strong> ${data.summary.weighted_yield.toFixed(2)}%`;
            metrics.appendChild(weightedYield);
            
            // Diversification score
            const diversification = document.createElement('div');
            diversification.className = 'col-md-3 mb-3';
            diversification.innerHTML = `<strong>Diversification:</strong> ${(data.summary.diversification_score * 100).toFixed(0)}%`;
            metrics.appendChild(diversification);
            
            // Total bonds
            const totalBonds = document.createElement('div');
            totalBonds.className = 'col-md-3 mb-3';
            totalBonds.innerHTML = `<strong>Total Bonds:</strong> ${data.summary.total_bonds}`;
            metrics.appendChild(totalBonds);
            
            summaryBody.appendChild(metrics);
        }
        
        summary.appendChild(summaryHeader);
        summary.appendChild(summaryBody);
        container.appendChild(summary);
        
        // Bonds list
        if (data.bonds) {
            const bondsHeader = document.createElement('h4');
            bondsHeader.textContent = 'Portfolio Bonds';
            bondsHeader.className = 'mt-4 mb-3';
            container.appendChild(bondsHeader);
            
            displayBondsList(data.bonds);
        }
        
        resultsContainer.appendChild(container);
    }

    // Display cashflow schedule
    function displayCashflowSchedule(data) {
        const container = document.createElement('div');
        
        // Bond details
        if (data.bond_details) {
            const bondDetails = document.createElement('div');
            bondDetails.className = 'bond-item mb-4';
            
            const header = document.createElement('h4');
            header.textContent = data.bond_details.issuer || 'Bond Details';
            bondDetails.appendChild(header);
            
            if (data.bond_details.isin) {
                const isin = document.createElement('p');
                isin.innerHTML = `<strong>ISIN:</strong> ${data.bond_details.isin}`;
                bondDetails.appendChild(isin);
            }
            
            container.appendChild(bondDetails);
        }
        
        // Cashflow table
        if (data.cashflows && data.cashflows.length > 0) {
            const tableContainer = document.createElement('div');
            tableContainer.className = 'table-responsive';
            
            const table = document.createElement('table');
            table.className = 'table table-striped';
            
            // Table header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            
            ['Payment Date', 'Amount', 'Type', 'Days'].forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                headerRow.appendChild(th);
            });
            
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            // Table body
            const tbody = document.createElement('tbody');
            
            data.cashflows.forEach(cashflow => {
                const row = document.createElement('tr');
                
                // Payment date
                const dateCell = document.createElement('td');
                dateCell.textContent = new Date(cashflow.payment_date).toLocaleDateString();
                row.appendChild(dateCell);
                
                // Amount
                const amountCell = document.createElement('td');
                amountCell.textContent = cashflow.amount ? cashflow.amount.toLocaleString() : 'N/A';
                row.appendChild(amountCell);
                
                // Type
                const typeCell = document.createElement('td');
                typeCell.textContent = cashflow.payment_type || 'N/A';
                row.appendChild(typeCell);
                
                // Days from previous
                const daysCell = document.createElement('td');
                daysCell.textContent = cashflow.days_from_previous || 'N/A';
                row.appendChild(daysCell);
                
                tbody.appendChild(row);
            });
            
            table.appendChild(tbody);
            tableContainer.appendChild(table);
            container.appendChild(tableContainer);
        }
        
        // Summary
        if (data.summary) {
            const summary = document.createElement('div');
            summary.className = 'alert alert-info mt-3';
            
            const totalInterest = document.createElement('p');
            totalInterest.innerHTML = `<strong>Total Interest:</strong> ${data.summary.total_interest.toLocaleString()}`;
            summary.appendChild(totalInterest);
            
            const totalPrincipal = document.createElement('p');
            totalPrincipal.innerHTML = `<strong>Total Principal:</strong> ${data.summary.total_principal.toLocaleString()}`;
            summary.appendChild(totalPrincipal);
            
            const dayCount = document.createElement('p');
            dayCount.innerHTML = `<strong>Day Count Convention:</strong> ${data.summary.day_count_convention}`;
            summary.appendChild(dayCount);
            
            container.appendChild(summary);
        }
        
        resultsContainer.appendChild(container);
    }

    // Display single bond details
    function displayBondDetails(bond) {
        const container = document.createElement('div');
        container.className = 'bond-details';
        
        const bondItem = document.createElement('div');
        bondItem.className = 'bond-item';
        
        // Bond header
        const header = document.createElement('h4');
        header.textContent = bond.issuer || 'Bond Details';
        bondItem.appendChild(header);
        
        // Create a details list
        const detailsList = document.createElement('dl');
        detailsList.className = 'row';
        
        // Helper function to add a detail item
        function addDetail(term, detail) {
            if (detail !== undefined && detail !== null) {
                const dtContainer = document.createElement('div');
                dtContainer.className = 'col-sm-6 mb-2';
                
                const dt = document.createElement('dt');
                dt.className = 'col-sm-4';
                dt.textContent = term;
                
                const dd = document.createElement('dd');
                dd.className = 'col-sm-8';
                dd.textContent = detail;
                
                dtContainer.appendChild(dt);
                dtContainer.appendChild(dd);
                detailsList.appendChild(dtContainer);
            }
        }
        
        // Add bond details
        addDetail('ISIN', bond.isin);
        addDetail('Issuer', bond.issuer);
        addDetail('Type', bond.bond_type);
        addDetail('Sector', bond.sector);
        addDetail('Rating', bond.rating);
        addDetail('Yield', bond.yield ? `${bond.yield.toFixed(2)}%` : null);
        addDetail('Coupon Rate', bond.coupon_rate ? `${bond.coupon_rate.toFixed(2)}%` : null);
        addDetail('Face Value', bond.face_value ? bond.face_value.toLocaleString() : null);
        addDetail('Issue Date', bond.issue_date ? new Date(bond.issue_date).toLocaleDateString() : null);
        addDetail('Maturity Date', bond.maturity_date ? new Date(bond.maturity_date).toLocaleDateString() : null);
        
        bondItem.appendChild(detailsList);
        container.appendChild(bondItem);
        
        resultsContainer.appendChild(container);
    }

    // Show loading indicator
    function showLoading() {
        resultsContainer.innerHTML = `
            <div class="text-center my-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Processing your request...</p>
            </div>
        `;
    }

    // Display error message
    function displayError(message, error) {
        resultsContainer.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Error</h4>
                <p>${message}</p>
                ${error ? `<p class="mb-0"><small>${error.toString()}</small></p>` : ''}
            </div>
        `;
        
        if (error) {
            console.error(error);
        }
    }

    function createDownloadButton(data, filename, type) {
        // Create a button element
        const button = document.createElement('button');
        button.className = 'download-btn';
        button.innerHTML = `<i class="fas fa-download"></i> ${type}`;
        
        // Add click event listener
        button.addEventListener('click', () => {
            let content = '';
            let mimeType = '';
            
            if (type === 'CSV') {
                // Convert data to CSV
                const headers = Object.keys(data[0]).join(',');
                const rows = data.map(row => Object.values(row).join(',')).join('\n');
                content = `${headers}\n${rows}`;
                mimeType = 'text/csv';
                filename = `${filename}.csv`;
            } else if (type === 'Excel') {
                // For Excel, we'll use a simple CSV that Excel can open
                const headers = Object.keys(data[0]).join(',');
                const rows = data.map(row => Object.values(row).join(',')).join('\n');
                content = `${headers}\n${rows}`;
                mimeType = 'application/vnd.ms-excel';
                filename = `${filename}.xls`;
            } else if (type === 'JSON') {
                // Convert data to JSON
                content = JSON.stringify(data, null, 2);
                mimeType = 'application/json';
                filename = `${filename}.json`;
            }
            
            // Create a blob and download link
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
        
        return button;
    }

    function addDownloadButtons(container, data, filename) {
        // Create a container for download buttons
        const downloadContainer = document.createElement('div');
        downloadContainer.className = 'download-container';
        
        // Add title
        const title = document.createElement('span');
        title.textContent = 'Download: ';
        downloadContainer.appendChild(title);
        
        // Add buttons for different formats
        downloadContainer.appendChild(createDownloadButton(data, filename, 'CSV'));
        downloadContainer.appendChild(createDownloadButton(data, filename, 'Excel'));
        downloadContainer.appendChild(createDownloadButton(data, filename, 'JSON'));
        
        // Add to container
        container.appendChild(downloadContainer);
    }

    function createDocumentPreviewPane(url) {
        // Create container
        const container = document.createElement('div');
        container.className = 'document-preview';
        
        // Create iframe for PDF
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.width = '100%';
        iframe.height = '500px';
        
        // Add to container
        container.appendChild(iframe);
        
        return container;
    }

    function renderTable(data, container) {
        // Create table
        const table = document.createElement('table');
        table.className = 'data-table';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        // Add headers
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        
        // Add rows
        data.forEach(row => {
            const tr = document.createElement('tr');
            
            // Add cells
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                
                // Format value if it's a number
                if (typeof value === 'number') {
                    if (value % 1 !== 0) {
                        td.textContent = value.toFixed(2);
                    } else {
                        td.textContent = value;
                    }
                } else {
                    td.textContent = value;
                }
                
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        container.appendChild(table);
        
        // Add download buttons
        addDownloadButtons(container, data, 'bond_data');
    }
}); 