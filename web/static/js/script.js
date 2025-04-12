document.addEventListener('DOMContentLoaded', function() {
    // Tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Deaktiviere alle Tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Aktiviere ausgewählten Tab
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Aktuelle Guild ID
    const guildId = document.querySelector('.server-header').dataset.guildId || 
                    window.location.pathname.split('/').pop();

    // Lade Kanal-Liste
    loadChannels();
    
    // Lade Rollen-Liste
    loadRoles();
    
    // Lade Tickets
    loadTickets();
    
    // Lade Kategorien
    loadCategories();
    
    // Event-Listener für Log-Kanal speichern
    document.getElementById('save-log-channel').addEventListener('click', saveLogChannel);
    
    // Event-Listener für Ticket-Panel erstellen
    document.getElementById('create-ticket-panel').addEventListener('click', createTicketPanel);
    
    // Event-Listener für Kategorien hinzufügen
    document.getElementById('add-category').addEventListener('click', addCategory);
    
    // Event-Listener für Kategorien speichern
    document.getElementById('save-categories').addEventListener('click', saveCategories);
    
    // Event-Listener für Rollen speichern
    document.getElementById('save-roles').addEventListener('click', saveRoles);
    
    // Event-Listener für Ticket-Filter
    document.getElementById('ticket-status-filter').addEventListener('change', filterTickets);
    
    // Modal schließen
    const modalCloseButtons = document.querySelectorAll('.modal .close');
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal');
            modal.style.display = 'none';
        });
    });
    
    // Klick außerhalb des Modals
    window.addEventListener('click', event => {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Button zum Hinzufügen von Rollen
    document.getElementById('confirm-add-role').addEventListener('click', confirmAddRole);
});

// Lade Server-Kanäle
async function loadChannels() {
    const guildId = window.location.pathname.split('/').pop();
    
    try {
        const response = await fetch(`/api/guild/${guildId}/channels`);
        const data = await response.json();
        
        const logChannelSelect = document.getElementById('log-channel');
        const ticketChannelSelect = document.getElementById('ticket-channel');
        
        // Lösche bestehende Optionen (außer der ersten)
        while (logChannelSelect.options.length > 1) {
            logChannelSelect.remove(1);
        }
        
        while (ticketChannelSelect.options.length > 1) {
            ticketChannelSelect.remove(1);
        }
        
        // Füge Kanäle hinzu
        data.channels.forEach(channel => {
            const option = document.createElement('option');
            option.value = channel.id;
            option.textContent = `#${channel.name} (${channel.category})`;
            
            logChannelSelect.appendChild(option.cloneNode(true));
            ticketChannelSelect.appendChild(option);
        });
        
        // Selektiere aktuellen Log-Kanal, falls vorhanden
        const serverHeader = document.querySelector('.server-header');
        if (serverHeader && serverHeader.dataset.logChannelId) {
            logChannelSelect.value = serverHeader.dataset.logChannelId;
        }
        
        // Selektiere aktuellen Ticket-Kanal, falls vorhanden
        if (serverHeader && serverHeader.dataset.ticketChannelId) {
            ticketChannelSelect.value = serverHeader.dataset.ticketChannelId;
        }
    } catch (error) {
        console.error('Fehler beim Laden der Kanäle:', error);
    }
}

// Lade Server-Rollen
async function loadRoles() {
    const guildId = window.location.pathname.split('/').pop();
    
    try {
        const response = await fetch(`/api/guild/${guildId}/roles`);
        const data = await response.json();
        
        // Speichere Rollen global für spätere Verwendung
        window.serverRoles = data.roles;
        
        // Admin-Rollen laden
        const adminRolesContainer = document.getElementById('admin-roles');
        adminRolesContainer.innerHTML = '';
        
        const serverHeader = document.querySelector('.server-header');
        const adminRoles = serverHeader && serverHeader.dataset.adminRoleIds 
                           ? serverHeader.dataset.adminRoleIds.split(',') 
                           : [];
        
        // Admin-Rollen anzeigen
        adminRoles.forEach(roleId => {
            const role = data.roles.find(r => r.id === roleId);
            if (role) {
                adminRolesContainer.appendChild(createRoleBadge(role));
            }
        });
        
        // "Rolle hinzufügen" Button für Admin-Rollen
        const addRoleBtn = document.createElement('button');
        addRoleBtn.className = 'btn secondary add-role-btn';
        addRoleBtn.innerHTML = '<i class="fas fa-plus"></i> Rolle hinzufügen';
        addRoleBtn.addEventListener('click', () => openRoleModal('admin'));
        adminRolesContainer.appendChild(addRoleBtn);
        
        // Fülle Rollen-Select im Modal
        const roleSelect = document.getElementById('role-select');
        while (roleSelect.options.length > 1) {
            roleSelect.remove(1);
        }
        
        data.roles.forEach(role => {
            const option = document.createElement('option');
            option.value = role.id;
            option.textContent = role.name;
            option.style.color = `#${role.color.toString(16).padStart(6, '0')}`;
            roleSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Fehler beim Laden der Rollen:', error);
    }
}

// Lade Ticket-Daten
async function loadTickets() {
    const guildId = window.location.pathname.split('/').pop();
    
    try {
        const response = await fetch(`/api/guild/${guildId}/tickets`);
        const data = await response.json();
        
        const ticketsList = document.getElementById('tickets-list');
        ticketsList.innerHTML = '';
        
        // Sortiere nach ID (neuste zuerst)
        const sortedTickets = Object.entries(data.tickets).sort((a, b) => {
            return parseInt(b[0]) - parseInt(a[0]);
        });
        
        sortedTickets.forEach(([ticketId, ticket]) => {
            const row = document.createElement('tr');
            
            // Formatiere Daten
            const createdAt = new Date(ticket.created_at).toLocaleString('de-DE');
            const closedAt = ticket.closed_at ? new Date(ticket.closed_at).toLocaleString('de-DE') : '-';
            
            row.innerHTML = `
                <td>${ticketId}</td>
                <td>${ticket.category}</td>
                <td class="user-id" data-user-id="${ticket.user_id}">Lädt...</td>
                <td><span class="status-badge ${ticket.status}">${ticket.status === 'open' ? 'Offen' : 'Geschlossen'}</span></td>
                <td>${createdAt}</td>
                <td>${closedAt}</td>
            `;
            
            row.dataset.status = ticket.status;
            ticketsList.appendChild(row);
            
            // Lade Benutzername asynchron
            fetchUserInfo(ticket.user_id, row.querySelector('.user-id'));
        });
        
        // Initial filtern
        filterTickets();
    } catch (error) {
        console.error('Fehler beim Laden der Tickets:', error);
    }
}

// Lade Benutzerinformationen
async function fetchUserInfo(userId, element) {
    try {
        const response = await fetch(`/api/user/${userId}`);
        if (response.ok) {
            const data = await response.json();
            element.textContent = data.username;
        } else {
            element.textContent = userId;
        }
    } catch (error) {
        element.textContent = userId;
    }
}

// Filter Tickets nach Status
function filterTickets() {
    const filter = document.getElementById('ticket-status-filter').value;
    const rows = document.querySelectorAll('#tickets-list tr');
    
    rows.forEach(row => {
        if (filter === 'all' || row.dataset.status === filter) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Lade Ticket-Kategorien
function loadCategories() {
    const serverHeader = document.querySelector('.server-header');
    if (!serverHeader || !serverHeader.dataset.categories) return;
    
    const categories = JSON.parse(serverHeader.dataset.categories);
    const container = document.getElementById('categories-container');
    container.innerHTML = '';
    
    categories.forEach((category, index) => {
        container.appendChild(createCategoryItem(category, index));
    });
}

// Erstelle Kategorie-Element
function createCategoryItem(category, index) {
    const template = document.getElementById('category-template');
    const item = template.content.cloneNode(true);
    
    const header = item.querySelector('.category-header h4');
    header.textContent = `Kategorie ${index + 1}`;
    
    const nameInput = item.querySelector('.category-name');
    nameInput.value = category.name || '';
    
    const descInput = item.querySelector('.category-description');
    descInput.value = category.description || '';
    
    const colorInput = item.querySelector('.category-color');
    colorInput.value = category.color ? '#' + category.color.toString(16).padStart(6, '0') : '#3498db';
    
    const rolesContainer = item.querySelector('.category-roles');
    rolesContainer.dataset.categoryIndex = index;
    
    // Füge Rollen hinzu
    if (category.role_ids && window.serverRoles) {
        category.role_ids.forEach(roleId => {
            const role = window.serverRoles.find(r => r.id === roleId);
            if (role) {
                rolesContainer.appendChild(createRoleBadge(role));
            }
        });
    }
    
    // "Rolle hinzufügen" Button
    const addRoleBtn = document.createElement('button');
    addRoleBtn.className = 'btn secondary add-role-btn';
    addRoleBtn.innerHTML = '<i class="fas fa-plus"></i> Rolle hinzufügen';
    addRoleBtn.addEventListener('click', () => openRoleModal('category', index));
    rolesContainer.appendChild(addRoleBtn);
    
    // Event für Löschen-Button
    const deleteBtn = item.querySelector('.delete-category');
    deleteBtn.addEventListener('click', () => {
        const categoryItem = deleteBtn.closest('.category-item');
        categoryItem.remove();
    });
    
    return item;
}

// Füge neue Kategorie hinzu
function addCategory() {
    const container = document.getElementById('categories-container');
    const index = container.children.length;
    
    const newCategory = {
        name: 'Neue Kategorie',
        description: 'Beschreibung der Kategorie',
        color: 0x3498db,
        role_ids: []
    };
    
    container.appendChild(createCategoryItem(newCategory, index));
}

// Erstelle Rollen-Badge
function createRoleBadge(role) {
    const template = document.getElementById('role-badge-template');
    const badge = template.content.cloneNode(true);
    
    const roleName = badge.querySelector('.role-name');
    roleName.textContent = role.name;
    roleName.style.backgroundColor = `#${role.color.toString(16).padStart(6, '0')}`;
    
    const removeBtn = badge.querySelector('.remove-role');
    removeBtn.addEventListener('click', () => {
        removeBtn.closest('.role-badge').remove();
    });
    
    badge.firstElementChild.dataset.roleId = role.id;
    
    return badge;
}

// Öffne Rollen-Modal
function openRoleModal(type, categoryIndex = null) {
    const modal = document.getElementById('add-role-modal');
    modal.dataset.type = type;
    if (categoryIndex !== null) {
        modal.dataset.categoryIndex = categoryIndex;
    }
    modal.style.display = 'block';
}

// Bestätige Rollenzuweisung
function confirmAddRole() {
    const modal = document.getElementById('add-role-modal');
    const roleSelect = document.getElementById('role-select');
    const roleId = roleSelect.value;
    
    if (!roleId) return;
    
    const role = window.serverRoles.find(r => r.id === roleId);
    if (!role) return;
    
    const type = modal.dataset.type;
    
    if (type === 'admin') {
        // Zur Admin-Rollen hinzufügen
        const container = document.getElementById('admin-roles');
        const addBtn = container.querySelector('.add-role-btn');
        container.insertBefore(createRoleBadge(role), addBtn);
    } else if (type === 'category') {
        // Zur Kategorie hinzufügen
        const categoryIndex = modal.dataset.categoryIndex;
        const container = document.querySelector(`.category-roles[data-category-index="${categoryIndex}"]`);
        const addBtn = container.querySelector('.add-role-btn');
        container.insertBefore(createRoleBadge(role), addBtn);
    }
    
    modal.style.display = 'none';
}

// Speichere Log-Kanal
async function saveLogChannel() {
    const guildId = window.location.pathname.split('/').pop();
    const logChannelId = document.getElementById('log-channel').value;
    
    try {
        const response = await fetch(`/api/guild/${guildId}/log-channel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ channel_id: logChannelId }),
        });
        
        if (response.ok) {
            showNotification('Log-Kanal erfolgreich gespeichert!', 'success');
        } else {
            showNotification('Fehler beim Speichern des Log-Kanals', 'error');
        }
    } catch (error) {
        console.error('Fehler:', error);
        showNotification('Fehler beim Speichern des Log-Kanals', 'error');
    }
}

// Erstelle Ticket-Panel
async function createTicketPanel() {
    const guildId = window.location.pathname.split('/').pop();
    const channelId = document.getElementById('ticket-channel').value;
    
    if (!channelId) {
        showNotification('Bitte wähle einen Kanal aus', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/guild/${guildId}/ticket-settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ channel_id: channelId }),
        });
        
        if (response.ok) {
            showNotification('Ticket-Panel erfolgreich erstellt!', 'success');
        } else {
            showNotification('Fehler beim Erstellen des Ticket-Panels', 'error');
        }
    } catch (error) {
        console.error('Fehler:', error);
        showNotification('Fehler beim Erstellen des Ticket-Panels', 'error');
    }
}

// Speichere Kategorien
async function saveCategories() {
    const guildId = window.location.pathname.split('/').pop();
    const categoryItems = document.querySelectorAll('#categories-container .category-item');
    
    const categories = Array.from(categoryItems).map(item => {
        // Sammle alle Rollen-IDs
        const roleIds = Array.from(item.querySelectorAll('.category-roles .role-badge'))
            .map(badge => badge.dataset.roleId);
        
        // Konvertiere Hex-Farbe zu Integer
        const colorHex = item.querySelector('.category-color').value;
        const colorInt = parseInt(colorHex.substring(1), 16);
        
        return {
            name: item.querySelector('.category-name').value,
            description: item.querySelector('.category-description').value,
            color: colorInt,
            role_ids: roleIds
        };
    });
    
    try {
        const response = await fetch(`/api/guild/${guildId}/categories`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ categories }),
        });
        
        if (response.ok) {
            showNotification('Kategorien erfolgreich gespeichert!', 'success');
        } else {
            showNotification('Fehler beim Speichern der Kategorien', 'error');
        }
    } catch (error) {
        console.error('Fehler:', error);
        showNotification('Fehler beim Speichern der Kategorien', 'error');
    }
}

// Speichere Admin-Rollen
async function saveRoles() {
    const guildId = window.location.pathname.split('/').pop();
    const adminRoleBadges = document.querySelectorAll('#admin-roles .role-badge');
    
    const adminRoles = Array.from(adminRoleBadges).map(badge => badge.dataset.roleId);
    
    try {
        const response = await fetch(`/api/guild/${guildId}/admin-roles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ admin_roles: adminRoles }),
        });
        
        if (response.ok) {
            showNotification('Rollen erfolgreich gespeichert!', 'success');
        } else {
            showNotification('Fehler beim Speichern der Rollen', 'error');
        }
    } catch (error) {
        console.error('Fehler:', error);
        showNotification('Fehler beim Speichern der Rollen', 'error');
    }
}

// Zeige Benachrichtigung
function showNotification(message, type = 'info') {
    // Prüfe, ob bereits eine Benachrichtigung existiert
    let notification = document.querySelector('.notification');
    
    if (!notification) {
        // Erstelle neue Benachrichtigung
        notification = document.createElement('div');
        notification.className = 'notification';
        document.body.appendChild(notification);
    }
    
    // Setze Klasse basierend auf Typ
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.display = 'block';
    
    // Verstecke nach 3 Sekunden
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}
