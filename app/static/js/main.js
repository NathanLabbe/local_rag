document.addEventListener('DOMContentLoaded', function() {
    // Show model info dialog on page load
    const modelInfoDialog = document.getElementById('model-info-dialog');
    modelInfoDialog.setAttribute('open', '');
    
    // Sidebar collapse/expand functionality
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        sidebarToggle.textContent = sidebar.classList.contains('collapsed') ? '→' : '←';
    });

    // System Prompt and Model Settings
    const systemPromptInput = document.getElementById('system-prompt');
    const llmModelInput = document.getElementById('llm-model');
    const saveSettingsBtn = document.getElementById('save-settings');
    
    saveSettingsBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    system_prompt: systemPromptInput.value,
                    llm_model: llmModelInput.value
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save settings');
            }
            
            showNotification('Settings saved successfully');
        } catch (error) {
            showNotification('Error saving settings: ' + error.message, true);
        }
    });

    // Dialog handling
    document.querySelectorAll('[data-target]').forEach(button => {
        button.addEventListener('click', () => {
            const target = button.dataset.target;
            const dialog = document.getElementById(target);
            if (dialog.hasAttribute('open')) {
                dialog.removeAttribute('open');
            } else {
                dialog.setAttribute('open', '');
            }
        });
    });

    // Google Drive import
    const driveImportBtn = document.getElementById('drive-import-btn');
    const driveImportForm = document.getElementById('drive-import-form');
    
    driveImportBtn.addEventListener('click', () => {
        driveImportForm.classList.toggle('hidden');
    });
    
    document.getElementById('drive-import-cancel').addEventListener('click', () => {
        driveImportForm.classList.add('hidden');
    });
    
    document.getElementById('drive-import-submit').addEventListener('click', async () => {
        const folderId = document.getElementById('folder-id').value;
        
        try {
            document.getElementById('loading-documents').classList.remove('hidden');
            const response = await fetch('/api/documents/drive', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ folder_id: folderId || null })
            });
            
            if (!response.ok) {
                throw new Error('Failed to import from Google Drive');
            }
            
            const result = await response.json();
            showNotification(`Successfully imported ${result.length} documents`);
            loadDocuments();
            driveImportForm.classList.add('hidden');
        } catch (error) {
            showNotification('Error importing from Google Drive: ' + error.message, true);
        } finally {
            document.getElementById('loading-documents').classList.add('hidden');
        }
    });

    // Document upload
    const uploadForm = document.getElementById('upload-form');
    
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('document-file');
        if (!fileInput.files.length) {
            showNotification('Please select a file', true);
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        try {
            document.getElementById('loading-documents').classList.remove('hidden');
            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to upload document');
            }
            
            const result = await response.json();
            showNotification(`Successfully uploaded ${result.document_name}`);
            loadDocuments();
            fileInput.value = '';
        } catch (error) {
            showNotification('Error uploading document: ' + error.message, true);
        } finally {
            document.getElementById('loading-documents').classList.add('hidden');
        }
    });

    // Chat functionality
    const chatForm = document.getElementById('chat-form');
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const useLlmCheckbox = document.getElementById('use-llm');
    
    let chatHistory = [];
    
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = messageInput.value.trim();
        if (!query) return;
        
        // Add user message to UI
        addMessage('user', query);
        messageInput.value = '';
        
        try {
            // Show loading indicator
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'message assistant loading';
            loadingMessage.textContent = 'Thinking...';
            chatMessages.appendChild(loadingMessage);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Get checkbox values
            const useLlm = useLlmCheckbox.checked;
            const useRetrieval = document.getElementById('use-retrieval').checked;
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    history: chatHistory,
                    use_llm: useLlm,
                    skip_retrieval: !useRetrieval // We inverse the value here
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            const result = await response.json();
            
            // Remove loading indicator
            chatMessages.removeChild(loadingMessage);
            
            // Add assistant message with sources
            addMessage('assistant', result.answer, result.sources);
            
            // Update chat history
            chatHistory.push({role: 'user', content: query});
            chatHistory.push({role: 'assistant', content: result.answer});
        } catch (error) {
            chatMessages.removeChild(chatMessages.lastChild); // Remove loading
            showNotification('Error: ' + error.message, true);
        }
    });

    // Load current settings from server
    async function loadSettings() {
        try {
            const response = await fetch('/api/settings');
            
            if (!response.ok) {
                throw new Error('Failed to fetch settings');
            }
            
            const settings = await response.json();
            
            // Update form fields with complete values
            if (settings.system_prompt) {
                systemPromptInput.value = settings.system_prompt;
                // Make sure textarea is big enough to show content
                systemPromptInput.style.height = 'auto';
                systemPromptInput.style.height = (systemPromptInput.scrollHeight) + 'px';
            }
            
            if (settings.llm_model) {
                llmModelInput.value = settings.llm_model;
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    // Make system prompt textarea resize as content changes
    systemPromptInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Document listing and management
    async function loadDocuments() {
        const documentsList = document.getElementById('documents');
        
        try {
            document.getElementById('loading-documents').classList.remove('hidden');
            const response = await fetch('/api/documents');
            
            if (!response.ok) {
                throw new Error('Failed to fetch documents');
            }
            
            const documents = await response.json();
            
            documentsList.innerHTML = '';
            
            if (documents.length === 0) {
                const emptyItem = document.createElement('li');
                emptyItem.textContent = 'No documents found';
                documentsList.appendChild(emptyItem);
                return;
            }
            
            documents.forEach(doc => {
                const item = document.createElement('li');
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = doc.document_name;
                nameSpan.title = `Chunks: ${doc.chunk_count}`;
                
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.className = 'secondary';
                deleteBtn.onclick = () => deleteDocument(doc.document_id, doc.document_name);
                
                item.appendChild(nameSpan);
                item.appendChild(deleteBtn);
                documentsList.appendChild(item);
            });
        } catch (error) {
            showNotification('Error loading documents: ' + error.message, true);
        } finally {
            document.getElementById('loading-documents').classList.add('hidden');
        }
    }
    
    async function deleteDocument(id, name) {
        if (!confirm(`Are you sure you want to delete "${name}"?`)) {
            return;
        }
        
        try {
            document.getElementById('loading-documents').classList.remove('hidden');
            const response = await fetch(`/api/documents/${id}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete document');
            }
            
            showNotification(`Deleted ${name}`);
            loadDocuments();
        } catch (error) {
            showNotification('Error deleting document: ' + error.message, true);
        } finally {
            document.getElementById('loading-documents').classList.add('hidden');
        }
    }
    
    function addMessage(role, content, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentP = document.createElement('p');
        contentP.textContent = content;
        messageDiv.appendChild(contentP);
        
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';
            sourcesDiv.innerHTML = '<strong>Sources:</strong>';
            
            sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = `${source.document_name} (Relevance: ${source.relevance.toFixed(2)})`;
                sourcesDiv.appendChild(sourceItem);
            });
            
            messageDiv.appendChild(sourcesDiv);
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function showNotification(message, isError = false) {
        const notification = document.createElement('div');
        notification.className = `notification ${isError ? 'error' : 'success'}`;
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '10px 20px';
        notification.style.borderRadius = '5px';
        notification.style.backgroundColor = isError ? '#f44336' : '#4CAF50';
        notification.style.color = 'white';
        notification.style.zIndex = '1000';
        notification.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }
    
    // Initial loads
    loadDocuments();
    loadSettings();
    
    // Logic to enable/disable retrieval checkbox based on use-llm checkbox
    const useRetrievalCheckbox = document.getElementById('use-retrieval');
    
    useLlmCheckbox.addEventListener('change', function() {
        useRetrievalCheckbox.disabled = !this.checked;
        if (!this.checked) {
            useRetrievalCheckbox.checked = true; // Always retrieve if not using LLM
        }
    });
});