import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Container,
    Box,
    Typography,
    Button,
    Grid,
    Card,
    CardContent,
    CardActions,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Paper,
    Divider,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    OutlinedInput,
    CircularProgress,
    Stack
} from '@mui/material';
import {
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    ChatBubbleOutline as ChatBubbleOutlineIcon,
    Group as GroupIcon
} from '@mui/icons-material';
import { chatAPI, authAPI } from '../services/api';

const ChatList = () => {
    const navigate = useNavigate();
    const [chats, setChats] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [openDialog, setOpenDialog] = useState(false);
    const [editingChat, setEditingChat] = useState(null);
    const [chatName, setChatName] = useState('');
    const [selectedUsers, setSelectedUsers] = useState([]);

    const fetchUsers = async () => {
        try {
            const response = await authAPI.getUsers();
            setUsers(response || []);
        } catch (err) {
            setError('Failed to fetch users');
        }
    };

    const fetchChats = async () => {
        try {
            const response = await chatAPI.getChats();
            setChats(response || []);
            setError('');
        } catch (err) {
            setError('Failed to fetch chats');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchChats();
        fetchUsers();
    }, []);

    const handleCreateChat = async () => {
        try {
            await chatAPI.createChat(chatName, 'single', true, selectedUsers);
            setOpenDialog(false);
            setChatName('');
            setSelectedUsers([]);
            fetchChats();
        } catch (err) {
            setError('Failed to create chat');
        }
    };

    const handleUpdateChat = async () => {
        if (!editingChat) return;
        try {
            await chatAPI.updateChat(editingChat.id, { name: chatName });
            setOpenDialog(false);
            setEditingChat(null);
            setChatName('');
            setSelectedUsers([]);
            fetchChats();
        } catch (err) {
            setError('Failed to update chat');
        }
    };

    const handleDeleteChat = async (chatId) => {
        try {
            await chatAPI.deleteChat(chatId);
            fetchChats();
        } catch (err) {
            setError('Failed to delete chat');
        }
    };

    const handleOpenDialog = (chat) => {
        if (chat) {
            setEditingChat(chat);
            setChatName(chat.name);
        } else {
            setEditingChat(null);
            setChatName('');
            setSelectedUsers([]);
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingChat(null);
        setChatName('');
        setSelectedUsers([]);
    };

    const handleUserChange = (event) => {
        const {
            target: { value },
        } = event;
        setSelectedUsers(
            typeof value === 'string' ? value.split(',') : value,
        );
    };

    return (
        <Container maxWidth="md" sx={{ minHeight: '100vh', py: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Typography variant="h4" component="h1" fontWeight={700}>
                    My Chats
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => handleOpenDialog()}
                    sx={{ borderRadius: 2, boxShadow: 1 }}
                >
                    New Chat
                </Button>
            </Box>

            {error && (
                <Typography color="error" sx={{ mb: 2 }}>
                    {error}
                </Typography>
            )}

            <Box>
                {loading ? (
                    <Stack alignItems="center" sx={{ py: 8 }}>
                        <CircularProgress size={48} />
                        <Typography variant="body1" sx={{ mt: 2 }}>Loading chats...</Typography>
                    </Stack>
                ) : chats.length === 0 ? (
                    <Stack alignItems="center" sx={{ py: 8, color: 'text.secondary' }}>
                        <ChatBubbleOutlineIcon sx={{ fontSize: 64, mb: 2 }} />
                        <Typography variant="h6" fontWeight={500}>No chats found</Typography>
                        <Typography variant="body2" sx={{ mb: 2 }}>Create a new chat to get started!</Typography>
                        <Button
                            variant="outlined"
                            startIcon={<AddIcon />}
                            onClick={() => handleOpenDialog()}
                        >
                            New Chat
                        </Button>
                    </Stack>
                ) : (
                    <Grid container spacing={3}>
                        {chats.map((chat) => (
                            <Grid item xs={12} sm={12} md={12} key={chat.id} sx={{ width: '100%' }}>
                                <Card
                                    sx={{
                                        position: 'relative',
                                        cursor: 'pointer',
                                        transition: 'box-shadow 0.2s',
                                        '&:hover': { boxShadow: 6 },
                                        minHeight: 170,
                                        width: '100%'
                                    }}
                                    onClick={() => navigate(`/chat/${chat.id}`)}
                                >
                                    <CardContent>
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                            {chat.type === 'group' ? (
                                                <GroupIcon color="primary" sx={{ mr: 1 }} />
                                            ) : (
                                                <ChatBubbleOutlineIcon color="primary" sx={{ mr: 1 }} />
                                            )}
                                            <Typography variant="h6" fontWeight={600} noWrap>
                                                {chat.name}
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                            Type: {chat.type.charAt(0).toUpperCase() + chat.type.slice(1)} | Status: {chat.is_active ? 'Active' : 'Inactive'}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Created: {new Date(chat.created_at).toLocaleString()}
                                        </Typography>
                                    </CardContent>
                                    <CardActions sx={{ position: 'absolute', top: 8, right: 8 }}>
                                        <IconButton
                                            aria-label="edit"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleOpenDialog(chat);
                                            }}
                                            sx={{ bgcolor: 'background.paper', boxShadow: 1, mr: 1, '&:hover': { bgcolor: 'primary.light' } }}
                                            size="small"
                                        >
                                            <EditIcon fontSize="small" />
                                        </IconButton>
                                        <IconButton
                                            aria-label="delete"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteChat(chat.id);
                                            }}
                                            sx={{ bgcolor: 'background.paper', boxShadow: 1, '&:hover': { bgcolor: 'error.light' } }}
                                            size="small"
                                        >
                                            <DeleteIcon fontSize="small" />
                                        </IconButton>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>

            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                <DialogTitle sx={{ fontWeight: 700, pb: 0 }}>
                    {editingChat ? 'Edit Chat' : 'Create New Chat'}
                </DialogTitle>
                <DialogContent sx={{ pt: 2 }}>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Chat Name"
                        fullWidth
                        value={chatName}
                        onChange={(e) => setChatName(e.target.value)}
                        sx={{ mb: 3 }}
                    />
                    {!editingChat && (
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel id="users-label">Select Participants</InputLabel>
                            <Select
                                labelId="users-label"
                                multiple
                                value={selectedUsers}
                                onChange={handleUserChange}
                                input={<OutlinedInput label="Select Participants" />}
                                renderValue={(selected) => (
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {selected.map((value) => {
                                            const user = users.find(u => u.id === value);
                                            return (
                                                <Chip key={value} label={user?.username || value} />
                                            );
                                        })}
                                    </Box>
                                )}
                            >
                                {users.map((user) => (
                                    <MenuItem key={user.id} value={user.id}>
                                        {user.username}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    )}
                </DialogContent>
                <DialogActions sx={{ px: 3, pb: 2, pt: 0 }}>
                    <Button onClick={handleCloseDialog} variant="outlined">Cancel</Button>
                    <Button
                        onClick={editingChat ? handleUpdateChat : handleCreateChat}
                        variant="contained"
                        disabled={!chatName || (!editingChat && selectedUsers.length === 0)}
                    >
                        {editingChat ? 'Update' : 'Create'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default ChatList; 