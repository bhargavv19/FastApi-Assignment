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
    console.log(currentUser);
    // Thread-related state
    const [selectedMessage, setSelectedMessage] = useState(null);
    const [threadMessages, setThreadMessages] = useState([]);
    const [threadOpen, setThreadOpen] = useState(false);
    const [threadNewMessage, setThreadNewMessage] = useState('');

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchChatData = async () => {
        try {
            setLoading(true);
            const chatData = await chatAPI.getChat(chatId);
            setChat(chatData);
            const messagesData = await messageAPI.getMessages(chatId);
            // Sort messages by created_at in ascending order (oldest to newest)
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

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim()) return;

        try {
            const messageData = {
                content: newMessage,
                message_type: "text", // or you can make this dynamic based on message type
                parent_message_id: null,
                chat_id: chatId
            };

            const response = await messageAPI.addMessage(chatId, messageData);
            setMessages(prev => [...prev, response]);
            setNewMessage('');
        } catch (err) {
            setError('Failed to send message');
        }
    };

    const handleMessageClick = async (message) => {
        setSelectedMessage(message);
        setThreadOpen(true);
        try {
            const threadData = await branchAPI.getBranches(chatId, message.id);
            console.log(threadData);
            setThreadMessages(threadData || []);
        } catch (err) {
            setError('Failed to load thread messages');
        }
    };

    const handleThreadSendMessage = async (e) => {
        e.preventDefault();
        if (!threadNewMessage.trim()) return;

        try {
            const messageData = {
                content: threadNewMessage,
                message_type: "text",
                parent_message_id: selectedMessage.id,
                chat_id: chatId
            };

            const response = await messageAPI.addMessage(chatId, messageData);
            setThreadMessages(prev => [...prev, response]);
            setThreadNewMessage('');
        } catch (err) {
            setError('Failed to send thread message');
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
                            <div ref={messagesEndRef} />
                        </List>
                    </Paper>

                    <Box component="form" onSubmit={handleSendMessage} sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            placeholder="Type your message..."
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
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