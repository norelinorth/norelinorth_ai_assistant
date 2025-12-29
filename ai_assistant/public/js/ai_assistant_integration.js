frappe.provide("frappe.ai_assistant");

frappe.ai_assistant = {
    supported_doctypes: [
        "Sales Order",
        "Purchase Order",
        "Sales Invoice",
        "Purchase Invoice",
        "Journal Entry"  // Already included - good!
    ],

    init_form: function(frm) {
        // Skip if new document or already initialized
        if (!frm || frm.is_new() || frm._ai_assistant_initialized) {
            return;
        }

        // Check user permission
        if (!frappe.user_roles.includes("AI Assistant User")) {
            console.log("AI Assistant: User doesn't have required role");
            return;
        }

        // Check if doctype is supported
        if (!this.supported_doctypes.includes(frm.doctype)) {
            return;
        }

        console.log("AI Assistant: Initializing for", frm.doctype);
        frm._ai_assistant_initialized = true;

        // Add AI Assistant section to form
        this.add_ai_section(frm);
    },

    add_ai_section: function(frm) {
        // Create AI Assistant as a collapsible section in the form body
        // This is more aligned with Frappe's native form structure

        // Check if we should add to sidebar or form body based on configuration
        const add_to_form_body = true; // Set to true to add in form body, false for sidebar

        const section_html = `
            <div class="ai-assistant-container" style="margin-bottom: 15px;">
                <div class="frappe-control">
                    <div class="ai-assistant-header" style="
                        padding: 10px;
                        background-color: var(--bg-color);
                        border-bottom: 1px solid var(--border-color);
                        font-weight: 600;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    ">
                        <span>AI Assistant</span>
                        <button class="btn btn-xs btn-default ai-clear-btn" title="${__('Clear conversation')}" onclick="event.stopPropagation()">
                            ${__('Clear')}
                        </button>
                    </div>
                    <div class="ai-assistant-body" style="
                        padding: 10px;
                        background-color: var(--control-bg);
                        border: 1px solid var(--border-color);
                        border-top: none;
                        display: block;
                    ">
                        <div class="ai-conversation-area" style="
                            max-height: 400px;
                            overflow-y: auto;
                            margin-bottom: 10px;
                            padding: 10px;
                            background-color: var(--bg-color);
                            border: 1px solid var(--border-color);
                            border-radius: var(--border-radius);
                            min-height: 200px;
                        ">
                            <div class="ai-messages" style="font-size: 13px;">
                                <div style="color: var(--text-muted); padding: 10px;">
                                    ${__('Ask me anything about this')} ${__(frm.doctype)}
                                </div>
                            </div>
                        </div>
                        <div class="ai-input-area">
                            <div class="form-group" style="margin-bottom: 10px;">
                                <textarea
                                    class="form-control ai-user-input"
                                    rows="3"
                                    placeholder="${__('Type your question and press Enter to send...')}"
                                    style="
                                        resize: vertical;
                                        min-height: 60px;
                                        font-size: 13px;
                                    "
                                ></textarea>
                            </div>
                            <div class="ai-actions" style="display: flex; justify-content: space-between; align-items: center;">
                                <div class="ai-status" style="
                                    font-size: 12px;
                                    color: var(--text-muted);
                                    display: none;
                                ">
                                    <span class="ai-status-text"></span>
                                </div>
                                <div>
                                    <button class="btn btn-xs btn-primary ai-send-btn" style="margin-right: 5px;">
                                        ${__('Send')} (Enter)
                                    </button>
                                    <button class="btn btn-xs btn-default ai-suggestion-btn">
                                        ${__('Suggestions')}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (add_to_form_body) {
            // Add to form body using Frappe's form layout structure
            // Find the best place to insert - after the main form fields
            const $form_layout = $(frm.wrapper).find('.form-layout');

            if ($form_layout.length > 0) {
                // Create a section break style container
                const ai_section_wrapper = `
                    <div class="form-section ai-assistant-section" style="width: 100%;">
                        <div class="section-head">
                            <span class="indicator-pill"></span>
                            <a class="section-toggle" style="padding: 7px 15px; display: block;">
                                <span class="section-title">
                                    AI Assistant
                                </span>
                                <span class="ml-2 collapse-indicator octicon octicon-chevron-down"></span>
                            </a>
                        </div>
                        <div class="section-body" style="display: block;">
                            ${section_html}
                        </div>
                    </div>
                `;

                // Add after last section or at the end of form
                $form_layout.append(ai_section_wrapper);

                // Handle section toggle
                $(frm.wrapper).find('.ai-assistant-section .section-head').on('click', function() {
                    const $section = $(this).parent();
                    const $body = $section.find('.section-body');
                    const $indicator = $(this).find('.collapse-indicator');

                    $body.slideToggle();
                    $(this).toggleClass('collapsed');

                    if ($(this).hasClass('collapsed')) {
                        $indicator.removeClass('octicon-chevron-up').addClass('octicon-chevron-down');
                    } else {
                        $indicator.removeClass('octicon-chevron-down').addClass('octicon-chevron-up');
                    }
                });
            } else {
                // Fallback: Add to sidebar if form layout not found
                const $sidebar = $(frm.wrapper).find('.form-sidebar');
                if ($sidebar.length > 0) {
                    $sidebar.prepend(section_html);
                } else {
                    // Last fallback: Add before form footer
                    $(frm.wrapper).find('.form-footer').before(section_html);
                }
            }
        } else {
            // Original sidebar implementation
            const $sidebar = $(frm.wrapper).find('.form-sidebar');
            if ($sidebar.length > 0) {
                $sidebar.prepend(section_html);
            } else {
                $(frm.wrapper).find('.form-footer').before(section_html);
            }
        }

        // Setup event handlers
        this.setup_ai_handlers(frm);
    },

    setup_ai_handlers: function(frm) {
        const $container = $(frm.wrapper).find('.ai-assistant-container');
        const $input = $container.find('.ai-user-input');
        const $sendBtn = $container.find('.ai-send-btn');
        const $clearBtn = $container.find('.ai-clear-btn');
        const $suggestionBtn = $container.find('.ai-suggestion-btn');
        const $messages = $container.find('.ai-messages');
        const $status = $container.find('.ai-status');
        const $statusText = $container.find('.ai-status-text');

        let session_id = null;
        let is_processing = false;

        // Helper function to add message to conversation
        const add_message = (content, type = 'user') => {
            const message_class = type === 'user' ? 'ai-user-message' : 'ai-assistant-message';
            const bg_color = type === 'user' ? 'var(--bg-blue)' : 'var(--bg-green)';
            const align = type === 'user' ? 'right' : 'left';
            const label = type === 'user' ? __('You') : __('AI Assistant');

            const message_html = `
                <div class="${message_class}" style="
                    margin-bottom: 10px;
                    text-align: ${align};
                ">
                    <div style="
                        display: inline-block;
                        max-width: 80%;
                        text-align: left;
                    ">
                        <div style="
                            font-weight: 600;
                            font-size: 11px;
                            color: var(--text-muted);
                            margin-bottom: 2px;
                        ">${label}</div>
                        <div style="
                            background-color: ${bg_color};
                            padding: 8px 12px;
                            border-radius: var(--border-radius);
                            white-space: pre-wrap;
                            word-wrap: break-word;
                        ">${frappe.utils.xss_sanitise(content)}</div>
                    </div>
                </div>
            `;

            // Clear placeholder if exists
            if ($messages.find('div[style*="text-align: center"]').length) {
                $messages.empty();
            }

            $messages.append(message_html);

            // Scroll to bottom
            const conversation_area = $container.find('.ai-conversation-area')[0];
            conversation_area.scrollTop = conversation_area.scrollHeight;
        };

        // Helper function to show status
        const show_status = (text, show = true) => {
            if (show) {
                $statusText.text(text);
                $status.show();
            } else {
                $status.hide();
            }
        };

        // Helper function to create or get session - Frappe pattern
        const ensure_session = function() {
            if (session_id) {
                // Use jQuery.Deferred for consistency with Frappe
                const deferred = $.Deferred();
                deferred.resolve(session_id);
                return deferred.promise();
            }

            show_status(__('Initializing AI Assistant...'));

            return frappe.call({
                method: 'ai_assistant.api.start_session',
                args: {
                    target_doctype: frm.doctype,
                    target_name: frm.doc.name || 'new'
                },
                callback: function(r) {
                    if (r.message && r.message.name) {
                        session_id = r.message.name;
                        show_status(__('Ready'), false);
                    }
                },
                error: function(err) {
                    show_status(__('Initialization failed'), false);
                    frappe.msgprint({
                        title: __('AI Assistant Error'),
                        message: __('Could not initialize AI Assistant. Please check configuration.'),
                        indicator: 'red'
                    });
                }
            }).then(function(r) {
                if (r.message && r.message.name) {
                    return r.message.name;
                }
                throw new Error(__('Failed to initialize session'));
            });
        };

        // Send message function - Frappe/ERPNext aligned pattern
        const send_message = () => {
            const message = $input.val().trim();

            if (!message) {
                frappe.show_alert({
                    message: __('Please enter a message'),
                    indicator: 'orange'
                });
                return;
            }

            if (is_processing) {
                return;
            }

            is_processing = true;
            $sendBtn.prop('disabled', true);
            $input.prop('disabled', true);

            // Add user message to conversation
            add_message(message, 'user');
            $input.val('');

            show_status(__('AI is thinking...'));

            // Reset UI function
            const reset_ui = () => {
                is_processing = false;
                $sendBtn.prop('disabled', false);
                $input.prop('disabled', false);
                $input.focus();
            };

            // Use Frappe's standard promise pattern
            ensure_session()
                .then(function(session) {
                    return frappe.call({
                        method: 'ai_assistant.api.chat_once',
                        args: {
                            session: session,
                            prompt: message
                        }
                    });
                })
                .then(function(r) {
                    if (r.message && r.message.reply) {
                        add_message(r.message.reply, 'assistant');
                        show_status(__('Response received'), false);
                    } else {
                        throw new Error(__('No response received'));
                    }
                    reset_ui();
                })
                .catch(function(err) {
                    console.error('AI Assistant Error:', err);

                    let error_msg = __('An error occurred');
                    if (err && err.message) {
                        if (err.message.includes('API')) {
                            error_msg = __('AI Provider not configured. Please contact administrator.');
                        } else if (err.message.includes('permission')) {
                            error_msg = __('Permission denied. Please contact administrator.');
                        } else {
                            error_msg = err.message;
                        }
                    }

                    add_message(error_msg, 'assistant');
                    show_status(__('Error'), false);
                    reset_ui();
                });
        };

        // Show suggestions
        const show_suggestions = () => {
            const suggestions = [
                __('Summarize this') + ' ' + __(frm.doctype),
                __('What are the key details?'),
                __('Are there any issues with this document?'),
                __('Suggest improvements'),
                __('Explain the workflow')
            ];

            const dialog = new frappe.ui.Dialog({
                title: __('AI Assistant Suggestions'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div style="font-size: 13px;">
                                ${__('Click on a suggestion to use it:')}
                            </div>
                            <div style="margin-top: 10px;">
                                ${suggestions.map(s => `
                                    <button class="btn btn-xs btn-default suggestion-item"
                                            style="margin: 2px;"
                                            data-suggestion="${s}">
                                        ${s}
                                    </button>
                                `).join('')}
                            </div>
                        `
                    }
                ]
            });

            dialog.show();

            // Handle suggestion clicks
            dialog.$wrapper.on('click', '.suggestion-item', function() {
                const suggestion = $(this).data('suggestion');
                $input.val(suggestion);
                dialog.hide();
                $input.focus();
            });
        };

        // Clear conversation
        const clear_conversation = () => {
            frappe.confirm(
                __('Clear the conversation history?'),
                () => {
                    $messages.html(`
                        <div style="color: var(--text-muted); text-align: center; padding: 20px;">
                            ${__('Ask me anything about this')} ${__(frm.doctype)}...
                        </div>
                    `);
                    session_id = null;
                    show_status(__('Conversation cleared'), false);
                }
            );
        };

        // Event handlers
        $sendBtn.on('click', send_message);
        $clearBtn.on('click', clear_conversation);
        $suggestionBtn.on('click', show_suggestions);

        // Enter key to send (without Shift)
        $input.on('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send_message();
            }
        });

        // Focus input when container is clicked
        $container.on('click', function() {
            if (!is_processing) {
                $input.focus();
            }
        });

        console.log("AI Assistant: Handlers setup complete");
    }
};

// Initialize on form events for each supported doctype
frappe.ai_assistant.supported_doctypes.forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        refresh: function(frm) {
            console.log("AI Assistant: Form refresh for", frm.doctype);
            frappe.ai_assistant.init_form(frm);
        },
        onload: function(frm) {
            console.log("AI Assistant: Form onload for", frm.doctype);
            // Check if AI is enabled from backend
            if (frm.doc.__onload && frm.doc.__onload.ai_assistant_enabled) {
                console.log("AI Assistant: Enabled from backend");
                frappe.ai_assistant.init_form(frm);
            }
        }
    });
});

// Log when script loads
$(document).ready(function() {
    console.log("AI Assistant: Integration script loaded successfully");
    console.log("AI Assistant: Supported doctypes:", frappe.ai_assistant.supported_doctypes);
});