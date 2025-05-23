import { useEffect, useRef, useCallback } from 'react';

const useWebSocket = (chatId, token) => {
    const ws = useRef(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    const connect = useCallback(() => {
        const wsUrl = `ws://747b-103-105-234-210.ngrok-free.app/api/v1/ws/chat/${chatId}?token=${token}`;
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log('WebSocket Connected');
            reconnectAttempts.current = 0;
        };

        ws.current.onclose = () => {
            console.log('WebSocket Disconnected');
            if (reconnectAttempts.current < maxReconnectAttempts) {
                reconnectAttempts.current++;
                setTimeout(() => {
                    console.log(`Reconnecting... Attempt ${reconnectAttempts.current}`);
                    connect();
                }, Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000));
            }
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };
    }, [chatId, token]);

    const sendMessage = useCallback((content, parentMessageId = null) => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket is not connected');
        }

        const message = {
            type: "send_message",
            data: {
                content,
                message_type: "text",
                parent_message_id: parentMessageId
            }
        };

        ws.current.send(JSON.stringify(message));
    }, []);

    const sendTypingIndicator = useCallback((isTyping, userId) => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;

        const message = {
            type: "typing_indicator",
            data: {
                is_typing: isTyping,
                user_id: userId
            }
        };

        ws.current.send(JSON.stringify(message));
    }, []);

    const sendReadReceipt = useCallback((messageId, userId) => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;

        const message = {
            type: "read_receipt",
            data: {
                message_id: messageId,
                user_id: userId
            }
        };

        ws.current.send(JSON.stringify(message));
    }, []);

    useEffect(() => {
        connect();

        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [connect]);

    return {
        sendMessage,
        sendTypingIndicator,
        sendReadReceipt,
        ws: ws.current
    };
};

export default useWebSocket; 