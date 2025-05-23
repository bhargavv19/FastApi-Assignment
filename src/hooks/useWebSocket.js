import { useEffect, useRef, useCallback } from 'react';

const useWebSocket = (chatId, token, userId) => {
    const ws = useRef(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    const connect = useCallback(() => {
        // Validate required parameters
        if (!token) {
            console.error('No token provided for WebSocket connection');
            return;
        }

        if (!chatId) {
            console.error('No chatId provided for WebSocket connection');
            return;
        }

        if (!userId) {
            console.error('No userId provided for WebSocket connection');
            return;
        }

        // Construct WebSocket URL with token as query parameter
        const wsUrl = `ws://localhost:8000/api/v1/ws/chat/${chatId}?token=${token}`;
        console.log('Attempting to connect to WebSocket:', wsUrl.replace(token, '[REDACTED]'));
        
        try {
            // Create new WebSocket connection
            ws.current = new WebSocket(wsUrl);

            // Connection opened
            ws.current.onopen = () => {
                console.log('WebSocket Connected Successfully');
                reconnectAttempts.current = 0;
            };

            // Connection closed
            ws.current.onclose = (event) => {
                console.log('WebSocket Disconnected:', {
                    code: event.code,
                    reason: event.reason,
                    wasClean: event.wasClean
                });
                
                // // Implement exponential backoff for reconnection
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    reconnectAttempts.current++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                    console.log(`Reconnecting in ${delay}ms... Attempt ${reconnectAttempts.current}`);
                    setTimeout(connect, delay);
                } else {
                    console.error('Max reconnection attempts reached');
                }
            };

            // Connection error
            ws.current.onerror = (error) => {
                console.error('WebSocket Error:', {
                    error,
                    readyState: ws.current?.readyState,
                    url: wsUrl.replace(token, '[REDACTED]')
                });
            };

            // Message received
            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket Message Received:', data);
                    
                    // Handle different message types
                    switch(data.type) {
                        case 'chat_message':
                            // Handle chat message
                            break;
                        case 'typing_indicator':
                            // Handle typing indicator
                            break;
                        case 'read_receipt':
                            // Handle read receipt
                            break;
                        default:
                            console.log('Unknown message type:', data.type);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

        } catch (error) {
            console.error('Error creating WebSocket connection:', error);
        }
    }, [chatId, token, userId]);

    // Send chat message
    const sendMessage = useCallback((content, parentMessageId = null) => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return;
        }

        try {
            const message = {
                type: "chat_message",
                data: {
                    content,
                    message_type: "text",
                    parent_message_id: parentMessageId,
                    chat_id: chatId,
                    sender_id: userId
                }
            };

            ws.current.send(JSON.stringify(message));
            console.log('Message sent successfully');
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }, [chatId, userId]);

    // Send typing indicator
    const sendTypingIndicator = useCallback((isTyping) => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return;
        }

        try {
            const message = {
                type: "typing_indicator",
                data: {
                    is_typing: isTyping,
                    user_id: userId,
                    chat_id: chatId
                }
            };

            ws.current.send(JSON.stringify(message));
        } catch (error) {
            console.error('Error sending typing indicator:', error);
        }
    }, [chatId, userId]);

    // Send read receipt
    const sendReadReceipt = useCallback((messageId) => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return;
        }

        try {
            const message = {
                type: "read_receipt",
                data: {
                    message_id: messageId,
                    user_id: userId,
                    chat_id: chatId
                }
            };

            ws.current.send(JSON.stringify(message));
        } catch (error) {
            console.error('Error sending read receipt:', error);
        }
    }, [chatId, userId]);

    // Setup and cleanup
    useEffect(() => {
        if (token && chatId && userId) {
            connect();
        }

        return () => {
            if (ws.current) {
                console.log('Cleaning up WebSocket connection');
                ws.current.close();
            }
        };
    }, [connect, token, chatId, userId]);

    return {
        sendMessage,
        sendTypingIndicator,
        sendReadReceipt,
        ws: ws.current
    };
};

export default useWebSocket;