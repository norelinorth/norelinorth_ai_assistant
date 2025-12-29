# Privacy Policy for AI Assistant

**Last Updated**: December 29, 2025

**Publisher**: Noreli North
**Contact**: honeyspotdaily@gmail.com

---

## 1. Introduction

This Privacy Policy describes how AI Assistant ("the App") collects, uses, and protects information when you use the application within your Frappe/ERPNext instance.

---

## 2. Information Collection

### 2.1 Data Processed by the App

The App processes the following data to provide AI assistance:

| Data Type | Purpose | Storage |
|-----------|---------|---------|
| Document content | Sent to AI provider for analysis | Not stored by App |
| Chat messages | Session history | Stored in your database |
| User identity | Permission checks | Your Frappe instance |
| AI responses | Display to user | Stored in your database |

### 2.2 Data Sent to Third-Party AI Providers

When you use AI features, the following data may be sent to your configured AI provider (OpenAI, Anthropic, or Azure):

- Document context (fields you're viewing)
- Your questions/prompts
- Session context for conversation continuity

**Important**: Data sent to AI providers is subject to their respective privacy policies:
- OpenAI: https://openai.com/privacy
- Anthropic: https://www.anthropic.com/privacy
- Azure OpenAI: https://privacy.microsoft.com

### 2.3 Langfuse Observability (Optional)

If you enable Langfuse integration, the following is sent to Langfuse:
- AI prompts and responses (for debugging)
- Token usage statistics
- Session metadata

Langfuse Privacy Policy: https://langfuse.com/privacy

---

## 3. Data Storage

### 3.1 Where Data is Stored

All App data (sessions, messages) is stored in **your own database** on your Frappe instance. The App does not maintain separate servers or databases.

### 3.2 Data Retention

- **AI Sessions**: Retained until you delete them
- **Messages**: Retained as part of session history
- **No automatic deletion**: You control data retention

### 3.3 GDPR Compliance

The App includes `user_data_fields` configuration for GDPR data export, enabling Frappe's built-in personal data export for user data requests.

---

## 4. Data Sharing

### 4.1 Third Parties

The App shares data with:

| Party | Data Shared | Purpose |
|-------|-------------|---------|
| AI Provider | Document context, prompts | Generate AI responses |
| Langfuse (optional) | Prompts, responses | Observability/debugging |

### 4.2 No Selling of Data

We do not sell, rent, or trade user data to third parties.

---

## 5. Security

### 5.1 Technical Measures

- API keys stored encrypted using Frappe's password encryption
- Permission-based access control
- No plain-text credential storage

### 5.2 Your Responsibilities

- Secure your AI provider API keys
- Configure appropriate user permissions
- Follow security best practices for your Frappe instance

---

## 6. User Rights

You have the right to:

- **Access**: View your AI sessions and messages
- **Delete**: Remove your sessions and conversation history
- **Export**: Use Frappe's data export for your personal data
- **Opt-out**: Disable AI features or uninstall the App

---

## 7. Children's Privacy

The App is not intended for use by children under 13. We do not knowingly collect data from children.

---

## 8. Changes to This Policy

We may update this Privacy Policy. Changes will be posted with an updated "Last Updated" date.

---

## 9. Contact

For privacy questions or concerns:

- **Email**: honeyspotdaily@gmail.com
- **GitHub**: https://github.com/norelinorth/ai_assistant/issues

---

## 10. Acceptance

By installing and using AI Assistant, you agree to this Privacy Policy and the privacy policies of your configured AI providers.
