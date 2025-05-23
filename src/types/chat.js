/**
 * @typedef {Object} Chat
 * @property {string} name - The name of the chat
 * @property {string} type - The type of chat (e.g., 'single')
 * @property {boolean} is_active - Whether the chat is active
 * @property {string} id - The unique identifier of the chat
 * @property {string} created_by - The ID of the user who created the chat
 * @property {string} created_at - The timestamp when the chat was created
 * @property {string} updated_at - The timestamp when the chat was last updated
 * @property {string|null} deleted_at - The timestamp when the chat was deleted, or null if not deleted
 */

/**
 * @typedef {Object} ChatResponse
 * @property {Chat[]} data - Array of chat objects
 */ 