document.addEventListener('DOMContentLoaded', function() {
    // Theme switcher
    const themeSwitcher = document.getElementById('theme-switcher');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeSwitcher.textContent = '☀️';
    }
    
    themeSwitcher.addEventListener('click', function(e) {
        e.preventDefault();
        if (document.documentElement.getAttribute('data-theme') === 'dark') {
            document.documentElement.setAttribute('data-theme', 'light');
            themeSwitcher.textContent = '🌙';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeSwitcher.textContent = '☀️';
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
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    history: chatHistory
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            const result = await response.json();
            
            // Remove loading indicator
            chatMessages.removeChild(loadingMessage);
            
            // Add assistant message with sources
            addMessage('assistant', result.answer, result.source_documents);
            
            // Update chat history
            chatHistory.push({role: 'user', content: query});
            chatHistory.push({role: 'assistant', content: result.answer});
        } catch (error) {
            chatMessages.removeChild(chatMessages.lastChild); // Remove loading
            showNotification('Error: ' + error.message, true);
        }
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
            
            sources.slice(0, 3).forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = `${source.metadata.document_name} (Chunk ${source.metadata.chunk_id + 1})`;
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
    
    // Initial document load
    loadDocuments();
});