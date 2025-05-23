import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Container,
    Typography,
    Box,
    Paper,
    TextField,
    Button,
    IconButton,
    List,
    ListItem,
    Divider,
    CircularProgress,
    Alert,
    Menu,
    MenuItem,
    Drawer,
} from '@mui/material';
import {
    Send as SendIcon,
    ArrowBack as BackIcon,
    Close as CloseIcon,
} from '@mui/icons-material';
import { chatAPI, messageAPI, branchAPI, authAPI } from '../services/api';
import useWebSocket from '../hooks/useWebSocket';

const ChatRoom = () => {
    const { chatId } = useParams();
    const navigate = useNavigate();
    const [chat, setChat] = useState(null);
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const messagesEndRef = useRef(null);
    const currentUser = JSON.parse(localStorage.getItem('user')) || null;
    const [isTyping, setIsTyping] = useState(false);
    const [typingUsers, setTypingUsers] = useState(new Set());

    // Thread-related state
    const [selectedMessage, setSelectedMessage] = useState(null);
    const [threadMessages, setThreadMessages] = useState([]);
    const [threadOpen, setThreadOpen] = useState(false);
    const [threadNewMessage, setThreadNewMessage] = useState('');

    // Get token from localStorage or your auth system
    const token = localStorage.getItem('token');
    const { sendMessage, sendTypingIndicator, sendReadReceipt, ws } = useWebSocket(chatId, token);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchChatData = async () => {
        try {
            setLoading(true);
            const chatData = await chatAPI.getChat(chatId);
            setChat(chatData);
            const messagesData = await messageAPI.getMessages(chatId);
            const sortedMessages = messagesData ? [...messagesData].sort((a, b) =>
                new Date(a.created_at) - new Date(b.created_at)
            ) : [];
            setMessages(sortedMessages);
            setError('');
        } catch (err) {
            setError('Failed to load chat data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchChatData();
    }, [chatId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // WebSocket message handler
    useEffect(() => {
        if (!ws) return;

        const handleMessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                switch (data.type) {
                    case 'new_message':
                        setMessages(prev => [...prev, data.data]);
                        sendReadReceipt(data.data.id, currentUser?.id);
                        break;
                    case 'typing_indicator':
                        if (data.data.is_typing) {
                            setTypingUsers(prev => new Set([...prev, data.data.user_id]));
                        } else {
                            setTypingUsers(prev => {
                                const newSet = new Set(prev);
                                newSet.delete(data.data.user_id);
                                return newSet;
                            });
                        }
                        break;
                    case 'read_receipt':
                        setMessages(prev => prev.map(msg =>
                            msg.id === data.data.message_id
                                ? { ...msg, read_by: [...(msg.read_by || []), data.data.user_id] }
                                : msg
                        ));
                        break;
                    default:
                        console.log('Unknown message type:', data.type);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.addEventListener('message', handleMessage);
        return () => ws.removeEventListener('message', handleMessage);
    }, [ws, currentUser?.id, sendReadReceipt]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim()) return;

        try {
            sendMessage(newMessage);
            setNewMessage('');
            setIsTyping(false);
            sendTypingIndicator(false, currentUser?.id);
        } catch (err) {
            setError('Failed to send message');
        }
    };

    const handleThreadSendMessage = async (e) => {
        e.preventDefault();
        if (!threadNewMessage.trim()) return;

        try {
            sendMessage(threadNewMessage, selectedMessage.id);
            setThreadNewMessage('');
        } catch (err) {
            setError('Failed to send thread message');
        }
    };

    const handleMessageClick = async (message) => {
        setSelectedMessage(message);
        setThreadOpen(true);
        try {
            const threadData = await branchAPI.getBranches(chatId, message.id);
            setThreadMessages(threadData || []);
        } catch (err) {
            setError('Failed to load thread messages');
        }
    };

    const handleTyping = () => {
        if (!isTyping) {
            setIsTyping(true);
            sendTypingIndicator(true, currentUser?.id);
        }
    };

    if (loading) {
        return (
            <Container>
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Box
            sx={{
                width: '100%',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            }}
        >
            <Container maxWidth="sm" sx={{ p: 0 }}>
                <Paper
                    elevation={6}
                    sx={{
                        borderRadius: 4,
                        boxShadow: 6,
                        p: { xs: 2, sm: 4 },
                        background: '#fff',
                        minHeight: { xs: '70vh', sm: '70vh' },
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <IconButton onClick={() => navigate('/chats')} sx={{ mr: 2 }}>
                            <BackIcon />
                        </IconButton>
                        <Typography variant="h5" component="h1" fontWeight={700}>
                            {chat?.name || 'Chat Room'}
                        </Typography>
                        <Typography variant="subtitle2" color="text.secondary" sx={{ ml: 2 }}>
                            {chat?.type === 'single' ? 'Single Chat' : 'Group Chat'}
                        </Typography>
                    </Box>

                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    <Paper
                        elevation={0}
                        sx={{
                            flex: 1,
                            height: '45vh',
                            overflowY: 'auto',
                            mb: 2,
                            p: 2,
                            background: '#f9fafb',
                            borderRadius: 2,
                        }}
                    >
                        <List>
                            {messages.map((message, index) => {
                                const isCurrentUser = message.sender_id === currentUser?.id;
                                return (
                                    <React.Fragment key={index}>
                                        <ListItem
                                            sx={{
                                                flexDirection: 'column',
                                                alignItems: isCurrentUser ? 'flex-end' : 'flex-start',
                                                px: 0,
                                                '&:hover': {
                                                    background: '#f0f0f0',
                                                    borderRadius: 1,
                                                },
                                            }}
                                            onClick={() => handleMessageClick(message)}
                                        >
                                            <Box
                                                sx={{
                                                    maxWidth: '70%',
                                                    backgroundColor: isCurrentUser ? '#dcf8c6' : '#ffffff',
                                                    borderRadius: 2,
                                                    p: 1.5,
                                                    boxShadow: 1,
                                                }}
                                            >
                                                {!isCurrentUser && (
                                                    <Typography
                                                        variant="subtitle2"
                                                        color="text.secondary"
                                                        sx={{ mb: 0.5 }}
                                                    >
                                                        {message.sender?.username || 'Unknown User'}
                                                    </Typography>
                                                )}
                                                <Typography variant="body1" sx={{ mb: 0.5 }}>
                                                    {message.content}
                                                </Typography>
                                                <Box sx={{
                                                    display: 'flex',
                                                    justifyContent: isCurrentUser ? 'flex-end' : 'flex-start',
                                                    alignItems: 'center',
                                                    gap: 1
                                                }}>
                                                    <Typography
                                                        variant="caption"
                                                        color="text.secondary"
                                                    >
                                                        {new Date(message.created_at).toLocaleString()}
                                                    </Typography>
                                                    {isCurrentUser && message.read_by && (
                                                        <Typography
                                                            variant="caption"
                                                            color="text.secondary"
                                                            sx={{
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                gap: 0.5
                                                            }}
                                                        >
                                                            {message.read_by.length > 0 ? '✓✓' : '✓'}
                                                        </Typography>
                                                    )}
                                                </Box>
                                            </Box>
                                        </ListItem>
                                        <Divider />
                                    </React.Fragment>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </List>
                    </Paper>

                    {typingUsers.size > 0 && (
                        <Box sx={{
                            mb: 1,
                            px: 2,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1
                        }}>
                            <Typography variant="caption" color="text.secondary">
                                {Array.from(typingUsers).map(userId => {
                                    const user = chat?.participants?.find(p => p.id === userId);
                                    return user?.username || 'Someone';
                                }).join(', ')}
                                {typingUsers.size === 1 ? ' is' : ' are'} typing...
                            </Typography>
                            <Box sx={{
                                display: 'flex',
                                gap: 0.5,
                                animation: 'typing 1s infinite'
                            }}>
                                <Box sx={{
                                    width: 4,
                                    height: 4,
                                    borderRadius: '50%',
                                    bgcolor: 'text.secondary',
                                    animation: 'typing 1s infinite 0.2s'
                                }} />
                                <Box sx={{
                                    width: 4,
                                    height: 4,
                                    borderRadius: '50%',
                                    bgcolor: 'text.secondary',
                                    animation: 'typing 1s infinite 0.4s'
                                }} />
                                <Box sx={{
                                    width: 4,
                                    height: 4,
                                    borderRadius: '50%',
                                    bgcolor: 'text.secondary',
                                    animation: 'typing 1s infinite 0.6s'
                                }} />
                            </Box>
                        </Box>
                    )}

                    <Box component="form" onSubmit={handleSendMessage} sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            placeholder="Type your message..."
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            onKeyPress={handleTyping}
                            sx={{ background: '#f5f7fa', borderRadius: 2 }}
                        />
                        <Button
                            type="submit"
                            variant="contained"
                            endIcon={<SendIcon />}
                            disabled={!newMessage.trim()}
                            sx={{ minWidth: 80, borderRadius: 2, boxShadow: 2 }}
                        >
                            Send
                        </Button>
                    </Box>

                    <style>
                        {`
                            @keyframes typing {
                                0%, 100% { transform: translateY(0); }
                                50% { transform: translateY(-4px); }
                            }
                        `}
                    </style>
                </Paper>
            </Container>

            {/* Thread Sidebar */}
            <Drawer
                anchor="right"
                open={threadOpen}
                onClose={() => setThreadOpen(false)}
                sx={{
                    '& .MuiDrawer-paper': {
                        width: { xs: '100%', sm: 400 },
                        boxSizing: 'border-box',
                        p: 2,
                    },
                }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <IconButton onClick={() => setThreadOpen(false)} sx={{ mr: 2 }}>
                        <CloseIcon />
                    </IconButton>
                    <Typography variant="h6">Thread</Typography>
                </Box>

                <Paper
                    elevation={0}
                    sx={{
                        flex: 1,
                        height: 'calc(100vh - 200px)',
                        overflowY: 'auto',
                        mb: 2,
                        p: 2,
                        background: '#f9fafb',
                        borderRadius: 2,
                    }}
                >
                    <List>
                        {threadMessages.map((message, index) => {
                            const isCurrentUser = message.sender_id === currentUser?.id;
                            return (
                                <React.Fragment key={index}>
                                    <ListItem
                                        sx={{
                                            flexDirection: 'column',
                                            alignItems: isCurrentUser ? 'flex-end' : 'flex-start',
                                            px: 0,
                                            '&:hover': {
                                                background: '#f0f0f0',
                                                borderRadius: 1,
                                            },
                                        }}
                                    >
                                        <Box
                                            sx={{
                                                maxWidth: '70%',
                                                backgroundColor: isCurrentUser ? '#dcf8c6' : '#ffffff',
                                                borderRadius: 2,
                                                p: 1.5,
                                                boxShadow: 1,
                                            }}
                                        >
                                            {!isCurrentUser && (
                                                <Typography
                                                    variant="subtitle2"
                                                    color="text.secondary"
                                                    sx={{ mb: 0.5 }}
                                                >
                                                    {message.sender?.username || 'Unknown User'}
                                                </Typography>
                                            )}
                                            <Typography variant="body1" sx={{ mb: 0.5 }}>
                                                {message.content}
                                            </Typography>
                                            <Typography
                                                variant="caption"
                                                color="text.secondary"
                                                sx={{
                                                    mt: 0.5,
                                                    display: 'block',
                                                    textAlign: isCurrentUser ? 'right' : 'left'
                                                }}
                                            >
                                                {new Date(message.created_at).toLocaleString()}
                                            </Typography>
                                        </Box>
                                    </ListItem>
                                    <Divider />
                                </React.Fragment>
                            );
                        })}
                    </List>
                </Paper>

                <Box component="form" onSubmit={handleThreadSendMessage} sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                        fullWidth
                        variant="outlined"
                        placeholder="Reply to thread..."
                        value={threadNewMessage}
                        onChange={(e) => setThreadNewMessage(e.target.value)}
                        sx={{ background: '#f5f7fa', borderRadius: 2 }}
                    />
                    <Button
                        type="submit"
                        variant="contained"
                        endIcon={<SendIcon />}
                        disabled={!threadNewMessage.trim()}
                        sx={{ minWidth: 80, borderRadius: 2, boxShadow: 2 }}
                    >
                        Reply
                    </Button>
                </Box>
            </Drawer>
        </Box>
    );
};

export default ChatRoom; 