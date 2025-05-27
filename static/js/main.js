document.addEventListener('DOMContentLoaded', function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const exampleLink = document.querySelector('.example-link');
    const walletInput = document.getElementById('walletAddress');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');
    const rawDataContainer = document.getElementById('rawDataContainer');
    const toggleRawBtn = document.getElementById('toggleRawBtn');
    const copyAddressBtn = document.getElementById('copyAddressBtn');
    
    // Example address click
    exampleLink.addEventListener('click', function(e) {
        e.preventDefault();
        walletInput.value = this.textContent.trim();
        analyzeWallet();
    });
    
    // Analyze button click
    analyzeBtn.addEventListener('click', function() {
        analyzeWallet();
    });
    
    // Enter key press in input
    walletInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeWallet();
        }
    });
    
    // Toggle raw data
    toggleRawBtn.addEventListener('click', function() {
        rawDataContainer.style.display = 
            rawDataContainer.style.display === 'none' ? 'flex' : 'none';
    });
    
    // Copy address button
    copyAddressBtn.addEventListener('click', function() {
        const addressText = document.getElementById('walletAddressDisplay').textContent;
        navigator.clipboard.writeText(addressText).then(function() {
            const originalText = copyAddressBtn.innerHTML;
            copyAddressBtn.innerHTML = '<i class="bi bi-check"></i>';
            setTimeout(() => {
                copyAddressBtn.innerHTML = originalText;
            }, 2000);
        });
    });
    
    function analyzeWallet() {
        const walletAddress = walletInput.value.trim();
        
        if (!walletAddress) {
            alert('Please enter a wallet address');
            return;
        }
        
        // Reset previous results
        resetResults();
        
        // Show loading and the results container (will be populated incrementally)
        loadingSpinner.style.display = 'block';
        resultsContainer.style.display = 'block';
        
        // Show section-specific loaders
        document.getElementById('profileLoading').style.display = 'block';
        document.getElementById('insightsLoading').style.display = 'block';
        document.getElementById('networkLoading').style.display = 'block';
        document.getElementById('timelineLoading').style.display = 'block';
        
        // Store data for combined display
        const combinedData = { profile: null };
        
        // Fetch profile data (fast)
        fetchProfileData(walletAddress)
            .then(data => {
                combinedData.profile = data.profile;
                displayProfile(combinedData.profile);
                document.getElementById('profileLoading').style.display = 'none';
            })
            .catch(error => {
                document.getElementById('profileLoading').style.display = 'none';
                document.getElementById('profileError').style.display = 'block';
                document.getElementById('profileError').textContent = `Error: ${error.message}`;
            });
        
        // Fetch LLM insights (can be slow)
        fetchLLMInsights(walletAddress)
            .then(data => {
                combinedData.llmInsights = data;
                displayLLMInsights(data);
                document.getElementById('insightsLoading').style.display = 'none';
            })
            .catch(error => {
                document.getElementById('insightsLoading').style.display = 'none';
                document.getElementById('insightsError').style.display = 'block';
                document.getElementById('insightsError').textContent = `Error: ${error.message}`;
            });
        
        // Fetch network graph
        // fetchNetworkGraph(walletAddress)
        //     .then(data => {
        //         displayNetworkGraph(data.graph);
        //         document.getElementById('networkLoading').style.display = 'none';
        //     })
        //     .catch(error => {
        //         document.getElementById('networkLoading').style.display = 'none';
        //         document.getElementById('networkError').style.display = 'block';
        //         document.getElementById('networkError').textContent = `Error: ${error.message}`;
        //     });
        
        // Fetch timeline graph
        fetchTimelineGraph(walletAddress)
            .then(data => {
                displayTimelineGraph(data.timeline);
                document.getElementById('timelineLoading').style.display = 'none';
            })
            .catch(error => {
                document.getElementById('timelineLoading').style.display = 'none';
                document.getElementById('timelineError').style.display = 'block';
                document.getElementById('timelineError').textContent = `Error: ${error.message}`;
            });
        
        // Hide main spinner when all requests are started
        loadingSpinner.style.display = 'none';
    }
    
    // Helper function to reset UI
    function resetResults() {
        // Hide error messages
        document.querySelectorAll('.error-message').forEach(el => el.style.display = 'none');
        
        // Clear existing content areas
        document.getElementById('healthSummary').innerHTML = '';
        document.getElementById('entitiesContainer').innerHTML = '';
        document.getElementById('usernamesContainer').innerHTML = '';
        document.getElementById('keyInsights').innerHTML = '';
        document.getElementById('transactionsTable').innerHTML = '';
        document.getElementById('rawJson').textContent = '';
        
        // Clear visualizations
        document.getElementById('networkGraph').innerHTML = '';
        document.getElementById('timelineGraph').innerHTML = '';
    }
    
    // API fetch functions
    async function fetchProfileData(walletAddress) {
        const response = await fetch('/analyze/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: walletAddress }),
        });
        
        if (!response.ok) {
            throw new Error(`Profile API error: ${response.status}`);
        }
        
        return response.json();
    }
    
    async function fetchLLMInsights(walletAddress) {
        const response = await fetch('/analyze/llm-insights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: walletAddress }),
        });
        
        if (!response.ok) {
            throw new Error(`LLM API error: ${response.status}`);
        }
        
        return response.json();
    }
    
    async function fetchNetworkGraph(walletAddress) {
        const response = await fetch('/analyze/network-graph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: walletAddress }),
        });
        
        if (!response.ok) {
            throw new Error(`Graph API error: ${response.status}`);
        }
        
        return response.json();
    }
    
    async function fetchTimelineGraph(walletAddress) {
        const response = await fetch('/analyze/timeline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: walletAddress }),
        });
        
        if (!response.ok) {
            throw new Error(`Timeline API error: ${response.status}`);
        }
        
        return response.json();
    }
    
    // Display functions for each data section
    function displayProfile(profile) {
        // Raw JSON for debugging
        document.getElementById('rawJson').textContent = JSON.stringify(profile, null, 2);
        
        // Fill in basic profile info
        document.getElementById('walletAddressDisplay').textContent = profile.address;
        document.getElementById('persona').textContent = profile.persona || 'Unknown';
        document.getElementById('walletAge').textContent = `${profile.wallet_age_days} days`;
        document.getElementById('txCount').textContent = profile.total_transactions;
        document.getElementById('primaryActivity').textContent = profile.primary_activity;
        
        // Transactions table
        const transactionsTable = document.getElementById('transactionsTable');
        transactionsTable.innerHTML = '';
        
        if (profile.transactions && profile.transactions.length > 0) {
            profile.transactions.forEach(tx => {
                const row = document.createElement('tr');
                
                const dateCell = document.createElement('td');
                dateCell.textContent = tx.Timestamp ? tx.Timestamp.split('T')[0] : 'N/A';
                
                const functionCell = document.createElement('td');
                functionCell.textContent = tx.Function || 'N/A';
                
                const typeCell = document.createElement('td');
                typeCell.textContent = tx.Type || 'N/A';
                
                const versionCell = document.createElement('td');
                versionCell.textContent = tx.Version || 'N/A';
                
                row.appendChild(dateCell);
                row.appendChild(functionCell);
                row.appendChild(typeCell);
                row.appendChild(versionCell);
                
                transactionsTable.appendChild(row);
            });
        } else {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 4;
            cell.textContent = 'No transactions found';
            cell.className = 'text-center';
            row.appendChild(cell);
            transactionsTable.appendChild(row);
        }  
    }
    
    function displayLLMInsights(insights) {
        // Health summary - parse markdown
        const healthSummary = document.getElementById('healthSummary');
        healthSummary.innerHTML = marked.parse(insights.health_summary || 'No health summary available');
        
        // Social handle
        document.getElementById('socialHandle').textContent = insights.social_handle || 'N/A';
        
        // Entity insights
        const entitiesContainer = document.getElementById('entitiesContainer');
        const usernamesContainer = document.getElementById('usernamesContainer');
        const keyInsights = document.getElementById('keyInsights');
        
        if (insights.entity_insights) {
            const entities = insights.entity_insights.prominent_entities || [];
            const usernames = insights.entity_insights.usernames || [];
            const companies = insights.entity_insights.companies || [];
            const insightsData = insights.entity_insights.insights || {};
            
            // Render entities and companies
            [...entities, ...companies].forEach(entity => {
                const tag = document.createElement('span');
                tag.className = 'tag tag-entity';
                tag.textContent = entity;
                entitiesContainer.appendChild(tag);
            });
            
            // Render usernames
            usernames.forEach(username => {
                const tag = document.createElement('span');
                tag.className = 'tag tag-username';
                tag.textContent = username;
                usernamesContainer.appendChild(tag);
            });
            
            // Render insights
            Object.entries(insightsData).forEach(([key, value]) => {
                const insightDiv = document.createElement('div');
                insightDiv.className = 'insight-item';
                insightDiv.innerHTML = `<strong>${key.replace(/_/g, ' ')}:</strong> ${value}`;
                keyInsights.appendChild(insightDiv);
            });
        }
    }
    
    // function displayNetworkGraph(graphJson) {
    //     if (graphJson) {
    //         Plotly.newPlot('networkGraph', JSON.parse(graphJson));
    //     }
    // }
    
    function displayTimelineGraph(timelineJson) {
        if (timelineJson) {
            Plotly.newPlot('timelineGraph', JSON.parse(timelineJson));
        }
    }
});
