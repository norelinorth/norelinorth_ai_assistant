frappe.pages['ai-chat'].on_page_load = function(wrapper) {
	frappe.ai_chat = new AIChatPage(wrapper);
}

class AIChatPage {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __('AI Assistant Chat'),
			single_column: false
		});
		
		this.current_session = null;
		this.setup_page();
		this.load_recent_sessions();
	}
	
	setup_page() {
		// Add custom CSS
		this.add_styles();
		
		// Create layout
		this.create_layout();
		
		// Add new session button
		this.page.set_primary_action(__('New Session'), () => {
			this.show_new_session_dialog();
		});
		
		// Add refresh button
		this.page.set_secondary_action(__('Refresh'), () => {
			this.load_recent_sessions();
		});
	}
	
	add_styles() {
		const style = `
			<style>
				.ai-chat-container {
					display: flex;
					height: calc(100vh - 120px);
				}
				.sessions-panel {
					width: 300px;
					border-right: 1px solid var(--border-color);
					overflow-y: auto;
					background: var(--card-bg);
				}
				.chat-panel {
					flex: 1;
					display: flex;
					flex-direction: column;
					background: var(--card-bg);
				}
				.session-item {
					padding: 12px;
					border-bottom: 1px solid var(--border-color);
					cursor: pointer;
					transition: background 0.2s;
				}
				.session-item:hover {
					background: var(--bg-color);
				}
				.session-item.active {
					background: var(--primary-bg);
				}
				.session-header {
					font-weight: 600;
					margin-bottom: 4px;
				}
				.session-meta {
					font-size: 0.85rem;
					color: var(--text-muted);
				}
				.chat-messages {
					flex: 1;
					overflow-y: auto;
					padding: 20px;
				}
				.chat-input-area {
					padding: 16px;
					border-top: 1px solid var(--border-color);
					background: var(--bg-color);
				}
				.message {
					margin-bottom: 16px;
					padding: 12px;
					border-radius: 8px;
				}
				.message.user {
					background: var(--primary-bg);
					margin-left: 20%;
				}
				.message.assistant {
					background: var(--bg-color);
					margin-right: 20%;
				}
				.message-role {
					font-weight: 600;
					margin-bottom: 8px;
					font-size: 0.85rem;
					text-transform: uppercase;
					opacity: 0.7;
				}
				.message-content {
					white-space: pre-wrap;
					word-wrap: break-word;
				}
				.empty-state {
					text-align: center;
					padding: 40px;
					color: var(--text-muted);
				}
				.chat-input-wrapper {
					display: flex;
					gap: 12px;
				}
				.chat-input {
					flex: 1;
				}
			</style>
		`;
		this.wrapper.innerHTML = style;
	}
	
	create_layout() {
		this.container = $(`
			<div class="ai-chat-container">
				<div class="sessions-panel">
					<div class="sessions-header" style="padding: 12px; border-bottom: 1px solid var(--border-color);">
						<h5>${__('Recent Sessions')}</h5>
					</div>
					<div class="sessions-list"></div>
				</div>
				<div class="chat-panel">
					<div class="chat-messages">
						<div class="empty-state">
							<i class="fa fa-comments" style="font-size: 48px; opacity: 0.3; margin-bottom: 16px;"></i>
							<p>${__('Select a session or create a new one to start chatting')}</p>
						</div>
					</div>
					<div class="chat-input-area" style="display: none;">
						<div class="chat-input-wrapper">
							<textarea class="form-control chat-input" rows="3" placeholder="${__('Type your message...')}"></textarea>
							<button class="btn btn-primary send-btn">${__('Send')}</button>
						</div>
					</div>
				</div>
			</div>
		`).appendTo(this.page.body);
		
		// Setup event handlers
		this.setup_events();
	}
	
	setup_events() {
		const sendBtn = this.container.find('.send-btn');
		const chatInput = this.container.find('.chat-input');
		
		sendBtn.on('click', () => this.send_message());
		
		chatInput.on('keydown', (e) => {
			if (e.key === 'Enter' && !e.shiftKey) {
				e.preventDefault();
				this.send_message();
			}
		});
	}
	
	load_recent_sessions() {
		frappe.call({
			method: 'ai_assistant.ai_assistant.page.ai_chat.ai_chat.get_recent_sessions',
			callback: (r) => {
				if (r.message) {
					this.render_sessions(r.message);
				}
			}
		});
	}
	
	render_sessions(sessions) {
		const sessionsList = this.container.find('.sessions-list');
		sessionsList.empty();
		
		if (sessions.length === 0) {
			sessionsList.html(`
				<div class="empty-state">
					<p>${__('No sessions yet')}</p>
				</div>
			`);
			return;
		}
		
		sessions.forEach(session => {
			const sessionItem = $(`
				<div class="session-item" data-session="${session.name}">
					<div class="session-header">
						${session.target_doctype || __('General Chat')}
						${session.target_name ? `: ${session.target_name}` : ''}
					</div>
					<div class="session-meta">
						<span class="badge badge-${session.status === 'Active' ? 'success' : 'secondary'}">${session.status}</span>
						<span style="margin-left: 8px;">${frappe.datetime.prettyDate(session.started_on)}</span>
					</div>
				</div>
			`).appendTo(sessionsList);
			
			sessionItem.on('click', () => this.load_session(session.name));
		});
	}
	
	load_session(session_name) {
		// Mark active session
		this.container.find('.session-item').removeClass('active');
		this.container.find(`.session-item[data-session="${session_name}"]`).addClass('active');
		
		frappe.call({
			method: 'ai_assistant.ai_assistant.page.ai_chat.ai_chat.get_session_messages',
			args: { session_name },
			callback: (r) => {
				if (r.message) {
					this.current_session = r.message.session;
					this.render_messages(r.message.messages);
					this.container.find('.chat-input-area').show();
				}
			}
		});
	}
	
	render_messages(messages) {
		const messagesContainer = this.container.find('.chat-messages');
		messagesContainer.empty();
		
		if (!messages || messages.length === 0) {
			messagesContainer.html(`
				<div class="empty-state">
					<p>${__('No messages yet. Start the conversation!')}</p>
				</div>
			`);
			return;
		}
		
		messages.forEach(msg => {
			const messageEl = $(`
				<div class="message ${msg.role}">
					<div class="message-role">${msg.role === 'user' ? __('You') : __('AI Assistant')}</div>
					<div class="message-content">${frappe.utils.xss_sanitise(msg.content)}</div>
				</div>
			`).appendTo(messagesContainer);
		});
		
		// Scroll to bottom
		messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
	}
	
	send_message() {
		const input = this.container.find('.chat-input');
		const message = input.val().trim();
		
		if (!message || !this.current_session) return;
		
		// Disable input while sending
		input.prop('disabled', true);
		this.container.find('.send-btn').prop('disabled', true);
		
		// Add user message to UI immediately
		const messagesContainer = this.container.find('.chat-messages');
		messagesContainer.find('.empty-state').remove();
		
		$(`
			<div class="message user">
				<div class="message-role">${__('You')}</div>
				<div class="message-content">${frappe.utils.xss_sanitise(message)}</div>
			</div>
		`).appendTo(messagesContainer);
		
		// Show loading indicator
		const loadingMsg = $(`
			<div class="message assistant">
				<div class="message-role">${__('AI Assistant')}</div>
				<div class="message-content"><i class="fa fa-spinner fa-spin"></i> ${__('Thinking...')}</div>
			</div>
		`).appendTo(messagesContainer);
		
		messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
		
		frappe.call({
			method: 'ai_assistant.api.chat_once',
			args: {
				session: this.current_session.name,
				prompt: message
			},
			callback: (r) => {
				loadingMsg.remove();
				
				if (r.message && r.message.reply) {
					$(`
						<div class="message assistant">
							<div class="message-role">${__('AI Assistant')}</div>
							<div class="message-content">${frappe.utils.xss_sanitise(r.message.reply)}</div>
						</div>
					`).appendTo(messagesContainer);
					
					messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
				}
				
				// Re-enable input
				input.val('').prop('disabled', false).focus();
				this.container.find('.send-btn').prop('disabled', false);
			},
			error: () => {
				loadingMsg.remove();
				frappe.msgprint(__('Error sending message'));
				
				// Re-enable input
				input.prop('disabled', false);
				this.container.find('.send-btn').prop('disabled', false);
			}
		});
	}
	
	show_new_session_dialog() {
		frappe.call({
			method: 'ai_assistant.ai_assistant.page.ai_chat.ai_chat.get_available_doctypes',
			callback: (r) => {
				const doctypes = r.message || [];
				
				const d = new frappe.ui.Dialog({
					title: __('New AI Assistant Session'),
					fields: [
						{
							label: __('Session Type'),
							fieldname: 'session_type',
							fieldtype: 'Select',
							options: ['General Chat', 'Document Context'],
							default: 'General Chat',
							change: () => {
								const isDocContext = d.get_value('session_type') === 'Document Context';
								d.set_df_property('target_doctype', 'hidden', !isDocContext);
								d.set_df_property('target_name', 'hidden', !isDocContext);
								d.set_df_property('target_doctype', 'reqd', isDocContext);
								d.set_df_property('target_name', 'reqd', isDocContext);
							}
						},
						{
							label: __('Document Type'),
							fieldname: 'target_doctype',
							fieldtype: 'Select',
							options: doctypes.map(dt => dt.name).join('\n'),
							hidden: 1,
							change: () => {
								const doctype = d.get_value('target_doctype');
								if (doctype) {
									d.set_df_property('target_name', 'options', doctype);
								}
							}
						},
						{
							label: __('Document'),
							fieldname: 'target_name',
							fieldtype: 'Link',
							hidden: 1
						}
					],
					primary_action_label: __('Create Session'),
					primary_action: (values) => {
						let args = {};
						if (values.session_type === 'Document Context') {
							args.target_doctype = values.target_doctype;
							args.target_name = values.target_name;
						}
						
						frappe.call({
							method: 'ai_assistant.api.start_session',
							args: args,
							callback: (r) => {
								if (r.message && r.message.name) {
									d.hide();
									this.load_recent_sessions();
									setTimeout(() => {
										this.load_session(r.message.name);
									}, 500);
								}
							}
						});
					}
				});
				
				d.show();
			}
		});
	}
}